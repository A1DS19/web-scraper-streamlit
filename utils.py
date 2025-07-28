import streamlit as st
from urllib.parse import urlparse
import time
import json
import re


def markdown_to_text(markdown_string):
    """
    Converts a markdown string to plain text.
    """
    # Remove headers
    text = re.sub(r"#+\s", "", markdown_string)
    # Remove bold and italics
    text = re.sub(r"\*\*(.*?)\*\*|\*(.*?)\*", r"\1\2", text)
    # Remove strikethrough
    text = re.sub(r"~~(.*?)~~", r"\1", text)
    # Remove inline code
    text = re.sub(r"`(.*?)`", r"\1", text)
    # Remove code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Remove links, keeping the text
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    # Remove images
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    # Remove horizontal rules
    text = re.sub(r"---", "", text)
    # Remove blockquotes
    text = re.sub(r"^>+\s?", "", text, flags=re.MULTILINE)
    # Remove list items
    text = re.sub(r"^\s*[\*\-]\s+", "", text, flags=re.MULTILINE)
    # Remove extra newlines
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


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
    other_elements = [
        r for r in results if r["tag"] not in ["button", "a", "form", "input"]
    ]

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
    if other_elements:
        markdown_lines.append("## 📜 Other Content")
        for i, result in enumerate(other_elements, 1):
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
            else:
                # Regular content with element ID or smart fallback
                if element_id:
                    section_title = f"{element_id}"
                else:
                    section_title = f"{element_tag.lower()}-{i}"

                markdown_lines.append(f"### {section_title} `({element_tag})`")
                markdown_lines.append(f"\n{result['text']}")

            # Add comprehensive metadata for all elements
            metadata_parts = [f"**Length:** {result['length']} chars"]

            if result.get("id"):
                metadata_parts.append(f"**ID:** `{result['id']}`")

            markdown_lines.append(f"\n*{' | '.join(metadata_parts)}*")
            markdown_lines.append("\n---\n")

    return "\n".join(markdown_lines)


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

    markdown_content = create_markdown_content(results, url, page_metadata)
    text_content = markdown_to_text(markdown_content)

    with col1:
        st.download_button(
            label="📄 Download as Text",
            data=text_content,
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

