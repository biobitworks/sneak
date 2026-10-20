"""Staged security-demo application for scan target binding."""

__version__ = "0.1.0"


def healthcheck() -> dict[str, str]:
    return {"status": "ok", "app": "sneak-security-demo", "version": __version__}
