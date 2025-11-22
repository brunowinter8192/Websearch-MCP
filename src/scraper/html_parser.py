# INFRASTRUCTURE
from html.parser import HTMLParser
from html import unescape


# ORCHESTRATOR
def parse_html(html: str) -> dict:
    parser = HTMLContentParser()
    parser.feed(html)
    return parser.get_result()


# FUNCTIONS

# HTMLParser subclass that builds structured representation
class HTMLContentParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.result = []
        self.tag_stack = []
        self.current_attrs = {}
        self.pre_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "pre":
            self.pre_depth += 1
        self.tag_stack.append(tag)
        self.current_attrs[tag] = dict(attrs)
        self.result.append({
            "type": "start",
            "tag": tag,
            "attrs": dict(attrs)
        })

    def handle_endtag(self, tag):
        if tag == "pre" and self.pre_depth > 0:
            self.pre_depth -= 1
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()
        self.result.append({
            "type": "end",
            "tag": tag
        })

    def handle_data(self, data):
        text = unescape(data)

        if self.pre_depth > 0:
            if text:
                self.result.append({
                    "type": "text",
                    "content": text,
                    "has_leading_space": False,
                    "has_trailing_space": False,
                    "parent_tags": list(self.tag_stack),
                    "in_pre": True
                })
        else:
            has_leading_space = bool(text and text[0].isspace())
            has_trailing_space = bool(text and text[-1].isspace())
            stripped = text.strip()
            if stripped:
                self.result.append({
                    "type": "text",
                    "content": stripped,
                    "has_leading_space": has_leading_space,
                    "has_trailing_space": has_trailing_space,
                    "parent_tags": list(self.tag_stack)
                })

    def handle_startendtag(self, tag, attrs):
        self.result.append({
            "type": "self_closing",
            "tag": tag,
            "attrs": dict(attrs)
        })

    def get_result(self) -> dict:
        return {
            "nodes": self.result,
            "tag_stack": self.tag_stack
        }
