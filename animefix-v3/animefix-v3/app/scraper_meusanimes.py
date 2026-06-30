import asyncio
import os
import random
import logging
import re
import httpx
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from typing import Tuple, Optional, List, Dict

logger = logging.getLogger(__name__)

# User Agent settings
ua_provider = UserAgent(os='linux', browsers=['chrome'])

def get_session():
    """Returns an httpx client with standard headers to bypass basic bot detection."""
    return httpx.AsyncClient(
        follow_redirects=True, 
        verify=False,
        headers={
            "User-Agent": ua_provider.random,
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://meusanimes.blog/"
        },
        timeout=15
    )

async def get_jikan_info(anime_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Queries the Jikan API (MyAnimeList) to fetch a high-resolution poster and MAL URL.
    Returns: (poster_url, mal_url)
    """
    try:
        clean_name = re.sub(r'\(\d+\)', '', anime_name).strip()
        
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"https://api.jikan.moe/v4/anime?q={clean_name}&limit=1"
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('data') and len(data['data']) > 0:
                    anime_data = data['data'][0]
                    mal_url = anime_data.get('url') # Link to MAL page
                    
                    images = anime_data.get('images', {})
                    webp = images.get('webp', {})
                    jpg = images.get('jpg', {})
                    poster_url = webp.get('large_image_url') or jpg.get('large_image_url')
                    return poster_url, mal_url
    except Exception as e:
        logger.warning(f"Failed to fetch info from Jikan for '{anime_name}': {e}")
    return None, None

async def scrape_meusanimes_episodes(anime_url: str):
    """
    Scrapes the anime main page from meusanimes.blog to extract episodes.
    """
    anime_name = "Unknown Anime"
    poster_url = None
    description = None
    episodes = []
    
    async with get_session() as client:
        try:
            logger.info(f"Loading anime page from meusanimes.blog: {anime_url}")
            resp = await client.get(anime_url)
            if resp.status_code != 200:
                logger.error(f"Failed to load anime page, status: {resp.status_code}")
                return anime_name, poster_url, description, episodes
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # Extract anime name
            h1 = soup.find('h1')
            if h1:
                anime_name = h1.text.strip()
            
            # Extract poster URL
            poster_img = soup.select_one('.poster img')
            if poster_img and poster_img.get('src'):
                poster_url = poster_img['src']
            
            # Extract description
            desc_container = soup.select_one('.wp-content, .resume')
            if desc_container:
                description = desc_container.text.strip()
            
            # Extract episodes list
            season_containers = soup.select('#seasons .se-c, #seasons .temporada')
            
            if season_containers:
                for s_idx, container in enumerate(season_containers):
                    season_num = s_idx + 1
                    season_title = container.find(['h3', 'span', 'div'], class_='title')
                    if season_title:
                        match = re.search(r'(\d+)', season_title.text)
                        if match: season_num = int(match.group(1))
                    
                    episode_items = container.select('.episodios li')
                    for ep_item in episode_items:
                        ep_link = ep_item.select_one('a.episodiotitle')
                        if ep_link and ep_link.get('href'):
                            href = ep_link['href']
                            title = ep_link.text.strip()
                            # Extract episode number
                            number_part = href.strip('/').split('/')[-1]
                            # Try to extract number from title or URL
                            number = number_part
                            if 'episodio' in title.lower():
                                # Extract from title like "Episódio 1"
                                num_match = re.search(r'episódio\s*(\d+)', title.lower())
                                if num_match:
                                    number = num_match.group(1)
                            
                            episodes.append({
                                "number": str(number)[:10],
                                "season": season_num,
                                "title": title[:150],
                                "page_url": href
                            })
            
            # Fallback: look for episode links in page
            if not episodes:
                ep_links = soup.find_all('a', href=True)
                for link in ep_links:
                    href = link['href']
                    if '/e/' in href and href != anime_url and href.strip('/').endswith('/e') is False:
                        if href not in [ep['page_url'] for ep in episodes]:
                            title = link.text.strip() or "Episódio"
                            episodes.append({
                                "number": href.strip('/').split('/')[-1],
                                "season": 1,
                                "title": title[:150],
                                "page_url": href
                            })
                            
            episodes.sort(key=lambda x: (int(x['season']), float(x['number']) if x['number'].replace('.','').isdigit() else 0))
                
        except Exception as e:
            logger.error(f"Error in scrape_meusanimes_episodes: {e}")
            
    return anime_name, poster_url, description, episodes

async def scrape_meusanimes_episode_video(episode_page_url: str):
    """
    Captures video stream from the episode page on meusanimes.blog.
    Returns: (stream_url, media_type, thumb_url, description)
    """
    stream_url = None
    media_type = None
    thumb_url = None
    description = None

    async with get_session() as client:
        try:
            logger.info(f"Loading episode page: {episode_page_url}")
            resp = await client.get(episode_page_url)
            if resp.status_code != 200:
                return None, None, None, None
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # Extract metadata
            img_el = soup.select_one('.imagen img, .wp-content img')
            if img_el and img_el.get('src'):
                thumb_url = img_el['src']
                
            desc_el = soup.select_one('.wp-content, .resume')
            if desc_el:
                description = desc_el.text.strip()

            # Find iframe with video player
            iframe = soup.select_one('iframe[src]')
            if iframe and iframe.get('src'):
                src = iframe['src']
                
                # Extrair mp4 direto da API se for meusdoramas.club
                if 'serv01.meusdoramas.club/#/video/' in src:
                    try:
                        match = re.search(r'#/video/(\d+)/(\d+)/(\d+)', src)
                        if match:
                            tmdb, s, e = match.groups()
                            api_url = f"https://serv01.meusdoramas.club/posts/get-video.php?episode_number={e}&season_number={s}&tmdb={tmdb}"
                            resp = await client.get(api_url)
                            data = resp.json()
                            video_url = data.get("videoUrl")
                            
                            if video_url:
                                if "serv01.meusdoramas.club/e/" in video_url:
                                    resp2 = await client.get(video_url)
                                    match2 = re.search(r'iframe\.php\?[a-z]+=([^/\'"\n]+/[^/\'"\n]+/[^/\'"\n]+)', resp2.text)
                                    if match2:
                                        new_path = match2.group(1)
                                        tmdb2, s2, e2 = new_path.split('/')
                                        api_url2 = f"https://serv01.meusdoramas.club/posts/get-video.php?episode_number={e2}&season_number={s2}&tmdb={tmdb2}"
                                        resp3 = await client.get(api_url2)
                                        video_url = resp3.json().get("videoUrl")
                                        
                                if video_url and "video.meusdoramas.club/embed" in video_url:
                                    resp4 = await client.get(video_url)
                                    match_file = re.search(r'"file":\s*"([^"]+\.(?:mp4|m3u8)[^"]*)"', resp4.text)
                                    if match_file:
                                        extracted_url = match_file.group(1).replace('\\/', '/')
                                        src = extracted_url
                                    else:
                                        src = video_url.replace('\\/', '/')
                                elif video_url and "serv01.meusdoramas.club/e/" not in video_url:
                                    src = video_url.replace('\\/', '/')
                    except Exception as ex:
                        logger.warning(f"Falha ao extrair mp4 direto da API meusdoramas: {ex}")

                # Check if it's a valid video URL
                if any(domain in src for domain in ['meusdoramas.club', 'cdn', 'video', '.mp4', '.m3u8', 'blogger', 'youtube', 'blogspot']):
                    stream_url = src
                    # Determine media type
                    if '.m3u8' in src.lower():
                        media_type = '.m3u8'
                    elif '.mp4' in src.lower():
                        media_type = '.mp4'
                    elif 'youtube' in src.lower() or 'blogger' in src.lower() or 'blogspot' in src.lower():
                        media_type = 'youtube'
                    else:
                        # Default to iframe type
                        media_type = 'iframe'
                        
            # Fallback: Look for direct video links
            if not stream_url:
                video_links = soup.find_all('a', href=True)
                for link in video_links:
                    href = link['href']
                    if any(ext in href.lower() for ext in ['.mp4', '.m3u8', 'video/']):
                        stream_url = href
                        if '.m3u8' in href.lower():
                            media_type = '.m3u8'
                        else:
                            media_type = '.mp4'
                        break

        except Exception as e:
            logger.error(f"Error in scrape_meusanimes_episode_video: {e}")
            
    return stream_url, media_type, thumb_url, description