"""Run the lifecycle decision without starting an HTTP server."""

from tenant_onboarding import OnboardingRequest, run_onboarding


def provision(_: OnboardingRequest) -> None:
    return None


request = OnboardingRequest(
    tenant_id="tenant_acme",
    account_id="account_42",
    admin_email="owner@example.com",
)
print(run_onboarding(request, provision).model_dump_json(indent=2))
