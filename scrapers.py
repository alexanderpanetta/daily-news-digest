"""
News fetching via RSS feeds - reliable and respectful of source sites
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
import feedparser
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class NewsScrapers:
    """RSS-based news fetchers for various sources"""

    def __init__(self):
        self.max_headlines = 6

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and clean text"""
        if not text:
            return ""
        soup = BeautifulSoup(text, 'html.parser')
        clean = soup.get_text()
        clean = ' '.join(clean.split())
        return clean.strip()

    def _truncate(self, text: str, length: int = 200) -> str:
        """Truncate text to specified length"""
        if not text or len(text) <= length:
            return text
        return text[:length].rsplit(' ', 1)[0] + "..."

    def _parse_feed(self, url: str, max_items: int = 6) -> list:
        """Parse RSS feed and return entries"""
        try:
            feed = feedparser.parse(url)
            if feed.bozo and not feed.entries:
                logger.warning(f"Feed parse error for {url}: {feed.bozo_exception}")
                return []
            return feed.entries[:max_items]
        except Exception as e:
            logger.error(f"Error parsing feed {url}: {e}")
            return []

    def _entry_to_headline(self, entry, include_summary: bool = True) -> Optional[dict]:
        """Convert feed entry to headline dict"""
        title = entry.get('title', '').strip()
        link = entry.get('link', '').strip()

        if not title:
            return None

        headline = {
            'title': self._clean_html(title),
            'url': link,
            'summary': ''
        }

        if include_summary:
            summary = entry.get('summary', '') or entry.get('description', '')
            if summary:
                headline['summary'] = self._truncate(self._clean_html(summary), 200)

        return headline

    def fetch_nytimes(self) -> dict:
        """Fetch NY Times headlines via official RSS feeds"""
        feeds = {
            'Top Stories': 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
            'World': 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
            'Opinion': 'https://rss.nytimes.com/services/xml/rss/nyt/Opinion.xml'
        }

        all_headlines = {}
        for section, url in feeds.items():
            try:
                entries = self._parse_feed(url, self.max_headlines)
                headlines = []
                for entry in entries:
                    headline = self._entry_to_headline(entry)
                    if headline:
                        headlines.append(headline)

                if headlines:
                    all_headlines[section] = headlines
                    logger.info(f"NY Times {section}: {len(headlines)} headlines")

            except Exception as e:
                logger.error(f"Error fetching NY Times {section}: {e}")

        return all_headlines

    def fetch_globe_and_mail(self) -> dict:
        """Fetch Globe and Mail headlines via RSS feeds"""
        feeds = {
            'Canada': 'https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/canada/',
            'Politics': 'https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/politics/',
            'Opinion': 'https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/opinion/'
        }

        all_headlines = {}
        for section, url in feeds.items():
            try:
                entries = self._parse_feed(url, 4)
                headlines = []
                for entry in entries:
                    headline = self._entry_to_headline(entry)
                    if headline:
                        headlines.append(headline)

                if headlines:
                    all_headlines[section] = headlines
                    logger.info(f"Globe and Mail {section}: {len(headlines)} headlines")

            except Exception as e:
                logger.error(f"Error fetching Globe and Mail {section}: {e}")

        return all_headlines

    def fetch_lapresse(self) -> dict:
        """Fetch La Presse headlines via RSS feeds"""
        # La Presse RSS feeds
        feeds = {
            'Actualités': 'https://www.lapresse.ca/actualites/rss',
            'International': 'https://www.lapresse.ca/international/rss',
            'Affaires': 'https://www.lapresse.ca/affaires/rss'
        }

        all_headlines = {}
        for section, url in feeds.items():
            try:
                entries = self._parse_feed(url, self.max_headlines)
                headlines = []
                for entry in entries:
                    headline = self._entry_to_headline(entry)
                    if headline:
                        headlines.append(headline)

                if headlines:
                    all_headlines[section] = headlines
                    logger.info(f"La Presse {section}: {len(headlines)} headlines")

            except Exception as e:
                logger.error(f"Error fetching La Presse {section}: {e}")

        return all_headlines

    def fetch_axios(self) -> list:
        """Fetch Axios headlines via RSS feed"""
        try:
            # Axios main RSS feed
            url = 'https://api.axios.com/feed/'
            entries = self._parse_feed(url, self.max_headlines)

            headlines = []
            for entry in entries:
                headline = self._entry_to_headline(entry)
                if headline:
                    headlines.append(headline)

            logger.info(f"Axios: {len(headlines)} headlines")
            return headlines

        except Exception as e:
            logger.error(f"Error fetching Axios: {e}")
            return []

    def fetch_substacks(self, usernames: list, hours: int = 24) -> list:
        """Fetch recent posts from specific Substack accounts"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_posts = []

        for username in usernames:
            try:
                feed_url = f"https://{username}.substack.com/feed"
                feed = feedparser.parse(feed_url)

                if not feed.entries:
                    continue

                for entry in feed.entries:
                    pub_date = self._parse_date(entry)
                    if not pub_date:
                        continue

                    if pub_date > cutoff:
                        title = entry.get('title', '').strip()
                        link = entry.get('link', '').strip()

                        if title:
                            recent_posts.append({
                                'title': f"@{username}: {title}",
                                'url': link,
                                'summary': f"Posted {pub_date.strftime('%b %d at %H:%M')}"
                            })
                            logger.info(f"Found Substack post from @{username}: {title[:50]}...")

            except Exception as e:
                logger.error(f"Error fetching Substack @{username}: {e}")

        return recent_posts

    def fetch_podcasts(self, feeds: dict, hours: int = 48) -> list:
        """Fetch recent podcast episodes"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_episodes = []

        for podcast_name, feed_url in feeds.items():
            try:
                feed = feedparser.parse(feed_url)

                if not feed.entries:
                    continue

                for entry in feed.entries:
                    pub_date = self._parse_date(entry)
                    if not pub_date:
                        continue

                    if pub_date > cutoff:
                        title = entry.get('title', '').strip()
                        link = entry.get('link', '').strip()

                        if title:
                            recent_episodes.append({
                                'title': f"{podcast_name}: {title}",
                                'url': link,
                                'summary': f"Published {pub_date.strftime('%b %d')}"
                            })
                            logger.info(f"Found episode from {podcast_name}: {title[:50]}...")

            except Exception as e:
                logger.error(f"Error fetching podcast {podcast_name}: {e}")

        return recent_episodes

    def _parse_date(self, entry) -> Optional[datetime]:
        """Parse publication date from feed entry"""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])

            if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6])

            if hasattr(entry, 'published') and entry.published:
                import email.utils
                parsed = email.utils.parsedate_tz(entry.published)
                if parsed:
                    return datetime(*parsed[:6])

        except Exception as e:
            logger.debug(f"Could not parse date: {e}")

        return None
