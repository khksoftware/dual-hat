<!-- SPDX-License-Identifier: Apache-2.0 -->

# Repository Governance

A repository root establishes the primary namespace. Descendants state responsibility and do not repeat the root, product, or domain name unless an external language, packaging, or interoperability contract requires it. Every exception records the constraint and validation.

## Roles and boundaries

Classify each artifact as product, framework, engineering state, mutable workspace, historical evidence, test/fixture, generated projection, or transient. Declare owner, canonical source, consumers, dependencies, packaging class, lifecycle, update trigger, and supersession. Exclusive roles have exactly one active authority.

Production code cannot depend on engineering administration, framework source, archives, or mutable workspace. Framework code cannot depend on a product or its archives. Profiles may depend on the framework. Archives are excluded from routine discovery, validation, context retrieval, and packaging.

## Structural change

Path-heavy work is scan-first: inventory sources, writers, readers, imports, manifests, schemas, tests, docs, generated state, histories, rollback, and unknowns before mutation. Produce a source-to-destination map, verify authorization, migrate atomically, rebind active consumers, preserve historical references, and avoid aliases without a demonstrated time-bounded consumer.

## Artifact lifecycle

At closure, retain active only with an ongoing consumer and trigger; archive only with audit, rollback, legal, provenance, or occasional-consultation value; otherwise delete reproducible transients. A name such as `legacy`, `migration`, `current`, or `durable` does not establish lifecycle. Completed capability artifacts do not remain in active paths by omission.

Generated state records its authoritative inputs, deterministic method, invalidation triggers, and replacement behavior. Superseded output is removed once required lineage and rollback evidence are preserved.
