---
name: use-dual-hat
description: Apply an installed Dual Hat framework to governed software work. Use when onboarding a repository, choosing Integrated or Split Mode, defining or executing a bounded work item, reviewing architecture or code, validating changes, managing handoffs, or closing and publishing work under Dual Hat.
---

# Use Dual Hat

Treat the installed Dual Hat framework as canonical. This skill routes work to it; it does not replace, weaken, or reproduce its authority.

## Resolve and verify the framework

1. Resolve the plugin root two directories above this skill, then read `framework-payload.json`.
2. Use the declared package-local `framework/dual-hat-1.16.0/` root by default. Verify its `release/VERSION.json`, `.dual-hat-release/content-manifest.json`, and every content hash before governed mutation.
3. If the user explicitly supplies an external framework override, validate the same required files and report both versions. Accept a 1.x override only when it is not older than the bundled version. A different major version requires its governed migration and compatibility review before use.
4. Accept a selected root only when it contains `repository/CANONICAL_ENTRYPOINTS.md`, `process/ONBOARDING.md`, and `governance/CONFORMANCE_POLICY.md`.
5. Report whether the selected root is bundled or external and its version. Fall back to the verified bundled root when an override is absent or invalid.

The bundled payload is an exact extraction of the published, checksum-bound Dual Hat 1.16.0 release. Treat it as read-only source. Do not copy the framework tree into a product repository outside the canonical binding workflow.

## Route the request

Read `references/framework-routing.md`, then open the listed canonical framework entrypoints for the user's task. Also read repository-local instructions and the active product profile before proposing mutation.

If sources conflict, stop and surface the conflict. The framework and approved product profile determine authority; this skill never resolves a governance conflict by itself.

## Operate

1. Establish the requested role and operating mode. Use Integrated Mode only when no approved project rule or user decision selects Split Mode.
2. Inspect before changing. Classify repository boundaries, authority, affected artifacts, dependency direction, and the smallest sufficient validation.
3. Respect approval boundaries. A plugin install grants no authority to create repositories, bind or remove framework state, accept debt, publish, push, or perform destructive work.
4. Use current framework templates, schemas, scripts, and validators from the verified installation rather than recreating their rules in chat.
5. Keep platform or model selection in the product's approved profile. Portable Dual Hat remains provider-neutral.
6. Report decisions, changed paths, validation evidence, limitations, and remaining approvals at handoff.

For onboarding, present the plan and approval package before material product mutation. For implementation, require a bounded authorized work item and perform proportionate validation. For review, preserve reviewer independence required by the current contract. For closure or publication, follow the current handoff, continuity, release, and remote-authority rules.

## Safety boundary

Do not send repository content, credentials, private data, or prompts to a new service merely because a platform plugin is installed. Do not start hooks, MCP servers, network clients, or executables: this package contains none. Apply the framework's current third-party dependency evaluation before proposing any such addition.
