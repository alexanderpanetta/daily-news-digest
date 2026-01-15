"""
Google Analytics Data API integration for fetching visitor metrics
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class AnalyticsFetcher:
    """Fetches visitor data from Google Analytics 4 properties"""

    def __init__(self):
        # GA4 Property IDs for each website
        # These should be set as environment variables
        self.properties = {
            'Wandering Well': os.environ.get('GA_PROPERTY_WANDERING_WELL'),
            'Stock Market Calculator': os.environ.get('GA_PROPERTY_STOCK_CALCULATOR'),
            'Movie Algorithm': os.environ.get('GA_PROPERTY_MOVIE_ALGORITHM'),
            'AI for You': os.environ.get('GA_PROPERTY_AI_FOR_YOU'),
        }

        # Service account credentials JSON
        self.credentials_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')

    def _get_client(self):
        """Create GA4 Data API client with service account credentials"""
        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.oauth2 import service_account

            if not self.credentials_json:
                logger.error("GOOGLE_APPLICATION_CREDENTIALS_JSON not set")
                return None

            # Parse credentials from JSON string
            credentials_info = json.loads(self.credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=['https://www.googleapis.com/auth/analytics.readonly']
            )

            return BetaAnalyticsDataClient(credentials=credentials)

        except ImportError:
            logger.error("google-analytics-data package not installed")
            return None
        except Exception as e:
            logger.error(f"Error creating GA client: {e}")
            return None

    def _get_visitors_for_property(self, client, property_id: str) -> Optional[int]:
        """Fetch yesterday's unique visitors for a single property"""
        try:
            from google.analytics.data_v1beta.types import (
                RunReportRequest,
                DateRange,
                Metric,
            )

            # Get yesterday's date
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

            request = RunReportRequest(
                property=f"properties/{property_id}",
                date_ranges=[DateRange(start_date=yesterday, end_date=yesterday)],
                metrics=[Metric(name="activeUsers")],
            )

            response = client.run_report(request)

            if response.rows:
                return int(response.rows[0].metric_values[0].value)
            return 0

        except Exception as e:
            logger.error(f"Error fetching data for property {property_id}: {e}")
            return None

    def fetch_all_visitors(self) -> Optional[dict]:
        """Fetch yesterday's visitors for all configured properties"""
        # Check if any properties are configured
        configured_properties = {k: v for k, v in self.properties.items() if v}

        if not configured_properties:
            logger.warning("No GA4 properties configured")
            return None

        client = self._get_client()
        if not client:
            return None

        results = {}
        for site_name, property_id in configured_properties.items():
            visitors = self._get_visitors_for_property(client, property_id)
            if visitors is not None:
                results[site_name] = visitors
                logger.info(f"{site_name}: {visitors} unique visitors")
            else:
                logger.warning(f"Could not fetch data for {site_name}")

        return results if results else None

    def format_visitor_summary(self, visitors: dict) -> str:
        """Format visitor counts into a single summary line"""
        if not visitors:
            return ""

        # Order: Wandering Well, Stock Market Calculator, Movie Algorithm, AI for You
        site_order = ['Wandering Well', 'Stock Market Calculator', 'Movie Algorithm', 'AI for You']

        parts = []
        for site in site_order:
            if site in visitors:
                count = visitors[site]
                parts.append(f"{count:,} to {site}")

        if not parts:
            return ""

        # Join with commas and 'and' before the last item
        if len(parts) == 1:
            return f"{parts[0]} yesterday"
        elif len(parts) == 2:
            return f"{parts[0]} and {parts[1]} yesterday"
        else:
            return f"{', '.join(parts[:-1])} and {parts[-1]} yesterday"
