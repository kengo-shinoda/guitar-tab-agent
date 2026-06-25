"""Minimal stdlib local web UI for the audio-only MVP."""

from __future__ import annotations

import html
import json
import tempfile
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from guitar_tab_agent.audio.basic_pitch_adapter import BasicPitchUnavailableError
from guitar_tab_agent.workflows import transcribe_audio_file_to_ascii_tab


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_UPLOAD_BYTES = 50 * 1024 * 1024

AudioToTabWorkflow = Callable[..., str]


@dataclass(frozen=True)
class AudioToTabWebOptions:
    """Optional audio filtering thresholds exposed by the local web UI."""

    min_confidence: float | None = None
    min_duration: float | None = None
    min_pitch: int | None = None
    max_pitch: int | None = None


def _first_query_value(
    query: dict[str, list[str]],
    key: str,
) -> str | None:
    values = query.get(key)
    if not values:
        return None
    value = values[0].strip()
    return value or None


def _optional_float(query: dict[str, list[str]], key: str) -> float | None:
    value = _first_query_value(query, key)
    return None if value is None else float(value)


def _optional_int(query: dict[str, list[str]], key: str) -> int | None:
    value = _first_query_value(query, key)
    return None if value is None else int(value)


def parse_audio_to_tab_options(query_string: str) -> AudioToTabWebOptions:
    """Parse web query parameters into workflow filter options."""

    query = parse_qs(query_string, keep_blank_values=True)
    return AudioToTabWebOptions(
        min_confidence=_optional_float(query, "min_confidence"),
        min_duration=_optional_float(query, "min_duration"),
        min_pitch=_optional_int(query, "min_pitch"),
        max_pitch=_optional_int(query, "max_pitch"),
    )


def generate_tab_from_upload(
    audio_bytes: bytes,
    *,
    filename: str,
    options: AudioToTabWebOptions,
    workflow: AudioToTabWorkflow = transcribe_audio_file_to_ascii_tab,
) -> str:
    """Persist uploaded bytes briefly and run the existing audio-to-TAB path."""

    if not audio_bytes:
        raise ValueError("audio upload is empty")

    suffix = Path(filename).suffix or ".wav"
    with tempfile.TemporaryDirectory(prefix="guitar-tab-agent-web-") as tmpdir:
        audio_path = Path(tmpdir) / f"upload{suffix}"
        audio_path.write_bytes(audio_bytes)
        return workflow(
            audio_path,
            min_confidence=options.min_confidence,
            min_duration=options.min_duration,
            min_pitch=options.min_pitch,
            max_pitch=options.max_pitch,
        )


def error_response_for_exception(exc: Exception) -> tuple[HTTPStatus, dict[str, str]]:
    """Return a readable JSON error response for local UI failures."""

    if isinstance(exc, BasicPitchUnavailableError):
        return HTTPStatus.SERVICE_UNAVAILABLE, {"error": str(exc)}
    if isinstance(exc, ValueError):
        return HTTPStatus.BAD_REQUEST, {"error": str(exc)}
    return HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"unexpected error: {exc}"}


def render_index_html() -> str:
    """Render the single-page local UI."""

    limitation = (
        "Output is a playable/editable TAB draft, not exact ground truth "
        "fingering."
    )
    escaped_limitation = html.escape(limitation)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>guitar-tab-agent local web UI</title>
  <style>
    body {{
      color: #1f2933;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
      margin: 2rem auto;
      max-width: 56rem;
      padding: 0 1rem;
    }}
    label {{ display: block; font-weight: 600; margin-top: 1rem; }}
    input {{ box-sizing: border-box; margin-top: 0.25rem; max-width: 24rem; width: 100%; }}
    button {{ margin-right: 0.5rem; margin-top: 1rem; }}
    pre {{
      background: #f6f8fa;
      border: 1px solid #d0d7de;
      overflow-x: auto;
      padding: 1rem;
      white-space: pre;
    }}
    .error {{ color: #b42318; font-weight: 600; }}
    .muted {{ color: #52616b; }}
  </style>
</head>
<body>
  <h1>guitar-tab-agent</h1>
  <p class="muted">{escaped_limitation}</p>
  <form id="tab-form">
    <label>Audio file
      <input id="audio-file" name="audio" type="file" accept="audio/*" required>
    </label>
    <label>Minimum confidence
      <input id="min-confidence" name="min_confidence" type="number" min="0" max="1" step="0.01" placeholder="optional">
    </label>
    <label>Minimum duration, seconds
      <input id="min-duration" name="min_duration" type="number" min="0" step="0.01" placeholder="optional">
    </label>
    <label>Minimum MIDI pitch
      <input id="min-pitch" name="min_pitch" type="number" min="0" max="127" step="1" placeholder="40">
    </label>
    <label>Maximum MIDI pitch
      <input id="max-pitch" name="max_pitch" type="number" min="0" max="127" step="1" placeholder="88">
    </label>
    <button type="submit">Generate</button>
    <button id="copy-tab" type="button">Copy TAB</button>
  </form>
  <p id="message" class="error"></p>
  <pre id="tab-output" aria-live="polite"></pre>
  <script>
    const form = document.getElementById("tab-form");
    const message = document.getElementById("message");
    const output = document.getElementById("tab-output");
    const copyButton = document.getElementById("copy-tab");

    form.addEventListener("submit", async (event) => {{
      event.preventDefault();
      message.textContent = "";
      output.textContent = "";

      const fileInput = document.getElementById("audio-file");
      const file = fileInput.files[0];
      if (!file) {{
        message.textContent = "Choose an audio file first.";
        return;
      }}

      const params = new URLSearchParams();
      for (const id of ["min-confidence", "min-duration", "min-pitch", "max-pitch"]) {{
        const input = document.getElementById(id);
        if (input.value) {{
          params.set(input.name, input.value);
        }}
      }}

      message.textContent = "Generating...";
      const response = await fetch(`/generate?${{params.toString()}}`, {{
        method: "POST",
        headers: {{
          "Content-Type": file.type || "application/octet-stream",
          "X-Filename": file.name,
        }},
        body: file,
      }});
      const payload = await response.json();
      if (!response.ok) {{
        message.textContent = payload.error || "Failed to generate TAB.";
        return;
      }}
      message.textContent = "";
      output.textContent = payload.tab;
    }});

    copyButton.addEventListener("click", async () => {{
      if (output.textContent) {{
        await navigator.clipboard.writeText(output.textContent);
      }}
    }});
  </script>
</body>
</html>
"""


def create_handler_class(
    *,
    workflow: AudioToTabWorkflow = transcribe_audio_file_to_ascii_tab,
) -> type[BaseHTTPRequestHandler]:
    """Create a local request handler with an injectable workflow for tests."""

    class LocalWebHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != "/":
                self._write_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            self._write_html(render_index_html())

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != "/generate":
                self._write_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return

            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0:
                    raise ValueError("audio upload is empty")
                if length > MAX_UPLOAD_BYTES:
                    raise ValueError("audio upload is too large")

                audio_bytes = self.rfile.read(length)
                options = parse_audio_to_tab_options(parsed.query)
                filename = self.headers.get("X-Filename", "upload.wav")
                tab = generate_tab_from_upload(
                    audio_bytes,
                    filename=filename,
                    options=options,
                    workflow=workflow,
                )
            except Exception as exc:  # noqa: BLE001 - local UI returns readable errors.
                status, payload = error_response_for_exception(exc)
                self._write_json(status, payload)
                return

            self._write_json(HTTPStatus.OK, {"tab": tab})

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _write_html(self, content: str) -> None:
            body = content.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _write_json(self, status: HTTPStatus, payload: dict[str, str]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return LocalWebHandler


def run_local_web_ui(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    open_browser: bool = False,
) -> None:
    """Run the local web UI until interrupted."""

    server = ThreadingHTTPServer((host, port), create_handler_class())
    url = f"http://{host}:{server.server_port}/"
    print(f"Local web UI running at {url}")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping local web UI.")
    finally:
        server.server_close()


__all__ = [
    "AudioToTabWebOptions",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "MAX_UPLOAD_BYTES",
    "create_handler_class",
    "error_response_for_exception",
    "generate_tab_from_upload",
    "parse_audio_to_tab_options",
    "render_index_html",
    "run_local_web_ui",
]
