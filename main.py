#!/usr/bin/env python3
"""
Daily News Aggregation Script
Fetches headlines from news sources via RSS feeds and sends email digest
"""

import logging
import sys
from datetime import datetime
import pytz
from scrapers import NewsScrapers
from email_sender import EmailSender

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main function to orchestrate news fetching and email sending"""
    try:
        ankara_tz = pytz.timezone('Europe/Istanbul')
        current_time = datetime.now(ankara_tz)
        logger.info(f"Starting daily news aggregation at {current_time.strftime('%Y-%m-%d %H:%M %Z')}")

        scrapers = NewsScrapers()
        email_sender = EmailSender()

        all_headlines = {}

        # NY Times (RSS feeds - most reliable)
        logger.info("Fetching NY Times...")
        nyt_headlines = scrapers.fetch_nytimes()
        if nyt_headlines:
            all_headlines['NEW YORK TIMES'] = nyt_headlines
            total = sum(len(h) for h in nyt_headlines.values())
            logger.info(f"Fetched {total} NY Times headlines")

        # Globe and Mail (RSS feeds)
        logger.info("Fetching Globe and Mail...")
        globe_headlines = scrapers.fetch_globe_and_mail()
        if globe_headlines:
            all_headlines['GLOBE AND MAIL'] = globe_headlines
            total = sum(len(h) for h in globe_headlines.values())
            logger.info(f"Fetched {total} Globe and Mail headlines")

        # La Presse (RSS feeds - switching from web scraping)
        logger.info("Fetching La Presse...")
        lapresse_headlines = scrapers.fetch_lapresse()
        if lapresse_headlines:
            all_headlines['LA PRESSE'] = lapresse_headlines
            total = sum(len(h) for h in lapresse_headlines.values())
            logger.info(f"Fetched {total} La Presse headlines")

        # Axios (RSS feed)
        logger.info("Fetching Axios...")
        axios_headlines = scrapers.fetch_axios()
        if axios_headlines:
            all_headlines['AXIOS'] = {'Top Stories': axios_headlines}
            logger.info(f"Fetched {len(axios_headlines)} Axios headlines")

        # Substack accounts (24-hour window)
        logger.info("Checking Substacks...")
        substack_accounts = [
            'everydayai',
            'understandingai',
            'aisnakeoil',
            'darioamodei',
            'sineadbovell'
        ]
        substack_posts = scrapers.fetch_substacks(substack_accounts, hours=24)
        all_headlines['SUBSTACK'] = {'AI Writers': substack_posts if substack_posts else []}
        if substack_posts:
            logger.info(f"Found {len(substack_posts)} recent Substack posts")
        else:
            logger.info("No recent Substack posts")

        # Podcasts (48-hour window)
        logger.info("Checking Podcasts...")
        podcast_feeds = {
            'The Cognitive Revolution': 'https://feeds.megaphone.fm/RINTP3108857801',
            'Ezra Klein Show': 'https://feeds.simplecast.com/82FI35Px'
        }
        podcast_episodes = scrapers.fetch_podcasts(podcast_feeds, hours=48)
        all_headlines['PODCASTS'] = {'New Episodes': podcast_episodes if podcast_episodes else []}
        if podcast_episodes:
            logger.info(f"Found {len(podcast_episodes)} recent podcast episodes")
        else:
            logger.info("No recent podcast episodes")

        # Send email
        if not all_headlines:
            logger.error("No headlines fetched from any source")
            return 1

        logger.info("Sending email digest...")
        success = email_sender.send_daily_digest(all_headlines)

        if success:
            logger.info("Daily news digest sent successfully!")
            return 0
        else:
            logger.error("Failed to send email")
            return 1

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
