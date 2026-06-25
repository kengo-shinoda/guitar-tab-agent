import http.client
import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from guitar_tab_agent.audio.basic_pitch_adapter import BasicPitchUnavailableError
from guitar_tab_agent.web.local_app import (
    AudioToTabWebOptions,
    create_handler_class,
    error_response_for_exception,
    generate_tab_from_upload,
    generate_tab_response_from_upload,
    parse_audio_to_tab_options,
    render_index_html,
)
from guitar_tab_agent.workflows import RenderedTabCandidate


def test_parse_audio_to_tab_options() -> None:
    options = parse_audio_to_tab_options(
        "min_confidence=0.55&min_duration=0.1&min_pitch=40&max_pitch=88"
    )

    assert options == AudioToTabWebOptions(
        min_confidence=0.55,
        min_duration=0.1,
        min_pitch=40,
        max_pitch=88,
    )


def test_parse_audio_to_tab_options_ignores_blank_values() -> None:
    options = parse_audio_to_tab_options(
        "min_confidence=&min_duration=&min_pitch=&max_pitch="
    )

    assert options == AudioToTabWebOptions()


def test_generate_tab_from_upload_uses_injected_workflow(tmp_path) -> None:
    calls: list[tuple[Path, float | None, float | None, int | None, int | None]] = []

    def fake_workflow(
        audio_path,
        *,
        min_confidence=None,
        min_duration=None,
        min_pitch=None,
        max_pitch=None,
    ):
        calls.append(
            (audio_path, min_confidence, min_duration, min_pitch, max_pitch)
        )
        assert audio_path.read_bytes() == b"audio bytes"
        return "e|0\nB|-\nG|-\nD|-\nA|-\nE|-"

    tab = generate_tab_from_upload(
        b"audio bytes",
        filename="input.wav",
        options=AudioToTabWebOptions(
            min_confidence=0.55,
            min_duration=0.1,
            min_pitch=40,
            max_pitch=88,
        ),
        workflow=fake_workflow,
    )

    assert tab == "e|0\nB|-\nG|-\nD|-\nA|-\nE|-"
    assert len(calls) == 1
    _, min_confidence, min_duration, min_pitch, max_pitch = calls[0]
    assert min_confidence == 0.55
    assert min_duration == 0.1
    assert min_pitch == 40
    assert max_pitch == 88


def test_generate_tab_from_upload_rejects_empty_audio() -> None:
    try:
        generate_tab_from_upload(
            b"",
            filename="input.wav",
            options=AudioToTabWebOptions(),
            workflow=lambda path: "tab",
        )
    except ValueError as exc:
        assert "audio upload is empty" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_generate_tab_response_from_upload_returns_tab_and_candidates() -> None:
    def fake_candidates_workflow(
        audio_path,
        *,
        top_k,
        min_confidence=None,
        min_duration=None,
        min_pitch=None,
        max_pitch=None,
    ):
        assert audio_path.read_bytes() == b"audio bytes"
        assert top_k == 5
        assert min_confidence == 0.55
        return (
            RenderedTabCandidate(rank=1, score=7.7, tab="candidate one", events=()),
            RenderedTabCandidate(rank=2, score=13.7, tab="candidate two", events=()),
        )

    payload = generate_tab_response_from_upload(
        b"audio bytes",
        filename="input.wav",
        options=AudioToTabWebOptions(min_confidence=0.55),
        workflow=fake_candidates_workflow,
    )

    assert payload == {
        "tab": "candidate one",
        "candidates": [
            {"rank": 1, "score": 7.7, "tab": "candidate one"},
            {"rank": 2, "score": 13.7, "tab": "candidate two"},
        ],
    }


def test_error_response_for_missing_basic_pitch_is_readable() -> None:
    status, payload = error_response_for_exception(
        BasicPitchUnavailableError("Basic Pitch is not installed")
    )

    assert status == HTTPStatus.SERVICE_UNAVAILABLE
    assert payload == {"error": "Basic Pitch is not installed"}


def test_create_handler_class_returns_request_handler_type() -> None:
    handler_class = create_handler_class(
        candidates_workflow=lambda audio_path, **kwargs: ()
    )

    assert issubclass(handler_class, BaseHTTPRequestHandler)


def test_generate_endpoint_returns_tab_and_candidates_json() -> None:
    def fake_candidates_workflow(audio_path, **kwargs):
        return (
            RenderedTabCandidate(rank=1, score=1.0, tab="best tab", events=()),
            RenderedTabCandidate(rank=2, score=2.0, tab="other tab", events=()),
        )

    handler_class = create_handler_class(candidates_workflow=fake_candidates_workflow)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_class)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            server.server_port,
            timeout=5,
        )
        connection.request(
            "POST",
            "/generate?min_confidence=0.55",
            body=b"audio bytes",
            headers={
                "Content-Type": "audio/wav",
                "X-Filename": "input.wav",
            },
        )
        response = connection.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert response.status == HTTPStatus.OK
    assert payload["tab"] == "best tab"
    assert payload["candidates"] == [
        {"rank": 1, "score": 1.0, "tab": "best tab"},
        {"rank": 2, "score": 2.0, "tab": "other tab"},
    ]


def test_render_index_html_includes_controls_and_limitation() -> None:
    html = render_index_html()

    assert 'type="file"' in html
    assert "Copy TAB" in html
    assert "min_confidence" in html
    assert "min_duration" in html
    assert "min_pitch" in html
    assert "max_pitch" in html
    assert "playable/editable TAB draft" in html


def test_render_index_html_includes_download_tab_control() -> None:
    html = render_index_html()

    assert 'id="download-tab"' in html
    assert "Download TAB" in html
    assert "guitar-tab-agent-tab.txt" in html
    assert "new Blob([selectedTabText]" in html
    assert "URL.createObjectURL(blob)" in html
    assert "link.download = downloadFilename" in html


def test_render_index_html_includes_candidate_selection_ui() -> None:
    html = render_index_html()

    assert 'id="candidate-section"' in html
    assert 'id="candidate-list"' in html
    assert 'input.name = "tab-candidate"' in html
    assert "Candidate ${candidate.rank} score=" in html
    assert "renderCandidates(candidates)" in html
    assert "setSelectedTab(candidate.tab)" in html


def test_copy_and_download_use_selected_tab_text() -> None:
    html = render_index_html()

    assert "let selectedTabText" in html
    assert "await navigator.clipboard.writeText(selectedTabText)" in html
    assert "new Blob([selectedTabText]" in html
