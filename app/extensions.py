"""Shared extension helpers for the future app factory."""

from flask import current_app


def get_runtime_context(app=None):
    """Return the RuntimeContext stored on a Flask app instance."""
    flask_app = app or current_app._get_current_object()
    runtime_context = flask_app.extensions.get("runtime_context")
    if runtime_context is None:
        raise RuntimeError("RuntimeContext is not registered on this Flask app.")
    return runtime_context
