<!-- SPDX-License-Identifier: Apache-2.0 -->

# Composing More Than One Write-Time Gate Behind One Hook Slot

Principle 14's own detector is a worked example of a write-time control: a fail-closed check
over active tracked content, wired so a violation cannot reach a commit unnoticed. Its stated
residual is that the check is a function, not a schedule — *"it fires when something invokes
it, and this framework ships no gate that does. An adopter that does not wire it into a commit
or closure gate has the detector and not the control."* This guide is the reference pattern for
that wiring, generalized past any single detector, for the moment an adopter needs more than
one.

**Advice, and stated as such rather than shipped as a control.** Nothing here is executable
framework source and nothing in this framework's shipped source enforces that an adopter follows
this pattern. It travels as a documented shape and as one measured lesson about where a gate
reads its content from; the detectors it dispatches to are necessarily project-specific, so
there is no generic, shippable module to hand an adopter — only the composition shape and the
reasoning behind it.

## The problem this pattern answers

Git dispatches exactly one `hooks/pre-commit`. An adopter arming principle 14's detector, and
then separately arming a second independent write-time gate, cannot install two hooks: the
second installation overwrites the first, and whichever installer runs last silently wins. This
is not a corner case — it is the ordinary state of a project that has grown past its first
write-time check, and it recurs the moment a second one is needed.

## The shape: a no-logic dispatcher over independently-armed markers

The fix is not a bigger hook. It is a hook that does nothing but dispatch:

- **The installed shim holds no logic of its own, only dispatch.** It does not implement, or
  even know the details of, any individual gate's rule.
- **Each gate owns its own independently-armable marker** — a small file in the repository's
  shared Git directory, written by that gate's own installer and checked only by that gate's own
  predicate.
- **The shim checks which markers are present and, for each one present, invokes that gate's own
  predicate.** A repository armed for neither gate runs neither. Armed for one, it runs only
  that one. Armed for both, it runs both, and refuses the commit if either one does.
- **Marker names are imported from each gate's own module, never re-typed in the shim.** A
  literal re-typed in two places can drift out of agreement with what the gate's own installer
  actually writes; importing the name from its single owning module makes that drift structurally
  impossible rather than merely discouraged.

This composes indefinitely — a third, fourth, or later gate is another marker and another
dispatch branch, never a second hook file competing for the one slot.

## Read the commit's actual staged content, never the working tree

A pre-commit gate that reads the working tree is wrong in the same repository this pattern is
built for, for two independent reasons, and both were established by direct measurement rather
than assumed:

1. **A partial-path commit reads only the paths it names.** Where the commit form in use commits
   working-tree content for an explicit path list rather than everything staged, a gate that
   reads the working tree for an unrelated path sees content that may never be part of this
   commit at all.
2. **A shared index can hold a derived value one step behind the working tree.** Where more than
   one contributor or process shares a single working tree and its Git index, a blob staged
   earlier keeps whatever derived value — a stamped hash, a restamped digest, a generated count —
   was true when it was staged, even after the working tree has since moved on. A gate that reads
   the working tree passes cleanly against content that is not what the commit will actually
   contain.

The correct read is the commit's own prepared index, through Git's own plumbing — reading the
blob Git has already resolved for the path under commit, rather than the file on disk. This
resolves correctly under both an explicit partial-path commit and an ordinary full-index one,
with one code path and no branching on which form the operator used, because Git itself performs
that resolution before the hook ever runs.

## State the bypass rather than hide it

A pre-commit hook is not a non-circumventable control. It can be skipped outright by the
operator, and it can be silently repointed to nowhere by reconfiguring where hooks are read from.
Neither of these is a defect in the pattern; both are properties of what a pre-commit hook is.
The pattern's own regression coverage exercises both bypass paths explicitly and asserts what
happens, rather than leaving them to be discovered later by someone who assumed the hook was
absolute. A control whose bypass is undocumented and untested is not a stronger control — it is
the same control with a surprise in it.

## An illustrative skeleton, not shippable code

The following is illustrative only — a shape to copy and fill in with an adopter's own gates,
not a module this framework ships or imports. Gate names, marker names, and predicates are all
placeholders.

```
# Owned by each gate's own module -- never re-typed in the shim.
GATE_A_MARKER_NAME = "gate-a.armed"
GATE_B_MARKER_NAME = "gate-b.armed"

def dispatch_pre_commit(git_dir, staged_paths, read_staged_blob):
    """The shim: no rule logic of its own, only marker-gated dispatch."""
    failures = []
    if (git_dir / GATE_A_MARKER_NAME).exists():
        failures += gate_a_predicate(staged_paths, read_staged_blob)
    if (git_dir / GATE_B_MARKER_NAME).exists():
        failures += gate_b_predicate(staged_paths, read_staged_blob)
    return failures  # non-empty -> refuse the commit
```

`read_staged_blob` is the one collaborator every gate predicate shares: a function that resolves
a path's content from the commit's own prepared index — never from the working tree — so every
gate composed behind this shim inherits the correct read by construction rather than by each
predicate's author remembering to get it right independently.
