"""Fournisseurs d'authentification, abstraits du mécanisme de vérification (US6.1)."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from ADM.accounts_service import (
    AccountLockedError,
    AccountSession,
    account_is_locked,
    register_failed_login,
    register_successful_login,
    verify_password,
)
from ADM.database import Account


@dataclass(frozen=True, slots=True)
class AuthenticatedAccount:
    """Identité minimale d'un compte authentifié, portée par la session Flask."""

    username: str
    role: str
    auth_generation: int


class AuthProvider(Protocol):
    """Vérifie des identifiants et retourne l'identité authentifiée, ou None.

    ``LocalAuthProvider`` peut également lever ``AccountLockedError`` (US6.3)
    lorsque le compte est temporairement verrouillé après trop d'échecs.
    """

    def authenticate(self, username: str, password: str) -> AuthenticatedAccount | None: ...


class LocalAuthProvider:
    """Authentifie contre les comptes stockés localement (JSON ou MySQL)."""

    def __init__(self, account_session_factory: Callable[[], AccountSession]) -> None:
        self._account_session_factory = account_session_factory

    def authenticate(self, username: str, password: str) -> AuthenticatedAccount | None:
        """Vérifie les identifiants fournis (US6.3 : protection contre le brute-force).

        Un compte inconnu, inactif ou dont le mot de passe est incorrect renvoie
        ``None``, sans distinction (pour ne pas révéler l'existence d'un compte).
        Un compte temporairement verrouillé après trop d'échecs lève
        ``AccountLockedError`` plutôt que de tenter la vérification du mot de passe.
        """
        account_session = self._account_session_factory()
        try:
            account = account_session.query(Account).filter_by(username=username).first()
            if account is None or not account.active:
                return None
            if account_is_locked(account):
                assert account.locked_until is not None  # garanti par account_is_locked
                remaining = (account.locked_until - datetime.now()).total_seconds()
                raise AccountLockedError(max(1, int(remaining) + 1))
            if not verify_password(account, password):
                register_failed_login(account)
                account_session.commit()
                return None
            register_successful_login(account)
            account_session.commit()
            return AuthenticatedAccount(
                username=account.username,
                role=account.role,
                auth_generation=account.auth_generation,
            )
        finally:
            account_session.close()


class UnsupportedAuthProviderError(ValueError):
    """Signale un fournisseur d'authentification reconnu mais non implémenté."""


def get_auth_provider(
    backend: str, account_session_factory: Callable[[], AccountSession]
) -> AuthProvider:
    """Sélectionne le fournisseur d'authentification selon la configuration.

    ``ldap``/``oidc`` sont des valeurs reconnues, réservées à une évolution
    future : elles échouent explicitement plutôt que de retomber silencieusement
    sur l'authentification locale.
    """
    normalized = backend.strip().casefold()
    if normalized == "local":
        return LocalAuthProvider(account_session_factory)
    if normalized in {"ldap", "oidc"}:
        raise UnsupportedAuthProviderError(
            f"Le fournisseur d'authentification {backend!r} n'est pas encore implémenté."
        )
    raise ValueError(f"Fournisseur d'authentification inconnu : {backend!r}.")
