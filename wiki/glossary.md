# Glossary

**Anchor** — A named literary or philosophical reference corpus used as a semantic coordination point. Anchor weights influence generation and are exposed in metadata.

**Anchor mode** — The policy for choosing anchors: automatic, manual selection, or neutral/no automatic influence.

**Context tail** — The final `⟦ctx: ...⟧` block attached to non-reverse surface output. It is the plain-text projection of generation metadata.

**Controlled variation** — An intentional output change caused by explicit configuration—such as seed, dialect, register, frame, or anchors—while unrelated choices remain stable.

**Deterministic baseline** — The dependency-light path whose result is reproducible for a fixed input, configuration, code version, and resource snapshot.

**Frame** — A semantic interpretation recorded with a name and weight/confidence in the intermediate representation.

**Golden set** — Inputs and expected outputs or hashes used to detect unintended generation drift.

**IR (intermediate representation)** — Structured information between source analysis and surface rendering. In Zyntalic this includes frames, pivot, anchors, sigil, and scope.

**Mirror/chiasmus** — A reciprocal A–B / B–A rhetorical structure produced deterministically by the mirror engine.

**Pivot** — The structural relationship between frames or sides of a generated sentence, represented by `PivotType`.

**Projection** — An optional learned matrix that maps an embedding into the space used for anchor comparison.

**Scope** — The set of generation controls such as evidentiality, register, dialect, frames, and anchor selection. A scope signature identifies the combination.

**Seed lock** — A proposed product concept for persisting the seed/configuration of a creative asset so it can be regenerated exactly.

**Sidecar** — The structured JSON-friendly metadata accompanying a surface translation. It is richer and safer for software than parsing the visible context tail.

**Sigil** — A compact generated symbol/string associated with a mirror or sentence transformation and recorded in the sidecar.

**S-O-V-C** — Subject–Object–Verb–Context, the project’s canonical high-level clause order.

**Surface form** — The rendered synthetic-language text seen by a reader, distinct from its source, gloss, or sidecar metadata.
