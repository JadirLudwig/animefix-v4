import asyncio
from app.scraper_meusanimes import scrape_meusanimes_episode_video

async def run():
    print("Testing correct episode URL")
    ep_url = "https://meusanimes.blog/e/avatar-aang-the-last-airbender-2026/"
    stream_url, media_type, thumb_url, ep_description = await scrape_meusanimes_episode_video(ep_url)
    print(f"Stream URL: {stream_url}")
    print(f"Media type: {media_type}")

asyncio.run(run())
