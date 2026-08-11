"""Deterministic estimates and continuity/full-closeout selection.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

from typing import Mapping, Sequence

from dispatch_reconciliation import DISPATCH_INVENTORY_SCHEMA
from dispatch_reconciliation import dispatch_inventory as reconcile_dispatch_inventory


FULL_TRIGGERS = frozenset({
    "phase_close", "milestone_close", "ownership_domain_change", "next_item_not_prompt",
    "external_rollout", "external_consumer_package", "published_dependency", "compatibility_boundary_change",
    "irreversible_recovery_point", "security_rights_privacy_integrity_isolation", "unpublished_work_unclear",
    "rollback_unclear", "stale_or_fragmented_evidence", "repository_divergence", "user_requested_full_closure",
})

RECONCILIATION_SOURCES = frozenset({"sealed_scope", "incremental_request", "interim_finding"})
RECONCILIATION_STATUSES = frozenset({"done", "partial", "not_done"})
RECONCILIATION_ITEM_REQUIRED_FIELDS = frozenset({"source", "description", "status", "evidence"})


def reconciliation_audit(*, reviewer_role: str, engineering_self_report_only: bool, items: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Independent, context-isolated audit reconciling the sealed work order's
    approved scope, every incremental stakeholder request, and every interim
    finding committed to being addressed against verified repository fact --
    facts, not words -- rather than Engineering self-report. Required at every
    capability's closing gate; a partially done or not done item blocks
    closure unless the author explicitly defers it."""
    if reviewer_role != "independent" or engineering_self_report_only:
        raise ValueError("closure reconciliation audit requires a context-isolated independent reviewer, not engineering self-report")
    if not items:
        raise ValueError("closure reconciliation audit requires at least one reconciled item")
    normalized: list[dict[str, object]] = []
    blocking: list[str] = []
    for item in items:
        missing = RECONCILIATION_ITEM_REQUIRED_FIELDS - set(item)
        if missing:
            raise ValueError(f"reconciliation item missing fields: {sorted(missing)}")
        if item["source"] not in RECONCILIATION_SOURCES:
            raise ValueError(f"unknown reconciliation source: {item['source']}")
        if item["status"] not in RECONCILIATION_STATUSES:
            raise ValueError(f"unknown reconciliation status: {item['status']}")
        if not item.get("evidence"):
            raise ValueError("reconciliation item requires cited evidence (commit hash, file path, or test name/result), not a narrative claim")
        deferred = bool(item.get("author_deferred"))
        if item["status"] != "done" and not deferred:
            blocking.append(str(item["description"]))
        normalized.append({"author_deferred": False, **item})
    return {
        "schema": "dual-hat-reconciliation-audit/1.0",
        "reviewer_role": "independent",
        "engineering_self_report_only": False,
        "items": normalized,
        "blocking_items": blocking,
        "closure_authorized": not blocking,
    }


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

def select_closeout(*, same_stream_next: bool, triggers: Sequence[str], continuity_count: int, continuity_evidence: Mapping[str, object], reconciliation_audit: Mapping[str, object], dispatch_inventory: Mapping[str, object], user_requested_publication: bool = False) -> dict[str, object]:
    """Select continuity or full closeout, refusing outright where a gate blocks.

    The delegated-dispatch disposition is **re-derived here from the registered
    workers** rather than read off the inventory's own summary. A gate that
    believes a caller's `closure_authorized` flag is a control over the
    reconciler's output, not over what a caller hands the gate: a hand-forged
    inventory holding a nonterminal worker would otherwise authorize closure
    without the reconciler ever running. Re-derivation calls the one
    implementation of the state vocabulary rather than restating it here, so the
    gate cannot drift away from the reconciler it enforces.
    """
    unknown = sorted(set(triggers) - FULL_TRIGGERS)
    if unknown:
        raise ValueError(f"unknown full-closure triggers: {unknown}")
    required_evidence = {"architecture_directed", "next_stream", "source"}
    if not required_evidence.issubset(continuity_evidence) or not continuity_evidence.get("source") or not continuity_evidence.get("next_stream"):
        raise ValueError("closeout selection requires architecture-bound continuity evidence")
    if same_stream_next and continuity_evidence.get("architecture_directed") is not True:
        raise ValueError("same-stream continuity is unsupported without architecture direction")
    required_reconciliation_fields = {"schema", "reviewer_role", "engineering_self_report_only", "items", "blocking_items", "closure_authorized"}
    if not required_reconciliation_fields.issubset(reconciliation_audit):
        raise ValueError("closeout selection requires a completed closure reconciliation audit")
    if reconciliation_audit.get("reviewer_role") != "independent" or reconciliation_audit.get("engineering_self_report_only") is True:
        raise ValueError("closure reconciliation audit must be independent, not engineering self-report")
    if reconciliation_audit.get("closure_authorized") is not True:
        raise ValueError("closure is blocked by unresolved reconciliation findings: " + ", ".join(reconciliation_audit.get("blocking_items") or ()))
    required_dispatch_fields = {"schema", "workers", "registered_count", "terminal_count", "nonterminal_count", "blocking_workers", "closure_authorized", "unregistered_dispatch_detectable"}
    if not required_dispatch_fields.issubset(dispatch_inventory):
        raise ValueError("closeout selection requires a completed delegated-dispatch reconciliation")
    if dispatch_inventory.get("schema") != DISPATCH_INVENTORY_SCHEMA:
        raise ValueError(f"delegated-dispatch inventory declares {dispatch_inventory.get('schema')!r}, not the published {DISPATCH_INVENTORY_SCHEMA}")
    registered = dispatch_inventory.get("workers")
    if not isinstance(registered, (list, tuple)):
        raise ValueError(f"delegated-dispatch inventory's workers must be the registered worker list, not {type(registered).__name__}")
    reconciled = reconcile_dispatch_inventory(workers=registered)
    if reconciled["closure_authorized"] is not True:
        raise ValueError("closure is blocked by unreconciled delegated workers: " + ", ".join(reconciled["blocking_workers"]))
    if dispatch_inventory.get("closure_authorized") is not True:
        raise ValueError("closure is blocked by unreconciled delegated workers: " + ", ".join(dispatch_inventory.get("blocking_workers") or ()))
    for field in ("registered_count", "terminal_count", "nonterminal_count", "blocking_workers", "unregistered_dispatch_detectable"):
        if dispatch_inventory.get(field) != reconciled[field]:
            raise ValueError(f"delegated-dispatch inventory contradicts its own registered workers at {field}: claims {dispatch_inventory.get(field)!r}, reconciles to {reconciled[field]!r}")
    material = sorted(set(triggers))
    advisory_counter = continuity_count >= 3
    full = bool(material or user_requested_publication or not same_stream_next)
    return {
        "schema": "dual-hat-closeout-decision/1.0", "selection": "full" if full else "lightweight_continuity",
        "full_closure_triggers": material, "advisory_three_item_threshold_reached": advisory_counter,
        "counter_forced_full_closure": False, "same_stream_next": same_stream_next,
        "continuity_evidence": dict(continuity_evidence),
        "publication_authorized": user_requested_publication,
        "required_lightweight_evidence": ["checkpoint_commit", "focused_validation", "clean_worktree", "exit_status", "current_handover", "unresolved_findings", "inherited_dependencies", "rollback_point", "pending_publication_inventory", "architecture_disposition_boundary", "no_engineering_self_acceptance", "independent_closure_reconciliation_audit", "delegated_dispatch_reconciliation"],
        "skipped_when_lightweight": ["standalone_export", "remote_publication", "semantic_release", "release_packaging", "manifest_and_checksums", "snapshot", "exhaustive_archival"],
        "reconciliation_audit": dict(reconciliation_audit),
    }


def deferred_publication_inventory(*, canonical_commit: str, retained_changes: Sequence[str], current_changes: Sequence[str], expected_version: str, compatibility: str, release_notes: Sequence[str], dependencies: Sequence[str]) -> dict[str, object]:
    return {
        "schema": "dual-hat-deferred-publication-inventory/1.0", "canonical_source_commit": canonical_commit,
        "retained_prior_changes": list(retained_changes), "current_work_item_changes": list(current_changes),
        "expected_semantic_version": expected_version, "compatibility_impact": compatibility,
        "pending_release_notes": list(release_notes), "dependencies_on_subsequent_work": list(dependencies),
        "published": False,
    }
