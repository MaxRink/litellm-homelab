# Homelab LiteLLM image: the official upstream runtime with this fork's
# Python modules overlaid.
#
# The fork carries no Rust or native changes, so the official image is used as
# the base and only the patched modules are copied over the installed package.
# This keeps the image small and makes the fork delta auditable: every file
# below is a file this repository still changes relative to upstream.
#
# Build context is the repository root:
#   docker build -f docker/homelab-v1103/Dockerfile -t litellm-homelab:v1.110.3 .
#
# Runtime switches (see HOMELAB.md):
#   LITELLM_HOMELAB_UNLIMITED=true   unlimited licence mode (default)
#   LITELLM_HOMELAB_UNLIMITED=false  restore upstream community enforcement
ARG BASE_IMAGE=ghcr.io/berriai/litellm:v1.110.3@sha256:1050d2c9ca58399de9cd51df6eb503812af697717f54d2f08c1c30589c75e1f7
FROM ${BASE_IMAGE}

ARG SITE=/app/.venv/lib/python3.13/site-packages/litellm

# Licence unlock: premium features, seat/team caps and the community SSO limit.
COPY litellm/homelab_fork.py ${SITE}/homelab_fork.py
COPY litellm/proxy/auth/litellm_license.py ${SITE}/proxy/auth/litellm_license.py
COPY litellm/repositories/user_repository.py ${SITE}/repositories/user_repository.py
COPY litellm/proxy/hooks/dynamic_rate_limiter.py ${SITE}/proxy/hooks/dynamic_rate_limiter.py
COPY litellm/proxy/hooks/dynamic_rate_limiter_v3.py ${SITE}/proxy/hooks/dynamic_rate_limiter_v3.py
COPY litellm/secret_managers/aws_secret_manager.py ${SITE}/secret_managers/aws_secret_manager.py

# Cache: authenticated caller isolation for response cache keys.
COPY litellm/caching/caching.py ${SITE}/caching/caching.py
COPY litellm/caching/caching_handler.py ${SITE}/caching/caching_handler.py
COPY litellm/proxy/hooks/batch_redis_get.py ${SITE}/proxy/hooks/batch_redis_get.py

# Observability and provider fixes.
COPY litellm/integrations/opentelemetry.py ${SITE}/integrations/opentelemetry.py
COPY litellm/integrations/prometheus.py ${SITE}/integrations/prometheus.py
COPY litellm/llms/chatgpt/common_utils.py ${SITE}/llms/chatgpt/common_utils.py
COPY litellm/llms/chatgpt/responses/transformation.py ${SITE}/llms/chatgpt/responses/transformation.py
COPY litellm/mcp_client/tools.py ${SITE}/mcp_client/tools.py

RUN python -m py_compile \
      ${SITE}/homelab_fork.py \
      ${SITE}/proxy/auth/litellm_license.py \
      ${SITE}/repositories/user_repository.py \
      ${SITE}/proxy/hooks/dynamic_rate_limiter.py \
      ${SITE}/proxy/hooks/dynamic_rate_limiter_v3.py \
      ${SITE}/secret_managers/aws_secret_manager.py \
      ${SITE}/caching/caching.py \
      ${SITE}/caching/caching_handler.py \
      ${SITE}/proxy/hooks/batch_redis_get.py \
      ${SITE}/integrations/opentelemetry.py \
      ${SITE}/integrations/prometheus.py \
      ${SITE}/llms/chatgpt/common_utils.py \
      ${SITE}/llms/chatgpt/responses/transformation.py \
      ${SITE}/mcp_client/tools.py \
    && find ${SITE} -name '__pycache__' -type d -prune -exec rm -rf {} + \
    && python -c "from litellm.homelab_fork import homelab_unlimited; assert homelab_unlimited() is True"
