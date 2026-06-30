import asyncio
from app.scraper_meusanimes import scrape_meusanimes_episodes, scrape_meusanimes_episode_video

async def run():
    url = "https://meusanimes.blog/a/avatar-aang-the-last-airbender-2026/"
    _, _, _, eps = await scrape_meusanimes_episodes(url)
    for ep in eps:
        print(f"\nChecking {ep['page_url']}")
        stream, media, thumb, desc = await scrape_meusanimes_episode_video(ep['page_url'])
        print(f"Result: {stream} ({media})")

asyncio.run(run())
