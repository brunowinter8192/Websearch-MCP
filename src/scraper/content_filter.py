# INFRASTRUCTURE
SKIP_TAGS = {'aside', 'script', 'style', 'noscript', 'iframe', 'svg', 'nav', 'footer'}
CONTENT_TAGS = {'main', 'article', 'section', 'div', 'body'}


# ORCHESTRATOR
def filter_content(parsed: dict) -> list:
    nodes = parsed.get("nodes", [])
    filtered = remove_skip_tags(nodes)
    main_content = extract_main_content(filtered)
    clean_content = remove_navigation_attributes(main_content)
    return clean_content


# FUNCTIONS

# Remove navigation elements by attributes
def remove_navigation_attributes(nodes: list) -> list:
    result = []
    skip_depth = 0
    current_skip_tag = None
    filterable_tags = {'div', 'section', 'aside', 'ul', 'ol', 'li', 'span', 'label', 'button', 'input', 'form'}

    for node in nodes:
        if node["type"] == "start" and node["tag"] in filterable_tags:
            attrs = node.get("attrs", {})
            class_attr = attrs.get("class", "").lower()
            id_attr = attrs.get("id", "").lower()
            role_attr = attrs.get("role", "").lower()

            nav_patterns = ['vector-', 'mw-portlet', 'mw-panel', 'navigation', 'noprint', 'toc', 'sidebar', 'menu', 'tools', 'p-lang', 'p-tb', 'p-navigation', 'p-interaction', 'wmde-banner', 'cn-fundraising', 'frb']

            should_skip = (
                role_attr in ['navigation', 'complementary', 'banner'] or
                any(pattern in class_attr for pattern in nav_patterns) or
                any(pattern in id_attr for pattern in nav_patterns)
            )

            if should_skip:
                if skip_depth == 0:
                    current_skip_tag = node["tag"]
                skip_depth += 1
                continue

        if node["type"] == "end" and skip_depth > 0:
            if node["tag"] == current_skip_tag:
                skip_depth -= 1
                if skip_depth == 0:
                    current_skip_tag = None
            continue

        if skip_depth == 0:
            result.append(node)

    return result


# Remove nodes that belong to skip tags using stack-based tracking
def remove_skip_tags(nodes: list) -> list:
    result = []
    skip_stack = []

    for node in nodes:
        if node["type"] == "start" and node["tag"] in SKIP_TAGS:
            skip_stack.append(node["tag"])
            continue

        if node["type"] == "end" and len(skip_stack) > 0:
            if node["tag"] == skip_stack[-1]:
                skip_stack.pop()
            continue

        if len(skip_stack) == 0:
            result.append(node)

    return result


# Extract content from main/article tags or return all
def extract_main_content(nodes: list) -> list:
    main_start = find_content_tag_start(nodes)
    if main_start == -1:
        return nodes

    main_end = find_matching_end(nodes, main_start)
    if main_end == -1:
        return nodes

    return nodes[main_start:main_end + 1]


# Find index of first content tag with improved priority
def find_content_tag_start(nodes: list) -> int:
    for priority_tag in ['main', 'article', 'section']:
        for i, node in enumerate(nodes):
            if node["type"] == "start" and node["tag"] == priority_tag:
                attrs = node.get("attrs", {})
                class_attr = attrs.get("class", "").lower()
                id_attr = attrs.get("id", "").lower()

                if priority_tag in ['main', 'article']:
                    return i

                if 'content' in class_attr or 'content' in id_attr or 'main' in class_attr or 'article' in class_attr:
                    return i
    return -1


# Find matching end tag index
def find_matching_end(nodes: list, start_idx: int) -> int:
    if start_idx == -1:
        return -1

    tag = nodes[start_idx]["tag"]
    depth = 1

    for i in range(start_idx + 1, len(nodes)):
        node = nodes[i]
        if node["type"] == "start" and node["tag"] == tag:
            depth += 1
        elif node["type"] == "end" and node["tag"] == tag:
            depth -= 1
            if depth == 0:
                return i

    return -1
