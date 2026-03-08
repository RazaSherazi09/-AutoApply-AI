import asyncio
from app.api.routes.jobs import _run_scrape
import sys

# Ensure logs go to stdout
from loguru import logger
logger.add(sys.stdout, colorize=True)

async def main():
    print("Triggering smart contextual scrape for user ID 6...")
    await _run_scrape(6)
    print("Scrape completed.")

if __name__ == "__main__":
    asyncio.run(main())
