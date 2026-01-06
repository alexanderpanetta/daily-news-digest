"""
Email formatting and sending via Gmail
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)


class EmailSender:
    """Handles email formatting and sending via Gmail SMTP"""

    def __init__(self):
        self.gmail_user = os.environ.get('GMAIL_USER', '')
        self.gmail_password = os.environ.get('GMAIL_PASSWORD', '')
        self.recipient_email = os.environ.get('RECIPIENT_EMAIL', self.gmail_user)

        if not self.gmail_user or not self.gmail_password:
            raise ValueError(
                "Gmail credentials not configured. "
                "Set GMAIL_USER and GMAIL_PASSWORD environment variables."
            )

    def format_email_body(self, all_headlines: dict) -> tuple[str, str]:
        """Format headlines into plain text and HTML email bodies"""
        # Source display order
        source_order = [
            'NEW YORK TIMES',
            'LA PRESSE',
            'GLOBE AND MAIL',
            'AXIOS',
            'SUBSTACK',
            'PODCASTS'
        ]

        text_lines = []
        html_parts = ['<html><body style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; padding: 20px;">']

        ankara_tz = pytz.timezone('Europe/Istanbul')
        current_date = datetime.now(ankara_tz)
        date_str = current_date.strftime("%A, %B %d, %Y")

        html_parts.append(f'<h1 style="color: #333; border-bottom: 2px solid #333; padding-bottom: 10px;">Daily News Digest</h1>')
        html_parts.append(f'<p style="color: #666; margin-bottom: 30px;">{date_str}</p>')

        text_lines.append(f"DAILY NEWS DIGEST - {date_str}")
        text_lines.append("=" * 50)
        text_lines.append("")

        for source in source_order:
            if source not in all_headlines:
                continue

            sections = all_headlines[source]

            # Check if source has any content
            has_content = any(headlines for headlines in sections.values() if headlines)

            # Always show SUBSTACK and PODCASTS sections
            if not has_content and source not in ['SUBSTACK', 'PODCASTS']:
                continue

            # Source header
            text_lines.append(f"\n{source}")
            text_lines.append("-" * len(source))

            html_parts.append(f'<h2 style="color: #1a1a1a; margin-top: 30px; font-size: 18px; text-transform: uppercase; letter-spacing: 1px;">{source}</h2>')

            if not has_content:
                if source == 'SUBSTACK':
                    msg = "No new posts in the last 24 hours"
                else:
                    msg = "No new episodes in the last 48 hours"
                text_lines.append(f"  {msg}")
                html_parts.append(f'<p style="color: #888; font-style: italic; margin-left: 15px;">{msg}</p>')
                continue

            for section_name, headlines in sections.items():
                if not headlines:
                    continue

                # Show section name if multiple sections
                if len(sections) > 1:
                    text_lines.append(f"\n  {section_name}:")
                    html_parts.append(f'<h3 style="color: #555; font-size: 14px; margin: 15px 0 10px 0;">{section_name}</h3>')

                html_parts.append('<ul style="list-style: none; padding: 0; margin: 0;">')

                for headline in headlines:
                    title = headline.get('title', '')
                    url = headline.get('url', '')
                    summary = headline.get('summary', '')

                    if not title:
                        continue

                    # Plain text format
                    if url:
                        text_lines.append(f"  - {title}")
                        text_lines.append(f"    {url}")
                    else:
                        text_lines.append(f"  - {title}")

                    if summary:
                        text_lines.append(f"    {summary}")

                    # HTML format
                    html_parts.append('<li style="margin-bottom: 15px; padding-left: 15px; border-left: 3px solid #ddd;">')
                    if url:
                        html_parts.append(f'<a href="{url}" style="color: #0066cc; text-decoration: none; font-weight: bold;">{title}</a>')
                    else:
                        html_parts.append(f'<strong>{title}</strong>')

                    if summary:
                        html_parts.append(f'<br><span style="color: #666; font-size: 14px;">{summary}</span>')

                    html_parts.append('</li>')

                html_parts.append('</ul>')

            text_lines.append("")

        # Footer
        text_lines.append("\n" + "=" * 50)
        text_lines.append("Delivered by Daily News Digest")

        html_parts.append('<hr style="margin-top: 40px; border: none; border-top: 1px solid #ddd;">')
        html_parts.append('<p style="color: #999; font-size: 12px; text-align: center;">Delivered by Daily News Digest</p>')
        html_parts.append('</body></html>')

        return '\n'.join(text_lines), '\n'.join(html_parts)

    def get_subject(self) -> str:
        """Generate email subject with current date"""
        ankara_tz = pytz.timezone('Europe/Istanbul')
        current_date = datetime.now(ankara_tz)
        return f"Daily News Digest - {current_date.strftime('%B %d, %Y')}"

    def send_daily_digest(self, all_headlines: dict) -> bool:
        """Send the daily news digest email"""
        try:
            if not all_headlines:
                logger.warning("No headlines to send")
                return False

            subject = self.get_subject()
            text_body, html_body = self.format_email_body(all_headlines)

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.gmail_user
            msg['To'] = self.recipient_email

            # Attach both plain text and HTML versions
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            # Send via Gmail SMTP
            logger.info(f"Connecting to Gmail SMTP...")
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.gmail_user, self.gmail_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {self.recipient_email}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error(
                "Gmail authentication failed. "
                "Make sure you're using an App Password, not your regular password. "
                "Enable 2FA and create an App Password at https://myaccount.google.com/apppasswords"
            )
            return False

        except Exception as e:
            logger.error(f"Error sending email: {e}", exc_info=True)
            return False
