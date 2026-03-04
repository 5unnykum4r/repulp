from repulp.fetcher import is_url, _guess_extension


class TestIsUrl:
    def test_http_url(self):
        assert is_url("http://example.com") is True

    def test_https_url(self):
        assert is_url("https://example.com/page.html") is True

    def test_file_path(self):
        assert is_url("/tmp/file.pdf") is False

    def test_relative_path(self):
        assert is_url("docs/report.pdf") is False

    def test_empty_string(self):
        assert is_url("") is False


class TestGuessExtension:
    def test_extension_from_url_path(self):
        assert _guess_extension("https://example.com/file.pdf", None) == ".pdf"

    def test_extension_from_content_type(self):
        assert _guess_extension("https://example.com/page", "text/html; charset=utf-8") == ".html"

    def test_default_html(self):
        assert _guess_extension("https://example.com/", None) == ".html"

    def test_content_type_pdf(self):
        assert _guess_extension("https://example.com/doc", "application/pdf") == ".pdf"
