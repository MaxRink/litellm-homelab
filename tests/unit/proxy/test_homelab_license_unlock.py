"""The homelab licence switch must lift every upstream enterprise limit.

These tests pin the behaviour that matters for the self-hosted deployment:
premium features are on by default, the community SSO/seat caps are gone, and
``LITELLM_HOMELAB_UNLIMITED=false`` gives back exact upstream enforcement.
"""

import pytest

from litellm.homelab_fork import HOMELAB_UNLIMITED_ENV, homelab_unlimited
from litellm.proxy.auth.litellm_license import LICENSE_ALL_FEATURES, LicenseCheck, _homelab_license_data


@pytest.fixture(autouse=True)
def clean_license_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Run each case from the fork's own default, not the suite-wide opt-out."""
    monkeypatch.delenv("LITELLM_LICENSE", raising=False)
    monkeypatch.delenv(HOMELAB_UNLIMITED_ENV, raising=False)
    return monkeypatch


def test_unlimited_is_the_default(clean_license_env: pytest.MonkeyPatch) -> None:
    assert homelab_unlimited() is True


@pytest.mark.parametrize("value", ["0", "false", "FALSE", "no", "off", " false "])
def test_falsy_values_restore_upstream_enforcement(clean_license_env: pytest.MonkeyPatch, value: str) -> None:
    clean_license_env.setenv(HOMELAB_UNLIMITED_ENV, value)
    assert homelab_unlimited() is False


@pytest.mark.parametrize("value", ["1", "true", "yes", "on", ""])
def test_enabled_values_keep_unlimited_mode(clean_license_env: pytest.MonkeyPatch, value: str) -> None:
    clean_license_env.setenv(HOMELAB_UNLIMITED_ENV, value)
    assert homelab_unlimited() is True


def test_homelab_license_data_is_unlimited_and_grants_every_feature() -> None:
    data = _homelab_license_data()
    assert data["allowed_features"] == [LICENSE_ALL_FEATURES]
    assert "max_users" not in data
    assert "max_teams" not in data


def test_premium_is_on_without_a_configured_license(clean_license_env: pytest.MonkeyPatch) -> None:
    license_check = LicenseCheck()

    assert license_check.is_premium() is True
    assert license_check.airgapped_license_data == _homelab_license_data()


def test_seat_and_team_limits_are_lifted(clean_license_env: pytest.MonkeyPatch) -> None:
    license_check = LicenseCheck()
    license_check.is_premium()

    assert license_check.user_seat_limit() is None
    assert license_check.is_over_limit(10_000) is False
    assert license_check.is_team_count_over_limit(10_000) is False


def test_every_gated_feature_is_granted(clean_license_env: pytest.MonkeyPatch) -> None:
    license_check = LicenseCheck()
    license_check.is_premium()

    assert license_check.grants_feature("auto_router") is True
    assert license_check.grants_feature("some_future_feature") is True
    # None means "no per-capability cap" for the auto-router classifier.
    assert license_check.auto_router_capability_limit() is None


def test_opt_out_keeps_upstream_community_behaviour(clean_license_env: pytest.MonkeyPatch) -> None:
    clean_license_env.setenv(HOMELAB_UNLIMITED_ENV, "false")
    license_check = LicenseCheck()

    assert license_check.airgapped_license_data is None
    assert license_check.is_premium() is False
    assert license_check.user_seat_limit() is None
    assert license_check.grants_feature("auto_router") is False
    assert license_check.auto_router_capability_limit() == 1
