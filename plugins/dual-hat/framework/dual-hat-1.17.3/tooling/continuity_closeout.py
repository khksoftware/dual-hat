"""Deterministic estimates and continuity/full-closeout selection.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

from typing import Mapping, Sequence


FULL_TRIGGERS = frozenset({
    "phase_close", "milestone_close", "ownership_domain_change", "next_item_not_prompt",
    "external_rollout", "external_consumer_package", "published_dependency", "compatibility_boundary_change",
    "irreversible_recovery_point", "security_rights_privacy_integrity_isolation", "unpublished_work_unclear",
    "rollback_unclear", "stale_or_fragmented_evidence", "repository_divergence", "user_requested_full_closure",
})


def work_estimate(*, low_hours: float, high_hours: float, segments: Sequence[str], included: Sequence[str], uncertainties: Sequence[str], expansion_conditions: Sequence[str], revision: int = 1, prior: Mapping[str, object] | None = None, revision_reason: str | None = None) -> dict[str, object]:
    if low_hours <= 0 or high_hours < low_hours or not segments:
        raise ValueError("estimate range and segments are invalid")
    if revision > 1 and (not prior or not revision_reason):
        raise ValueError("material estimate revision requires prior estimate and reason")
    return {
        "schema": "dual-hat-work-estimate/1.0", "revision": revision,
        "estimated_active_hours": {"low": low_hours, "high": high_hours},
        "segments": list(segments), "included": list(included), "uncertainties": list(uncertainties),
        "expansion_conditions": list(expansion_conditions), "assumes_no_architectural_hard_stop": True,
        "prior_revision": prior.get("revision") if prior else None, "revision_reason": revision_reason,
    }

def select_closeout(*, same_stream_next: bool, triggers: Sequence[str], continuity_count: int, continuity_evidence: Mapping[str, object], user_requested_publication: bool = False) -> dict[str, object]:
    unknown = sorted(set(triggers) - FULL_TRIGGERS)
    if unknown:
        raise ValueError(f"unknown full-closure triggers: {unknown}")
    required_evidence = {"architecture_directed", "next_stream", "source"}
    if not required_evidence.issubset(continuity_evidence) or not continuity_evidence.get("source") or not continuity_evidence.get("next_stream"):
        raise ValueError("closeout selection requires architecture-bound continuity evidence")
    if same_stream_next and continuity_evidence.get("architecture_directed") is not True:
        raise ValueError("same-stream continuity is unsupported without architecture direction")
    material = sorted(set(triggers))
    advisory_counter = continuity_count >= 3
    full = bool(material or user_requested_publication or not same_stream_next)
    return {
        "schema": "dual-hat-closeout-decision/1.0", "selection": "full" if full else "lightweight_continuity",
        "full_closure_triggers": material, "advisory_three_item_threshold_reached": advisory_counter,
        "counter_forced_full_closure": False, "same_stream_next": same_stream_next,
        "continuity_evidence": dict(continuity_evidence),
        "publication_authorized": user_requested_publication,
        "required_lightweight_evidence": ["checkpoint_commit", "focused_validation", "clean_worktree", "exit_status", "current_handover", "unresolved_findings", "inherited_dependencies", "rollback_point", "pending_publication_inventory", "architecture_disposition_boundary", "no_engineering_self_acceptance"],
        "skipped_when_lightweight": ["standalone_export", "remote_publication", "semantic_release", "release_packaging", "manifest_and_checksums", "snapshot", "exhaustive_archival"],
    }


def deferred_publication_inventory(*, canonical_commit: str, retained_changes: Sequence[str], current_changes: Sequence[str], expected_version: str, compatibility: str, release_notes: Sequence[str], dependencies: Sequence[str]) -> dict[str, object]:
    return {
        "schema": "dual-hat-deferred-publication-inventory/1.0", "canonical_source_commit": canonical_commit,
        "retained_prior_changes": list(retained_changes), "current_work_item_changes": list(current_changes),
        "expected_semantic_version": expected_version, "compatibility_impact": compatibility,
        "pending_release_notes": list(release_notes), "dependencies_on_subsequent_work": list(dependencies),
        "published": False,
    }
