from __future__ import annotations

from .models import ComparisonRow, Observation, ScanReport


def _status(obs: Observation | None) -> str:
    return "MISSING" if obs is None else obs.display


def _classify(pre: Observation | None, post: Observation | None) -> str:
    if pre is None or post is None:
        return "missing_data"
    if pre.display == post.display:
        return "unchanged"
    if pre.outcome != "POSITIVE" and post.outcome == "POSITIVE":
        return "opened_after_auth"
    if pre.outcome == "POSITIVE" and post.outcome != "POSITIVE":
        return "restricted_after_auth"
    return "changed"


def compare_reports(pre: ScanReport, post: ScanReport) -> list[ComparisonRow]:
    pre_map = {item.probe_id: item for item in pre.observations}
    post_map = {item.probe_id: item for item in post.observations}
    probe_ids = list(dict.fromkeys([*pre_map.keys(), *post_map.keys()]))

    rows: list[ComparisonRow] = []
    for probe_id in probe_ids:
        before = pre_map.get(probe_id)
        after = post_map.get(probe_id)
        label = before.label if before is not None else after.label if after is not None else probe_id
        rows.append(
            ComparisonRow(
                probe_id=probe_id,
                label=label,
                pre=_status(before),
                post=_status(after),
                change=_classify(before, after),
            )
        )
    return rows
