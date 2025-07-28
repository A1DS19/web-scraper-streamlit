import streamlit as st
import json
from urllib.parse import urlparse
import time

from scraper import (
    scrape_website,
    filter_by_tags,
    filter_by_class_id,
    filter_by_text_content,
    extract_text_content,
)
from utils import create_markdown_content, display_results


def main():
    st.set_page_config(
        page_title="Betanything Web Text Scraper",
        page_icon="🕷️",
        layout="wide",
    )

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

    st.markdown(
        '<div class="main-header">🕷️ Betanything Web Text Scraper</div>',
        unsafe_allow_html=True,
    )

    st.sidebar.header("⚙️ Configuration")
    url = st.text_input("🌐 Enter Website URL:", placeholder="https://example.com")

    mode = st.sidebar.radio("Select Mode:", ("Simple", "Advanced"))

    if mode == "Advanced":
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.subheader("🔍 Filtering Options")
        col1, col2 = st.columns(2)

        with col1:
            tag_filter = st.text_input(
                "HTML Tags (comma-separated):",
                placeholder="p, h1, h2, div, a, button, input, form, nav",
                help="Filter by specific HTML tags",
            )

            id_filter = st.text_input(
                "Element IDs (comma-separated):",
                placeholder="main-content, header, footer",
                help="Filter by element IDs",
            )

        with col2:
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

        st.sidebar.subheader("🔧 Advanced Options")
        remove_scripts = st.sidebar.checkbox(
            "Remove Scripts/Styles", value=True, help="Remove script and style tags"
        )
        show_debug = st.sidebar.checkbox(
            "Show Debug Info", value=False, help="Show debug information"
        )
        extract_metadata = st.sidebar.checkbox(
            "Extract Page Metadata",
            value=True,
            help="Extract page title, description, etc.",
        )
        custom_headers = st.sidebar.text_area(
            "Custom Headers (JSON):",
            placeholder='{"key": "value"}',
            help="Add custom HTTP headers",
        )
    else:
        tag_filter = None
        id_filter = None
        search_terms = None
        match_type = "contains"
        min_length = 10
        remove_scripts = True
        show_debug = False
        extract_metadata = True
        custom_headers = None

    if st.button("Start Scraping", type="primary"):
        if not url:
            st.error("Please enter a URL")
            st.stop()

        with st.spinner("Scraping website..."):
            headers = None
            if custom_headers:
                try:
                    headers = json.loads(custom_headers)
                except json.JSONDecodeError:
                    st.warning("Invalid JSON in custom headers, using default headers")

            soup, error, page_metadata = scrape_website(url, headers)

            if error:
                st.error(f"Error scraping website: {error}")
                st.stop()

            if remove_scripts:
                for script in soup(["script", "style", "noscript"]):
                    script.decompose()

            elements = []

            if tag_filter:
                tags = [tag.strip() for tag in tag_filter.split(",") if tag.strip()]
                elements.extend(filter_by_tags(soup, tags))

            if id_filter:
                ids = [i.strip() for i in id_filter.split(",") if i.strip()]
                elements.extend(filter_by_class_id(soup, None, ids))

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

            if search_terms:
                terms = [
                    term.strip() for term in search_terms.split(",") if term.strip()
                ]
                elements = filter_by_text_content(elements, terms, match_type)

            results = extract_text_content(elements, min_length)

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
                        r
                        for r in results
                        if r["tag"] in ["a", "button", "input", "form"]
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

            display_results(results, url, page_metadata, extract_metadata, show_debug)

    st.markdown("---")
    st.markdown("Jose Padilla 2025")


if __name__ == "__main__":
    main()