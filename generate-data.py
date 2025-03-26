#!/usr/bin/env python3
import json
import random

# Liste des clés pour les réponses (et les commentaires associés)
response_keys = [
    "doc", "team", "roadmap", "tech_obsolete", "mco", "support",
    "etat_art", "respect", "code_source", "tests", "securite",
    "vulnerabilites", "surveillance", "incidents", "performances",
    "scalable", "besoins_metier", "recouvrement", "evolutivite",
    "fonctions", "couplage", "decommissionnement"
]

# Options possibles pour les réponses
response_options = [
    "Oui total", "Non", "Partiel", "Partiellement", "Insuffisant",
    "Majoritairement", "Non applicable", "Totalement", "Non total"
]

# Pour les commentaires, nous allons générer un texte simple indiquant le sujet
def generate_comment(key, app_name):
    return f"Commentaire pour {key} de l'application {app_name}"

# Définition des données de base pour chaque application selon l'exemple fourni
data_samples = [
    {
        "name": "NEC",
        "type": "Interne",
        "rda": "Toto",
        "disponibilite": "D1",
        "integrite": "I2",
        "confidentialite": "C3",
        "perennite": "P1",
        "score": 7,
        "answered_questions": 21,
        "last_evaluation": "2025-03-13 10:38:28",
        "criticite": "2",
        "evaluator_name": "Laurent Labit"
    },
    {
        "name": "PICRIS",
        "type": "Editeur onPrem",
        "rda": "Bernard Campan",
        "disponibilite": "D2",
        "integrite": "I3",
        "confidentialite": "C3",
        "perennite": "P3",
        "score": 25,
        "answered_questions": 20,
        "last_evaluation": "2025-03-12 14:21:12",
        "criticite": "1",
        "evaluator_name": "Bernard Campan"
    },
    {
        "name": "DICP App Manager",
        "type": "Interne cloud",
        "rda": "Moi",
        "disponibilite": "D1",
        "integrite": "I1",
        "confidentialite": "C1",
        "perennite": "P1",
        "score": 1,
        "answered_questions": 21,
        "last_evaluation": "2025-03-12 15:08:59",
        "criticite": "4",
        "evaluator_name": "Toi"
    },
    {
        "name": "Confluence",
        "type": "SaaS",
        "rda": "Eric Cantona",
        "disponibilite": "D1",
        "integrite": "I1",
        "confidentialite": "C2",
        "perennite": "P2",
        "score": 0,
        "answered_questions": 18,
        "last_evaluation": "2025-03-12 14:54:58",
        "criticite": "3",
        "evaluator_name": "Eric Cantona"
    },
    {
        "name": "Sales+",
        "type": "SaaS",
        "rda": "Antoine Dupond",
        "disponibilite": "D3",
        "integrite": "I3",
        "confidentialite": "C3",
        "perennite": "P2",
        "score": 2,
        "answered_questions": 16,
        "last_evaluation": "2025-03-14 12:43:28",
        "criticite": "2",
        "evaluator_name": "Antoine Dupond"
    },
    {
        "name": "PILVAL",
        "type": "Editeur cloud",
        "rda": "François Beranger",
        "disponibilite": "D1",
        "integrite": "I1",
        "confidentialite": "C2",
        "perennite": "P1",
        "score": None,
        "answered_questions": 0,
        "last_evaluation": None,
        "criticite": "4",
        "evaluator_name": "François Beranger"
    },
    {
        "name": "AOAGR",
        "type": "Interne cloud",
        "rda": "Non identifi\u00e9",
        "disponibilite": "D2",
        "integrite": "I3",
        "confidentialite": "C3",
        "perennite": "P3",
        "score
