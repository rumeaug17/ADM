"""Tests des fournisseurs d'authentification (US6.1, US6.3)."""

from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ADM.accounts_json import AccountJsonSession, init_account_db
from ADM.accounts_service import (
    LOGIN_LOCKOUT_THRESHOLD,
    AccountLockedError,
    create_account,
)
from ADM.auth_providers import (
    LocalAuthProvider,
    UnsupportedAuthProviderError,
    get_auth_provider,
)
from ADM.database import Account


def _account_session_factory(tmp_path: Path) -> Callable[[], AccountJsonSession]:
    engine = init_account_db(str(tmp_path / "accounts.json"))
    return lambda: AccountJsonSession(engine)


def test_local_auth_provider_authenticates_valid_credentials(tmp_path: Path) -> None:
    factory = _account_session_factory(tmp_path)
    session = factory()
    create_account(session, username="alice", password="secret-de-test", role="admin")
    session.commit()
    session.close()

    provider = LocalAuthProvider(factory)
    identity = provider.authenticate("alice", "secret-de-test")

    assert identity is not None
    assert identity.username == "alice"
    assert identity.role == "admin"


def test_local_auth_provider_rejects_wrong_password(tmp_path: Path) -> None:
    factory = _account_session_factory(tmp_path)
    session = factory()
    create_account(session, username="alice", password="secret-de-test", role="admin")
    session.commit()
    session.close()

    provider = LocalAuthProvider(factory)

    assert provider.authenticate("alice", "mauvais-mot-de-passe") is None


def test_local_auth_provider_rejects_unknown_username(tmp_path: Path) -> None:
    provider = LocalAuthProvider(_account_session_factory(tmp_path))

    assert provider.authenticate("inconnu", "peu importe") is None


def test_local_auth_provider_rejects_inactive_account(tmp_path: Path) -> None:
    factory = _account_session_factory(tmp_path)
    session = factory()
    create_account(session, username="alice", password="secret-de-test", role="admin")
    create_account(session, username="bob", password="secret-de-test", role="user", active=False)
    session.commit()
    session.close()

    provider = LocalAuthProvider(factory)

    assert provider.authenticate("bob", "secret-de-test") is None


def test_get_auth_provider_returns_local_provider(tmp_path: Path) -> None:
    provider = get_auth_provider("local", _account_session_factory(tmp_path))
    assert isinstance(provider, LocalAuthProvider)


def test_get_auth_provider_is_case_insensitive(tmp_path: Path) -> None:
    provider = get_auth_provider(" Local ", _account_session_factory(tmp_path))
    assert isinstance(provider, LocalAuthProvider)


@pytest.mark.parametrize("backend", ["ldap", "oidc"])
def test_get_auth_provider_rejects_unimplemented_backends(tmp_path: Path, backend: str) -> None:
    with pytest.raises(UnsupportedAuthProviderError, match=backend):
        get_auth_provider(backend, _account_session_factory(tmp_path))


def test_get_auth_provider_rejects_unknown_backend(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="inconnu"):
        get_auth_provider("keycloak-maison", _account_session_factory(tmp_path))


# --- US6.3 : verrouillage temporaire après échecs de connexion répétés ---


def test_local_auth_provider_locks_account_after_repeated_failures(tmp_path: Path) -> None:
    factory = _account_session_factory(tmp_path)
    session = factory()
    create_account(session, username="alice", password="secret-de-test", role="admin")
    session.commit()
    session.close()

    provider = LocalAuthProvider(factory)
    for _ in range(LOGIN_LOCKOUT_THRESHOLD):
        assert provider.authenticate("alice", "mauvais-mot-de-passe") is None

    # Même avec le bon mot de passe, le compte verrouillé refuse l'authentification.
    with pytest.raises(AccountLockedError):
        provider.authenticate("alice", "secret-de-test")


def test_local_auth_provider_unlocks_after_delay(tmp_path: Path) -> None:
    factory = _account_session_factory(tmp_path)
    session = factory()
    create_account(session, username="alice", password="secret-de-test", role="admin")
    session.commit()
    session.close()

    provider = LocalAuthProvider(factory)
    for _ in range(LOGIN_LOCKOUT_THRESHOLD):
        provider.authenticate("alice", "mauvais-mot-de-passe")

    # On simule l'écoulement du délai de verrouillage en le levant directement.
    unlock_session = factory()
    account = unlock_session.query(Account).filter_by(username="alice").first()
    assert account is not None
    account.locked_until = datetime.now() - timedelta(seconds=1)
    unlock_session.commit()
    unlock_session.close()

    identity = provider.authenticate("alice", "secret-de-test")
    assert identity is not None

    verify_session = factory()
    refreshed = verify_session.query(Account).filter_by(username="alice").first()
    assert refreshed is not None
    assert refreshed.failed_login_attempts == 0
    assert refreshed.locked_until is None


def test_local_auth_provider_resets_counter_after_successful_login(tmp_path: Path) -> None:
    factory = _account_session_factory(tmp_path)
    session = factory()
    create_account(session, username="alice", password="secret-de-test", role="admin")
    session.commit()
    session.close()

    provider = LocalAuthProvider(factory)
    provider.authenticate("alice", "mauvais-mot-de-passe")
    provider.authenticate("alice", "mauvais-mot-de-passe")
    assert provider.authenticate("alice", "secret-de-test") is not None

    verify_session = factory()
    refreshed = verify_session.query(Account).filter_by(username="alice").first()
    assert refreshed is not None
    assert refreshed.failed_login_attempts == 0
