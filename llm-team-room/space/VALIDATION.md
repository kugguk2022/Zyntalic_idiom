# Validation — 12 November 2026

- `python -m unittest -v`: 16 tests passed, including real local HTTP requests.
- `node --check static/app.js`: passed.
- Seven synthetic manipulation scenarios preserve the expected guarded outcome.
- A deliberately forged legitimate-slot relay succeeds structurally; identity remains explicitly unverified.
- Browser test attempted with installed Chromium and Playwright. Chromium failed at `process_singleton_posix.cc`, reporting `socket() failed: Operation not permitted`. No screenshot or visual/UI pass is claimed.
- Dockerfile prepared; no container build was performed in this task.
- No external model APIs were called. No actual ballots were collected or inferred.
- HF authentication inspected: connected as kugguk; read-repos, read-mcp, jobs, openid, profile scopes. No repository write scope. Space not deployed.
