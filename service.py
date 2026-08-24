"""HTTP boundary for tenant onboarding and admin retries."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from infrai import InfraiError
from tenant_onboarding import LifecycleResult, OnboardingRequest, run_onboarding

service = FastAPI(title="Tenant onboarding failure tracker")


def provision_account(_: OnboardingRequest) -> None:
    """Replace with the application's real provisioning agent step."""
    return None


@service.exception_handler(InfraiError)
async def infrai_rejection_handler(_, exc: InfraiError) -> JSONResponse:
    status = exc.status_code if 400 <= exc.status_code < 500 else 502
    return JSONResponse(status_code=status, content={"error": exc.detail})


@service.post("/admin/onboarding", response_model=LifecycleResult)
def onboard_tenant(request: OnboardingRequest) -> LifecycleResult:
    return run_onboarding(request, provision_account)
