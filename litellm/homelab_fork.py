"""Switches for this self-hosted homelab fork.

The deployment runs without a BerriAI enterprise contract, so the fork treats
the proxy as fully licensed by default: premium features are enabled, seat and
team caps are lifted, and the community SSO limit does not apply.

Set ``LITELLM_HOMELAB_UNLIMITED=false`` to restore upstream licence
enforcement (community limits when no ``LITELLM_LICENSE`` is configured).
"""

import os
from typing import Final

HOMELAB_UNLIMITED_ENV: Final = "LITELLM_HOMELAB_UNLIMITED"

_FALSY_VALUES: Final = frozenset({"0", "false", "no", "off"})


def homelab_unlimited() -> bool:
    """Return whether this fork should run as an unlimited licensed proxy."""
    return os.getenv(HOMELAB_UNLIMITED_ENV, "true").strip().lower() not in _FALSY_VALUES
