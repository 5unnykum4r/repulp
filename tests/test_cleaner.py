from repulp.cleaner import clean_markdown


class TestCleanMarkdown:
    def test_normalize_multiple_blank_lines(self):
        raw = "# Title\n\n\n\nParagraph one.\n\n\n\nParagraph two."
        result = clean_markdown(raw)
        assert "\n\n\n" not in result
        assert "# Title\n\nParagraph one.\n\nParagraph two." == result

    def test_strip_trailing_whitespace(self):
        raw = "Hello world   \nNext line  \n"
        result = clean_markdown(raw)
        assert result == "Hello world\nNext line"

    def test_normalize_heading_spacing(self):
        raw = "Some text\n# Heading\nMore text"
        result = clean_markdown(raw)
        assert result == "Some text\n\n# Heading\n\nMore text"

    def test_heading_at_start_no_extra_blank(self):
        raw = "# Title\nSome text"
        result = clean_markdown(raw)
        assert result == "# Title\n\nSome text"

    def test_fix_table_alignment(self):
        raw = "|Name|Age|\n|---|---|\n|Alice|30|\n|Bob|25|"
        result = clean_markdown(raw)
        assert "| Name  | Age |" in result
        assert "| Alice | 30  |" in result
        assert "| Bob   | 25  |" in result

    def test_strip_common_artifacts(self):
        raw = "Content here\n\x0c\nMore content\n\x00"
        result = clean_markdown(raw)
        assert "\x0c" not in result
        assert "\x00" not in result
        assert "Content here\n\nMore content" == result

    def test_empty_input(self):
        assert clean_markdown("") == ""

    def test_already_clean_passthrough(self):
        clean = "# Title\n\nA paragraph.\n\n## Section\n\nAnother paragraph."
        assert clean_markdown(clean) == clean
