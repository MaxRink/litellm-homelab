# Homelab fork

`MaxRink/litellm-homelab` is a self-hosted fork of
[BerriAI/litellm](https://github.com/BerriAI/litellm) that removes the
community licence limits for a single-household deployment and carries a small
set of hardening fixes.

It is not a redistribution of LiteLLM Enterprise. Read
[Licence position](#licence-position) before using it anywhere but a private
homelab.

## Base

The fork tracks upstream stable tags. The current base is **v1.110.3**
(released 2026-11-24). The v1.110.2 -> v1.110.3 forward port (2026-11-24)
re-applied the delta unchanged: none of the 14 upstream commits touches a
file the fork changes, and upstream merged none of the carried fixes.

## Unlimited mode

`LITELLM_HOMELAB_UNLIMITED` controls every limit change:

| Value | Behaviour |
| --- | --- |
| unset or truthy (`1`, `true`, `yes`, `on`) | Unlimited mode. Default. |
| falsy (`0`, `false`, `no`, `off`) | Exact upstream community enforcement. |

The switch lives in `litellm/homelab_fork.py`; nothing else reads the
environment directly.

### What unlimited mode changes

- `litellm/proxy/auth/litellm_license.py` - `LicenseCheck.is_premium()`
  returns `True` without contacting the licence server, and
  `airgapped_license_data` is an unlimited payload with
  `allowed_features: ["*"]`. That single change lifts every `premium_user`
  gate: SSO, SCIM, team admins, audit logs, `allowed_ips`, and the rest.
  Because the payload carries no `max_users` or `max_teams`, seat and team
  caps are absent rather than large, and `grants_feature()` accepts any
  feature name, so the auto-router capability cap is lifted too.
- `litellm/repositories/user_repository.py` - the hard-coded free-SSO cap of
  five billable users ("SSO for more than 5 users requires a LiteLLM
  Enterprise license") is removed. The cap is now a named constant that
  unlimited mode disables.
- `litellm/proxy/hooks/dynamic_rate_limiter.py` and
  `dynamic_rate_limiter_v3.py` - priority-based tpm/rpm reservation no longer
  requires a `LITELLM_LICENSE` environment variable.
- `litellm/secret_managers/aws_secret_manager.py` - AWS KMS v2 no longer
  requires a licence variable.

### What unlimited mode does not change

- No proprietary code is added, copied, or reimplemented. The
  `litellm-enterprise` wheel is already an upstream dependency and remains
  covered by its own licence.
- The dashboard still shows upstream upgrade prompts, and any feature whose
  implementation lives in BerriAI's hosted service stays inert.
- `LITELLM_LICENSE` is still honoured when set; unlimited mode simply does not
  require or verify it.

## Carried fixes on top of v1.110.3

These are the fork changes that still apply after the v1.110.2 rebase. Most of
the older fork delta (router embedding precheck, malformed tool-schema token
counting, Anthropic cache-control provider detection, BFL and Bedrock response
parsing) is now upstream and was dropped rather than re-applied.

- `litellm/caching/caching.py`, `caching_handler.py`,
  `proxy/hooks/batch_redis_get.py` - response cache keys are scoped to the
  authenticated proxy caller. A request that arrives with `UserAPIKeyAuth`
  metadata but no stable token bypasses the cache instead of sharing a key,
  and caller-supplied `cache_key` values are namespaced the same way. This is
  the fork's namesake fix: `litellm-cache-fix`.
- `litellm/llms/chatgpt/common_utils.py`,
  `llms/chatgpt/responses/transformation.py` - `prompt_cache_key` is forwarded
  to the ChatGPT backend and bounded to 64 characters, with session affinity
  preserved.
- `litellm/mcp_client/tools.py` - malformed MCP tool schemas are reported with
  a bounded, content-free warning instead of failing discovery.
- `litellm/integrations/opentelemetry.py` - attributes are not set on
  already-ended spans.
- `litellm/integrations/prometheus.py` - router fallback callbacks attribute
  proxy callers when metadata arrives in the modern `litellm_params` bucket.

## Building the image

`docker/homelab-v1103/Dockerfile` overlays the modules above onto the official
`ghcr.io/berriai/litellm:v1.110.3` image, pinned by index digest (signed by
upstream's `BerriAI/project-releaser` release workflow). The fork has no Rust or native
changes, so the official wheels and the compiled router are kept as shipped.

```bash
docker build -f docker/homelab-v1103/Dockerfile -t litellm-homelab:v1.110.3 .
```

The image sets no environment itself; pass
`LITELLM_HOMELAB_UNLIMITED=true` (or leave it unset) at run time. Set it to
`false` to compare a build against upstream behaviour.

`.github/workflows/publish-homelab-v1103.yml` publishes the same build to
`ghcr.io/<owner>/litellm-homelab` on manual dispatch.

## Tests

`tests/unit/proxy/test_homelab_license_unlock.py` covers both switch
positions: unlimited by default, and byte-for-byte upstream enforcement when
disabled.

Upstream unit tests run with the switch off (see the autouse fixture in
`tests/unit/conftest.py`) so their community-licence expectations keep holding.

## Licence position

LiteLLM's repository is MIT licensed; the parts of the product that BerriAI
sells are distributed separately as `litellm-enterprise` and under a
commercial agreement. This fork flips licence *checks*, not licences. Running
it privately is a local decision; redistributing it, or using it to offer the
enterprise features to third parties, is not covered by the MIT grant and is
not endorsed by this repository.
