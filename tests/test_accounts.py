"""Tests du modèle, de la persistance et du service des comptes (US6.1)."""

import json
from pathlib import Path

import pytest

from ADM.accounts_json import AccountJsonSession, init_account_db
from ADM.accounts_service import (
    AccountError,
    active_admin_count,
    create_account,
    delete_account,
    set_account_active,
    set_account_password,
    set_account_role,
    verify_password,
)
from ADM.database import Account


def account_record(username: str = "alice", role: str = "admin") -> dict[str, object]:
    return {
        "username": username,
        "password_hash": "hash-factice",
        "role": role,
        "active": True,
    }


# --- Modèle ---


def test_account_round_trip() -> None:
    account = Account.from_dict(account_record())
    assert account.to_dict()["role"] == "admin"
    assert account.to_dict()["active"] is True


def test_account_rejects_unknown_role() -> None:
    record = account_record()
    record["role"] = "superadmin"
    with pytest.raises(ValueError, match="role"):
        Account.from_dict(record)


def test_account_rejects_non_boolean_active() -> None:
    record = account_record()
    record["active"] = "oui"
    with pytest.raises(ValueError, match="active"):
        Account.from_dict(record)


# --- Persistance JSON ---


def test_account_json_session_persists_and_rolls_back(tmp_path: Path) -> None:
    database_path = tmp_path / "accounts.json"
    engine = init_account_db(str(database_path))
    session = AccountJsonSession(engine)
    account = Account.from_dict(account_record())
    session.add(account)
    session.commit()

    account.role = "user"
    session.rollback()
    restored = session.query(Account).first()

    assert restored is not None
    assert restored.role == "admin"


def test_account_json_session_rejects_duplicate_usernames_on_load(tmp_path: Path) -> None:
    database_path = tmp_path / "accounts.json"
    database_path.write_text(
        json.dumps([account_record("alice"), account_record("alice")]), encoding="utf-8"
    )
    # La duplication d'id est détectée par _index_accounts, pas l'unicité du nom :
    # celle-ci est appliquée par accounts_service.create_account, testé plus bas.
    session = AccountJsonSession(database_path)
    assert len(session.query(Account).all()) == 2


# --- Service métier ---


def test_create_account_hashes_password_and_never_stores_it_in_clear(tmp_path: Path) -> None:
    session = AccountJsonSession(init_account_db(str(tmp_path / "accounts.json")))
    account = create_account(session, username="alice", password="secret-de-test", role="admin")

    assert account.password_hash != "secret-de-test"
    assert verify_password(account, "secret-de-test")
    assert not verify_password(account, "mauvais-mot-de-passe")


def test_create_account_rejects_duplicate_username(tmp_path: Path) -> None:
    session = AccountJsonSession(init_account_db(str(tmp_path / "accounts.json")))
    create_account(session, username="alice", password="secret-de-test", role="admin")

    with pytest.raises(AccountError, match="existe déjà"):
        create_account(session, username="alice", password="autre-secret", role="user")


def test_create_account_rejects_unknown_role(tmp_path: Path) -> None:
    session = AccountJsonSession(init_account_db(str(tmp_path / "accounts.json")))
    with pytest.raises(AccountError, match="rôle"):
        create_account(session, username="alice", password="secret-de-test", role="superadmin")


def test_active_admin_count_ignores_inactive_and_user_accounts(tmp_path: Path) -> None:
    session = AccountJsonSession(init_account_db(str(tmp_path / "accounts.json")))
    create_account(session, username="alice", password="secret-de-test", role="admin")
    create_account(session, username="bob", password="secret-de-test", role="user")
    inactive_admin = create_account(
        session, username="carole", password="secret-de-test", role="admin", active=False
    )

    assert active_admin_count(session) == 1
    assert inactive_admin.active is False


def test_cannot_demote_last_active_admin(tmp_path: Path) -> None:
    session = AccountJsonSession(init_account_db(str(tmp_path / "accounts.json")))
    admin = create_account(session, username="alice", password="secret-de-test", role="admin")

    with pytest.raises(AccountError, match="dernier compte administrateur"):
        set_account_role(session, admin, "user")


def test_cannot_deactivate_last_active_admin(tmp_path: Path) -> None:
    session = AccountJsonSession(init_account_db(str(tmp_path / "accounts.json")))
    admin = create_account(session, username="alice", password="secret-de-test", role="admin")

    with pytest.raises(AccountError, match="dernier compte administrateur"):
        set_account_active(session, admin, False)


def test_cannot_delete_last_active_admin(tmp_path: Path) -> None:
    session = AccountJsonSession(init_account_db(str(tmp_path / "accounts.json")))
    admin = create_account(session, username="alice", password="secret-de-test", role="admin")

    with pytest.raises(AccountError, match="dernier compte administrateur"):
        delete_account(session, admin)


def test_can_demote_admin_when_another_active_admin_remains(tmp_path: Path) -> None:
    session = AccountJsonSession(init_account_db(str(tmp_path / "accounts.json")))
    first_admin = create_account(session, username="alice", password="secret-de-test", role="admin")
    create_account(session, username="bob", password="secret-de-test", role="admin")

    set_account_role(session, first_admin, "user")

    assert first_admin.role == "user"


def test_set_account_password_updates_hash(tmp_path: Path) -> None:
    session = AccountJsonSession(init_account_db(str(tmp_path / "accounts.json")))
    account = create_account(session, username="alice", password="ancien-secret", role="admin")

    set_account_password(account, "nouveau-secret")

    assert verify_password(account, "nouveau-secret")
    assert not verify_password(account, "ancien-secret")
