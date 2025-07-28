import streamlit as st
from urllib.parse import urlparse
import time


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
