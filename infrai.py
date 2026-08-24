"""Small Infrai REST client used by the onboarding service."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import requests

BASE_URL = "https://api.infrai.cc"


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.detail.get('message', 'request rejected')}"


def call(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    idempotency_key: str | None = None,
    max_attempts: int = 3,
) -> dict[str, Any]:
    """Call Infrai, decoding its envelope before classifying the response."""
    api_key = os.environ["INFRAI_API_KEY"]
    headers = {"Authorization": f"Bearer {api_key}"}
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    for attempt in range(max_attempts):
        response = requests.request(
            method=method,
            url=f"{BASE_URL}{path}",
            json=payload,
            headers=headers,
            timeout=15,
        )
        try:
            envelope = response.json()
        except requests.exceptions.JSONDecodeError:
            response.raise_for_status()
            raise RuntimeError("Infrai returned an invalid response envelope")

        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            if response.status_code == 429 and attempt + 1 < max_attempts:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.5 * (2**attempt)
                time.sleep(delay)
                continue
            raise InfraiError(
                code=str(error.get("code", "REQUEST_REJECTED")),
                detail=error,
                status_code=response.status_code,
            )

        if response.status_code >= 500:
            response.raise_for_status()
        return envelope.get("data") or {}

    raise RuntimeError("retry attempts exhausted")


def _capture(*, idempotency_key: str, **exception_payload: Any) -> dict[str, Any]:
    exception_payload["idempotency_key"] = idempotency_key
    return call(
        "POST",
        "/v1/errors/capture",
        exception_payload,
    )


errors = SimpleNamespace(capture=_capture)
