"""Blueprints HTTP de l'application ADM."""

import base64
import csv
import io
import os
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any, cast

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy.exc import SQLAlchemyError

from ADM.catalogue_io import replace_catalogue, serialize_catalogue
from ADM.database import Application, Evaluation
from ADM.persistence import TransactionSession, transactional_session
from ADM.scoring import filter_questions_by_type
from ADM.services import (
    Questions,
    application_to_dict,
    axis_scores,
    calculate_risk,
    category_sums,
    generate_radar_chart,
    question_definition,
    update_all_metrics,
    update_app_metrics,
)
from ADM.validation import (
    InputValidationError,
    validate_application_form,
    validate_evaluation_form,
    validate_import,
    validate_login_form,
)

auth = Blueprint("auth", __name__)
applications = Blueprint("applications", __name__)
evaluations = Blueprint("evaluations", __name__)
exports = Blueprint("exports", __name__)


def session_factory() -> Callable[[], TransactionSession]:
    return cast(Callable[[], TransactionSession], current_app.extensions["adm_session_factory"])


def questions() -> Questions:
    return cast(Questions, current_app.extensions["adm_questions"])


def scoring_map() -> dict[str, int | None]:
    return cast(dict[str, int | None], current_app.extensions["adm_scoring_map"])


def categories() -> dict[str, list[str]]:
    return cast(dict[str, list[str]], current_app.extensions["adm_categories"])


def get_app_by_name(name: str, database_session: Any) -> Application | None:
    return database_session.query(Application).filter_by(name=name).first()


def calculate_axis_scores(data: list[dict[str, object]]) -> dict[str, float]:
    return axis_scores(data, questions(), categories(), scoring_map())


def calculate_category_sums(data: dict[str, object]) -> dict[str, int]:
    return category_sums(data, questions(), categories(), scoring_map())


def login_required(function: Any) -> Any:
    @wraps(function)
    def decorated(*args: object, **kwargs: object) -> Any:
        if not session.get("logged_in"):
            return redirect(url_for("auth.login"))
        return function(*args, **kwargs)

    return decorated


@auth.route("/login", methods=["GET", "POST"])
def login() -> Any:
    """Route de connexion avec authentification minimale."""
    if request.method == "POST":
        try:
            username, password = validate_login_form(request.form)
        except InputValidationError as error:
            flash(str(error), "danger")
            return render_template("login.html"), 400
        expected_username = os.environ.get("ADM_USERNAME")
        expected_password = os.environ.get("ADM_PASSWORD")
        if not expected_username or not expected_password:
            abort(503, description="Authentification non configurée")
        if username == expected_username and password == expected_password:
            session["logged_in"] = True
            flash("Connexion réussie.", "success")
            return redirect(url_for("applications.index"))
        else:
            flash("Identifiants incorrects.", "danger")
    return render_template("login.html")


@auth.route("/logout")
def logout() -> Any:
    """Déconnexion et redirection vers la page de connexion."""
    session.pop("logged_in", None)
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for("auth.login"))


@applications.route("/")
@login_required
def index():
    session_db = session_factory()()
    try:
        app_objs = session_db.query(Application).all()
        # Convertir les objets ORM en dictionnaires
        applications = [application_to_dict(app) for app in app_objs]
        # Mettre à jour les métriques pour chaque application convertie
        for app_item in applications:
            update_app_metrics(app_item)
        return render_template("index.html", applications=applications)
    finally:
        session_db.close()


@applications.route("/add", methods=["GET", "POST"])
@login_required
def add_application():
    if request.method == "POST":
        try:
            fields = validate_application_form(request.form, require_name=True)
        except InputValidationError as error:
            flash(str(error), "danger")
            return render_template("add.html"), 400
        session_db = session_factory()()
        try:
            # Création d'une nouvelle application
            new_app = Application(
                **fields,
                score=None,
                answered_questions=0,
                last_evaluation=None,
                responses={},
                comments={},
            )
            try:
                session_db.add(new_app)
                session_db.commit()
            except (SQLAlchemyError, ValueError, OSError):
                session_db.rollback()
                current_app.logger.warning("Echec d'enregistrement d'une application.")
                flash("L'application n'a pas pu être enregistrée.", "danger")
                return render_template("add.html"), 409
            return redirect(url_for("applications.index"))
        finally:
            session_db.close()
    return render_template("add.html")


@applications.route("/edit/<name>", methods=["GET", "POST"])
@login_required
def edit_application(name):
    session_db = session_factory()()
    try:
        app_to_edit = get_app_by_name(name, session_db)
        if not app_to_edit:
            abort(404, description="Application non trouvée")
        if request.method == "POST":
            try:
                fields = validate_application_form(request.form, require_name=False)
            except InputValidationError as error:
                flash(str(error), "danger")
                return render_template("edit.html", application=app_to_edit), 400
            # Mise à jour des champs modifiables
            for field, value in fields.items():
                setattr(app_to_edit, field, value)
            session_db.commit()
            return redirect(url_for("applications.index"))
        return render_template("edit.html", application=app_to_edit)
    finally:
        session_db.close()


@applications.route("/delete/<name>", methods=["POST"])
@login_required
def delete_application(name):
    session_db = session_factory()()
    try:
        app_to_delete = get_app_by_name(name, session_db)
        if not app_to_delete:
            abort(404, description="Application non trouvée")
        session_db.delete(app_to_delete)
        session_db.commit()
        return redirect(url_for("applications.index"))
    finally:
        session_db.close()


@evaluations.route("/score/<name>", methods=["GET", "POST"])
@login_required
def score_application(name):
    session_db = session_factory()()
    try:
        app_item = get_app_by_name(name, session_db)
        if not app_item:
            abort(404, description="Application non trouvée")

        if request.method == "POST":
            question_keys = frozenset(
                key
                for questions_by_category in questions().values()
                for key in questions_by_category
                if not key.startswith("_")
            )
            try:
                validate_evaluation_form(request.form, question_keys, frozenset(scoring_map()))
            except InputValidationError as error:
                flash(str(error), "danger")
                return render_template(
                    "score.html", application=app_item, questions=questions()
                ), 400
            # Mode brouillon : on ne vérifie pas que tous les commentaires sont remplis
            if "save_draft" in request.form:
                draft_responses = {}
                draft_comments = {}
                for key, value in request.form.items():
                    if key.endswith("_comment"):
                        draft_comments[key] = value
                    elif value in scoring_map():
                        draft_responses[key] = value
                # Enregistrer le brouillon sans validation stricte des commentaires.
                app_item.responses = draft_responses
                app_item.comments = draft_comments
                # On peut enregistrer aussi le nom de l'évaluateur (facultatif)
                app_item.evaluator_name = request.form.get("evaluator_name", "")
                # Si vous souhaitez enregistrer un brouillon, vous ne mettez pas à jour le score final.
                session_db.commit()
                flash("Brouillon enregistré.", "success")
                return redirect(url_for("applications.index"))
            else:
                # Mode évaluation finale : on vérifie que tous les commentaires sont renseignés
                for key, value in request.form.items():
                    if key.endswith("_comment") and not value.strip():
                        flash(
                            "Tous les commentaires sont obligatoires pour l'évaluation.", "danger"
                        )
                        return render_template(
                            "score.html", application=app_item, questions=questions()
                        )

                evaluation_responses = {}
                evaluation_comments = {}
                score = 0
                answered_questions = 0
                for key, value in request.form.items():
                    if key.endswith("_comment"):
                        evaluation_comments[key] = value
                    elif value in scoring_map():
                        evaluation_responses[key] = value
                        if scoring_map()[value] is not None:
                            # Récupérer la définition de la question pour déterminer le poids (par défaut 1)
                            q_def = question_definition(key, questions())
                            weight = q_def.get("weight", 1)
                            score += scoring_map()[value] * weight
                            answered_questions += weight

                new_eval = Evaluation(
                    score=score,
                    answered_questions=answered_questions,
                    last_evaluation=datetime.now(),
                    evaluator_name=request.form.get("evaluator_name", ""),
                    responses=evaluation_responses,
                    comments=evaluation_comments,
                )
                # Ajoute la nouvelle évaluation à l'historique de l'application
                app_item.evaluations.append(new_eval)
                # Met à jour l'application avec la nouvelle évaluation
                app_item.evaluator_name = new_eval.evaluator_name
                app_item.score = score
                app_item.answered_questions = answered_questions
                app_item.last_evaluation = new_eval.last_evaluation
                app_item.responses = evaluation_responses
                app_item.comments = evaluation_comments
                session_db.commit()
                flash("Évaluation enregistrée.", "success")
                return redirect(url_for("applications.index"))

        # return render_template("score.html", application=app_item, questions=questions())
        # Filtrer les questions à afficher en fonction du type d'application
        filtered_questions = filter_questions_by_type(
            questions(), app_item.type_app, app_item.hosting
        )
        return render_template("score.html", application=app_item, questions=filtered_questions)

    finally:
        session_db.close()


@evaluations.route("/reset/<name>", methods=["POST"])
@login_required
def reset_evaluation(name):
    session_db = session_factory()()
    try:
        app_to_reset = get_app_by_name(name, session_db)
        if not app_to_reset:
            abort(404, description="Application non trouvée")
        # Réinitialiser les évaluations de l'application
        app_to_reset.score = None
        app_to_reset.answered_questions = 0
        app_to_reset.last_evaluation = None
        app_to_reset.evaluator_name = None
        session_db.commit()
        flash(f"L'évaluation de l'application '{name}' a été réinitialisée.", "success")
        return redirect(url_for("applications.index"))
    finally:
        session_db.close()


@evaluations.route("/reevaluate_all", methods=["POST"])
@login_required
def reevaluate_all():
    session_db = session_factory()()
    try:
        applications = session_db.query(Application).all()
        for app_item in applications:
            app_item.score = None
            app_item.answered_questions = 0
            app_item.last_evaluation = None
            app_item.evaluator_name = None
        session_db.commit()
        flash("Toutes les évaluations ont été réinitialisées.", "success")
        return redirect(url_for("applications.index"))
    finally:
        session_db.close()


# --- Nouvelle route : Radar Chart ---
@evaluations.route("/radar/<name>")
@login_required
def radar_chart(name):
    session_db = session_factory()()
    try:
        app_obj = get_app_by_name(name, session_db)
        if not app_obj:
            abort(404, description="Application non trouvée")
        # Pour générer le graphique radar, on utilise les réponses stockées.
        # On suppose que la fonction calculate_axis_scores attend un dictionnaire avec la clé "responses".
        avg_axis_scores = calculate_axis_scores([{"responses": app_obj.responses}])
        chart_data = generate_radar_chart(avg_axis_scores)
        return Response(base64.b64decode(chart_data), mimetype="image/png")
    finally:
        session_db.close()


# --- Nouvelle route : Synthèse ---
@evaluations.route("/synthese")
@login_required
def synthese():
    session_db = session_factory()()
    try:
        filter_score = request.args.get("filter_score", "above_30")
        db_apps = session_db.query(Application).all()
        # Conversion des objets ORM en dictionnaires
        data = [application_to_dict(app) for app in db_apps]

        # Mise à jour des métriques pour chaque application
        for app_item in data:
            update_app_metrics(app_item)
        evaluated_risks = [
            app_item.get("risque") for app_item in data if app_item.get("risque") is not None
        ]
        global_risk = (
            round(sum(evaluated_risks) / len(evaluated_risks), 2) if evaluated_risks else None
        )
        total_apps = len(data)

        if filter_score == "above_30":
            scored_apps = [app for app in data if app.get("percentage") and app["percentage"] > 30]
        elif filter_score == "above_60":
            scored_apps = [app for app in data if app.get("percentage") and app["percentage"] > 60]
        else:
            scored_apps = data.copy()

        avg_score = (
            round(sum(app["score"] for app in data if app.get("score") is not None) / len(data), 2)
            if data
            else 0
        )
        apps_above_30 = len(
            [app for app in data if app.get("percentage") and app["percentage"] > 30]
        )
        apps_above_60 = len(
            [app for app in data if app.get("percentage") and app["percentage"] > 60]
        )
        avg_axis_scores = calculate_axis_scores(data)
        chart_data = generate_radar_chart(avg_axis_scores)
        scored_apps.sort(key=lambda app: app.get("score") or 0, reverse=True)

        # Calcul des pires scores (ou meilleurs, selon la logique)
        best_by_category = {}
        for category in categories():
            best_app = None
            best_score = -1
            for app_item in data:
                cat_score = calculate_category_sums(app_item).get(category, 0)
                if cat_score > best_score:
                    best_score = cat_score
                    best_app = app_item.get("name")
            best_by_category[category] = (best_app, best_score)
        best_grouped = {}
        for category, (app_name, score_val) in best_by_category.items():
            if app_name:
                best_grouped.setdefault(app_name, []).append((category, score_val))

        return render_template(
            "synthese.html",
            applications=scored_apps,
            total_apps=total_apps,
            avg_score=avg_score,
            apps_above_30=apps_above_30,
            apps_above_60=apps_above_60,
            filter_score=filter_score,
            avg_axis_scores=avg_axis_scores,
            chart_data=chart_data,
            global_risk=global_risk,
            best_grouped=best_grouped,
        )
    finally:
        session_db.close()


# --- Nouvelle route : Export CSV ---
@exports.route("/export_csv")
@login_required
def export_csv():
    session_db = session_factory()()
    try:
        db_apps = session_db.query(Application).all()
        applications = [application_to_dict(app) for app in db_apps]
        update_all_metrics(applications)
        for app_item in applications:
            app_item["risque"] = calculate_risk(app_item)
        si = io.StringIO()
        writer = csv.writer(si, delimiter=";")
        header = [
            "Nom",
            "Type",
            "RDA",
            "Criticité",
            "Disponibilité",
            "Intégrité",
            "Confidentialité",
            "Pérennité",
            "Score",
            "Max Score",
            "Pourcentage",
            "Dernière évaluation",
            "Évaluateur",
            "Risque",
        ]
        writer.writerow(header)
        for app_item in applications:
            row = [
                app_item.get("name", ""),
                f"{app_item.get('type_app', '')} / {app_item.get('hosting', '')}",
                app_item.get("rda", ""),
                app_item.get("criticite", ""),
                app_item.get("disponibilite", ""),
                app_item.get("integrite", ""),
                app_item.get("confidentialite", ""),
                app_item.get("perennite", ""),
                app_item.get("score", ""),
                app_item.get("max_score", ""),
                app_item.get("percentage", ""),
                app_item.get("last_evaluation", ""),
                app_item.get("evaluator_name", ""),
                "" if app_item.get("risque") is None else round(app_item.get("risque")),
            ]
            writer.writerow(row)
        output = si.getvalue()
        si.close()
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=applications_export.csv"},
        )
    finally:
        session_db.close()


@evaluations.route("/resume/<name>")
@login_required
def resume(name):
    session_db = session_factory()()
    try:
        app_obj = get_app_by_name(name, session_db)
        if not app_obj:
            abort(404, description="Application non trouvée")

        # Convertir l'objet Application en dictionnaire pour faciliter le calcul des métriques
        app_item = application_to_dict(app_obj)

        # Tri des évaluations par date de création (si created_at est nul, on utilise datetime.min)
        evaluations_sorted = sorted(
            app_obj.evaluations,
            key=lambda ev: ev.created_at if ev.created_at is not None else datetime.min,
        )

        # Si au moins une évaluation existe, on utilise la plus récente
        if evaluations_sorted:
            last_eval_obj = evaluations_sorted[-1]
            last_eval = {
                "score": last_eval_obj.score,
                "answered_questions": last_eval_obj.answered_questions,
                "last_evaluation": last_eval_obj.last_evaluation.isoformat()
                if last_eval_obj.last_evaluation
                else None,
                "evaluator_name": last_eval_obj.evaluator_name,
                "responses": last_eval_obj.responses,
                "comments": last_eval_obj.comments,
            }
            # Mettez à jour les données affichées avec la dernière évaluation
            app_item.update(last_eval)
        update_app_metrics(app_item)

        current_responses = app_item.get("responses", {}) if evaluations_sorted else {}
        current_category_sums = calculate_category_sums({"responses": current_responses})

        # Si au moins deux évaluations existent, on récupère l'évaluation précédente
        if len(evaluations_sorted) > 1:
            previous_eval_obj = evaluations_sorted[-2]
            previous_eval = {
                "score": previous_eval_obj.score,
                "answered_questions": previous_eval_obj.answered_questions,
                "last_evaluation": previous_eval_obj.last_evaluation.isoformat()
                if previous_eval_obj.last_evaluation
                else None,
                "evaluator_name": previous_eval_obj.evaluator_name,
                "responses": previous_eval_obj.responses,
                "comments": previous_eval_obj.comments,
            }
            previous_category_sums = calculate_category_sums(
                {"responses": previous_eval.get("responses", {})}
            )
        else:
            previous_eval = {}
            previous_category_sums = {}

        current_axis_scores = calculate_axis_scores([{"responses": app_item.get("responses", {})}])
        radar_chart_data = generate_radar_chart(current_axis_scores)

        return render_template(
            "resume.html",
            app=app_item,
            radar_chart=radar_chart_data,
            category_sums=current_category_sums,
            previous_category_sums=previous_category_sums,
            questions=questions(),
            current_eval=last_eval if evaluations_sorted else {},
            previous_eval=previous_eval,
        )
    finally:
        session_db.close()


@exports.route("/export_all")
@login_required
def export_all():
    session_db = session_factory()()
    try:
        # Récupérer toutes les applications via la session (quelle que soit leur origine)
        db_apps = session_db.query(Application).all()
        # Convertir les objets en dictionnaire (incluant l'historique des évaluations)
        # Exporter au format JSON avec une mise en forme lisible
        json_data = serialize_catalogue(db_apps)
        # Retourne une réponse avec les en-têtes appropriés pour télécharger un fichier
        return Response(
            json_data,
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=export_all.json"},
        )
    finally:
        session_db.close()


@exports.route("/import_data", methods=["GET", "POST"])
@login_required
def import_data():
    if request.method == "POST":
        # Vérifier que le fichier a bien été transmis
        if "file" not in request.files:
            flash("Aucun fichier n'a été sélectionné.", "danger")
            return redirect(url_for("exports.import_data"))
        file = request.files["file"]
        if file.filename == "":
            flash("Aucun fichier n'a été sélectionné.", "danger")
            return redirect(url_for("exports.import_data"))
        try:
            applications = validate_import(file)
        except InputValidationError as error:
            flash(str(error), "danger")
            return redirect(url_for("exports.import_data"))

        try:
            # Suppression et ajout appartiennent à une transaction unique : un échec
            # conserve donc le catalogue dans son état antérieur.
            with transactional_session(session_factory()) as session_db:
                replace_catalogue(session_db, applications)
            flash("Les données ont été réimportées avec succès.", "success")
        except (SQLAlchemyError, ValueError, OSError):
            current_app.logger.warning("Echec de persistance d'un import JSON.")
            flash("Les données importées n'ont pas pu être enregistrées.", "danger")
        return redirect(url_for("applications.index"))
    # En GET, on affiche le formulaire de sélection de fichier avec modale.
    return render_template("import_data.html")
