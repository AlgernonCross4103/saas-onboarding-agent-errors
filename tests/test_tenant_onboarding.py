from unittest.mock import patch

from tenant_onboarding import OnboardingRequest, run_onboarding


def test_failed_provisioning_keeps_account_pending_and_records_context() -> None:
    request = OnboardingRequest(
        tenant_id="tenant_acme",
        account_id="account_42",
        admin_email="owner@example.com",
    )

    def reject_provisioning(_: OnboardingRequest) -> None:
        raise ValueError("billing profile is incomplete")

    with patch("tenant_onboarding.infrai.errors.capture") as capture:
        result = run_onboarding(request, reject_provisioning)

    assert result.state == "pending"
    assert result.next_admin_action == "retry_onboarding"
    capture.assert_called_once()
    sent = capture.call_args.kwargs
    assert sent["fingerprint"] == ["tenant_acme", "onboarding", "provision_account"]
    assert sent["context"]["account_id"] == "account_42"
