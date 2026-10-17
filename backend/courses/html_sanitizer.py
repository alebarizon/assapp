"""
Sanitizador HTML por allowlist (conteúdo do editor rico de aulas e descrição do curso).
"""
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse

ALLOWED_TAGS = {
    "p", "br", "strong", "b", "em", "i", "u", "s", "strike", "blockquote", "pre", "code",
    "h1", "h2", "h3", "h4", "ul", "ol", "li", "a", "img", "span", "sub", "sup", "hr",
}
VOID_TAGS = {"br", "img", "hr"}
DROP_CONTENT_TAGS = {"script", "style", "iframe", "object", "embed", "template", "noscript"}
ALLOWED_ATTRS = {
    "a": {"href", "target", "rel"},
    "img": {"src", "alt", "width", "height"},
    "*": {"class"},
}
ALLOWED_SCHEMES = {"http", "https", "mailto", ""}


def _safe_url(value: str) -> bool:
    value = (value or "").strip()
    if value.startswith("//"):
        return False
    scheme = urlparse(value).scheme.lower()
    return scheme in ALLOWED_SCHEMES


class _Sanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.open_tags: list[str] = []
        self.drop_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in DROP_CONTENT_TAGS:
            self.drop_depth += 1
            return
        if self.drop_depth or tag not in ALLOWED_TAGS:
            return
        allowed = ALLOWED_ATTRS.get(tag, set()) | ALLOWED_ATTRS["*"]
        parts = []
        for name, value in attrs:
            name = name.lower()
            if name not in allowed or value is None or name == "rel":
                continue
            if name in ("href", "src") and not _safe_url(value):
                continue
            if name == "class" and not all(c.startswith("ql-") for c in value.split()):
                continue
            parts.append(f' {name}="{escape(value, quote=True)}"')
        if tag == "a":
            parts.append(' rel="noopener noreferrer"')
        self.out.append(f"<{tag}{''.join(parts)}>")
        if tag not in VOID_TAGS:
            self.open_tags.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag.lower() not in VOID_TAGS and self.open_tags and self.open_tags[-1] == tag.lower():
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in DROP_CONTENT_TAGS:
            self.drop_depth = max(0, self.drop_depth - 1)
            return
        if self.drop_depth or tag not in ALLOWED_TAGS or tag in VOID_TAGS:
            return
        if tag in self.open_tags:
            while self.open_tags:
                current = self.open_tags.pop()
                self.out.append(f"</{current}>")
                if current == tag:
                    break

    def handle_data(self, data):
        if not self.drop_depth:
            self.out.append(escape(data, quote=False))

    def result(self) -> str:
        while self.open_tags:
            self.out.append(f"</{self.open_tags.pop()}>")
        return "".join(self.out)


def sanitize_html(value: str | None) -> str:
    if not value:
        return ""
    parser = _Sanitizer()
    parser.feed(value)
    parser.close()
    return parser.result()
