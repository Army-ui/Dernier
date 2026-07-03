# -*- coding: utf-8 -*-
"""
Dictionnaire de traductions FR / EN pour le Dashboard de détection de doublons.
"""

TRADUCTIONS = {
    # ── Brand / Titres ──────────────────────────────────────────────────
    "app_title": {
        "fr": "Détection de doublons",
        "en": "Duplicate Detection"
    },
    "app_subtitle": {
        "fr": "Gouvernance des données — Tableau de bord",
        "en": "Data Governance — Dashboard"
    },

    # ── KPI Cards ──────────────────────────────────────────────────────
    "kpi_total_files": {
        "fr": "Total fichiers",
        "en": "Total files"
    },
    "kpi_duplicates": {
        "fr": "Doublons",
        "en": "Duplicates"
    },
    "kpi_waste_percent": {
        "fr": "% gaspillage",
        "en": "% waste"
    },
    "kpi_space": {
        "fr": "Espace gaspillé",
        "en": "Wasted space"
    },

    # ── Filtres ────────────────────────────────────────────────────────
    "filter_categorie": {
        "fr": "Catégorie",
        "en": "Category"
    },

    # ── Graphiques ────────────────────────────────────────────────────
    "chart_status": {
        "fr": "Originaux vs Doublons",
        "en": "Originals vs Duplicates"
    },
    "chart_top_categorie": {
        "fr": "Top catégories",
        "en": "Top categories"
    },
    "chart_top_proprietaire": {
        "fr": "Top propriétaires",
        "en": "Top owners"
    },
    "chart_top_folders": {
        "fr": "Top dossiers impactés",
        "en": "Top impacted folders"
    },

    # ── Tableau ────────────────────────────────────────────────────────
    "table_title": {
        "fr": "Liste des doublons",
        "en": "Duplicates list"
    },
    "col_name": {
        "fr": "Fichier",
        "en": "File"
    },
    "col_path": {
        "fr": "Chemin",
        "en": "Path"
    },
    "col_size": {
        "fr": "Taille",
        "en": "Size"
    },
    "col_status": {
        "fr": "Statut",
        "en": "Status"
    },
    "col_proprietaire": {
        "fr": "Propriétaire",
        "en": "Owner"
    },
    "col_categorie": {
        "fr": "Catégorie",
        "en": "Category"
    },
    "col_folder": {
        "fr": "Dossier",
        "en": "Folder"
    },

    # ── Boutons ────────────────────────────────────────────────────────
    "btn_export": {
        "fr": "Exporter PDF",
        "en": "Export PDF"
    },

    # ── Thème ──────────────────────────────────────────────────────────
    "theme_dark": {
        "fr": "Sombre",
        "en": "Dark"
    },
    "theme_light": {
        "fr": "Clair",
        "en": "Light"
    },

    # ── Messages ──────────────────────────────────────────────────────
    "no_duplicates": {
        "fr": "Aucun doublon détecté",
        "en": "No duplicates detected"
    },
}


def t(langue, cle):
    """Retourne la traduction d'une clé pour la langue donnée."""
    entree = TRADUCTIONS.get(cle, {})
    return entree.get(langue, entree.get("fr", cle))


def detect_lang_from_header(accept_language):
    """Détecte la langue depuis l'en-tête Accept-Language."""
    if not accept_language:
        return "fr"
    lang = accept_language.split(",")[0].split("-")[0].lower()
    return lang if lang in ("fr", "en") else "fr"
