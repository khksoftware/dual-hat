<!-- SPDX-License-Identifier: Apache-2.0 -->

# Product Repository Template

Mandatory surfaces are a product source/runtime boundary, tests where behavior is testable, product architecture/governance, engineering planning/session/validation, ignored workspace policy, source-control policy, and canonical entrypoint/domain indexes. Create optional decisions, ontology, schemas, storage, migrations, templates, and archive directories only when their first artifact exists.

Suggested responsibilities:

```text
product/{architecture,data,governance,src,tests,templates}
engineering/{agents,architecture,governance,handoffs,planning,process,repository,sessions,validation,migrations,archive}
workspace/
```

Each created directory records owner, authority, dependencies, packaging role, lifecycle, navigation, and creation trigger. Do not create empty folder theatre.
