"""Tests de l'interface d'administration des comptes (US6.1)."""

import json
from pathlib import Path

from flask import Flask

from ADM.accounts_json import AccountJsonSession, init_account_db
from ADM.accounts_service import create_account, verify_password
from ADM.database import Account


def _config_path(tmp_path: Path) -> Path:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "db_backend": "json",
                "json_connection_url": "applications.json",
                "display_thresholds": {
                    "score": {"warning": 30, "critical": 60},
                    "risk": {"warning": 100, "critical": 350},
                },
            }
        ),
        encoding="utf-8",
    )
    return config_path


def _seed_account(
    tmp_path: Path, *, username: str, password: str, role: str, active: bool = True
) -> Path:
    accounts_path = tmp_path / "accounts.json"
    engine = init_account_db(str(accounts_path))
    accounts_session = AccountJsonSession(engine)
    create_account(accounts_session, username=username, password=password, role=role, active=active)
    accounts_session.commit()
    accounts_session.close()
    return accounts_path


def _create_test_app(tmp_path: Path, accounts_path: Path) -> Flask:
    from ADM.app import create_app

    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
            "DB_CONNECTION": str(tmp_path / "catalogue.json"),
            "CONFIG": str(_config_path(tmp_path)),
            "ACCOUNTS_CONNECTION": str(accounts_path),
        }
    )


def _admin_session(client: object, username: str = "alice") -> None:
    with client.session_transaction() as sess:  # type: ignore[attr-defined]
        sess["logged_in"] = True
        sess["username"] = username
        sess["role"] = "admin"
        sess["csrf_token"] = "jeton-de-test"


def test_list_accounts_forbidden_for_non_admin(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="bob", password="secret-de-test", role="user")
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "bob"
        sess["role"] = "user"

    response = client.get("/accounts")

    assert response.status_code == 403


def test_list_accounts_shows_seeded_account(tmp_path: Path) -> None:
    accounts_path = _seed_account(
        tmp_path, username="alice", password="secret-de-test", role="admin"
    )
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    _admin_session(client)

    response = client.get("/accounts")

    assert response.status_code == 200
    assert "alice" in response.get_data(as_text=True)


def test_create_account_via_form(tmp_path: Path) -> None:
    accounts_path = _seed_account(
        tmp_path, username="alice", password="secret-de-test", role="admin"
    )
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    _admin_session(client)

    response = client.post(
        "/accounts",
        data={
            "csrf_token": "jeton-de-test",
            "username": "bob",
            "password": "autre-secret",
            "password_confirm": "autre-secret",
            "role": "user",
        },
    )

    assert response.status_code == 302
    saved = json.loads(accounts_path.read_text(encoding="utf-8"))
    assert any(record["username"] == "bob" and record["role"] == "user" for record in saved)


def test_create_account_rejects_mismatched_passwords(tmp_path: Path) -> None:
    accounts_path = _seed_account(
        tmp_path, username="alice", password="secret-de-test", role="admin"
    )
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    _admin_session(client)

    response = client.post(
        "/accounts",
        data={
            "csrf_token": "jeton-de-test",
            "username": "bob",
            "password": "secret-un",
            "password_confirm": "secret-deux",
            "role": "user",
        },
    )

    assert response.status_code == 302
    saved = json.loads(accounts_path.read_text(encoding="utf-8"))
    assert not any(record["username"] == "bob" for record in saved)


def test_create_account_rejects_duplicate_username(tmp_path: Path) -> None:
    accounts_path = _seed_account(
        tmp_path, username="alice", password="secret-de-test", role="admin"
    )
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    _admin_session(client)

    response = client.post(
        "/accounts",
        data={
            "csrf_token": "jeton-de-test",
            "username": "alice",
            "password": "autre-secret",
            "password_confirm": "autre-secret",
            "role": "user",
        },
    )

    assert response.status_code == 302
    saved = json.loads(accounts_path.read_text(encoding="utf-8"))
    assert len(saved) == 1


def test_change_account_role(tmp_path: Path) -> None:
    accounts_path = tmp_path / "accounts.json"
    engine = init_account_db(str(accounts_path))
    accounts_session = AccountJsonSession(engine)
    create_account(accounts_session, username="alice", password="secret-de-test", role="admin")
    create_account(accounts_session, username="bob", password="secret-de-test", role="user")
    accounts_session.commit()
    accounts_session.close()
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    _admin_session(client)

    response = client.post(
        "/accounts/bob/role",
        data={"csrf_token": "jeton-de-test", "role": "admin"},
    )

    assert response.status_code == 302
    saved = json.loads(accounts_path.read_text(encoding="utf-8"))
    bob = next(record for record in saved if record["username"] == "bob")
    assert bob["role"] == "admin"


def test_change_role_cannot_demote_last_active_admin(tmp_path: Path) -> None:
    accounts_path = _seed_account(
        tmp_path, username="alice", password="secret-de-test", role="admin"
    )
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    _admin_session(client)

    response = client.post(
        "/accounts/alice/role",
        data={"csrf_token": "jeton-de-test", "role": "user"},
    )

    assert response.status_code == 302
    saved = json.loads(accounts_path.read_text(encoding="utf-8"))
    assert saved[0]["role"] == "admin"


def test_toggle_account_active(tmp_path: Path) -> None:
    accounts_path = tmp_path / "accounts.json"
    engine = init_account_db(str(accounts_path))
    accounts_session = AccountJsonSession(engine)
    create_account(accounts_session, username="alice", password="secret-de-test", role="admin")
    create_account(accounts_session, username="bob", password="secret-de-test", role="user")
    accounts_session.commit()
    accounts_session.close()
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    _admin_session(client)

    response = client.post("/accounts/bob/active", data={"csrf_token": "jeton-de-test"})

    assert response.status_code == 302
    saved = json.loads(accounts_path.read_text(encoding="utf-8"))
    bob = next(record for record in saved if record["username"] == "bob")
    assert bob["active"] is False


def test_toggle_active_cannot_deactivate_last_active_admin(tmp_path: Path) -> None:
    accounts_path = _seed_account(
        tmp_path, username="alice", password="secret-de-test", role="admin"
    )
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    _admin_session(client)

    response = client.post("/accounts/alice/active", data={"csrf_token": "jeton-de-test"})

    assert response.status_code == 302
    saved = json.loads(accounts_path.read_text(encoding="utf-8"))
    assert saved[0]["active"] is True


def test_reset_account_password(tmp_path: Path) -> None:
    accounts_path = tmp_path / "accounts.json"
    engine = init_account_db(str(accounts_path))
    accounts_session = AccountJsonSession(engine)
    create_account(accounts_session, username="alice", password="secret-de-test", role="admin")
    create_account(accounts_session, username="bob", password="ancien-secret", role="user")
    accounts_session.commit()
    accounts_session.close()
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    _admin_session(client)

    response = client.post(
        "/accounts/bob/password",
        data={
            "csrf_token": "jeton-de-test",
            "password": "nouveau-secret",
            "password_confirm": "nouveau-secret",
        },
    )

    assert response.status_code == 302
    saved = json.loads(accounts_path.read_text(encoding="utf-8"))
    bob = next(record for record in saved if record["username"] == "bob")
    assert bob["password_hash"] != "ancien-secret"


def test_reset_account_password_rejects_mismatched_confirmation(tmp_path: Path) -> None:
    accounts_path = tmp_path / "accounts.json"
    engine = init_account_db(str(accounts_path))
    accounts_session = AccountJsonSession(engine)
    create_account(accounts_session, username="alice", password="secret-de-test", role="admin")
    create_account(accounts_session, username="bob", password="ancien-secret", role="user")
    accounts_session.commit()
    accounts_session.close()
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    _admin_session(client)

    response = client.post(
        "/accounts/bob/password",
        data={
            "csrf_token": "jeton-de-test",
            "password": "secret-un",
            "password_confirm": "secret-deux",
        },
    )

    assert response.status_code == 302
    saved = json.loads(accounts_path.read_text(encoding="utf-8"))
    bob_record = next(record for record in saved if record["username"] == "bob")
    bob_account = Account.from_dict(bob_record)
    assert verify_password(bob_account, "ancien-secret")


def test_delete_account(tmp_path: Path) -> None:
    accounts_path = tmp_path / "accounts.json"
    engine = init_account_db(str(accounts_path))
    accounts_session = AccountJsonSession(engine)
    create_account(accounts_session, username="alice", password="secret-de-test", role="admin")
    create_account(accounts_session, username="bob", password="secret-de-test", role="user")
    accounts_session.commit()
    accounts_session.close()
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    _admin_session(client)

    response = client.post("/accounts/bob/delete", data={"csrf_token": "jeton-de-test"})

    assert response.status_code == 302
    saved = json.loads(accounts_path.read_text(encoding="utf-8"))
    assert not any(record["username"] == "bob" for record in saved)


def test_delete_account_refuses_self_deletion(tmp_path: Path) -> None:
    accounts_path = _seed_account(
        tmp_path, username="alice", password="secret-de-test", role="admin"
    )
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    _admin_session(client)

    response = client.post("/accounts/alice/delete", data={"csrf_token": "jeton-de-test"})

    assert response.status_code == 302
    saved = json.loads(accounts_path.read_text(encoding="utf-8"))
    assert any(record["username"] == "alice" for record in saved)


def test_delete_account_cannot_remove_last_active_admin(tmp_path: Path) -> None:
    accounts_path = tmp_path / "accounts.json"
    engine = init_account_db(str(accounts_path))
    accounts_session = AccountJsonSession(engine)
    create_account(accounts_session, username="alice", password="secret-de-test", role="admin")
    create_account(accounts_session, username="bob", password="secret-de-test", role="admin")
    accounts_session.commit()
    accounts_session.close()
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    _admin_session(client, username="alice")

    response = client.post("/accounts/bob/delete", data={"csrf_token": "jeton-de-test"})
    assert response.status_code == 302
    saved = json.loads(accounts_path.read_text(encoding="utf-8"))
    assert not any(record["username"] == "bob" for record in saved)


def test_account_routes_require_csrf_token(tmp_path: Path) -> None:
    accounts_path = _seed_account(
        tmp_path, username="alice", password="secret-de-test", role="admin"
    )
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "alice"
        sess["role"] = "admin"

    response = client.post(
        "/accounts",
        data={"username": "bob", "password": "x", "password_confirm": "x", "role": "user"},
    )

    assert response.status_code == 400
