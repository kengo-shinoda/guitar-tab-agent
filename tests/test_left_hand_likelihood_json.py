import json

import pytest

from guitar_tab_agent.video.left_hand_likelihood_json import (
    load_left_hand_fret_likelihood_json,
)


def test_load_left_hand_likelihood_json_parses_times_frets_and_scores(tmp_path) -> None:
    path = tmp_path / "likelihood.json"
    path.write_text(
        json.dumps(
            [
                {"time": 0.0, "likelihood": {"9": 1.0}},
                {"time": 0.5, "likelihood": {"10": 0.75}},
            ]
        ),
        encoding="utf-8",
    )

    assert load_left_hand_fret_likelihood_json(path) == {
        0.0: {9: 1.0},
        0.5: {10: 0.75},
    }


def test_load_left_hand_likelihood_json_allows_missing_or_null_likelihood(
    tmp_path,
) -> None:
    path = tmp_path / "likelihood.json"
    path.write_text(
        json.dumps(
            [
                {"time": 0.0},
                {"time": 0.5, "likelihood": None},
            ]
        ),
        encoding="utf-8",
    )

    assert load_left_hand_fret_likelihood_json(path) == {
        0.0: None,
        0.5: None,
    }


def test_load_left_hand_likelihood_json_rejects_invalid_json(tmp_path) -> None:
    path = tmp_path / "likelihood.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid left-hand likelihood JSON"):
        load_left_hand_fret_likelihood_json(path)


def test_load_left_hand_likelihood_json_rejects_negative_scores(tmp_path) -> None:
    path = tmp_path / "likelihood.json"
    path.write_text(
        json.dumps([{"time": 0.0, "likelihood": {"9": -0.1}}]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="score for fret 9 must be non-negative"):
        load_left_hand_fret_likelihood_json(path)


def test_load_left_hand_likelihood_json_rejects_non_integer_fret_keys(tmp_path) -> None:
    path = tmp_path / "likelihood.json"
    path.write_text(
        json.dumps([{"time": 0.0, "likelihood": {"fret9": 1.0}}]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="non-integer fret key"):
        load_left_hand_fret_likelihood_json(path)
