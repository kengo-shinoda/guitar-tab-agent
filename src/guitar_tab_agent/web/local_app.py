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
from guitar_tab_agent.fusion.simple_decoder import (
    FingeringPosition,
    parse_fingering_position,
)
from guitar_tab_agent.schema import DecodedTabEvent
from guitar_tab_agent.tab.ascii_tab import render_ascii_tab
from guitar_tab_agent.workflows import (
    RenderedTabCandidate,
    transcribe_audio_file_to_ascii_tab,
    transcribe_audio_file_to_ascii_tab_candidates,
)


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
DEFAULT_TOP_K_CANDIDATES = 5

AudioToTabWorkflow = Callable[..., str]
AudioToTabCandidatesWorkflow = Callable[..., tuple[RenderedTabCandidate, ...]]


@dataclass(frozen=True)
class AudioToTabWebOptions:
    """Optional audio filtering thresholds exposed by the local web UI."""

    min_confidence: float | None = None
    min_duration: float | None = None
    min_pitch: int | None = None
    max_pitch: int | None = None
    first_position: FingeringPosition | None = None


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
    first_position_value = _first_query_value(query, "first_position")
    return AudioToTabWebOptions(
        min_confidence=_optional_float(query, "min_confidence"),
        min_duration=_optional_float(query, "min_duration"),
        min_pitch=_optional_int(query, "min_pitch"),
        max_pitch=_optional_int(query, "max_pitch"),
        first_position=(
            parse_fingering_position(first_position_value)
            if first_position_value is not None
            else None
        ),
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
            first_position=options.first_position,
        )


def _event_payload(index: int, event: DecodedTabEvent) -> dict[str, object]:
    return {
        "index": index,
        "start": event.start,
        "end": event.end,
        "pitch_midi": event.pitch_midi,
        "string": event.string,
        "fret": event.fret,
    }


def _candidate_payload(candidate: RenderedTabCandidate) -> dict[str, object]:
    return {
        "rank": candidate.rank,
        "score": candidate.score,
        "tab": candidate.tab,
        "events": [
            _event_payload(index, event)
            for index, event in enumerate(candidate.events, start=1)
        ],
    }


def generate_tab_response_from_upload(
    audio_bytes: bytes,
    *,
    filename: str,
    options: AudioToTabWebOptions,
    top_k: int = DEFAULT_TOP_K_CANDIDATES,
    workflow: AudioToTabCandidatesWorkflow = transcribe_audio_file_to_ascii_tab_candidates,
) -> dict[str, object]:
    """Run the top-k audio-to-TAB path and return a web response payload."""

    if not audio_bytes:
        raise ValueError("audio upload is empty")
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    suffix = Path(filename).suffix or ".wav"
    with tempfile.TemporaryDirectory(prefix="guitar-tab-agent-web-") as tmpdir:
        audio_path = Path(tmpdir) / f"upload{suffix}"
        audio_path.write_bytes(audio_bytes)
        candidates = workflow(
            audio_path,
            top_k=top_k,
            min_confidence=options.min_confidence,
            min_duration=options.min_duration,
            min_pitch=options.min_pitch,
            max_pitch=options.max_pitch,
            first_position=options.first_position,
        )

    candidate_payloads = [_candidate_payload(candidate) for candidate in candidates]
    tab = candidate_payloads[0]["tab"] if candidate_payloads else render_ascii_tab([])
    return {
        "tab": tab,
        "candidates": candidate_payloads,
    }


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
    #candidate-list {{ margin-top: 1rem; }}
    .candidate-option {{ display: block; margin: 0.5rem 0; }}
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
    <label>Optional first-note position hint
      <input id="first-position" name="first_position" type="text" placeholder="5s-0f">
    </label>
    <button type="submit">Generate</button>
    <button id="play-tab" type="button" disabled>Play selected</button>
    <button id="stop-tab" type="button" disabled>Stop</button>
    <button id="copy-tab" type="button">Copy TAB</button>
    <button id="download-tab" type="button" disabled>Download TAB</button>
  </form>
  <p id="message" class="error"></p>
  <pre id="tab-output" aria-live="polite"></pre>
  <section id="candidate-section" hidden>
    <h2>Candidate TABs</h2>
    <div id="candidate-list"></div>
  </section>
  <script>
    const form = document.getElementById("tab-form");
    const message = document.getElementById("message");
    const output = document.getElementById("tab-output");
    const playButton = document.getElementById("play-tab");
    const stopButton = document.getElementById("stop-tab");
    const copyButton = document.getElementById("copy-tab");
    const downloadButton = document.getElementById("download-tab");
    const candidateSection = document.getElementById("candidate-section");
    const candidateList = document.getElementById("candidate-list");
    const downloadFilename = "guitar-tab-agent-tab.txt";
    let selectedTabText = "";
    let selectedCandidateEvents = [];
    let audioContext = null;
    let activeOscillators = [];
    let playbackTimers = [];

    function midiToFrequency(pitchMidi) {{
      return 440 * 2 ** ((pitchMidi - 69) / 12);
    }}

    function stopPlayback() {{
      for (const timer of playbackTimers) {{
        clearTimeout(timer);
      }}
      playbackTimers = [];
      for (const oscillator of activeOscillators) {{
        try {{
          oscillator.stop();
        }} catch (error) {{
          // Oscillator may already have stopped.
        }}
        try {{
          oscillator.disconnect();
        }} catch (error) {{
          // Oscillator may already be disconnected.
        }}
      }}
      activeOscillators = [];
      playButton.disabled = !selectedCandidateEvents.length;
      stopButton.disabled = true;
    }}

    function setSelectedCandidate(tabText, events) {{
      stopPlayback();
      selectedTabText = tabText || "";
      selectedCandidateEvents = Array.isArray(events) ? events : [];
      output.textContent = selectedTabText;
      downloadButton.disabled = !selectedTabText;
      playButton.disabled = !selectedCandidateEvents.length;
      stopButton.disabled = true;
    }}

    function renderCandidates(candidates) {{
      candidateList.textContent = "";
      candidateSection.hidden = !candidates.length;
      for (const candidate of candidates) {{
        const label = document.createElement("label");
        label.className = "candidate-option";

        const input = document.createElement("input");
        input.type = "radio";
        input.name = "tab-candidate";
        input.value = String(candidate.rank);
        input.checked = candidate.rank === 1;
        input.addEventListener("change", () => setSelectedCandidate(candidate.tab, candidate.events));

        const title = document.createElement("span");
        title.textContent = ` Candidate ${{candidate.rank}} score=${{Number(candidate.score).toFixed(3)}}`;

        const preview = document.createElement("pre");
        preview.textContent = candidate.tab;

        label.appendChild(input);
        label.appendChild(title);
        label.appendChild(preview);
        candidateList.appendChild(label);
      }}
    }}

    form.addEventListener("submit", async (event) => {{
      event.preventDefault();
      message.textContent = "";
      setSelectedCandidate("", []);
      renderCandidates([]);

      const fileInput = document.getElementById("audio-file");
      const file = fileInput.files[0];
      if (!file) {{
        message.textContent = "Choose an audio file first.";
        return;
      }}

      const params = new URLSearchParams();
      for (const id of ["min-confidence", "min-duration", "min-pitch", "max-pitch", "first-position"]) {{
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
      const candidates = Array.isArray(payload.candidates) ? payload.candidates : [];
      renderCandidates(candidates);
      setSelectedCandidate(payload.tab, candidates[0] ? candidates[0].events : []);
    }});

    playButton.addEventListener("click", async () => {{
      if (!selectedCandidateEvents.length) {{
        return;
      }}
      stopPlayback();
      audioContext = audioContext || new AudioContext();
      if (audioContext.state === "suspended") {{
        await audioContext.resume();
      }}

      const starts = selectedCandidateEvents.map((event) => Number(event.start)).filter(Number.isFinite);
      const baseStart = starts.length ? Math.min(...starts) : 0;
      const scheduleStart = audioContext.currentTime + 0.05;
      let latestEnd = scheduleStart;

      for (const event of selectedCandidateEvents) {{
        const pitchMidi = Number(event.pitch_midi);
        const startSeconds = Number(event.start);
        const endSeconds = Number(event.end);
        if (!Number.isFinite(pitchMidi) || !Number.isFinite(startSeconds) || !Number.isFinite(endSeconds)) {{
          continue;
        }}

        const noteStart = scheduleStart + Math.max(0, startSeconds - baseStart);
        const duration = Math.max(0.05, endSeconds - startSeconds);
        const noteEnd = noteStart + duration;
        const releaseStart = Math.max(noteStart + 0.01, noteEnd - 0.02);
        const oscillator = audioContext.createOscillator();
        const gain = audioContext.createGain();

        oscillator.type = "sine";
        oscillator.frequency.setValueAtTime(midiToFrequency(pitchMidi), noteStart);
        gain.gain.setValueAtTime(0.0001, noteStart);
        gain.gain.exponentialRampToValueAtTime(0.08, noteStart + 0.01);
        gain.gain.setValueAtTime(0.08, releaseStart);
        gain.gain.exponentialRampToValueAtTime(0.0001, noteEnd);
        oscillator.connect(gain);
        gain.connect(audioContext.destination);
        oscillator.start(noteStart);
        oscillator.stop(noteEnd + 0.01);
        oscillator.addEventListener("ended", () => {{
          try {{
            oscillator.disconnect();
            gain.disconnect();
          }} catch (error) {{
            // Nodes may already be disconnected after Stop.
          }}
        }});
        activeOscillators.push(oscillator);
        latestEnd = Math.max(latestEnd, noteEnd);
      }}

      playButton.disabled = true;
      stopButton.disabled = false;
      const resetTimer = setTimeout(() => {{
        activeOscillators = [];
        playButton.disabled = !selectedCandidateEvents.length;
        stopButton.disabled = true;
      }}, Math.max(0, latestEnd - audioContext.currentTime) * 1000 + 50);
      playbackTimers.push(resetTimer);
    }});

    stopButton.addEventListener("click", stopPlayback);

    copyButton.addEventListener("click", async () => {{
      if (selectedTabText) {{
        await navigator.clipboard.writeText(selectedTabText);
      }}
    }});

    downloadButton.addEventListener("click", () => {{
      if (!selectedTabText) {{
        return;
      }}
      const blob = new Blob([selectedTabText], {{ type: "text/plain;charset=utf-8" }});
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = downloadFilename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }});
  </script>
</body>
</html>
"""


def create_handler_class(
    *,
    candidates_workflow: AudioToTabCandidatesWorkflow = transcribe_audio_file_to_ascii_tab_candidates,
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
                payload = generate_tab_response_from_upload(
                    audio_bytes,
                    filename=filename,
                    options=options,
                    workflow=candidates_workflow,
                )
            except Exception as exc:  # noqa: BLE001 - local UI returns readable errors.
                status, payload = error_response_for_exception(exc)
                self._write_json(status, payload)
                return

            self._write_json(HTTPStatus.OK, payload)

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _write_html(self, content: str) -> None:
            body = content.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _write_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
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
    "DEFAULT_TOP_K_CANDIDATES",
    "MAX_UPLOAD_BYTES",
    "create_handler_class",
    "error_response_for_exception",
    "generate_tab_from_upload",
    "generate_tab_response_from_upload",
    "parse_audio_to_tab_options",
    "render_index_html",
    "run_local_web_ui",
]
