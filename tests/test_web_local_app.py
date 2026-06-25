from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path

from guitar_tab_agent.audio.basic_pitch_adapter import BasicPitchUnavailableError
from guitar_tab_agent.web.local_app import (
    AudioToTabWebOptions,
    create_handler_class,
    error_response_for_exception,
    generate_tab_from_upload,
    parse_audio_to_tab_options,
    render_index_html,
)


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


def test_error_response_for_missing_basic_pitch_is_readable() -> None:
    status, payload = error_response_for_exception(
        BasicPitchUnavailableError("Basic Pitch is not installed")
    )

    assert status == HTTPStatus.SERVICE_UNAVAILABLE
    assert payload == {"error": "Basic Pitch is not installed"}


def test_create_handler_class_returns_request_handler_type() -> None:
    handler_class = create_handler_class(workflow=lambda audio_path, **kwargs: "tab")

    assert issubclass(handler_class, BaseHTTPRequestHandler)


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
    assert "new Blob([output.textContent]" in html
    assert "URL.createObjectURL(blob)" in html
    assert "link.download = downloadFilename" in html
