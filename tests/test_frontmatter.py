import re

from repulp.frontmatter import (
    count_words,
    estimate_reading_time,
    generate_frontmatter,
    inject_frontmatter,
)


class TestCountWords:
    def test_simple_text(self):
        assert count_words("Hello world foo bar") == 4

    def test_markdown_stripped(self):
        assert count_words("# Hello\n\n**bold** text") == 3

    def test_urls_stripped(self):
        result = count_words("Visit https://example.com for more info")
        assert result == 4

    def test_empty(self):
        assert count_words("") == 0


class TestEstimateReadingTime:
    def test_short_text(self):
        assert estimate_reading_time(100) == "< 1 min"

    def test_exact_wpm(self):
        assert estimate_reading_time(200) == "1 min"

    def test_medium_text(self):
        assert estimate_reading_time(600) == "3 min"

    def test_very_short(self):
        assert estimate_reading_time(10) == "< 1 min"


class TestGenerateFrontmatter:
    def test_basic_frontmatter(self):
        fm = generate_frontmatter("# My Doc\n\nSome content here.", "report.pdf")
        assert "---" in fm
        assert 'title: "My Doc"' in fm
        assert 'source: "report.pdf"' in fm
        assert "word_count:" in fm
        assert "reading_time:" in fm
        assert "converted:" in fm

    def test_custom_title(self):
        fm = generate_frontmatter("Some text", "file.txt", title="Custom Title")
        assert 'title: "Custom Title"' in fm

    def test_extra_fields(self):
        fm = generate_frontmatter("Text", "file.txt", extra={"author": "Sunny"})
        assert 'author: "Sunny"' in fm

    def test_title_from_heading(self):
        fm = generate_frontmatter("# First Heading\n\nParagraph", "doc.pdf")
        assert 'title: "First Heading"' in fm

    def test_title_from_filename_no_heading(self):
        fm = generate_frontmatter("No heading here", "my-report.pdf")
        assert 'title: "my-report"' in fm


class TestInjectFrontmatter:
    def test_inject_adds_frontmatter(self):
        result = inject_frontmatter("# Hello\n\nWorld", "test.txt")
        assert result.startswith("---\n")
        assert "# Hello" in result
        assert "World" in result

    def test_inject_has_two_separators(self):
        result = inject_frontmatter("Content", "file.pdf")
        assert result.count("---") == 2
