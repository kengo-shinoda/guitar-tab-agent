import http.client
import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from guitar_tab_agent.audio.basic_pitch_adapter import BasicPitchUnavailableError
from guitar_tab_agent.fusion.simple_decoder import FingeringPosition
from guitar_tab_agent.schema import DecodedTabEvent
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


def _decoded_event(
    index: int,
    *,
    pitch_midi: int,
    string: int,
    fret: int,
) -> DecodedTabEvent:
    start = (index - 1) * 0.25
    return DecodedTabEvent(
        start=start,
        end=start + 0.2,
        string=string,
        fret=fret,
        pitch_midi=pitch_midi,
        confidence=0.9,
    )


def test_parse_audio_to_tab_options() -> None:
    options = parse_audio_to_tab_options(
        "min_confidence=0.55&min_duration=0.1&min_pitch=40&max_pitch=88&first_position=5s-0f"
    )

    assert options == AudioToTabWebOptions(
        min_confidence=0.55,
        min_duration=0.1,
        min_pitch=40,
        max_pitch=88,
        first_position=FingeringPosition(string=5, fret=0),
    )


def test_parse_audio_to_tab_options_ignores_blank_values() -> None:
    options = parse_audio_to_tab_options(
        "min_confidence=&min_duration=&min_pitch=&max_pitch=&first_position="
    )

    assert options == AudioToTabWebOptions()


def test_parse_audio_to_tab_options_rejects_invalid_first_position() -> None:
    try:
        parse_audio_to_tab_options("first_position=bad")
    except ValueError as exc:
        assert "first_position must use format" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_generate_tab_from_upload_uses_injected_workflow(tmp_path) -> None:
    calls: list[
        tuple[
            Path,
            float | None,
            float | None,
            int | None,
            int | None,
            FingeringPosition | None,
        ]
    ] = []

    def fake_workflow(
        audio_path,
        *,
        min_confidence=None,
        min_duration=None,
        min_pitch=None,
        max_pitch=None,
        first_position=None,
    ):
        calls.append(
            (
                audio_path,
                min_confidence,
                min_duration,
                min_pitch,
                max_pitch,
                first_position,
            )
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
            first_position=FingeringPosition(string=5, fret=0),
        ),
        workflow=fake_workflow,
    )

    assert tab == "e|0\nB|-\nG|-\nD|-\nA|-\nE|-"
    assert len(calls) == 1
    _, min_confidence, min_duration, min_pitch, max_pitch, first_position = calls[0]
    assert min_confidence == 0.55
    assert min_duration == 0.1
    assert min_pitch == 40
    assert max_pitch == 88
    assert first_position == FingeringPosition(string=5, fret=0)


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
        first_position=None,
    ):
        assert audio_path.read_bytes() == b"audio bytes"
        assert top_k == 5
        assert min_confidence == 0.55
        assert first_position == FingeringPosition(string=5, fret=0)
        return (
            RenderedTabCandidate(
                rank=1,
                score=7.7,
                tab="candidate one",
                events=(
                    _decoded_event(1, pitch_midi=45, string=5, fret=0),
                    _decoded_event(2, pitch_midi=55, string=4, fret=5),
                ),
            ),
            RenderedTabCandidate(
                rank=2,
                score=13.7,
                tab="candidate two",
                events=(_decoded_event(1, pitch_midi=45, string=5, fret=0),),
            ),
        )

    payload = generate_tab_response_from_upload(
        b"audio bytes",
        filename="input.wav",
        options=AudioToTabWebOptions(
            min_confidence=0.55,
            first_position=FingeringPosition(string=5, fret=0),
        ),
        workflow=fake_candidates_workflow,
    )

    assert payload == {
        "tab": "candidate one",
        "candidates": [
            {
                "rank": 1,
                "score": 7.7,
                "tab": "candidate one",
                "events": [
                    {
                        "index": 1,
                        "start": 0.0,
                        "end": 0.2,
                        "pitch_midi": 45,
                        "string": 5,
                        "fret": 0,
                    },
                    {
                        "index": 2,
                        "start": 0.25,
                        "end": 0.45,
                        "pitch_midi": 55,
                        "string": 4,
                        "fret": 5,
                    },
                ],
            },
            {
                "rank": 2,
                "score": 13.7,
                "tab": "candidate two",
                "events": [
                    {
                        "index": 1,
                        "start": 0.0,
                        "end": 0.2,
                        "pitch_midi": 45,
                        "string": 5,
                        "fret": 0,
                    }
                ],
            },
        ],
    }


def test_generate_tab_response_from_upload_preserves_empty_candidates_fallback() -> None:
    payload = generate_tab_response_from_upload(
        b"audio bytes",
        filename="input.wav",
        options=AudioToTabWebOptions(),
        workflow=lambda audio_path, **kwargs: (),
    )

    assert payload["tab"] == "e|\nB|\nG|\nD|\nA|\nE|"
    assert payload["candidates"] == []


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
    calls = []

    def fake_candidates_workflow(audio_path, **kwargs):
        calls.append(kwargs)
        return (
            RenderedTabCandidate(
                rank=1,
                score=1.0,
                tab="best tab",
                events=(
                    _decoded_event(1, pitch_midi=45, string=5, fret=0),
                    _decoded_event(2, pitch_midi=55, string=4, fret=5),
                ),
            ),
            RenderedTabCandidate(
                rank=2,
                score=2.0,
                tab="other tab",
                events=(_decoded_event(1, pitch_midi=47, string=5, fret=2),),
            ),
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
            "/generate?min_confidence=0.55&first_position=5s-0f",
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
    assert calls[0]["first_position"] == FingeringPosition(string=5, fret=0)
    assert payload["tab"] == "best tab"
    assert payload["candidates"] == [
        {
            "rank": 1,
            "score": 1.0,
            "tab": "best tab",
            "events": [
                {
                    "index": 1,
                    "start": 0.0,
                    "end": 0.2,
                    "pitch_midi": 45,
                    "string": 5,
                    "fret": 0,
                },
                {
                    "index": 2,
                    "start": 0.25,
                    "end": 0.45,
                    "pitch_midi": 55,
                    "string": 4,
                    "fret": 5,
                },
            ],
        },
        {
            "rank": 2,
            "score": 2.0,
            "tab": "other tab",
            "events": [
                {
                    "index": 1,
                    "start": 0.0,
                    "end": 0.2,
                    "pitch_midi": 47,
                    "string": 5,
                    "fret": 2,
                }
            ],
        },
    ]


def test_generate_endpoint_returns_readable_error_for_invalid_first_position() -> None:
    handler_class = create_handler_class(candidates_workflow=lambda audio_path, **kwargs: ())
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
            "/generate?first_position=bad",
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

    assert response.status == HTTPStatus.BAD_REQUEST
    assert "first_position must use format" in payload["error"]


def test_render_index_html_includes_controls_and_limitation() -> None:
    html = render_index_html()

    assert 'type="file"' in html
    assert "Copy TAB" in html
    assert "min_confidence" in html
    assert "min_duration" in html
    assert "min_pitch" in html
    assert "max_pitch" in html
    assert "Optional first-note position hint" in html
    assert 'id="first-position"' in html
    assert 'name="first_position"' in html
    assert 'placeholder="5s-0f"' in html
    assert "playable/editable TAB draft" in html


def test_render_index_html_includes_download_tab_control() -> None:
    html = render_index_html()

    assert 'id="download-tab"' in html
    assert "Download TAB" in html
    assert "guitar-tab-agent-tab.txt" in html
    assert "new Blob([selectedTabText]" in html
    assert "URL.createObjectURL(blob)" in html
    assert "link.download = downloadFilename" in html


def test_render_index_html_includes_selected_candidate_playback_controls() -> None:
    html = render_index_html()

    assert 'id="play-tab"' in html
    assert "Play selected" in html
    assert 'id="stop-tab"' in html
    assert ">Stop</button>" in html
    assert "new AudioContext()" in html


def test_render_index_html_includes_candidate_selection_ui() -> None:
    html = render_index_html()

    assert 'id="candidate-section"' in html
    assert 'id="candidate-list"' in html
    assert 'input.name = "tab-candidate"' in html
    assert "Candidate ${candidate.rank} score=" in html
    assert "renderCandidates(candidates)" in html
    assert "setSelectedCandidate(candidate.tab, candidate.events)" in html


def test_playback_uses_selected_candidate_events() -> None:
    html = render_index_html()

    assert "let selectedCandidateEvents = []" in html
    assert "selectedCandidateEvents = Array.isArray(events) ? events : []" in html
    assert "setSelectedCandidate(payload.tab, candidates[0] ? candidates[0].events : [])" in html
    assert "for (const event of selectedCandidateEvents)" in html
    assert "Number(event.pitch_midi)" in html
    assert "Number(event.start)" in html
    assert "Number(event.end)" in html


def test_playback_includes_midi_pitch_to_frequency_conversion() -> None:
    html = render_index_html()

    assert "function midiToFrequency(pitchMidi)" in html
    assert "440 * 2 ** ((pitchMidi - 69) / 12)" in html
    assert "oscillator.frequency.setValueAtTime(midiToFrequency(pitchMidi)" in html
    assert "gain.gain.exponentialRampToValueAtTime" in html


def test_playback_stops_on_candidate_change_and_new_generation() -> None:
    html = render_index_html()

    assert "function stopPlayback()" in html
    assert "setSelectedCandidate(\"\", [])" in html
    assert "input.addEventListener(\"change\", () => setSelectedCandidate(candidate.tab, candidate.events))" in html
    assert "stopButton.addEventListener(\"click\", stopPlayback)" in html
    assert "oscillator.stop()" in html


def test_copy_and_download_use_selected_tab_text() -> None:
    html = render_index_html()

    assert "let selectedTabText" in html
    assert "await navigator.clipboard.writeText(selectedTabText)" in html
    assert "new Blob([selectedTabText]" in html
