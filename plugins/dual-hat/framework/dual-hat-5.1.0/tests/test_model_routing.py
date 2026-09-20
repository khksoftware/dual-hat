# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))

from model_routing import ORDER, TIERS, bind_development_environment, fingerprint, production_configuration, require_tier, switch_selection, tier_for_activity

DUAL_HAT_CAPABILITY_PROOFS = {"explicit_user_and_architecture_reporting", "resumable_handoff"}


class ModelRoutingTests(unittest.TestCase):
    def models(self, adapter="test-host", tools=("files","tests"), runtime=None):
        runtime=runtime or {"os":"fixture"}; environment=fingerprint({"adapter_identity":adapter,"tools":sorted(set(tools)),"runtime":runtime})
        def row(selection, tiers, confirmed=True):
            capability={"source_type":"governed_registry","authority_id":"fixture-registry","observation_id":f"capability-{selection}", "verified_tiers":list(tiers),"environment_fingerprint":environment}; capability["evidence_hash"]=fingerprint(capability)
            availability={"source_type":"adapter_probe","authority_id":adapter,"observation_id":f"availability-{selection}", "adapter_identity":adapter, "observed_available":True,"environment_fingerprint":environment}; availability["evidence_hash"]=fingerprint(availability)
            return {"selection_id":selection, "capability_evidence":capability, "availability_evidence":availability, "user_confirmation":{"selection_id":selection,"adapter_identity":adapter,"environment_fingerprint":environment,"confirmed":confirmed,"confirmed_by":"fixture-user"}}
        return [row("local-standard", ORDER[:2]), row("confirmed-advanced", [ORDER[2]])]

    def test_portable_tiers_are_abstract_and_assign_activities(self):
        self.assertEqual(4, len(TIERS)); self.assertEqual(ORDER[3], tier_for_activity("security_review"))
        text = " ".join(str(value) for value in TIERS.values()).casefold()
        self.assertNotIn("provider", text); self.assertNotIn("model name", text)

    def test_onboarding_and_project_lifecycle_require_current_project_mapping(self):
        onboarding = (ROOT / "process/ONBOARDING.md").read_text(encoding="utf-8")
        planning = (ROOT / "planning/PLANNING_MODEL.md").read_text(encoding="utf-8")
        profile = (ROOT / "governance/PLATFORM_PROFILE_CONTRACT.md").read_text(encoding="utf-8")
        handover = (ROOT / "sessions/SESSION_AND_HANDOVER_PROTOCOL.md").read_text(encoding="utf-8")
        self.assertIn("Onboarding is incomplete when tiers remain abstract", onboarding)
        self.assertIn("project-local model-tier mapping", onboarding)
        self.assertIn("assigns the abstract model tier", planning)
        self.assertIn("environment fingerprint", planning)
        self.assertIn("model-tier mapping", profile)
        self.assertIn("model-tier mapping identity and environment fingerprint", handover)

    def test_evidence_binding_remaps_and_hard_stops_missing_mandatory_tier(self):
        first = bind_development_environment(adapter_identity="test-host", tools=["files", "tests"], runtime_fingerprint={"os": "fixture"}, configured_models=self.models())
        second = bind_development_environment(adapter_identity="new-host", tools=["files"], runtime_fingerprint={"os": "fixture2"}, configured_models=self.models(), prior_binding=first)
        self.assertTrue(second["environment_changed"]); self.assertEqual("satisfied", require_tier(first, ORDER[2])["status"])
        self.assertEqual("hard_stop", require_tier(second, ORDER[2])["status"])
        stop = require_tier(first, ORDER[3]); self.assertEqual("hard_stop", stop["status"]); self.assertTrue(stop["resumable"])
        optional = require_tier(first, ORDER[3], mandatory=False); self.assertEqual("fallback_requires_confirmation", optional["status"])
        same_adapter_changed=bind_development_environment(adapter_identity="test-host",tools=["files"],runtime_fingerprint={"os":"fixture2"},configured_models=self.models(),prior_binding=first); self.assertEqual("hard_stop",require_tier(same_adapter_changed,ORDER[2])["status"])

    def test_production_requires_explicit_concrete_approval(self):
        stop = production_configuration({}); self.assertEqual("hard_stop", stop["status"]); self.assertFalse(stop["silent_provider_selection"])
        capability={"source_type":"governed_registry","authority_id":"fixture-registry","observation_id":"production-capability","verified_tiers":[ORDER[0],ORDER[1]]}; capability["evidence_hash"]=fingerprint(capability)
        values = {"provider":"fixture-provider", "model":"fixture-model", "reasoning_effort":"standard", "fallback":"stop", "privacy_preference":"no training", "local_or_cloud":"local", "cost_sensitivity":"balanced", "latency_preference":"balanced", "data_retention_restrictions":"none retained", "permitted_task_classes":["routine"], "unavailable_model_behavior":"stop", "capability_evidence":capability, "approved_by_user":True}
        approved = production_configuration(values); self.assertEqual("approved", approved["status"]); self.assertFalse(approved["derived_from_development_detection"])
        self.assertEqual(64, len(approved["configuration_hash"]))

    def test_switching_only_at_safe_boundary(self):
        capability={"source_type":"governed_registry","authority_id":"fixture-registry","observation_id":"production-capability","verified_tiers":[ORDER[1]]}; capability["evidence_hash"]=fingerprint(capability)
        values = {"provider":"fixture-provider", "model":"b", "reasoning_effort":"standard", "fallback":"stop", "privacy_preference":"no training", "local_or_cloud":"local", "cost_sensitivity":"balanced", "latency_preference":"balanced", "data_retention_restrictions":"none retained", "permitted_task_classes":["routine"], "unavailable_model_behavior":"stop", "capability_evidence":capability, "approved_by_user":True}
        approved=production_configuration(values); available={"selection_id":"b","observed_available":True,"source_type":"adapter_probe","authority_id":"fixture-host","observation_id":"available-b"}; available["evidence_hash"]=fingerprint(available); unavailable={"selection_id":"b","observed_available":False,"source_type":"adapter_probe","authority_id":"fixture-host","observation_id":"unavailable-b"}; unavailable["evidence_hash"]=fingerprint(unavailable)
        common={"current":"a","target":"b","required_tier":ORDER[1],"approved_configuration":approved,"operation_id":"op-1"}
        self.assertEqual("deferred_to_safe_boundary", switch_selection(atomic_operation_active=True,availability_evidence=available,**common)["status"])
        self.assertEqual("hard_stop", switch_selection(atomic_operation_active=False,availability_evidence=unavailable,**common)["status"])
        self.assertEqual("switch_authorized", switch_selection(atomic_operation_active=False,availability_evidence=available,**common)["status"])
        self.assertEqual("hard_stop",switch_selection(atomic_operation_active=False,availability_evidence=available,**{**common,"required_tier":ORDER[3]})["status"])
        with self.assertRaises(Exception): switch_selection(atomic_operation_active=False,availability_evidence=available,**{**common,"target":"not-approved"})


if __name__ == "__main__": unittest.main()
