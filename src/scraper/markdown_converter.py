# INFRASTRUCTURE
import re
from urllib.parse import urlparse, urlunparse

INLINE_TAGS = {'a', 'strong', 'b', 'em', 'i', 'code', 'span', 'img'}
BLOCK_TAGS = {'p', 'div', 'section', 'article', 'main', 'blockquote'}
HEADING_TAGS = {'h1': '# ', 'h2': '## ', 'h3': '### ', 'h4': '#### ', 'h5': '##### ', 'h6': '###### '}
LIST_TAGS = {'ul', 'ol'}


# ORCHESTRATOR
def to_markdown(nodes: list, max_content_length: int) -> str:
    raw_markdown = convert_nodes_to_markdown(nodes)
    cleaned = clean_markdown_artifacts(raw_markdown)
    cleaned = clean_whitespace(cleaned)
    return cleaned


# FUNCTIONS

# Strip tracking parameters from URLs
def strip_tracking_params(url: str) -> str:
    if not url or '?' not in url:
        return url
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', parsed.fragment))


# Extract image markdown with lazy loading support and size filtering
def extract_image_markdown(attrs: dict) -> str:
    src = attrs.get("src", "")
    if not src or src.startswith("data:"):
        src = attrs.get("data-src", "") or attrs.get("data-lazy-src", "")
    if not src:
        srcset = attrs.get("srcset", "")
        if srcset:
            src = srcset.split(",")[-1].strip().split(" ")[0]
    if not src:
        return ""

    width = attrs.get("width", "")
    height = attrs.get("height", "")
    if width and width.isdigit() and int(width) < 100:
        return ""
    if height and height.isdigit() and int(height) < 100:
        return ""
    if "resize:fill:32" in src or "resize:fill:48" in src or "resize:fill:64" in src:
        return ""

    alt = attrs.get("alt", "")
    return f"![{alt}]({src})"


# Check if space should be added before inline tag marker
def should_add_space_before(result: list, last_text_node: dict | None, nodes: list, current_index: int) -> bool:
    if not last_text_node or not last_text_node.get("has_trailing_space"):
        return False
    if not result or not result[-1]:
        return False
    last_char = result[-1][-1:]
    if not last_char.isalnum():
        return False
    if current_index > 0 and nodes[current_index - 1]["type"] == "start":
        return False
    return True


# Find next node in list
def find_next_node(nodes: list, current_index: int) -> dict | None:
    if current_index + 1 < len(nodes):
        return nodes[current_index + 1]
    return None


# Check if space should be added after inline tag marker
def should_add_space_after(result: list, nodes: list, current_index: int) -> bool:
    next_node = find_next_node(nodes, current_index)
    if not next_node or next_node["type"] != "text":
        return False
    if not next_node.get("has_leading_space"):
        return False
    return True


# Convert parsed nodes to markdown string
def convert_nodes_to_markdown(nodes: list) -> str:
    result = []
    list_stack = []
    link_href = None
    pre_depth = 0
    last_text_node = None

    for i, node in enumerate(nodes):
        if node["type"] == "start":
            tag = node["tag"]
            attrs = node.get("attrs", {})

            if tag in HEADING_TAGS:
                result.append("\n\n" + HEADING_TAGS[tag])
            elif tag == "p":
                result.append("\n\n")
            elif tag == "br":
                result.append("\n")
            elif tag == "strong" or tag == "b":
                if should_add_space_before(result, last_text_node, nodes, i):
                    result.append(" ")
                result.append("**")
            elif tag == "em" or tag == "i":
                if should_add_space_before(result, last_text_node, nodes, i):
                    result.append(" ")
                result.append("*")
            elif tag == "code":
                if pre_depth == 0:
                    if should_add_space_before(result, last_text_node, nodes, i):
                        result.append(" ")
                    result.append("`")
            elif tag == "pre":
                pre_depth += 1
                result.append("\n\n```\n")
            elif tag == "a":
                link_href = strip_tracking_params(attrs.get("href", ""))
                if should_add_space_before(result, last_text_node, nodes, i):
                    result.append(" ")
                result.append("[")
            elif tag == "img":
                img_md = extract_image_markdown(attrs)
                if img_md:
                    result.append(img_md)
            elif tag == "ul":
                list_stack.append("ul")
                result.append("\n")
            elif tag == "ol":
                list_stack.append("ol")
                result.append("\n")
            elif tag == "li":
                indent = "  " * (len(list_stack) - 1)
                if list_stack and list_stack[-1] == "ol":
                    result.append(f"{indent}1. ")
                else:
                    result.append(f"{indent}- ")
            elif tag == "blockquote":
                result.append("\n\n> ")
            elif tag in BLOCK_TAGS:
                result.append("\n\n")

        elif node["type"] == "end":
            tag = node["tag"]

            if tag in HEADING_TAGS:
                result.append("\n")
            elif tag == "strong" or tag == "b":
                result.append("**")
                if should_add_space_after(result, nodes, i):
                    result.append(" ")
            elif tag == "em" or tag == "i":
                result.append("*")
                if should_add_space_after(result, nodes, i):
                    result.append(" ")
            elif tag == "code":
                if pre_depth == 0:
                    result.append("`")
                    if should_add_space_after(result, nodes, i):
                        result.append(" ")
            elif tag == "pre":
                pre_depth -= 1
                result.append("\n```\n\n")
            elif tag == "a":
                result.append(f"]({link_href})")
                if should_add_space_after(result, nodes, i):
                    result.append(" ")
                link_href = None
            elif tag == "li":
                result.append("\n")
            elif tag == "ul" or tag == "ol":
                if list_stack:
                    list_stack.pop()
                result.append("\n")
            elif tag in BLOCK_TAGS:
                result.append("\n")

        elif node["type"] == "text":
            if node.get("in_pre", False):
                result.append(node["content"])
            else:
                need_space = False

                if node.get("has_leading_space") and result and result[-1] and result[-1][-1:].isalnum():
                    need_space = True

                if last_text_node and last_text_node.get("has_trailing_space") and result and result[-1] and result[-1][-1:].isalnum():
                    need_space = True

                if need_space and result and result[-1] not in [' ', '\n']:
                    result.append(' ')

                result.append(node["content"])
            last_text_node = node

        elif node["type"] == "self_closing":
            tag = node["tag"]
            attrs = node.get("attrs", {})

            if tag == "br":
                result.append("\n")
            elif tag == "img":
                img_md = extract_image_markdown(attrs)
                if img_md:
                    result.append(img_md)
            elif tag == "hr":
                result.append("\n\n---\n\n")

    return "".join(result)


# Remove Wikipedia-specific artifacts from Markdown
def clean_markdown_artifacts(markdown: str) -> str:
    markdown = re.sub(r'\[\[(\d+)\]\]\(#cite_note-[^)]*\)', '', markdown)
    markdown = re.sub(r'\[\[(\d+)\]\]\([^)]*cite[^)]*\)', '', markdown)
    markdown = re.sub(r'\[\]\(/wiki/[^)]*\)', '', markdown)
    markdown = re.sub(r'\[([^\]]+)\]\(/wiki/[^)]*\)', r' \1 ', markdown)
    markdown = re.sub(r'\[\s*\]\([^)]+\)', '', markdown)

    replacements = {
        '%C3%A4': 'ä', '%C3%84': 'Ä',
        '%C3%BC': 'ü', '%C3%9C': 'Ü',
        '%C3%B6': 'ö', '%C3%96': 'Ö',
        '%C3%9F': 'ß',
        '%28': '(', '%29': ')',
    }
    for encoded, decoded in replacements.items():
        markdown = markdown.replace(encoded, decoded)

    return markdown


# Remove excessive whitespace while preserving code blocks
def clean_whitespace(text: str) -> str:
    parts = []
    current_pos = 0
    in_code_block = False

    pattern = r'```'
    for match in re.finditer(pattern, text):
        chunk = text[current_pos:match.start()]

        if in_code_block:
            parts.append(chunk)
        else:
            chunk = re.sub(r' {2,}', ' ', chunk)
            chunk = re.sub(r'\n{3,}', '\n\n', chunk)
            chunk = re.sub(r'\n ', '\n', chunk)
            chunk = re.sub(r' \n', '\n', chunk)
            parts.append(chunk)

        parts.append('```')
        current_pos = match.end()
        in_code_block = not in_code_block

    chunk = text[current_pos:]
    if not in_code_block:
        chunk = re.sub(r' {2,}', ' ', chunk)
        chunk = re.sub(r'\n{3,}', '\n\n', chunk)
        chunk = re.sub(r'\n ', '\n', chunk)
        chunk = re.sub(r' \n', '\n', chunk)
    parts.append(chunk)

    return ''.join(parts).strip()
