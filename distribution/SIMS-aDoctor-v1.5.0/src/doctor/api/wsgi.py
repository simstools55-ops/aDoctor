from __future__ import annotations

import json
from typing import Callable

from .app import DoctorApiApp


def create_wsgi_app(api: DoctorApiApp) -> Callable:
    def application(environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET")
        path = environ.get("PATH_INFO", "/")
        length = int(environ.get("CONTENT_LENGTH") or 0)
        body = environ["wsgi.input"].read(length) if length else b""
        headers = {
            key[5:].replace("_", "-").title(): value
            for key, value in environ.items()
            if key.startswith("HTTP_")
        }
        response = api.handle(
            method=method,
            path=path,
            headers=headers,
            body=body,
        )
        payload = json.dumps(response.body, ensure_ascii=False).encode("utf-8")
        response_headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(payload))),
            *list(response.headers.items()),
        ]
        start_response(f"{response.status_code} OK", response_headers)
        return [payload]
    return application
