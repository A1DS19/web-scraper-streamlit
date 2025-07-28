import streamlit as st
from urllib.parse import urlparse
import time
import json
import re


def markdown_to_text(markdown_string):
    """
    Converts a markdown string to plain text with organized sections and proper spacing.
    """
    # Remove code blocks first to avoid interference
    text = re.sub(r"```.*?```", "", markdown_string, flags=re.DOTALL)

    # Remove inline code
    text = re.sub(r"`(.*?)`", r"\1", text)

    # Remove images
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

    # Convert links to "link name -> link URL" format
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1 -> \2", text)

    # Remove strikethrough
    text = re.sub(r"~~(.*?)~~", r"\1", text)

    # Remove bold and italics
    text = re.sub(r"\*\*(.*?)\*\*|\*(.*?)\*", r"\1\2", text)

    # Process headers - convert to section headers with spacing
    text = re.sub(r"^### (.*?)$", r"\n\1:\n", text, flags=re.MULTILINE)
    text = re.sub(r"^## (.*?)$", r"\n\n\1:\n", text, flags=re.MULTILINE)
    text = re.sub(r"^# (.*?)$", r"\n\n\1\n" + "=" * 50 + "\n", text, flags=re.MULTILINE)

    # Remove remaining header markers
    text = re.sub(r"^#+\s", "", text, flags=re.MULTILINE)

    # Remove horizontal rules
    text = re.sub(r"^---+$", "", text, flags=re.MULTILINE)

    # Remove blockquotes
    text = re.sub(r"^>+\s?", "", text, flags=re.MULTILINE)

    # Remove list item markers but keep the content
    text = re.sub(r"^\s*[\*\-]\s+", "• ", text, flags=re.MULTILINE)

    # Clean up extra newlines but preserve section spacing
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Add spacing after section headers
    text = re.sub(r"(\w+:)\n", r"\1\n\n", text)

    return text.strip()


def create_organized_text_content(results, url, page_metadata):
    """Create organized plain text content grouped by element types"""
    text_lines = []
    domain = urlparse(url).netloc

    # Page header
    page_title = page_metadata.get("title", f"Scraped Content from {domain}")
    text_lines.append(page_title)
    text_lines.append("=" * 50)
    text_lines.append("")

    # Page metadata section
    text_lines.append("Page Metadata:")
    text_lines.append("")
    text_lines.append(f"• Source URL: {url}")
    text_lines.append(f"• Domain: {domain}")
    text_lines.append(f"• Scraped on: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    text_lines.append(f"• Total elements: {len(results)}")

    if page_metadata.get("description"):
        text_lines.append(f"• Description: {page_metadata['description']}")
    if page_metadata.get("keywords"):
        text_lines.append(f"• Keywords: {page_metadata['keywords']}")
    if page_metadata.get("author"):
        text_lines.append(f"• Author: {page_metadata['author']}")
    if page_metadata.get("lang"):
        text_lines.append(f"• Language: {page_metadata['lang']}")
    if page_metadata.get("canonical"):
        text_lines.append(f"• Canonical URL: {page_metadata['canonical']}")

    text_lines.append("")
    text_lines.append("")

    # Group elements by type
    element_groups = {}
    for result in results:
        tag = result["tag"].upper()
        if tag not in element_groups:
            element_groups[tag] = []
        element_groups[tag].append(result)

    # Define the order of sections
    section_order = [
        "BUTTON",
        "A",
        "FORM",
        "INPUT",
        "H1",
        "H2",
        "H3",
        "H4",
        "H5",
        "H6",
        "P",
        "DIV",
        "SPAN",
        "SECTION",
        "LI",
        "LABEL",
        "NAV",
        "HEADER",
        "FOOTER",
        "MAIN",
    ]

    # Add sections in order
    for tag in section_order:
        if tag in element_groups:
            elements = element_groups[tag]

            # Section header with proper spacing
            if tag == "A":
                text_lines.append("Links:")
            elif tag == "BUTTON":
                text_lines.append("Buttons:")
            elif tag == "P":
                text_lines.append("Paragraphs:")
            elif tag == "DIV":
                text_lines.append("Divs:")
            elif tag == "SPAN":
                text_lines.append("Spans:")
            elif tag == "FORM":
                text_lines.append("Forms:")
            elif tag == "INPUT":
                text_lines.append("Input Fields:")
            elif tag.startswith("H"):
                text_lines.append("Headers:")
            else:
                text_lines.append(f"{tag.title()}s:")

            text_lines.append("")

            # Add content for this section
            for element in elements:
                if tag == "A" and element.get("href"):
                    # Format links as "text -> url"
                    href = element.get("href", "")
                    # Convert relative URLs to absolute
                    if href.startswith("/"):
                        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                        href = base_url + href
                    elif href.startswith("#"):
                        href = url + href
                    elif not href.startswith((
                        "http://",
                        "https://",
                        "mailto:",
                        "tel:",
                    )):
                        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                        href = base_url + "/" + href.lstrip("/")

                    text_lines.append(f"{element['text']} -> {href}")
                else:
                    # For all other types, just add the text content
                    text_lines.append(element["text"])

            text_lines.append("")
            text_lines.append("")

    # Add any remaining element types not in the ordered list
    for tag, elements in element_groups.items():
        if tag not in section_order:
            text_lines.append(f"{tag.title()}s:")
            text_lines.append("")

            for element in elements:
                text_lines.append(element["text"])

            text_lines.append("")
            text_lines.append("")

    return "\n".join(text_lines).strip()


def create_markdown_content(results, url, page_metadata):
    """Create comprehensive markdown content with organized sections"""
    markdown_lines = []
    domain = urlparse(url).netloc

    # Page header with title from metadata
    page_title = page_metadata.get("title", f"Scraped Content from {domain}")
    markdown_lines.append(f"# {page_title}")
    markdown_lines.append("")

    # Comprehensive page metadata section
    markdown_lines.append("## 📄 Page Metadata")
    markdown_lines.append("")
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

    markdown_lines.append("")
    markdown_lines.append("---")
    markdown_lines.append("")

    # Group elements by type
    element_groups = {}
    for result in results:
        tag = result["tag"].upper()
        if tag not in element_groups:
            element_groups[tag] = []
        element_groups[tag].append(result)

    # Define the order of sections
    section_order = [
        "BUTTON",
        "A",
        "FORM",
        "INPUT",
        "H1",
        "H2",
        "H3",
        "H4",
        "H5",
        "H6",
        "P",
        "DIV",
        "SPAN",
        "SECTION",
        "LI",
        "LABEL",
        "NAV",
        "HEADER",
        "FOOTER",
        "MAIN",
    ]

    # Add sections in order
    for tag in section_order:
        if tag in element_groups:
            elements = element_groups[tag]

            # Section header with proper spacing and emoji
            if tag == "A":
                markdown_lines.append("## 🔗 Links")
            elif tag == "BUTTON":
                markdown_lines.append("## 🔘 Buttons")
            elif tag == "P":
                markdown_lines.append("## 📝 Paragraphs")
            elif tag == "DIV":
                markdown_lines.append("## 📦 Divs")
            elif tag == "SPAN":
                markdown_lines.append("## 🏷️ Spans")
            elif tag == "FORM":
                markdown_lines.append("## 📋 Forms")
            elif tag == "INPUT":
                markdown_lines.append("## 📄 Input Fields")
            elif tag.startswith("H"):
                markdown_lines.append("## 📰 Headers")
            elif tag == "SECTION":
                markdown_lines.append("## 📑 Sections")
            elif tag == "LI":
                markdown_lines.append("## 📋 List Items")
            elif tag == "LABEL":
                markdown_lines.append("## 🏷️ Labels")
            elif tag == "NAV":
                markdown_lines.append("## 🧭 Navigation")
            elif tag == "HEADER":
                markdown_lines.append("## 🎯 Header Elements")
            elif tag == "FOOTER":
                markdown_lines.append("## 🦶 Footer Elements")
            elif tag == "MAIN":
                markdown_lines.append("## 🎯 Main Content")
            else:
                markdown_lines.append(f"## {tag.title()}s")

            markdown_lines.append("")

            # Add content for this section
            for element in elements:
                if tag == "A" and element.get("href"):
                    # Format links as markdown links
                    href = element.get("href", "")
                    # Convert relative URLs to absolute
                    if href.startswith("/"):
                        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                        href = base_url + href
                    elif href.startswith("#"):
                        href = url + href
                    elif not href.startswith((
                        "http://",
                        "https://",
                        "mailto:",
                        "tel:",
                    )):
                        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                        href = base_url + "/" + href.lstrip("/")

                    markdown_lines.append(f"- [{element['text']}]({href})")
                else:
                    # For all other types, add as quoted text blocks
                    if element["text"].strip():  # Only add non-empty content
                        markdown_lines.append(f"> {element['text']}")
                        markdown_lines.append("")

            markdown_lines.append("")
            markdown_lines.append("---")
            markdown_lines.append("")

    # Add any remaining element types not in the ordered list
    for tag, elements in element_groups.items():
        if tag not in section_order:
            markdown_lines.append(f"## {tag.title()}s")
            markdown_lines.append("")

            for element in elements:
                if element["text"].strip():  # Only add non-empty content
                    markdown_lines.append(f"> {element['text']}")
                    markdown_lines.append("")

            markdown_lines.append("")
            markdown_lines.append("---")
            markdown_lines.append("")

    return "\n".join(markdown_lines).strip()


def display_results(results, url, page_metadata, extract_metadata, show_debug):
    """Display results in the Streamlit UI"""
    if not results:
        st.warning(
            "No text content found matching your filters. Try adjusting your filter criteria."
        )
        return

    st.success(f"Found {len(results)} text segments")

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

    if extract_metadata and any(page_metadata.values()):
        st.markdown('<div class="metadata-box">', unsafe_allow_html=True)
        st.subheader("📄 Page Metadata")
        meta_col1, meta_col2 = st.columns(2)

        with meta_col1:
            if page_metadata.get("title"):
                st.write(f"**Title:** {page_metadata['title']}")
            if page_metadata.get("description"):
                st.write(f"**Description:** {page_metadata['description'][:100]}...")
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

    st.subheader("📥 Export Options")
    col1, col2, col3 = st.columns(3)

    # Use the new organized text content function
    organized_text_content = create_organized_text_content(results, url, page_metadata)
    markdown_content = create_markdown_content(results, url, page_metadata)

    with col1:
        st.download_button(
            label="📄 Download as Text",
            data=organized_text_content,  # Use the new organized content
            file_name=f"scraped_text_{urlparse(url).netloc}.txt",
            mime="text/plain",
        )

    with col2:
        st.download_button(
            label="📝 Download as Markdown",
            data=markdown_content,
            file_name=f"scraped_content_{urlparse(url).netloc}.md",
            mime="text/markdown",
        )

    with col3:
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

    st.subheader("📝 Extracted Content")

    sort_by = st.selectbox(
        "Sort by:", ["order", "length_desc", "length_asc", "tag_type"]
    )

    if sort_by == "length_desc":
        results.sort(key=lambda x: x["length"], reverse=True)
    elif sort_by == "length_asc":
        results.sort(key=lambda x: x["length"])
    elif sort_by == "tag_type":
        results.sort(key=lambda x: (x["tag"], x["length"]), reverse=True)

    items_per_page = st.selectbox("Items per page:", [10, 25, 50, 100], index=1)
    total_pages = (len(results) - 1) // items_per_page + 1

    if total_pages > 1:
        page = st.selectbox("Page:", range(1, total_pages + 1))
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_results = results[start_idx:end_idx]
    else:
        page_results = results

    for i, result in enumerate(page_results, 1):
        title_parts = [
            f"#{i}",
            result["tag"].upper(),
            f"({result['length']} chars)",
        ]

        if result.get("id"):
            title_parts.insert(2, f"ID: {result['id']}")

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

            st.code(result["text"], language=None)
