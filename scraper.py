import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    """Create a requests session with retry strategy"""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def scrape_website(url, headers=None):
    """Scrape website and return BeautifulSoup object with metadata"""
    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    try:
        session = create_session()
        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Extract page metadata
        page_metadata = {
            "title": "",
            "description": "",
            "keywords": "",
            "author": "",
            "canonical": "",
            "robots": "",
            "og_title": "",
            "og_description": "",
            "og_image": "",
            "lang": "",
            "charset": "",
        }

        # Extract title
        title_tag = soup.find("title")
        if title_tag:
            page_metadata["title"] = title_tag.get_text().strip()

        # Extract language
        html_tag = soup.find("html")
        if html_tag:
            page_metadata["lang"] = html_tag.get("lang", "")

        # Extract charset
        charset_meta = soup.find("meta", attrs={"charset": True})
        if charset_meta:
            page_metadata["charset"] = charset_meta.get("charset", "")

        # Extract standard meta tags
        meta_tags = {
            "description": soup.find("meta", attrs={"name": "description"}),
            "keywords": soup.find("meta", attrs={"name": "keywords"}),
            "author": soup.find("meta", attrs={"name": "author"}),
            "robots": soup.find("meta", attrs={"name": "robots"}),
        }

        for key, meta_tag in meta_tags.items():
            if meta_tag:
                page_metadata[key] = meta_tag.get("content", "")

        # Extract Open Graph tags
        og_tags = {
            "og_title": soup.find("meta", attrs={"property": "og:title"}),
            "og_description": soup.find("meta", attrs={"property": "og:description"}),
            "og_image": soup.find("meta", attrs={"property": "og:image"}),
        }

        for key, og_tag in og_tags.items():
            if og_tag:
                page_metadata[key] = og_tag.get("content", "")

        # Extract canonical URL
        canonical_link = soup.find("link", attrs={"rel": "canonical"})
        if canonical_link:
            page_metadata["canonical"] = canonical_link.get("href", "")

        return soup, None, page_metadata

    except requests.exceptions.RequestException as e:
        return None, str(e), {}


def clean_text(text):
    """Clean and normalize text"""
    # Remove extra whitespace and newlines
    text = re.sub(r"\s+", " ", text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def filter_by_tags(soup, tags):
    """Filter content by HTML tags"""
    elements = []
    for tag in tags:
        elements.extend(soup.find_all(tag.strip()))
    return elements


def filter_by_class_id(soup, classes=None, ids=None):
    """Filter content by CSS classes or IDs"""
    elements = []

    if classes:
        for class_name in classes:
            elements.extend(soup.find_all(class_=class_name.strip()))

    if ids:
        for id_name in ids:
            element = soup.find(id=id_name.strip())
            if element:
                elements.append(element)

    return elements


def filter_by_text_content(elements, search_terms, match_type="contains"):
    """Filter elements by text content"""
    filtered_elements = []

    for element in elements:
        text = element.get_text().lower()

        for term in search_terms:
            term = term.strip().lower()
            if not term:
                continue

            if match_type == "contains" and term in text:
                filtered_elements.append(element)
                break
            elif match_type == "starts_with" and text.startswith(term):
                filtered_elements.append(element)
                break
            elif match_type == "ends_with" and text.endswith(term):
                filtered_elements.append(element)
                break
            elif match_type == "exact" and term == text:
                filtered_elements.append(element)
                break

    return filtered_elements


def extract_text_content(elements, min_length=0):
    """Extract clean text from elements with comprehensive attributes"""
    results = []

    for element in elements:
        text = clean_text(element.get_text())
        if len(text) >= min_length:
            result = {
                "text": text,
                "tag": element.name,
                "length": len(text),
                "id": element.get("id", ""),
            }

            # Extract additional attributes for specific elements
            if element.name == "a":
                result["href"] = element.get("href", "")
                result["target"] = element.get("target", "")
                result["title"] = element.get("title", "")
                result["rel"] = element.get("rel", "")

            elif element.name == "button":
                result["type"] = element.get("type", "button")
                result["onclick"] = element.get("onclick", "")
                result["form"] = element.get("form", "")
                result["disabled"] = element.get("disabled", False)

            elif element.name == "input":
                result["type"] = element.get("type", "text")
                result["name"] = element.get("name", "")
                result["placeholder"] = element.get("placeholder", "")
                result["value"] = element.get("value", "")
                result["required"] = element.get("required", False)

            elif element.name == "img":
                result["src"] = element.get("src", "")
                result["alt"] = element.get("alt", "")

            elif element.name == "form":
                result["action"] = element.get("action", "")
                result["method"] = element.get("method", "get")

            results.append(result)

    return results
