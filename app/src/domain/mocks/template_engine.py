import random
import re
import uuid

from src.domain.mocks.schemas import MockTemplateContext


class TemplateEngine:
    def render(self, template: str, context: MockTemplateContext) -> str:
        """
        文字列内のプレースホルダーを置換する。

        Supported tags:
          {{uuid}}: Random UUIDv4
          {{now_iso}}: Current timestamp (ISO8601)
          {{random_int}}: Random integer (0-100)
        """
        result = template

        def replace_uuid(_match: re.Match) -> str:
            return str(uuid.uuid4())

        result = re.sub(r"\{\{uuid\}\}", replace_uuid, result)

        def replace_now_iso(_match: re.Match) -> str:
            return context.timestamp

        result = re.sub(r"\{\{now_iso\}\}", replace_now_iso, result)

        def replace_random_int(_match: re.Match) -> str:
            return str(random.randint(0, 100))

        return re.sub(r"\{\{random_int\}\}", replace_random_int, result)
