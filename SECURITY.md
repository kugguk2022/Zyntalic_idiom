# Security Policy

## Supported versions

Zyntalic is currently pre-stable. Security fixes are applied to the latest code on the default branch; older releases are not guaranteed to receive patches.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's **Report a vulnerability** function in the repository Security tab to submit a private advisory.

Include the affected version or commit, vulnerable component, reproduction steps, realistic impact, required attacker access, and suggested mitigation when possible. Please allow maintainers a reasonable opportunity to investigate and release a fix before public disclosure. You should receive acknowledgement within seven days.

## Deployment guidance

- Set a strong `ZYNTALIC_API_KEY` for every network-facing deployment.
- Never enable `ZYNTALIC_ALLOW_UNAUTHENTICATED_LOCAL` on a network interface.
- Restrict `ZYNTALIC_CORS_ORIGINS` to trusted origins in production.
- Enforce shared rate limiting at the gateway for multiple workers or instances.
- Apply upload and text-size limits appropriate to the deployment.
- Store caches on a protected path and do not treat them as a secrets store.
- Keep optional parsers, web dependencies, and the container base image updated.
- Do not send confidential source text to external model services without explicit operator approval.

Built-in authentication and rate limiting are application safeguards, not replacements for TLS, network controls, monitoring, backups, and normal production hardening.
