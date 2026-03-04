import threading
import time
from pathlib import Path

import pytest

from repulp.watcher import WatchEvent, _should_process, _resolve_output, watch_directory


class TestWatchEvent:
    def test_default_fields(self):
        event = WatchEvent(source_path=Path("/tmp/file.html"))
        assert event.source_path == Path("/tmp/file.html")
        assert event.output_path is None
        assert event.success is True
        assert event.error is None

    def test_custom_fields(self):
        event = WatchEvent(
            source_path=Path("/src/doc.pdf"),
            output_path=Path("/out/doc.md"),
            success=False,
            error="conversion failed",
        )
        assert event.source_path == Path("/src/doc.pdf")
        assert event.output_path == Path("/out/doc.md")
        assert event.success is False
        assert event.error == "conversion failed"


class TestShouldProcess:
    def test_supported_extension_no_filters(self):
        assert _should_process(Path("report.html"), None, None) is True

    def test_unsupported_extension(self):
        assert _should_process(Path("file.xyz"), None, None) is False

    def test_include_filter_matches(self):
        assert _should_process(Path("data.csv"), ["*.csv"], None) is True

    def test_include_filter_rejects(self):
        assert _should_process(Path("page.html"), ["*.csv"], None) is False

    def test_exclude_filter_rejects(self):
        assert _should_process(Path("temp.html"), None, ["temp.*"]) is False

    def test_exclude_filter_allows(self):
        assert _should_process(Path("page.html"), None, ["temp.*"]) is True

    def test_include_and_exclude_combined(self):
        assert _should_process(Path("data.csv"), ["*.csv"], ["data.*"]) is False


class TestResolveOutput:
    def test_preserves_directory_structure(self):
        source = Path("/watched/sub/dir/file.html")
        result = _resolve_output(source, Path("/watched"), Path("/output"))
        assert result == Path("/output/sub/dir/file.md")

    def test_top_level_file(self):
        source = Path("/watched/file.pdf")
        result = _resolve_output(source, Path("/watched"), Path("/output"))
        assert result == Path("/output/file.md")

    def test_same_source_and_output(self):
        source = Path("/dir/file.docx")
        result = _resolve_output(source, Path("/dir"), Path("/dir"))
        assert result == Path("/dir/file.md")


class TestWatchDirectory:
    def test_converts_new_file(self, tmp_path: Path):
        """Create an HTML file while watcher is running and verify conversion."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        watch_dir = tmp_path / "source"
        watch_dir.mkdir()

        events: list[WatchEvent] = []
        stop = threading.Event()

        def callback(event: WatchEvent) -> None:
            events.append(event)

        watcher_thread = threading.Thread(
            target=watch_directory,
            kwargs={
                "source": watch_dir,
                "output_dir": output_dir,
                "on_change": callback,
                "stop_event": stop,
                "debounce_ms": 100,
            },
            daemon=True,
        )
        watcher_thread.start()

        # Allow the watcher to initialize before writing the file
        time.sleep(0.5)

        html_file = watch_dir / "test.html"
        html_file.write_text("<h1>Hello</h1><p>World</p>")

        # Wait for the watcher to detect and process the change
        time.sleep(2.0)

        stop.set()
        watcher_thread.join(timeout=5)

        assert len(events) >= 1
        event = events[0]
        assert event.success is True
        assert event.source_path == html_file
        assert event.output_path == output_dir / "test.md"
        assert event.output_path.exists()

        content = event.output_path.read_text(encoding="utf-8")
        assert "Hello" in content

    def test_ignores_unsupported_extensions(self, tmp_path: Path):
        """Files with unsupported extensions should not trigger events."""
        watch_dir = tmp_path / "source"
        watch_dir.mkdir()

        events: list[WatchEvent] = []
        stop = threading.Event()

        def callback(event: WatchEvent) -> None:
            events.append(event)

        watcher_thread = threading.Thread(
            target=watch_directory,
            kwargs={
                "source": watch_dir,
                "on_change": callback,
                "stop_event": stop,
                "debounce_ms": 100,
            },
            daemon=True,
        )
        watcher_thread.start()

        time.sleep(0.5)

        unsupported_file = watch_dir / "file.xyz"
        unsupported_file.write_text("this should be ignored")

        time.sleep(2.0)

        stop.set()
        watcher_thread.join(timeout=5)

        assert len(events) == 0

    def test_respects_include_filter(self, tmp_path: Path):
        """Only files matching include patterns should be processed."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        watch_dir = tmp_path / "source"
        watch_dir.mkdir()

        events: list[WatchEvent] = []
        stop = threading.Event()

        def callback(event: WatchEvent) -> None:
            events.append(event)

        watcher_thread = threading.Thread(
            target=watch_directory,
            kwargs={
                "source": watch_dir,
                "output_dir": output_dir,
                "include": ["*.csv"],
                "on_change": callback,
                "stop_event": stop,
                "debounce_ms": 100,
            },
            daemon=True,
        )
        watcher_thread.start()

        time.sleep(0.5)

        # Write both files; only the CSV should trigger a conversion
        csv_file = watch_dir / "data.csv"
        csv_file.write_text("name,age\nAlice,30\n")

        html_file = watch_dir / "page.html"
        html_file.write_text("<h1>Ignored</h1>")

        time.sleep(2.0)

        stop.set()
        watcher_thread.join(timeout=5)

        assert len(events) == 1
        assert events[0].source_path == csv_file
        assert events[0].success is True
