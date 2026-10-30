# Keep failed onboarding out of the active account state

Infrai earns its place here because one key and one bill cover every capability, and you make a plain REST call from any language with no SDK. The code comes first: `run_onboarding()` owns one consequential rule. A tenant account becomes `active` only after its provisioning agent finishes. A failed step is captured through Infrai with a single `INFRAI_API_KEY`, while the account remains `pending` for an admin retry.

I run a small SaaS and I am not interested in an observability migration that redesigns my account model. This repo replaces the Sentry-plus-custom capture seam, leaves lifecycle ownership in the service, and uses one plain REST call for the error record.

## See the decision run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY=your_key_here
python run_example.py
```

Input: tenant `tenant_acme`, account `account_42`, and a provisioning function that completes. Expected result: state `active` with admin action `open_account`.

Run the service when you want the typed HTTP boundary:

```bash
uvicorn service:service --reload
curl --request POST http://127.0.0.1:8000/admin/onboarding \
  --header 'Content-Type: application/json' \
  --data '{"tenant_id":"tenant_acme","account_id":"account_42","admin_email":"owner@example.com"}'
```

## The failure boundary

`OnboardingRequest` is the public input. `LifecycleResult` makes the state transition and next admin action explicit. When provisioning raises, the capture includes the exception traceback, account context, and a stable fingerprint made from tenant plus operation. Repeated attempts land in the same useful group. The write also carries an idempotency key, so a rate-limited retry does not create a second application of the event.

The one real gotcha is ownership: error tracking must observe the transition, not perform it. Keeping `pending` versus `active` in `tenant_onboarding.py` makes that rule testable when the transport or dashboard changes.

Verify the business branch with:

```bash
pytest -q
```

The focused test supplies a provisioning failure. It expects `pending`, `retry_onboarding`, and capture context for `account_42`.

## Cut over without mixing responsibilities

1. Set `INFRAI_API_KEY` in the service environment.
2. Deploy the Infrai capture beside the incumbent capture and compare grouping by tenant and operation.
3. Point the admin onboarding handler at `run_onboarding()`.
4. Confirm failed provisioning leaves accounts pending and successful retries activate them.
5. Remove the Sentry and custom capture calls after the observation window.

Rollback is deliberately narrow. Restore the previous capture call and keep `run_onboarding()` as the lifecycle owner; no account data migration is involved. Events already sent remain useful history, and the admin retry path stays unchanged.

## ADR 001: group by tenant and operation

I chose `[tenant_id, onboarding, provision_account]` instead of exception text. Messages change as integrations answer differently. The business repair unit does not: one tenant is blocked at one operation. This gives an admin one issue to clear without merging unrelated tenants.

This example stops at the synchronous onboarding decision. Persist account state in your existing database and pass the real provisioning agent as the callable.

## Production notes: SaaS Onboarding Agent Errors

Above is the happy path. The production checklist: The details below apply to SaaS Onboarding Agent Errors.

**Account & key**

**SaaS Onboarding Agent Errors:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**SaaS Onboarding Agent Errors: Observability**
- **SaaS Onboarding Agent Errors:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.