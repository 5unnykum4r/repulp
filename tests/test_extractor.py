from repulp.extractor import (
    extract_tables,
    extract_links,
    extract_headings,
    extract_images,
    extract_elements,
    extract_all,
)


SAMPLE_MD = """# Main Title

Some intro text with a [link](https://example.com) and another [link2](https://other.com).

## Section One

| Name  | Age |
| ----- | --- |
| Alice | 30  |
| Bob   | 25  |

Here's an image: ![Alt text](https://example.com/image.png)

### Sub Section

Another [duplicate](https://example.com) link here.

| Product | Price |
| ------- | ----- |
| Widget  | $10   |
| Gadget  | $20   |

![Logo](https://example.com/logo.jpg)
"""


class TestExtractTables:
    def test_finds_all_tables(self):
        tables = extract_tables(SAMPLE_MD)
        assert len(tables) == 2

    def test_table_content(self):
        tables = extract_tables(SAMPLE_MD)
        assert "Alice" in tables[0]
        assert "Widget" in tables[1]

    def test_no_tables(self):
        assert extract_tables("# Just a heading\n\nNo tables here.") == []


class TestExtractLinks:
    def test_finds_unique_links(self):
        links = extract_links(SAMPLE_MD)
        urls = [l["url"] for l in links]
        assert "https://example.com" in urls
        assert "https://other.com" in urls

    def test_deduplicates(self):
        links = extract_links(SAMPLE_MD)
        urls = [l["url"] for l in links]
        assert urls.count("https://example.com") == 1

    def test_skips_data_urls(self):
        md = "![img](data:image/gif;base64,abc123)"
        links = extract_links(md)
        assert len(links) == 0

    def test_no_links(self):
        assert extract_links("Plain text only.") == []


class TestExtractHeadings:
    def test_finds_all_headings(self):
        headings = extract_headings(SAMPLE_MD)
        assert len(headings) == 3

    def test_heading_levels(self):
        headings = extract_headings(SAMPLE_MD)
        assert headings[0] == {"level": "1", "text": "Main Title"}
        assert headings[1] == {"level": "2", "text": "Section One"}
        assert headings[2] == {"level": "3", "text": "Sub Section"}


class TestExtractImages:
    def test_finds_images(self):
        images = extract_images(SAMPLE_MD)
        assert len(images) == 2

    def test_image_content(self):
        images = extract_images(SAMPLE_MD)
        assert images[0]["alt"] == "Alt text"
        assert images[0]["src"] == "https://example.com/image.png"

    def test_skips_data_urls(self):
        md = "![img](data:image/gif;base64,abc)"
        assert extract_images(md) == []


class TestExtractElements:
    def test_specific_elements(self):
        result = extract_elements(SAMPLE_MD, ["tables", "headings"])
        assert len(result.tables) == 2
        assert len(result.headings) == 3
        assert result.links == []
        assert result.images == []

    def test_all_elements(self):
        result = extract_all(SAMPLE_MD)
        assert len(result.tables) == 2
        assert len(result.links) >= 2
        assert len(result.headings) == 3
        assert len(result.images) == 2
