"""JSON loading for left-hand fret likelihood evidence.

The JSON format is a list of records:

```json
[
  {"time": 0.0, "likelihood": {"9": 1.0}},
  {"time": 0.5, "likelihood": null}
]
```

`time` values are note start times in seconds. `likelihood` maps frets
`1..max_fret` to non-negative evidence scores. Missing or null likelihood means
no left-hand evidence for that time. Open strings receive neutral evidence in
the decoder; this file format does not make the workflow full video end-to-end
transcription.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_left_hand_fret_likelihood_json(
    path: str | Path,
) -> dict[float, dict[int, float] | None]:
    """Load left-hand fret likelihood evidence from JSON."""

    json_path = Path(path)
    try:
        raw_records = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid left-hand likelihood JSON in {json_path}: {exc.msg} "
            f"(line {exc.lineno}, column {exc.colno})"
        ) from exc
    except OSError as exc:
        raise ValueError(f"could not read left-hand likelihood JSON {json_path}: {exc}") from exc

    if not isinstance(raw_records, list):
        raise ValueError(
            f"expected a JSON list of left-hand likelihood records in {json_path}"
        )

    likelihood_by_time: dict[float, dict[int, float] | None] = {}
    for index, raw_record in enumerate(raw_records):
        if not isinstance(raw_record, dict):
            raise ValueError(
                f"left-hand likelihood record at index {index} must be a JSON object"
            )

        time = _record_time(raw_record, index=index)
        if time in likelihood_by_time:
            raise ValueError(f"duplicate left-hand likelihood time at index {index}")

        raw_likelihood = raw_record.get("likelihood")
        likelihood_by_time[time] = (
            None
            if raw_likelihood is None
            else _record_likelihood(raw_likelihood, index=index)
        )

    return likelihood_by_time


def _record_time(raw_record: dict[str, Any], *, index: int) -> float:
    if "time" not in raw_record:
        raise ValueError(f"left-hand likelihood record at index {index} is missing time")
    time = raw_record["time"]
    if not _is_number(time):
        raise ValueError(
            f"left-hand likelihood record at index {index} has non-numeric time"
        )
    return float(time)


def _record_likelihood(raw_likelihood: Any, *, index: int) -> dict[int, float]:
    if not isinstance(raw_likelihood, dict):
        raise ValueError(
            f"left-hand likelihood record at index {index} likelihood must be an object"
        )

    likelihood: dict[int, float] = {}
    for raw_fret, raw_score in raw_likelihood.items():
        fret = _fret_key(raw_fret, index=index)
        if fret <= 0:
            raise ValueError(
                f"left-hand likelihood record at index {index} fret must be positive"
            )
        if not _is_number(raw_score):
            raise ValueError(
                f"left-hand likelihood record at index {index} score for fret "
                f"{fret} must be numeric"
            )
        score = float(raw_score)
        if score < 0:
            raise ValueError(
                f"left-hand likelihood record at index {index} score for fret "
                f"{fret} must be non-negative"
            )
        likelihood[fret] = score

    return likelihood


def _fret_key(raw_fret: Any, *, index: int) -> int:
    try:
        return int(raw_fret)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"left-hand likelihood record at index {index} has non-integer fret key"
        ) from exc


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


__all__ = ["load_left_hand_fret_likelihood_json"]
