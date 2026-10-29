"""Stable entry point: preserves uvicorn server:app and maintenance integrations.

Execute the application in this namespace so existing integrations that override
DB, clock or configuration continue to reference the same function globals.
Business code lives in backend/application.py; no duplicated implementation.
"""
from pathlib import Path as _Path
_source = _Path(__file__).resolve().parent / 'backend' / 'application.py'
exec(compile(_source.read_bytes(), str(_source), 'exec'), globals())
