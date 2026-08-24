"""Account lifecycle decisions around one observable agent step."""

from __future__ import annotations

import traceback
from collections.abc import Callable
from typing import Any, Literal

from pydantic import BaseModel, Field

import infrai


class OnboardingRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    admin_email: str = Field(min_length=3)


class LifecycleResult(BaseModel):
    tenant_id: str
    account_id: str
    state: Literal["pending", "active"]
    next_admin_action: Literal["retry_onboarding", "open_account"]


def run_onboarding(
    request: OnboardingRequest,
    provision: Callable[[OnboardingRequest], Any],
) -> LifecycleResult:
    """Activate only after provisioning completes; otherwise capture and stay pending."""
    try:
        provision(request)
    except Exception as exc:
        event_key = f"onboarding:{request.tenant_id}:{request.account_id}"
        infrai.errors.capture(
            idempotency_key=event_key,
            title="tenant onboarding agent failed",
            message=f"{type(exc).__name__}: {exc}",
            level="error",
            fingerprint=[request.tenant_id, "onboarding", "provision_account"],
            exception=traceback.format_exc(),
            context={
                "tenant_id": request.tenant_id,
                "account_id": request.account_id,
                "operation": "provision_account",
            },
        )
        return LifecycleResult(
            tenant_id=request.tenant_id,
            account_id=request.account_id,
            state="pending",
            next_admin_action="retry_onboarding",
        )

    return LifecycleResult(
        tenant_id=request.tenant_id,
        account_id=request.account_id,
        state="active",
        next_admin_action="open_account",
    )
