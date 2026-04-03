from __future__ import annotations

from sepa.api.factory import create_app


app = create_app()

__all__ = ['app', 'create_app']
