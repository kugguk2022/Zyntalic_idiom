# Repository Guide

## Where things belong

```text
apps/                 Application adapters (web and CLI wrappers)
data/                 Small fixtures and anchor inputs
data_generation/      Corpus acquisition and transformation pipeline
docker/               Container build files
evals/                Small evaluation/smoke suites
lexicon/              Checkout/runtime literary lexicons
scripts/              Operational, training, and maintenance commands
tests/                Primary automated behavior tests
wiki/                 Product, architecture, history, and roadmap
zyntalic/              Installable Python engine
zyntalic_docs/         Generated language-design reference
zyntalic-flow/         React/Vite frontend
```

Root-level files should be limited to project entry points and repository-wide configuration: README, license, changelog, contribution policy, packaging, environment example, and compatibility launchers.

## Documentation model

- Put **how to install/run** in the root README.
- Put **what the project is and why** in `wiki/`.
- Put **language rules** in `zyntalic_docs/`, backed by tests where normative.
- Put **dataset operations** in `DATASET.md` until that guide is intentionally migrated.
- Keep `BACKLOG.md` as the terse engineering ledger; use the wiki roadmap for narrative and rationale.
- Record released behavior in `CHANGELOG.md`, not in the roadmap.

## Safe cleanup policy

The working tree may contain local changes and generated artifacts. Before reorganizing:

1. inspect `git status`;
2. do not move a modified file without understanding the change;
3. use `rg` to find imports, path strings, documentation links, CI references, and packaging rules;
4. add compatibility shims for public launchers;
5. update tests and docs in the same change;
6. verify both editable-install and checkout execution paths.

Generated directories such as `__pycache__`, `.pytest_cache`, `dist`, `build`, `*.egg-info`, model outputs, and runtime caches are already ignored. They can be removed in a dedicated cleanup change after confirming no untracked work is stored there.

## Test organization

- New behavior tests belong in `tests/`.
- `evals/` should contain small evaluation or smoke gates with a clearly distinct purpose.
- Do not add new tests to `unittests/`; migrate unique legacy coverage into `tests/`, then remove the duplicate tree in a dedicated change.
- Golden fixtures belong under `data/fixtures/` and should identify the version/schema that produced them.

## Data and lexicon organization

Source, generated, and packaged data should not be edited independently. The desired future flow is:

```text
canonical source → validation/build step → packaged resource
                                  └──────→ generated corpus/artifact
```

Until that flow is implemented, changes to root `lexicon/` should be checked against `zyntalic/resources/lexicon/` to prevent packaging drift.

## Change checklist

- Does the baseline still work without optional dependencies?
- Is every pseudo-random choice derived from the project RNG utility?
- Does non-reverse output retain a final valid context tail?
- Are structured fields backward compatible or versioned?
- Are security-sensitive API defaults still fail-closed?
- Are new claims in the language docs demonstrated by a test?
- Are new files placed in the narrowest existing directory rather than the root?
