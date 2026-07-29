import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse
import requests

from src.email_utils import email_matches_domain, is_generic_email
from src.logger import get_logger

logger = get_logger("email_extractor")


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """
    Holds structured results of web crawling and contact information extraction.
    """
    emails: List[str]
    best_email: Optional[str]
    owner_name: Optional[str]
    owner_title: Optional[str]
    owner_email: Optional[str]
    html_pages: List[str] = field(default_factory=list)
    html_page_urls: List[str] = field(default_factory=list)
    email_sources: Dict[str, str] = field(default_factory=dict)


class EmailExtractor:
    """
    Responsible for downloading webpages, locating candidate contact URLs,
    extracting visible email addresses, and detecting business owner details.
    """

    def __init__(self, timeout_secs: int = 10, max_pages: int = 10):
        self.timeout_secs = timeout_secs
        self.max_pages = max_pages
        
        # Standard list of ignored placeholder keywords
        self.ignored_patterns = [
            "example.com", "yourdomain", "yourwebsite", "yourcompany",
            "placeholder", "email.com", "domain.com", "test.com",
            "username@", "yourname@", "you@", "john@doe.com"
        ]

        self.ignored_off_domain_email_domains = {
            "agentfire.com",
            "boomtownroi.com",
            "mlsgrid.com",
            "info.properties",
            "moxiworks.com",
            "sentry-next.wixpress.com",
            "siteservice.net",
        }
        self.ignored_off_domain_local_parts = {"dmcanotice", "support"}

        self.asset_email_domain_suffixes = {
            ".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"
        }

    def extract_from_website(self, homepage_url: str) -> ExtractionResult:
        """
        Crawls the homepage and up to 9 other candidate subpages of a domain
        to find public email addresses and detect owner information.
        """
        if not homepage_url:
            return ExtractionResult([], None, None, None, None)

        # Normalize scheme
        parsed_home = urlparse(homepage_url)
        if not parsed_home.scheme:
            homepage_url = "http://" + homepage_url
            parsed_home = urlparse(homepage_url)

        base_url = f"{parsed_home.scheme}://{parsed_home.netloc}"
        base_domain = parsed_home.hostname or ""
        
        # Prepare candidate paths list (up to 10 distinct URLs in total)
        paths = [
            "/",
            "/contact",
            "/contact-us",
            "/about",
            "/about-us",
            "/team",
            "/our-team",
            "/agents",
            "/staff",
            "/brokers"
        ]
        
        urls_to_visit: List[str] = []
        seen_urls: Set[str] = set()
        for p in paths:
            u = urljoin(base_url, p)
            if u not in seen_urls:
                seen_urls.add(u)
                urls_to_visit.append(u)

        all_emails: List[str] = []
        owner_name: Optional[str] = None
        owner_title: Optional[str] = None
        owner_email: Optional[str] = None
        html_pages: List[str] = []
        html_page_urls: List[str] = []
        email_sources: Dict[str, str] = {}

        session = requests.Session()
        session.max_redirects = 5

        # 1. Visit homepage first
        homepage = urls_to_visit[0]
        logger.info(f"Visiting homepage for extraction: {homepage}")
        home_html = self._download_page(session, homepage)
        
        if home_html:
            html_pages.append(home_html)
            html_page_urls.append(homepage)
            home_emails = self._rank_emails(self._parse_emails(home_html), base_domain)
            all_emails.extend(home_emails)
            for email in home_emails:
                email_sources.setdefault(email.lower(), homepage)
            
            # Check owner details
            owner_name, owner_title, owner_email = self._detect_owner(home_html, home_emails)

        # 2. Crawl remaining candidate paths so homepage footer/vendor emails do not
        # prevent higher-quality contact and leadership discovery.
        for url in urls_to_visit[1:self.max_pages]:
            logger.info(f"Crawling candidate URL: {url}")
            html = self._download_page(session, url)
            if html:
                html_pages.append(html)
                html_page_urls.append(url)
                sub_emails = self._rank_emails(self._parse_emails(html), base_domain)
                all_emails.extend(sub_emails)
                for email in sub_emails:
                    email_sources.setdefault(email.lower(), url)
                
                # Try to detect owner details on this page if not found yet
                if not owner_name:
                    owner_name, owner_title, owner_email = self._detect_owner(html, all_emails)

        # Rank all unique emails found
        ranked_emails = self._rank_emails(all_emails, base_domain)
        best_email = ranked_emails[0] if ranked_emails else None

        # Re-resolve owner email from the final ranked list if owner was detected
        if owner_name and not owner_email:
            owner_email = self._find_owner_email(owner_name, ranked_emails)

        return ExtractionResult(
            emails=ranked_emails,
            best_email=best_email,
            owner_name=owner_name,
            owner_title=owner_title,
            owner_email=owner_email,
            html_pages=html_pages,
            html_page_urls=html_page_urls,
            email_sources=email_sources
        )

    def _download_page(self, session: requests.Session, url: str) -> Optional[str]:
        """
        Downloads a webpage safely handling SSL, timeouts, redirects, and HTTP errors.
        """
        try:
            response = session.get(url, timeout=self.timeout_secs, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) RealEstateLeadGen/1.1"
            })
            if response.status_code == 200:
                return response.text
        except Exception as e:
            logger.warning(f"Failed downloading URL {url}: {e}")
        return None

    def _parse_emails(self, html: str) -> List[str]:
        """
        Extracts valid email addresses from HTML text, ignoring placeholders.
        """
        # Look for mailto: links first to capture hidden emails
        mailto_emails = re.findall(r'href=["\']mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})["\']', html, re.IGNORECASE)
        
        # Standard raw email regex search in HTML text
        raw_emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', html)
        
        found = mailto_emails + raw_emails
        valid: List[str] = []
        for email in found:
            email_clean = email.strip()
            if "@" not in email_clean:
                continue

            local_part, email_domain = email_clean.rsplit("@", 1)

            # Recover addresses concatenated after labels in compressed page text,
            # such as "Phone913.393.9469EmailDavid@example.com".
            label_match = re.search(
                r'(?i)e-?mail([a-z][a-z0-9._%+-]*)$',
                local_part,
            )
            if (
                label_match
                and any(char.isdigit() for char in local_part[:label_match.start()])
            ):
                local_part = label_match.group(1)
                email_clean = f"{local_part}@{email_domain}"

            # Reject phone/text concatenations and asset filenames that merely
            # resemble email addresses.
            if re.match(r'^\d{6,}', local_part):
                continue
            if email_domain.lower().endswith(
                tuple(self.asset_email_domain_suffixes)
            ):
                continue
            if len(local_part) > 64 or len(email_domain) > 253:
                continue

            # Basic validation check
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email_clean):
                continue
            
            email_lower = email_clean.lower()
            # Ignore placeholder patterns
            is_placeholder = any(pattern in email_lower for pattern in self.ignored_patterns)
            if is_placeholder:
                continue
                
            valid.append(email_clean)
        return valid

    def _rank_emails(self, emails: List[str], target_domain: Optional[str] = None) -> List[str]:
        """
        Rejects known off-domain platform noise, deduplicates case-insensitively,
        and ranks personal addresses first with target-domain addresses preferred
        within each personal/generic tier.
        """
        unique_emails = []
        seen = set()
        for email in emails:
            email_lower = email.strip().lower()
            email_domain = email_lower.rsplit("@", 1)[-1]
            local_part = email_lower.rsplit("@", 1)[0]
            is_target_domain = bool(
                target_domain and email_matches_domain(email_lower, target_domain)
            )
            is_ignored_off_domain = (
                not is_target_domain
                and (
                    local_part in self.ignored_off_domain_local_parts
                    or any(
                        email_domain == ignored_domain
                        or email_domain.endswith(f".{ignored_domain}")
                        for ignored_domain in self.ignored_off_domain_email_domains
                    )
                )
            )
            if is_ignored_off_domain:
                continue
            if email_lower not in seen:
                seen.add(email_lower)
                unique_emails.append(email)

        def get_score(email: str) -> Tuple[int, int]:
            generic_rank = 1 if is_generic_email(email) else 0
            domain_rank = (
                0
                if target_domain and email_matches_domain(email, target_domain)
                else 1
            )
            return generic_rank, domain_rank

        return sorted(unique_emails, key=get_score)

    def _detect_owner(self, html: str, emails: List[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Attempts to parse structural tags to detect owner names and matching emails.
        """
        # Convert HTML to clean plain text lines
        lines: List[str] = []
        for line in re.split(r'\n+', re.sub(r'<[^>]+>', '\n', html)):
            trimmed = line.strip()
            if trimmed:
                lines.append(trimmed)

        target_titles = [
            "principal broker", "managing broker", "owner", "founder", "ceo", "president", "broker"
        ]
        
        title_display_map = {
            "principal broker": "Principal Broker",
            "managing broker": "Managing Broker",
            "owner": "Owner",
            "founder": "Founder",
            "ceo": "CEO",
            "president": "President",
            "broker": "Broker"
        }

        name_regex = re.compile(r'^[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,2}$')

        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check exact matching lines
            if line_lower in target_titles:
                # Check previous line
                if i > 0 and name_regex.match(lines[i - 1]):
                    title = title_display_map[line_lower]
                    name = lines[i - 1]
                    owner_email = self._find_owner_email(name, emails)
                    return name, title, owner_email
                # Check next line
                if i < len(lines) - 1 and name_regex.match(lines[i + 1]):
                    title = title_display_map[line_lower]
                    name = lines[i + 1]
                    owner_email = self._find_owner_email(name, emails)
                    return name, title, owner_email

            # Check inline formats (e.g., "John Doe - Owner" or "Founder: Jane Smith")
            for t in target_titles:
                title_pattern = rf"(?i:{re.escape(t)})"
                # Name followed by Title
                pattern_name_title = r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,2})\b\s*(?:,|\s*-\s*|\s*\|\s*)\s*\b' + title_pattern + r'\b'
                match = re.search(pattern_name_title, line)
                if match:
                    name = match.group(1).strip()
                    return name, title_display_map[t], self._find_owner_email(name, emails)

                # Title followed by Name
                pattern_title_name = r'\b' + title_pattern + r'\b\s*(?::|\s*-\s*|\s*\|\s*)?\s*\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,2})\b'
                match = re.search(pattern_title_name, line)
                if match:
                    name = match.group(1).strip()
                    return name, title_display_map[t], self._find_owner_email(name, emails)

        return None, None, None

    def _find_owner_email(self, name: str, emails: List[str]) -> Optional[str]:
        """
        Attempts to link a discovered owner name with one of the extracted emails.
        """
        tokens = name.lower().split()
        if len(tokens) < 2:
            return None
        first = tokens[0]
        last = tokens[-1]

        for email in emails:
            username = email.split('@')[0].lower()
            if first in username and last in username:
                return email
            if username == first or username == last:
                return email
            if username == (first[0] + last):
                return email
            if username == (first + last[0]):
                return email
            if username == f"{first}.{last}" or username == f"{first}_{last}":
                return email

        return None
