import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json

# Configure page
st.set_page_config(
    page_title="Betanything Web Text Scraper", page_icon="🕷️", layout="wide"
)

# Custom CSS for better styling
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-align: center;
        color: #1f77b4;
    }
    .filter-section {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .result-box {
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .metadata-box {
        background-color: #e8f4f8;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 1rem 0;
    }
    .debug-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


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


def create_markdown_content(results, url, page_metadata):
    """Create comprehensive markdown content with metadata and summaries"""
    markdown_lines = []
    domain = urlparse(url).netloc

    # Page header with title from metadata
    page_title = page_metadata.get("title", f"Scraped Content from {domain}")
    markdown_lines.append(f"# {page_title}")

    # Comprehensive page metadata section
    markdown_lines.append(f"\n## 📄 Page Metadata")
    markdown_lines.append(f"- **Source URL:** {url}")
    markdown_lines.append(f"- **Domain:** {domain}")
    markdown_lines.append(f"- **Scraped on:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    markdown_lines.append(f"- **Total elements:** {len(results)}")

    if page_metadata.get("description"):
        markdown_lines.append(f"- **Description:** {page_metadata['description']}")
    if page_metadata.get("keywords"):
        markdown_lines.append(f"- **Keywords:** {page_metadata['keywords']}")
    if page_metadata.get("author"):
        markdown_lines.append(f"- **Author:** {page_metadata['author']}")
    if page_metadata.get("lang"):
        markdown_lines.append(f"- **Language:** {page_metadata['lang']}")
    if page_metadata.get("canonical"):
        markdown_lines.append(f"- **Canonical URL:** {page_metadata['canonical']}")
    if page_metadata.get("robots"):
        markdown_lines.append(f"- **Robots:** {page_metadata['robots']}")
    if page_metadata.get("og_title"):
        markdown_lines.append(f"- **OG Title:** {page_metadata['og_title']}")
    if page_metadata.get("og_description"):
        markdown_lines.append(
            f"- **OG Description:** {page_metadata['og_description']}"
        )

    markdown_lines.append("\n---\n")

    # Separate elements by type for summary
    buttons = [r for r in results if r["tag"] == "button"]
    links = [r for r in results if r["tag"] == "a" and r.get("href")]
    forms = [r for r in results if r["tag"] == "form"]
    inputs = [r for r in results if r["tag"] == "input"]

    # Interactive elements summary
    if buttons or links or forms or inputs:
        markdown_lines.append(f"## 🎯 Interactive Elements Summary")

        if buttons:
            markdown_lines.append(f"\n### 🔘 Buttons ({len(buttons)})")
            for i, btn in enumerate(buttons, 1):
                btn_id = btn.get("id") or f"button-{i}"
                btn_type = btn.get("type", "button")
                markdown_lines.append(
                    f'- **{btn_id}**: "{btn["text"]}" (Type: {btn_type})'
                )

        if links:
            markdown_lines.append(f"\n### 🔗 Links ({len(links)})")
            for i, link in enumerate(links, 1):
                link_id = link.get("id") or f"link-{i}"
                href = link.get("href", "No URL")
                # Convert relative URLs to absolute
                if href.startswith("/"):
                    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                    href = base_url + href
                elif href.startswith("#"):
                    href = url + href
                elif not href.startswith(("http://", "https://", "mailto:", "tel:")):
                    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                    href = base_url + "/" + href.lstrip("/")
                markdown_lines.append(f"- **{link_id}**: [{link['text']}]({href})")

        if forms:
            markdown_lines.append(f"\n### 📝 Forms ({len(forms)})")
            for i, form in enumerate(forms, 1):
                form_id = form.get("id") or f"form-{i}"
                method = form.get("method", "GET").upper()
                action = form.get("action", "No action")
                markdown_lines.append(f"- **{form_id}**: {method} → {action}")

        if inputs:
            markdown_lines.append(f"\n### 📄 Input Fields ({len(inputs)})")
            for i, inp in enumerate(inputs, 1):
                input_id = inp.get("id") or inp.get("name") or f"input-{i}"
                inp_type = inp.get("type", "text")
                placeholder = inp.get("placeholder", "")
                if placeholder:
                    markdown_lines.append(
                        f'- **{input_id}**: {inp_type} - "{placeholder}"'
                    )
                else:
                    markdown_lines.append(f"- **{input_id}**: {inp_type}")

        markdown_lines.append("\n---\n")

    # Content sections with proper ID-based headers
    for i, result in enumerate(results, 1):
        element_id = result.get("id", "").strip()
        element_tag = result["tag"].upper()

        # Create smart section headers based on element type and ID
        if result["tag"] in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            header_level = int(result["tag"][1]) + 1
            if element_id:
                markdown_lines.append(
                    f"{'#' * header_level} {result['text']} `#{element_id}`"
                )
            else:
                markdown_lines.append(f"{'#' * header_level} {result['text']}")

        elif result["tag"] == "title":
            markdown_lines.append(f"## 📄 Page Title")
            markdown_lines.append(f"\n{result['text']}")

        elif result["tag"] == "a":
            # Handle links with comprehensive details
            section_title = element_id if element_id else f"link-{i}"
            markdown_lines.append(f"## 🔗 {section_title}")
            markdown_lines.append(f"\n**Link Text:** {result['text']}")

            if result.get("href"):
                href = result["href"]
                # Make relative URLs absolute
                if href.startswith("/"):
                    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                    href = base_url + href
                elif href.startswith("#"):
                    href = url + href
                elif not href.startswith(("http://", "https://", "mailto:", "tel:")):
                    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                    href = base_url + "/" + href.lstrip("/")

                markdown_lines.append(f"**URL:** {href}")
                markdown_lines.append(f"\n[{result['text']}]({href})")
            else:
                markdown_lines.append(f"**URL:** No href attribute")

            if result.get("target"):
                markdown_lines.append(f"**Target:** {result['target']}")
            if result.get("title"):
                markdown_lines.append(f"**Title:** {result['title']}")
            if result.get("rel"):
                markdown_lines.append(f"**Rel:** {result['rel']}")

        elif result["tag"] == "button":
            # Handle buttons with comprehensive details
            section_title = element_id if element_id else f"button-{i}"
            markdown_lines.append(f"## 🔘 {section_title}")
            markdown_lines.append(f"\n**Button Text:** {result['text']}")

            button_type = result.get("type", "button")
            markdown_lines.append(f"**Button Type:** {button_type}")

            if result.get("onclick"):
                markdown_lines.append(f"**OnClick Event:** `{result['onclick']}`")

            if result.get("form"):
                markdown_lines.append(f"**Associated Form:** {result['form']}")

            if result.get("disabled"):
                markdown_lines.append(f"**Disabled:** Yes")

        elif result["tag"] == "input":
            # Handle input fields
            section_title = (
                element_id if element_id else (result.get("name") or f"input-{i}")
            )
            markdown_lines.append(f"## 📝 {section_title}")
            markdown_lines.append(f"\n**Input Type:** {result.get('type', 'text')}")

            if result.get("placeholder"):
                markdown_lines.append(f"**Placeholder:** {result['placeholder']}")
            if result.get("value"):
                markdown_lines.append(f"**Value:** {result['value']}")
            if result.get("name"):
                markdown_lines.append(f"**Name:** {result['name']}")
            if result.get("required"):
                markdown_lines.append(f"**Required:** Yes")

        elif result["tag"] == "form":
            # Handle forms
            section_title = element_id if element_id else f"form-{i}"
            markdown_lines.append(f"## 📋 {section_title}")
            markdown_lines.append(f"\n**Form Content:** {result['text']}")
            markdown_lines.append(f"**Method:** {result.get('method', 'GET').upper()}")
            if result.get("action"):
                markdown_lines.append(f"**Action:** {result['action']}")

        else:
            # Regular content with element ID or smart fallback
            if element_id:
                section_title = f"{element_id}"
            else:
                section_title = f"{element_tag.lower()}-{i}"

            markdown_lines.append(f"## {section_title} `({element_tag})`")
            markdown_lines.append(f"\n{result['text']}")

        # Add comprehensive metadata for all elements
        metadata_parts = [f"**Length:** {result['length']} chars"]

        if result.get("id"):
            metadata_parts.append(f"**ID:** `{result['id']}`")

        markdown_lines.append(f"\n*{' | '.join(metadata_parts)}*")
        markdown_lines.append("\n---\n")

    return "\n".join(markdown_lines)


# Main app
st.markdown(
    '<div class="main-header">🕷️ Betanything Web Text Scraper</div>',
    unsafe_allow_html=True,
)

# Sidebar for configuration
st.sidebar.header("⚙️ Configuration")

# URL Input
url = st.text_input("🌐 Enter Website URL:", placeholder="https://example.com")

# Filtering Options
st.markdown('<div class="filter-section">', unsafe_allow_html=True)
st.subheader("🔍 Filtering Options")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Tag Filtering")
    tag_filter = st.text_input(
        "HTML Tags (comma-separated):",
        placeholder="p, h1, h2, div, a, button, input, form, nav",
        help="Filter by specific HTML tags",
    )

    st.subheader("ID Filtering")
    id_filter = st.text_input(
        "Element IDs (comma-separated):",
        placeholder="main-content, header, footer",
        help="Filter by element IDs",
    )

with col2:
    st.subheader("Text Content Filtering")
    search_terms = st.text_input(
        "Search Terms (comma-separated):",
        placeholder="keyword1, keyword2, phrase",
        help="Filter by text content",
    )

    match_type = st.selectbox(
        "Match Type:",
        ["contains", "starts_with", "ends_with", "exact"],
        help="How to match search terms",
    )

    min_length = st.number_input(
        "Minimum Text Length:",
        min_value=0,
        value=10,
        step=1,
        help="Minimum character length for results",
    )

st.markdown("</div>", unsafe_allow_html=True)

# Advanced options in sidebar
st.sidebar.subheader("🔧 Advanced Options")
remove_scripts = st.sidebar.checkbox(
    "Remove Scripts/Styles", value=True, help="Remove script and style tags"
)
show_debug = st.sidebar.checkbox(
    "Show Debug Info", value=False, help="Show element IDs and classes found"
)
extract_metadata = st.sidebar.checkbox(
    "Extract Page Metadata", value=True, help="Extract page title, description, etc."
)
custom_headers = st.sidebar.text_area(
    "Custom Headers (JSON):",
    placeholder='{"Referer": "https://google.com"}',
    help="Add custom HTTP headers",
)

# Scrape button
if st.button("Start Scraping", type="primary"):
    if not url:
        st.error("Please enter a URL")
        st.stop()

    with st.spinner("Scraping website..."):
        # Parse custom headers
        headers = None
        if custom_headers:
            try:
                headers = json.loads(custom_headers)
            except:
                st.warning("Invalid JSON in custom headers, using default headers")

        # Scrape website
        soup, error, page_metadata = scrape_website(url, headers)

        if error:
            st.error(f"Error scraping website: {error}")
            st.stop()

        # Remove scripts and styles if requested
        if remove_scripts:
            for script in soup(["script", "style", "noscript"]):
                script.decompose()

        # Start with all elements or filter by tags/classes/ids
        elements = []

        # Apply filters
        if tag_filter:
            tags = [tag.strip() for tag in tag_filter.split(",") if tag.strip()]
            elements.extend(filter_by_tags(soup, tags))

        if id_filter:
            ids = [i.strip() for i in id_filter.split(",") if i.strip()]
            elements.extend(filter_by_class_id(soup, None, ids))

        # If no specific filters, get comprehensive content tags
        if not elements:
            default_tags = [
                "p",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "div",
                "span",
                "article",
                "section",
                "a",
                "button",
                "input",
                "form",
                "li",
                "td",
                "th",
                "label",
                "nav",
                "header",
                "footer",
                "main",
            ]
            elements = filter_by_tags(soup, default_tags)

        # Filter by text content if specified
        if search_terms:
            terms = [term.strip() for term in search_terms.split(",") if term.strip()]
            elements = filter_by_text_content(elements, terms, match_type)

        # Extract text content
        results = extract_text_content(elements, min_length)

        # Debug information
        if show_debug and results:
            st.markdown('<div class="debug-box">', unsafe_allow_html=True)
            st.subheader("🔍 Debug Information")
            debug_col1, debug_col2, debug_col3 = st.columns(3)

            with debug_col1:
                st.write("**Elements with IDs:**")
                elements_with_ids = [r for r in results if r.get("id")]
                if elements_with_ids:
                    for elem in elements_with_ids[:8]:
                        st.write(
                            f'- `{elem["id"]}` ({elem["tag"]}) - "{elem["text"][:40]}..."'
                        )
                    if len(elements_with_ids) > 8:
                        st.write(f"... and {len(elements_with_ids) - 8} more")
                else:
                    st.write("❌ No elements with IDs found")

            with debug_col2:
                st.write("**Interactive Elements:**")
                interactive = [
                    r for r in results if r["tag"] in ["a", "button", "input", "form"]
                ]
                if interactive:
                    for elem in interactive[:8]:
                        extra = elem.get(
                            "href", elem.get("type", elem.get("method", ""))
                        )
                        st.write(
                            f'- {elem["tag"].upper()}: "{elem["text"][:25]}..." ({extra})'
                        )
                    if len(interactive) > 8:
                        st.write(f"... and {len(interactive) - 8} more")
                else:
                    st.write("❌ No interactive elements found")

            with debug_col3:
                st.write("**Tag Distribution:**")
                tag_counts = {}
                for r in results:
                    tag_counts[r["tag"]] = tag_counts.get(r["tag"], 0) + 1
                for tag, count in sorted(
                    tag_counts.items(), key=lambda x: x[1], reverse=True
                )[:8]:
                    st.write(f"- {tag}: {count}")

            st.markdown("</div>", unsafe_allow_html=True)

        # Display results
        st.success(f"Found {len(results)} text segments")

        if results:
            # Summary statistics
            total_chars = sum(r["length"] for r in results)
            avg_length = total_chars / len(results) if results else 0
            interactive_count = len([
                r for r in results if r["tag"] in ["a", "button", "input", "form"]
            ])

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Elements", len(results))
            with col2:
                st.metric("Interactive Elements", interactive_count)
            with col3:
                st.metric("Total Characters", total_chars)
            with col4:
                st.metric("Average Length", f"{avg_length:.1f}")

            # Page metadata section
            if extract_metadata and any(page_metadata.values()):
                st.markdown('<div class="metadata-box">', unsafe_allow_html=True)
                st.subheader("📄 Page Metadata")
                meta_col1, meta_col2 = st.columns(2)

                with meta_col1:
                    if page_metadata.get("title"):
                        st.write(f"**Title:** {page_metadata['title']}")
                    if page_metadata.get("description"):
                        st.write(
                            f"**Description:** {page_metadata['description'][:100]}..."
                        )
                    if page_metadata.get("author"):
                        st.write(f"**Author:** {page_metadata['author']}")
                    if page_metadata.get("lang"):
                        st.write(f"**Language:** {page_metadata['lang']}")

                with meta_col2:
                    if page_metadata.get("keywords"):
                        st.write(f"**Keywords:** {page_metadata['keywords']}")
                    if page_metadata.get("canonical"):
                        st.write(f"**Canonical:** {page_metadata['canonical']}")
                    if page_metadata.get("robots"):
                        st.write(f"**Robots:** {page_metadata['robots']}")
                    if page_metadata.get("og_title"):
                        st.write(f"**OG Title:** {page_metadata['og_title']}")

                st.markdown("</div>", unsafe_allow_html=True)

            # Export options
            st.subheader("📥 Export Options")
            col1, col2, col3 = st.columns(3)

            with col1:
                # Download as text
                text_content = "\n\n---\n\n".join([r["text"] for r in results])
                st.download_button(
                    label="📄 Download as Text",
                    data=text_content,
                    file_name=f"scraped_text_{urlparse(url).netloc}.txt",
                    mime="text/plain",
                )

            with col2:
                # Download as Markdown
                markdown_content = create_markdown_content(results, url, page_metadata)
                st.download_button(
                    label="📝 Download as Markdown",
                    data=markdown_content,
                    file_name=f"scraped_content_{urlparse(url).netloc}.md",
                    mime="text/markdown",
                )

            with col3:
                # Download as JSON
                json_data = {
                    "metadata": page_metadata,
                    "url": url,
                    "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_elements": len(results),
                    "elements": results,
                }
                json_content = json.dumps(json_data, indent=2, ensure_ascii=False)
                st.download_button(
                    label="📊 Download as JSON",
                    data=json_content,
                    file_name=f"scraped_data_{urlparse(url).netloc}.json",
                    mime="application/json",
                )

            # Display results
            st.subheader("📝 Extracted Content")

            # Sort options
            sort_by = st.selectbox(
                "Sort by:", ["order", "length_desc", "length_asc", "tag_type"]
            )

            if sort_by == "length_desc":
                results.sort(key=lambda x: x["length"], reverse=True)
            elif sort_by == "length_asc":
                results.sort(key=lambda x: x["length"])
            elif sort_by == "tag_type":
                results.sort(key=lambda x: (x["tag"], x["length"]), reverse=True)

            # Display with pagination
            items_per_page = st.selectbox("Items per page:", [10, 25, 50, 100], index=1)
            total_pages = (len(results) - 1) // items_per_page + 1

            if total_pages > 1:
                page = st.selectbox("Page:", range(1, total_pages + 1))
                start_idx = (page - 1) * items_per_page
                end_idx = start_idx + items_per_page
                page_results = results[start_idx:end_idx]
            else:
                page_results = results

            # Display results
            for i, result in enumerate(page_results, 1):
                # Create a more descriptive title for the expander
                title_parts = [
                    f"#{i}",
                    result["tag"].upper(),
                    f"({result['length']} chars)",
                ]

                if result.get("id"):
                    title_parts.insert(2, f"ID: {result['id']}")

                # Add type-specific info to title
                if result["tag"] == "a" and result.get("href"):
                    title_parts.append("🔗")
                elif result["tag"] == "button":
                    title_parts.append("🔘")
                elif result["tag"] == "input":
                    title_parts.append("📝")
                elif result["tag"] == "form":
                    title_parts.append("📋")

                expander_title = " - ".join(title_parts)

                with st.expander(expander_title):
                    st.text_area(
                        "Text Content:",
                        value=result["text"],
                        height=min(200, max(100, len(result["text"]) // 10)),
                        key=f"text_{i}_{result.get('id', 'no_id')}",
                        label_visibility="collapsed",
                    )

                    # Show additional attributes in organized columns
                    attr_cols = st.columns(3)

                    with attr_cols[0]:
                        if result.get("id"):
                            st.caption(f"**ID:** `{result['id']}`")

                    with attr_cols[1]:
                        if result.get("href"):
                            st.caption(f"**Link:** {result['href']}")
                        if result.get("type") and result["tag"] in ["button", "input"]:
                            st.caption(f"**Type:** {result['type']}")
                        if result.get("method") and result["tag"] == "form":
                            st.caption(f"**Method:** {result['method']}")

                    with attr_cols[2]:
                        if result.get("onclick"):
                            st.caption(f"**OnClick:** `{result['onclick']}`")
                        if result.get("placeholder"):
                            st.caption(f"**Placeholder:** {result['placeholder']}")
                        if result.get("action"):
                            st.caption(f"**Action:** {result['action']}")

                    # Copy button (using clipboard)
                    st.code(result["text"], language=None)

        else:
            st.warning(
                "No text content found matching your filters. Try adjusting your filter criteria."
            )

# Footer
st.markdown("---")
st.markdown("Jose Padilla 2025")
