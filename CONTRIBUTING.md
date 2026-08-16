# Contributing to Zyntalic

Thank you for helping improve Zyntalic. Contributions are welcome across the language engine, tests, documentation, frontend, data tooling, and developer experience.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md). For vulnerabilities, use the private process in [SECURITY.md](SECURITY.md) instead of opening a public issue.

## Before you start

- Search existing issues and pull requests before opening a duplicate.
- Use a focused issue for behavior changes or work that affects deterministic output.
- Keep pull requests small enough to review and validate as one coherent change.
- Do not mix generated artifacts, unrelated formatting, or broad file moves into a feature fix.

## Development setup

Python 3.10 or newer is required.

```bash
git clone https://github.com/kugguk2022/Zyntalic_idiom.git
cd Zyntalic_idiom
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,web,pdf]"
```

For frontend changes:

```bash
cd zyntalic-flow
npm ci
npm run dev
```

## Quality checks

Run focused tests while iterating, then full checks before requesting review:

```bash
ruff check .
pytest
```

For REST API work:

```bash
pytest tests/test_web_api.py tests/test_api_connection.py tests/test_cache.py
```

For generator or language-rule work:

```bash
pytest tests/test_determinism.py tests/test_generator_stages.py \
  tests/test_surface_rules.py tests/test_mirror_rules.py \
  tests/test_quality_gate_golden.py
```

The repository currently reports three inherited regressions separately in CI; see issue #9. New work must not add failures or expand the exclusion list.

## Deterministic output changes

Treat generated output as a compatibility surface. A change that alters stable output must include:

1. the reason for the change;
2. representative before/after examples;
3. tests for the intended rule;
4. an intentional golden-fixture update, if applicable;
5. a changelog entry explaining downstream impact;
6. any cache or schema version bump required to prevent stale results.

Use `zyntalic.utils.rng.get_rng` for pseudo-random behavior. Do not introduce process-randomized hashes, global random state, current time, network responses, or machine-specific paths into the baseline generation path.

## Code conventions

- Keep the core functional with NumPy alone.
- Load optional dependencies lazily and provide a deterministic fallback.
- Prefer type annotations for new public functions and data structures.
- Keep public API behavior backward compatible, or version the change.
- Preserve final context-tail placement for non-reverse output.
- Add end-to-end coverage when integrating an experimental module into a public interface.
- Keep network-facing API defaults fail-closed.

## Documentation changes

- Installation and common commands belong in `README.md`.
- Product concepts, architecture, and rationale belong in `wiki/`.
- Normative language rules belong in `zyntalic_docs/` and should have executable examples.
- User-visible changes belong in `CHANGELOG.md` under **Unreleased**.

Check relative links and avoid documenting proposed features as shipped behavior.

## Data and lexicon contributions

Only contribute data that the project can legally redistribute. Public-domain or clearly licensed sources are preferred. Include source URL, author, title, license/public-domain rationale, retrieval date, and transformation steps.

Never commit personal information, private corpora, credentials, copyrighted books without permission, or large generated artifacts. Changes to `lexicon/` must account for the packaged copy under `zyntalic/resources/lexicon/` until a single-source build process replaces the duplicate trees.

## Pull requests

A good pull request explains the problem and approach, links its issue, lists validation, calls out deterministic-output or API-contract changes, includes screenshots for visible frontend changes, and updates documentation and the changelog when users are affected.
