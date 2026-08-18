"""The one place that decides where the Zyntalic service listens.

Every launcher, health check, restart tool, and client script imports from here. Before this
module existed the port was written out by hand in a dozen files, and they disagreed: the README
and the compose file said 8000 while every operational script said 8001. The result was a server
that its own tooling could not see -- ``check_status`` probed a port nothing was bound to and
reported "not running", ``kill_and_restart`` killed whichever unrelated process happened to hold
the port it guessed, and the real server stayed up indefinitely because nothing ever looked where
it actually was.

The default is deliberately not 8000. That port is the FastAPI/uvicorn convention, so it is the
one every other local service grabs first; sharing it is what let a neighbouring project's API
answer requests meant for this one. Override with ``ZYNTALIC_PORT`` when running more than one
instance, but override it in the environment -- not by editing a literal into a script, which is
how the numbers drifted apart in the first place.
"""

from __future__ import annotations

import os

#: Chosen to sit clear of the 8000/8080 range that generic dev servers default to.
DEFAULT_PORT = 8004
DEFAULT_HOST = "127.0.0.1"


def resolve_port() -> int:
    """The port to bind or probe, from ``ZYNTALIC_PORT`` or :data:`DEFAULT_PORT`.

    A malformed value raises rather than silently falling back: binding somewhere other than where
    the operator asked is the exact failure this module exists to prevent.
    """
    raw = os.getenv("ZYNTALIC_PORT")
    if raw is None or not raw.strip():
        return DEFAULT_PORT
    try:
        port = int(raw)
    except ValueError:
        raise ValueError(f"ZYNTALIC_PORT must be an integer, got {raw!r}") from None
    if not 1 <= port <= 65535:
        raise ValueError(f"ZYNTALIC_PORT must be in 1-65535, got {port}")
    return port


def resolve_host() -> str:
    """The interface to bind or probe, from ``ZYNTALIC_HOST`` or :data:`DEFAULT_HOST`."""
    return os.getenv("ZYNTALIC_HOST", DEFAULT_HOST).strip() or DEFAULT_HOST


def base_url() -> str:
    """Root URL of the service, for health probes and client scripts."""
    return f"http://{resolve_host()}:{resolve_port()}"
