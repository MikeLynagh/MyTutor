from html import escape
from html.parser import HTMLParser


class _AllowedHtmlSanitizer(HTMLParser):
    allowed_tags = {
        "article",
        "section",
        "h2",
        "h3",
        "p",
        "ul",
        "ol",
        "li",
        "strong",
        "em",
        "code",
        "pre",
        "blockquote",
        "figure",
        "figcaption",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "hr",
        "div",
        "span",
    }
    allowed_classes = {
        "lesson-callout",
        "lesson-example",
        "lesson-check",
        "lesson-sequence",
        "lesson-comparison",
        "lesson-diagram",
        "lesson-muted",
        "lesson-label",
    }
    ignored_content_tags = {"script", "style", "iframe"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.ignored_depth = 0

    def handle_starttag(self, tag: str, attrs):
        if tag in self.ignored_content_tags:
            self.ignored_depth += 1
            return

        if tag in self.allowed_tags:
            class_attr = self._sanitize_class(attrs)
            self.parts.append(f"<{tag}{class_attr}>")

    def handle_endtag(self, tag: str):
        if tag in self.ignored_content_tags and self.ignored_depth > 0:
            self.ignored_depth -= 1
            return

        if tag in self.allowed_tags:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data: str):
        if self.ignored_depth > 0:
            return
        self.parts.append(escape(data))

    def handle_entityref(self, name: str):
        if self.ignored_depth > 0:
            return
        self.parts.append(f"&{name};")

    def handle_charref(self, name: str):
        if self.ignored_depth > 0:
            return
        self.parts.append(f"&#{name};")

    def get_html(self) -> str:
        return "".join(self.parts)

    def _sanitize_class(self, attrs) -> str:
        class_value = ""
        for name, value in attrs:
            if name == "class" and value:
                class_value = value
                break

        if not class_value:
            return ""

        safe_classes = [class_name for class_name in class_value.split() if class_name in self.allowed_classes]
        if not safe_classes:
            return ""

        return f' class="{escape(" ".join(safe_classes), quote=True)}"'


class LessonSanitizer:
    def sanitize(self, html: str) -> str:
        parser = _AllowedHtmlSanitizer()
        parser.feed(html)
        parser.close()
        return parser.get_html().strip()
