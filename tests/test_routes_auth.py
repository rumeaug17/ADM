"""Tests de la route de connexion et de l'autorisation par rôle (US6.1)."""

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
    account_session = AccountJsonSession(engine)
    create_account(account_session, username=username, password=password, role=role, active=active)
    account_session.commit()
    account_session.close()
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


def _extract_csrf_token(html: str) -> str:
    marker = 'name="csrf_token" value="'
    start = html.index(marker) + len(marker)
    end = html.index('"', start)
    return html[start:end]


def test_login_succeeds_with_valid_local_account(tmp_path: Path) -> None:
    accounts_path = _seed_account(
        tmp_path, username="alice", password="secret-de-test", role="admin"
    )
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    csrf_token = _extract_csrf_token(client.get("/login").get_data(as_text=True))

    response = client.post(
        "/login",
        data={"csrf_token": csrf_token, "username": "alice", "password": "secret-de-test"},
    )

    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert sess["logged_in"] is True
        assert sess["username"] == "alice"
        assert sess["role"] == "admin"


def test_login_rejects_wrong_password(tmp_path: Path) -> None:
    accounts_path = _seed_account(
        tmp_path, username="alice", password="secret-de-test", role="admin"
    )
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    csrf_token = _extract_csrf_token(client.get("/login").get_data(as_text=True))

    response = client.post(
        "/login",
        data={"csrf_token": csrf_token, "username": "alice", "password": "mauvais-mot-de-passe"},
    )

    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert "logged_in" not in sess


def test_login_rejects_inactive_account(tmp_path: Path) -> None:
    accounts_path = tmp_path / "accounts.json"
    engine = init_account_db(str(accounts_path))
    account_session = AccountJsonSession(engine)
    create_account(account_session, username="alice", password="secret-de-test", role="admin")
    create_account(
        account_session, username="bob", password="secret-de-test", role="user", active=False
    )
    account_session.commit()
    account_session.close()
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    csrf_token = _extract_csrf_token(client.get("/login").get_data(as_text=True))

    response = client.post(
        "/login",
        data={"csrf_token": csrf_token, "username": "bob", "password": "secret-de-test"},
    )

    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert "logged_in" not in sess


def test_login_rejects_unknown_username(tmp_path: Path) -> None:
    accounts_path = _seed_account(
        tmp_path, username="alice", password="secret-de-test", role="admin"
    )
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    csrf_token = _extract_csrf_token(client.get("/login").get_data(as_text=True))

    response = client.post(
        "/login",
        data={"csrf_token": csrf_token, "username": "inconnu", "password": "peu importe"},
    )

    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert "logged_in" not in sess


def test_logout_clears_identity(tmp_path: Path) -> None:
    accounts_path = _seed_account(
        tmp_path, username="alice", password="secret-de-test", role="admin"
    )
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "alice"
        sess["role"] = "admin"

    client.get("/logout")

    with client.session_transaction() as sess:
        assert "logged_in" not in sess
        assert "username" not in sess
        assert "role" not in sess


def test_settings_forbidden_for_non_admin_role(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="bob", password="secret-de-test", role="user")
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "bob"
        sess["role"] = "user"

    response = client.get("/settings")

    assert response.status_code == 403


def test_settings_allowed_for_admin_role(tmp_path: Path) -> None:
    accounts_path = _seed_account(
        tmp_path, username="alice", password="secret-de-test", role="admin"
    )
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "alice"
        sess["role"] = "admin"

    response = client.get("/settings")

    assert response.status_code == 200


def test_deactivated_account_loses_access_immediately(tmp_path: Path) -> None:
    """Une session signée pour un compte désactivé après coup ne doit plus donner
    accès aux pages protégées, même si le cookie affirme toujours 'logged_in'."""
    accounts_path = tmp_path / "accounts.json"
    engine = init_account_db(str(accounts_path))
    account_session = AccountJsonSession(engine)
    create_account(account_session, username="alice", password="secret-de-test", role="admin")
    create_account(account_session, username="bob", password="secret-de-test", role="user")
    account_session.commit()
    account_session.close()
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "bob"
        sess["role"] = "user"

    # Un autre administrateur désactive le compte pendant que la session est active.
    account_session = AccountJsonSession(init_account_db(str(accounts_path)))
    bob = account_session.query(Account).filter_by(username="bob").first()
    assert bob is not None
    bob.active = False
    account_session.commit()
    account_session.close()

    response = client.get("/")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    with client.session_transaction() as sess:
        assert "logged_in" not in sess


def test_change_own_password_succeeds_with_correct_current_password(tmp_path: Path) -> None:
    accounts_path = _seed_account(
        tmp_path, username="alice", password="ancien-secret", role="admin"
    )
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "alice"
        sess["role"] = "admin"
    csrf_token = _extract_csrf_token(client.get("/account/password").get_data(as_text=True))

    response = client.post(
        "/account/password",
        data={
            "csrf_token": csrf_token,
            "current_password": "ancien-secret",
            "new_password": "nouveau-secret",
            "new_password_confirm": "nouveau-secret",
        },
    )

    assert response.status_code == 302
    account_session = AccountJsonSession(init_account_db(str(accounts_path)))
    alice = account_session.query(Account).filter_by(username="alice").first()
    assert alice is not None
    assert verify_password(alice, "nouveau-secret")
    assert not verify_password(alice, "ancien-secret")


def test_change_own_password_rejects_wrong_current_password(tmp_path: Path) -> None:
    accounts_path = _seed_account(
        tmp_path, username="alice", password="ancien-secret", role="admin"
    )
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "alice"
        sess["role"] = "admin"
    csrf_token = _extract_csrf_token(client.get("/account/password").get_data(as_text=True))

    response = client.post(
        "/account/password",
        data={
            "csrf_token": csrf_token,
            "current_password": "mauvais-mot-de-passe",
            "new_password": "nouveau-secret",
            "new_password_confirm": "nouveau-secret",
        },
    )

    assert response.status_code == 400
    account_session = AccountJsonSession(init_account_db(str(accounts_path)))
    alice = account_session.query(Account).filter_by(username="alice").first()
    assert alice is not None
    assert verify_password(alice, "ancien-secret")


def test_demoted_admin_loses_admin_access_immediately(tmp_path: Path) -> None:
    """Une rétrogradation vers 'user' effectuée par un autre administrateur doit
    s'appliquer dès la requête suivante, sans que l'ancien rôle mis en cache dans la
    session persiste jusqu'à sa restauration explicite."""
    accounts_path = tmp_path / "accounts.json"
    engine = init_account_db(str(accounts_path))
    account_session = AccountJsonSession(engine)
    create_account(account_session, username="alice", password="secret-de-test", role="admin")
    create_account(account_session, username="bob", password="secret-de-test", role="admin")
    account_session.commit()
    account_session.close()
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "bob"
        sess["role"] = "admin"

    account_session = AccountJsonSession(init_account_db(str(accounts_path)))
    bob = account_session.query(Account).filter_by(username="bob").first()
    assert bob is not None
    bob.role = "user"
    account_session.commit()
    account_session.close()

    response = client.get("/settings")

    assert response.status_code == 403
    with client.session_transaction() as sess:
        assert sess["role"] == "user"
