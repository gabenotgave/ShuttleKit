"""Uvicorn entry: ``uvicorn main:app`` (run from the ``api/`` directory)."""

from shuttlekit.main import app

__all__ = ["app"]
