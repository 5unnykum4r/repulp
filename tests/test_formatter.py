import json

from repulp.formatter import to_plain_text, to_json, format_output


class TestToPlainText:
    def test_strips_headings(self):
        result = to_plain_text("# Hello\n\n## World")
        assert "Hello" in result
        assert "#" not in result

    def test_strips_bold_italic(self):
        result = to_plain_text("This is **bold** and *italic*")
        assert result == "This is bold and italic"

    def test_strips_links(self):
        result = to_plain_text("Visit [Google](https://google.com)")
        assert result == "Visit Google"

    def test_strips_images(self):
        result = to_plain_text("![Alt](https://img.png)")
        assert result == "Alt"

    def test_empty(self):
        assert to_plain_text("") == ""


class TestToJson:
    def test_returns_valid_json(self):
        result = to_json("# Title\n\nContent", "test.pdf")
        data = json.loads(result)
        assert data["source"] == "test.pdf"
        assert "# Title" in data["content"]
        assert "Title" in data["plain_text"]
        assert "structure" in data

    def test_includes_metadata(self):
        result = to_json("Text", "file.txt", metadata={"author": "Sunny"})
        data = json.loads(result)
        assert data["metadata"]["author"] == "Sunny"


class TestFormatOutput:
    def test_md_passthrough(self):
        assert format_output("# Hello", "md") == "# Hello"

    def test_text_format(self):
        result = format_output("# Hello\n\n**World**", "text")
        assert "#" not in result
        assert "Hello" in result

    def test_json_format(self):
        result = format_output("# Title", "json", "test.pdf")
        data = json.loads(result)
        assert data["source"] == "test.pdf"
