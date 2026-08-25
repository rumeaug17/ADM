"""Fournisseurs d'authentification, abstraits du mécanisme de vérification (US6.1)."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from ADM.accounts_service import AccountSession, verify_password
from ADM.database import Account


@dataclass(frozen=True, slots=True)
class AuthenticatedAccount:
    """Identité minimale d'un compte authentifié, portée par la session Flask."""

    username: str
    role: str


class AuthProvider(Protocol):
    """Vérifie des identifiants et retourne l'identité authentifiée, ou None."""

    def authenticate(self, username: str, password: str) -> AuthenticatedAccount | None: ...


class LocalAuthProvider:
    """Authentifie contre les comptes stockés localement (JSON ou MySQL)."""

    def __init__(self, account_session_factory: Callable[[], AccountSession]) -> None:
        self._account_session_factory = account_session_factory

    def authenticate(self, username: str, password: str) -> AuthenticatedAccount | None:
        account_session = self._account_session_factory()
        try:
            account = account_session.query(Account).filter_by(username=username).first()
            if account is None or not account.active:
                return None
            if not verify_password(account, password):
                return None
            return AuthenticatedAccount(username=account.username, role=account.role)
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