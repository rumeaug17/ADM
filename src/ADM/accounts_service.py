"""Opérations métier sur les comptes, indépendantes de Flask (US6.1)."""

from datetime import datetime, timedelta
from typing import Final, Protocol

from werkzeug.security import check_password_hash, generate_password_hash

from ADM.database import Account

ROLES: frozenset[str] = frozenset({"admin", "user"})

# --- Verrouillage temporaire après échecs de connexion répétés (US6.3) ---

LOGIN_LOCKOUT_THRESHOLD: Final[int] = 5
"""Nombre d'échecs de connexion consécutifs déclenchant un premier verrouillage."""

LOGIN_LOCKOUT_BASE_SECONDS: Final[int] = 30
"""Durée du premier verrouillage ; elle double à chaque échec supplémentaire."""

LOGIN_LOCKOUT_MAX_SECONDS: Final[int] = 900
"""Durée maximale d'un verrouillage (15 minutes), quel que soit le nombre d'échecs."""

_LOGIN_LOCKOUT_MAX_EXPONENT: Final[int] = 10
"""Borne l'exposant du calcul de délai, pour ne jamais manipuler d'entiers énormes."""


class AccountQueryLike(Protocol):
    """Requête minimale nécessaire à la gestion des comptes."""

    def all(self) -> list[Account]: ...
    def filter_by(self, **criteria: object) -> "AccountQueryLike": ...
    def first(self) -> Account | None: ...


class AccountSession(Protocol):
    """Session minimale partagée par les backends SQL et JSON pour les comptes."""

    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def close(self) -> None: ...
    def query(self, model: type[Account]) -> AccountQueryLike: ...
    def add(self, item: Account) -> None: ...
    def delete(self, item: Account) -> None: ...


class AccountError(ValueError):
    """Signale une opération de compte invalide, affichable sans donnée sensible."""


class AccountLockedError(AccountError):
    """Signale un compte temporairement verrouillé après trop d'échecs de connexion."""

    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        minutes = max(1, (retry_after_seconds + 59) // 60)
        super().__init__(
            "Compte temporairement verrouillé après plusieurs échecs de connexion. "
            f"Réessayez dans {minutes} minute(s)."
        )


def hash_password(password: str) -> str:
    """Calcule le hash stocké d'un mot de passe (jamais le mot de passe en clair)."""
    return str(generate_password_hash(password))


def verify_password(account: Account, password: str) -> bool:
    """Vérifie un mot de passe contre le hash stocké, sans le journaliser."""
    return bool(check_password_hash(account.password_hash, password))


def account_is_locked(account: Account, *, now: datetime | None = None) -> bool:
    """Indique si le compte est actuellement sous verrouillage temporaire (US6.3)."""
    reference = now or datetime.now()
    return account.locked_until is not None and reference < account.locked_until


def register_failed_login(account: Account, *, now: datetime | None = None) -> None:
    """Incrémente le compteur d'échecs et verrouille temporairement au-delà du seuil.

    Une fois ``LOGIN_LOCKOUT_THRESHOLD`` échecs atteints, le délai de verrouillage
    double à chaque échec supplémentaire (30 s, 60 s, 120 s, ...), jusqu'à
    ``LOGIN_LOCKOUT_MAX_SECONDS``.
    """
    reference = now or datetime.now()
    account.failed_login_attempts += 1
    if account.failed_login_attempts >= LOGIN_LOCKOUT_THRESHOLD:
        exponent = min(
            account.failed_login_attempts - LOGIN_LOCKOUT_THRESHOLD, _LOGIN_LOCKOUT_MAX_EXPONENT
        )
        duration_seconds = min(
            LOGIN_LOCKOUT_BASE_SECONDS * (2**exponent), LOGIN_LOCKOUT_MAX_SECONDS
        )
        account.locked_until = reference + timedelta(seconds=duration_seconds)


def register_successful_login(account: Account) -> None:
    """Réinitialise le compteur d'échecs et lève tout verrouillage en cours (US6.3)."""
    account.failed_login_attempts = 0
    account.locked_until = None


def active_admin_count(session: AccountSession) -> int:
    """Compte les comptes admin actifs : invariant central de l'habilitation."""
    return sum(
        1 for account in session.query(Account).all() if account.role == "admin" and account.active
    )


def create_account(
    session: AccountSession, *, username: str, password: str, role: str, active: bool = True
) -> Account:
    """Crée un compte après validation du rôle et de l'unicité du nom."""
    if role not in ROLES:
        raise AccountError(f"Le rôle doit être l'un de {sorted(ROLES)}.")
    if session.query(Account).filter_by(username=username).first() is not None:
        raise AccountError(f"Le compte {username!r} existe déjà.")
    account = Account(
        username=username,
        password_hash=hash_password(password),
        role=role,
        active=active,
        auth_generation=0,
        failed_login_attempts=0,
        locked_until=None,
    )
    session.add(account)
    return account


def set_account_role(session: AccountSession, account: Account, role: str) -> None:
    """Change le rôle d'un compte, en préservant l'invariant du dernier admin actif."""
    if role not in ROLES:
        raise AccountError(f"Le rôle doit être l'un de {sorted(ROLES)}.")
    if (
        account.role == "admin"
        and account.active
        and role != "admin"
        and active_admin_count(session) <= 1
    ):
        raise AccountError("Impossible de rétrograder le dernier compte administrateur actif.")
    account.role = role


def set_account_active(session: AccountSession, account: Account, active: bool) -> None:
    """Active ou désactive un compte, en préservant l'invariant du dernier admin actif."""
    is_last_active_admin = (
        account.role == "admin" and account.active and active_admin_count(session) <= 1
    )
    if is_last_active_admin and not active:
        raise AccountError("Impossible de désactiver le dernier compte administrateur actif.")
    account.active = active


def delete_account(session: AccountSession, account: Account) -> None:
    """Supprime un compte, en préservant l'invariant du dernier admin actif."""
    if account.role == "admin" and account.active and active_admin_count(session) <= 1:
        raise AccountError("Impossible de supprimer le dernier compte administrateur actif.")
    session.delete(account)


def set_account_password(account: Account, password: str) -> None:
    """Change le mot de passe et révoque les sessions authentifiées existantes."""
    account.password_hash = hash_password(password)
    account.auth_generation += 1
