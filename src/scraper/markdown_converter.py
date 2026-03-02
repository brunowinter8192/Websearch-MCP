# INFRASTRUCTURE
import re
from urllib.parse import urlparse, urlunparse

INLINE_TAGS = {'a', 'strong', 'b', 'em', 'i', 'code', 'span', 'img'}
BLOCK_TAGS = {'p', 'div', 'section', 'article', 'main', 'blockquote'}
HEADING_TAGS = {'h1': '# ', 'h2': '## ', 'h3': '### ', 'h4': '#### ', 'h5': '##### ', 'h6': '###### '}
LIST_TAGS = {'ul', 'ol'}
TABLE_TAGS = {'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td'}


# ORCHESTRATOR
def to_markdown(nodes: list, max_content_length: int, cleanup_tags: list = []) -> str:
    raw_markdown = convert_nodes_to_markdown(nodes)
    cleaned = clean_markdown_artifacts(raw_markdown, cleanup_tags)
    cleaned = clean_whitespace(cleaned)
    return cleaned


# FUNCTIONS

# Strip tracking parameters from URLs
def strip_tracking_params(url: str) -> str:
    if not url or '?' not in url:
        return url
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', parsed.fragment))


# Sanitize image alt text for markdown compatibility
def sanitize_image_alt(alt: str) -> str:
    alt = re.sub(r'\.(jpg|jpeg|png|gif|webp|svg|bmp)\s*$', '', alt, flags=re.IGNORECASE)
    alt = re.sub(r'[\[\]\(\)]', '', alt)
    if len(alt) > 100:
        alt = alt[:97] + '...'
    return alt.strip()


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

    alt = sanitize_image_alt(attrs.get("alt", ""))
    return f"![{alt}]({src})"


# Check if space should be added before inline tag marker
def should_add_space_before(result: list, last_text_node: dict | None, nodes: list, current_index: int, trailing_space_consumed: bool = False) -> bool:
    if not result or not result[-1]:
        return False
    if last_text_node and last_text_node.get("has_trailing_space") and not trailing_space_consumed:
        return True
    last_char = result[-1][-1:]
    if not last_char.isalnum():
        return False
    current_node = nodes[current_index] if current_index < len(nodes) else None
    if current_node and current_node.get("tag") in {'strong', 'b', 'em', 'i', 'code'}:
        if current_index > 0 and nodes[current_index - 1].get("type") == "text":
            prev_content = nodes[current_index - 1].get("content", "")
            if prev_content and prev_content[-1].isalnum():
                return True
    return False


# Find next node in list
def find_next_node(nodes: list, current_index: int) -> dict | None:
    if current_index + 1 < len(nodes):
        return nodes[current_index + 1]
    return None


# Check if space should be added after inline tag marker
def should_add_space_after(result: list, nodes: list, current_index: int) -> bool:
    idx = current_index + 1
    while idx < len(nodes):
        next_node = nodes[idx]
        node_type = next_node.get("type")

        if node_type == "text":
            if next_node.get("has_leading_space"):
                return True
            next_content = next_node.get("content", "")
            if not next_content:
                return False
            first_char = next_content[0]
            if first_char.isalnum():
                return True
            if first_char in '([{':
                return True
            return False

        if node_type == "start":
            tag = next_node.get("tag", "")
            if tag in INLINE_TAGS:
                idx += 1
                continue
            return False

        return False

    return False


# Process opening HTML tag and append markdown equivalent
def handle_start_tag(node: dict, result: list, list_stack: list, pre_depth: int,
                     last_text_node: dict | None, nodes: list, current_index: int,
                     table_state: dict, trailing_space_state: list = None) -> tuple[str | None, int]:
    if trailing_space_state is None:
        trailing_space_state = [False]

    tag = node["tag"]
    attrs = node.get("attrs", {})
    link_href = None

    if tag in HEADING_TAGS:
        result.append("\n\n" + HEADING_TAGS[tag])
    elif tag == "p":
        result.append("\n\n")
    elif tag == "br":
        result.append("\n")
    elif tag == "strong" or tag == "b":
        if should_add_space_before(result, last_text_node, nodes, current_index, trailing_space_state[0]):
            result.append(" ")
            if last_text_node and last_text_node.get("has_trailing_space"):
                trailing_space_state[0] = True
        result.append("**")
    elif tag == "em" or tag == "i":
        if should_add_space_before(result, last_text_node, nodes, current_index, trailing_space_state[0]):
            result.append(" ")
            if last_text_node and last_text_node.get("has_trailing_space"):
                trailing_space_state[0] = True
        result.append("*")
    elif tag == "code":
        if pre_depth == 0:
            if should_add_space_before(result, last_text_node, nodes, current_index, trailing_space_state[0]):
                result.append(" ")
                if last_text_node and last_text_node.get("has_trailing_space"):
                    trailing_space_state[0] = True
            result.append("`")
    elif tag == "pre":
        pre_depth += 1
        result.append("\n\n```\n")
    elif tag == "a":
        link_href = strip_tracking_params(attrs.get("href", ""))
        if should_add_space_before(result, last_text_node, nodes, current_index, trailing_space_state[0]):
            result.append(" ")
            if last_text_node and last_text_node.get("has_trailing_space"):
                trailing_space_state[0] = True
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
    elif tag == "table":
        result.append("\n\n")
        table_state["in_table"] = True
        table_state["first_row"] = True
        table_state["is_header_row"] = False
    elif tag == "thead":
        table_state["is_header_row"] = True
    elif tag == "tr":
        result.append("| ")
        table_state["cell_count"] = 0
    elif tag == "th":
        table_state["is_header_row"] = True
    elif tag == "td":
        pass
    elif tag in BLOCK_TAGS:
        result.append("\n\n")

    return link_href, pre_depth


# Process closing HTML tag and append markdown equivalent
def handle_end_tag(node: dict, result: list, list_stack: list, pre_depth: int,
                   link_href: str | None, nodes: list, current_index: int,
                   table_state: dict) -> tuple[str | None, int]:
    tag = node["tag"]

    if tag in HEADING_TAGS:
        result.append("\n")
    elif tag == "strong" or tag == "b":
        result.append("**")
        if should_add_space_after(result, nodes, current_index):
            result.append(" ")
    elif tag == "em" or tag == "i":
        result.append("*")
        if should_add_space_after(result, nodes, current_index):
            result.append(" ")
    elif tag == "code":
        if pre_depth == 0:
            result.append("`")
            if should_add_space_after(result, nodes, current_index):
                result.append(" ")
    elif tag == "pre":
        pre_depth -= 1
        result.append("\n```\n\n")
    elif tag == "a":
        result.append(f"]({link_href})")
        if should_add_space_after(result, nodes, current_index):
            result.append(" ")
        link_href = None
    elif tag == "li":
        result.append("\n")
    elif tag == "ul" or tag == "ol":
        if list_stack:
            list_stack.pop()
        result.append("\n")
    elif tag == "th" or tag == "td":
        result.append(" | ")
        table_state["cell_count"] = table_state.get("cell_count", 0) + 1
    elif tag == "tr":
        result.append("\n")
        if table_state.get("is_header_row") and table_state.get("first_row"):
            cell_count = table_state.get("cell_count", 0)
            if cell_count > 0:
                separator = "| " + " | ".join(["---"] * cell_count) + " |\n"
                result.append(separator)
            table_state["first_row"] = False
            table_state["is_header_row"] = False
    elif tag == "thead":
        table_state["is_header_row"] = False
    elif tag == "table":
        result.append("\n")
        table_state["in_table"] = False
    elif tag in BLOCK_TAGS:
        result.append("\n")

    return link_href, pre_depth


# Process text content with whitespace normalization
def handle_text_node(node: dict, result: list, last_text_node: dict | None) -> None:
    if node.get("in_pre", False):
        result.append(node["content"])
        return

    need_space = False

    if node.get("has_leading_space") and result and result[-1] and result[-1][-1:].isalnum():
        need_space = True

    if last_text_node and last_text_node.get("has_trailing_space") and result and result[-1] and result[-1][-1:].isalnum():
        need_space = True

    if need_space and result and result[-1] not in [' ', '\n']:
        result.append(' ')

    result.append(node["content"])


# Process self-closing HTML tag (br, img, hr)
def handle_self_closing_tag(node: dict, result: list) -> None:
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


# Convert parsed nodes to markdown string
def convert_nodes_to_markdown(nodes: list) -> str:
    result = []
    list_stack = []
    link_href = None
    pre_depth = 0
    last_text_node = None
    trailing_space_state = [False]
    table_state = {
        "in_table": False,
        "first_row": True,
        "is_header_row": False,
        "cell_count": 0
    }

    for i, node in enumerate(nodes):
        node_type = node["type"]

        if node_type == "start":
            new_link_href, pre_depth = handle_start_tag(
                node, result, list_stack, pre_depth, last_text_node, nodes, i, table_state, trailing_space_state
            )
            if new_link_href is not None:
                link_href = new_link_href
        elif node_type == "end":
            link_href, pre_depth = handle_end_tag(
                node, result, list_stack, pre_depth, link_href, nodes, i, table_state
            )
        elif node_type == "text":
            handle_text_node(node, result, last_text_node)
            last_text_node = node
            trailing_space_state[0] = False
        elif node_type == "self_closing":
            handle_self_closing_tag(node, result)

    return "".join(result)


# Run profile-selected and generic cleanup on markdown
def clean_markdown_artifacts(markdown: str, cleanup_tags: list) -> str:
    cleanup_map = {
        "wiki_citations": clean_wiki_citations,
        "wiki_links": clean_wiki_links,
        "wiki_redlinks": clean_wiki_redlinks,
        "sphinx_source": clean_sphinx_source,
        "german_url_decode": clean_german_url_decode,
    }

    for tag in cleanup_tags:
        if tag in cleanup_map:
            markdown = cleanup_map[tag](markdown)

    markdown = clean_generic_artifacts(markdown)
    return markdown


# Remove Wikipedia citation references
def clean_wiki_citations(markdown: str) -> str:
    markdown = re.sub(r'\[\[(\d+)\]\]\(#cite_note-[^)]*\)', '', markdown)
    markdown = re.sub(r'\[\[(\d+)\]\]\([^)]*cite[^)]*\)', '', markdown)
    markdown = re.sub(r'\[\d+\](?!\()', '', markdown)
    return markdown


# Remove Wikipedia internal /wiki/ links, keep link text
def clean_wiki_links(markdown: str) -> str:
    markdown = re.sub(r'\(\s*\[([^\]]+)\]\(/wiki/[^)]*\)\s*\)', r'(\1)', markdown)
    markdown = re.sub(r'\[\]\(/wiki/[^)]*\)', '', markdown)
    markdown = re.sub(r'\[([^\]]+)\]\(/wiki/[^)]*\)[,.:;)\*]*', r'\1', markdown)
    return markdown


# Remove Wikipedia redlinks (/w/index.php), keep link text
def clean_wiki_redlinks(markdown: str) -> str:
    markdown = re.sub(r'\[([^\]]+)\]\(/w/index\.php[^)]*\)', r'\1', markdown)
    return markdown


# Remove Sphinx [source] buttons and paragraph markers
def clean_sphinx_source(markdown: str) -> str:
    markdown = re.sub(r'\[\[source\]\]\([^)]+\)', '', markdown)
    markdown = re.sub(r'\[source\]', '', markdown)
    markdown = re.sub(r'\[¶\]', '', markdown)
    markdown = re.sub(r'\[↑\]', '', markdown)
    return markdown


# Decode German URL-encoded characters
def clean_german_url_decode(markdown: str) -> str:
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


# Remove generic markdown artifacts that apply to all profiles
def clean_generic_artifacts(markdown: str) -> str:
    markdown = re.sub(r'\[​\]\([^)]+\)', '', markdown)
    markdown = re.sub(r'\[#\]\(#[^)]+\)', '', markdown)
    markdown = re.sub(r'\[\]\(#[^)]+\)', '', markdown)
    markdown = re.sub(r'\[#\](?!\()', '', markdown)

    markdown = re.sub(r'\[\[([^\]]+)\]\]\([^)]+\)', '', markdown)
    markdown = re.sub(r'\(#[^)]+\)', '', markdown)

    markdown = re.sub(r'!\[\[([^\]]+)\]\]\([^)]+\)', r'\1', markdown)
    markdown = re.sub(r'!\[\[', '![', markdown)

    markdown = re.sub(r'!\[\s*\]\([^)]+\)', '', markdown)
    markdown = re.sub(r'\[\s*\]\([^)]+\)', '', markdown)
    markdown = re.sub(r'\[\]', '', markdown)

    markdown = re.sub(r'\s*\.(jpg|jpeg|png|gif|webp|svg)\s*\)', '', markdown, flags=re.IGNORECASE)

    markdown = re.sub(r'\(\s*\)', '', markdown)
    markdown = re.sub(r'\)\s*,\s*\)', '),', markdown)
    markdown = re.sub(r'\)\*\s+', ' ', markdown)
    markdown = re.sub(r'\):\*\s+', ': ', markdown)
    markdown = re.sub(r'\s+\)', ')', markdown)
    markdown = re.sub(r'\(\s+', '(', markdown)

    return markdown


# Clean non-code-block chunk of whitespace issues
def clean_whitespace_chunk(chunk: str) -> str:
    chunk = re.sub(r' {2,}', ' ', chunk)
    chunk = re.sub(r'\n{3,}', '\n\n', chunk)
    chunk = re.sub(r'\n ', '\n', chunk)
    chunk = re.sub(r' \n', '\n', chunk)
    chunk = re.sub(r'^(-)\s*\n+(\s*)', r'\1 ', chunk, flags=re.MULTILINE)
    chunk = re.sub(r'^(\d+\.)\s*\n+(\s*)', r'\1 ', chunk, flags=re.MULTILINE)
    chunk = re.sub(r'^\s*-\s*$', '', chunk, flags=re.MULTILINE)
    chunk = re.sub(r'(- )+(?=- |##)', '', chunk, flags=re.MULTILINE)
    chunk = re.sub(r'\*{3,}', '*, ', chunk)
    chunk = re.sub(r'\*\*([^*]+)\*\*\(', r'**\1** (', chunk)
    chunk = re.sub(r'\*([^*]+)\*\(', r'*\1* (', chunk)
    return chunk


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
            parts.append(clean_whitespace_chunk(chunk))

        parts.append('```')
        current_pos = match.end()
        in_code_block = not in_code_block

    chunk = text[current_pos:]
    if not in_code_block:
        chunk = clean_whitespace_chunk(chunk)
    parts.append(chunk)

    return ''.join(parts).strip()
