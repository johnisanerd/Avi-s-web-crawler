"""
HTML Parser abstraction that converts raw HTML documents into structured PageBlock objects.
Decouples DOM parsing, pre-normalization, and structure extraction from candidate evaluation logic.
"""

import html
import re
import unicodedata
from typing import List, Optional
from urllib.parse import urlparse
from src.models import PageBlock
from src.email_utils import normalize_email

# Precompiled regex patterns for performance
MAILTO_REGEX = re.compile(r'href=["\']mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})["\']', re.IGNORECASE)
RAW_EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
FOOTER_REGEX = re.compile(r'<(?:footer|div[^>]*class=["\'][^"\']*footer[^"\']*["\'])[^>]*>(.*?)</(?:footer|div)>', re.DOTALL | re.IGNORECASE)
CARD_REGEX = re.compile(
    r'<(?:div|article|section)[^>]*class=["\'][^"\']*(?:agent-card|team-member|card|profile|staff-card|leadership-card)[^"\']*["\'][^>]*>(.*?)</(?:div|article|section)>',
    re.DOTALL | re.IGNORECASE
)
TAG_REGEX = re.compile(r'<[^>]+>')
WHITESPACE_REGEX = re.compile(r'\s+')
MULTIPLE_NEWLINES_REGEX = re.compile(r'\n+')


def normalize_html_text(raw_html: str) -> str:
    """
    Pre-normalizes HTML before parsing:
    - Unicode normalization (NFKC)
    - Unescapes HTML entities (&amp;, &nbsp;, etc.)
    - Replaces NBSP (\xa0) with standard space
    - Replaces smart quotes with standard quotes
    - Normalizes whitespace and line endings
    """
    if not raw_html:
        return ""

    # Unicode NFKC normalization
    text = unicodedata.normalize('NFKC', raw_html)

    # HTML entity unescaping
    text = html.unescape(text)

    # Smart quotes & NBSP replacement
    text = text.replace('\xa0', ' ')
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2018', "'").replace('\u2019', "'")

    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    return text


def classify_page_type(url: str) -> str:
    """
    Classifies a URL into standard page types (about, team, leadership, our-story, contact, homepage, footer).
    """
    if not url:
        return "general"
    
    path = urlparse(url).path.lower().strip()
    if path in ("", "/", "/index.html", "/home"):
        return "homepage"
    
    if any(k in path for k in ["/about", "/about-us", "/company"]):
        return "about"
    if any(k in path for k in ["/team", "/our-team", "/people", "/staff"]):
        return "team"
    if any(k in path for k in ["/leadership", "/executives", "/management"]):
        return "leadership"
    if any(k in path for k in ["/our-story", "/story", "/history"]):
        return "our-story"
    if any(k in path for k in ["/contact", "/contact-us"]):
        return "contact"

    return "general"


def parse_html_to_blocks(page_url: str, html_text: str) -> List[PageBlock]:
    """
    Parses pre-normalized HTML text into a structured collection of PageBlock objects.
    Extracts text, headings, cards, footers, mailto links, and email addresses.
    """
    blocks: List[PageBlock] = []
    if not html_text:
        return blocks

    normalized_html = normalize_html_text(html_text)
    page_type = classify_page_type(page_url)

    # 1. Parse Mailto links & raw emails using precompiled regex
    mailto_emails = [normalize_email(e) for e in MAILTO_REGEX.findall(normalized_html)]
    raw_emails = [normalize_email(e) for e in RAW_EMAIL_REGEX.findall(normalized_html)]
    all_page_emails = list(dict.fromkeys(mailto_emails + raw_emails))

    # 2. Extract footer block if present
    footer_match = FOOTER_REGEX.search(normalized_html)
    if footer_match:
        footer_html = footer_match.group(1)
        footer_text = TAG_REGEX.sub(' ', footer_html)
        footer_text = WHITESPACE_REGEX.sub(' ', footer_text).strip()
        footer_emails = [e for e in all_page_emails if e in footer_text.lower()]
        blocks.append(PageBlock(
            page_url=page_url,
            page_type="footer",
            heading="Footer",
            text=footer_text,
            emails=footer_emails,
            container_type="footer"
        ))

    # 3. Extract profile/team card blocks
    card_matches = CARD_REGEX.findall(normalized_html)
    for card_html in card_matches:
        card_text = TAG_REGEX.sub(' ', card_html)
        card_text = WHITESPACE_REGEX.sub(' ', card_text).strip()
        card_emails = [e for e in all_page_emails if e in card_html.lower()]
        blocks.append(PageBlock(
            page_url=page_url,
            page_type=page_type,
            heading="Profile Card",
            text=card_text,
            emails=card_emails,
            container_type="card"
        ))

    # 4. Extract structured text lines
    clean_text = TAG_REGEX.sub('\n', normalized_html)
    lines = []
    for line in MULTIPLE_NEWLINES_REGEX.split(clean_text):
        trimmed = WHITESPACE_REGEX.sub(' ', line).strip()
        if trimmed and len(trimmed) < 200:
            lines.append(trimmed)

    full_plain_text = "\n".join(lines)

    # General block covering plain text content
    blocks.append(PageBlock(
        page_url=page_url,
        page_type=page_type,
        heading="Page Main Text",
        text=full_plain_text,
        emails=all_page_emails,
        container_type="general"
    ))

    return blocks
