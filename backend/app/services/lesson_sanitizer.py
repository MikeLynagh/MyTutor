from html import escape
from html.parser import HTMLParser


class _AllowedHtmlSanitizer(HTMLParser):
    allowed_tags = {"article", "section", "h2", "h3", "p", "ul", "ol", "li", "strong", "em", "code", "pre", "blockquote"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag in self.allowed_tags:
            self.parts.append(f"<{tag}>")

    def handle_endtag(self, tag: str):
        if tag in self.allowed_tags:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data: str):
        self.parts.append(escape(data))

    def handle_entityref(self, name: str):
        self.parts.append(f"&{name};")

    def handle_charref(self, name: str):
        self.parts.append(f"&#{name};")

    def get_html(self) -> str:
        return "".join(self.parts)


class LessonSanitizer:
    def sanitize(self, html: str) -> str:
        parser = _AllowedHtmlSanitizer()
        parser.feed(html)
        parser.close()
        return parser.get_html().strip()
