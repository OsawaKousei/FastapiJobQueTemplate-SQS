from src.domain.mocks.schemas import MockTemplateContext
from src.domain.mocks.template_engine import TemplateEngine


class TestTemplateEngine:
    def test_replace_uuid(self):
        engine = TemplateEngine()
        template = "ID: {{uuid}}"
        context = MockTemplateContext(
            request_id="req-1", timestamp="2024-01-01T00:00:00Z"
        )

        result = engine.render(template, context)

        assert "ID: " in result
        assert "{{uuid}}" not in result
        # UUID format check (simple length check)
        assert len(result.split(": ")[1]) == 36

    def test_replace_now_iso(self):
        engine = TemplateEngine()
        template = "Time: {{now_iso}}"
        context = MockTemplateContext(
            request_id="req-1", timestamp="2024-01-01T00:00:00Z"
        )

        result = engine.render(template, context)

        assert "Time: " in result
        assert "{{now_iso}}" not in result
        # ISO format check (simple check)
        assert "T" in result

    def test_replace_random_int(self):
        engine = TemplateEngine()
        template = "Score: {{random_int}}"
        context = MockTemplateContext(
            request_id="req-1", timestamp="2024-01-01T00:00:00Z"
        )

        result = engine.render(template, context)

        assert "Score: " in result
        assert "{{random_int}}" not in result
        val = int(result.split(": ")[1])
        assert 0 <= val <= 100

    def test_replace_multiple(self):
        engine = TemplateEngine()
        template = "{{uuid}} / {{random_int}}"
        context = MockTemplateContext(
            request_id="req-1", timestamp="2024-01-01T00:00:00Z"
        )

        result = engine.render(template, context)

        assert "{{uuid}}" not in result
        assert "{{random_int}}" not in result

    def test_no_tags(self):
        engine = TemplateEngine()
        template = "Hello World"
        context = MockTemplateContext(
            request_id="req-1", timestamp="2024-01-01T00:00:00Z"
        )

        result = engine.render(template, context)

        assert result == "Hello World"
