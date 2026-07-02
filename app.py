# -*- coding: utf-8 -*-
"""
Dashboard de visualisation des doublons — version simplifiée.
Lecture directe du fichier clean_file_metadata.csv
Adapté pour les colonnes : proprietaire, categorie_fichier, a_supprimer
"""

import os
import sys
import io
import flask
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import (
    Dash, html, dcc, dash_table, Output, Input, State,
    no_update,
)
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from i18n import t, detect_lang_from_header

# =========================
# CONFIG - RECHERCHE DU FICHIER
# =========================

def find_csv_file():
    """Recherche le fichier clean_file_metadata.csv dans plusieurs emplacements."""
    paths_to_try = []
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    paths_to_try.append(os.path.join(script_dir, "cleaned_file_metadata.csv"))
    paths_to_try.append(os.path.join(os.getcwd(), "cleaned_file_metadata.csv"))
    paths_to_try.append("cleaned_file_metadata.csv")
    paths_to_try.append(os.path.join(script_dir, "data", "cleaned_file_metadata.csv"))
    paths_to_try.append(os.path.join(os.getcwd(), "data", "cleaned_file_metadata.csv"))
    paths_to_try.append(os.path.join(script_dir, "output", "cleaned_file_metadata.csv"))
    paths_to_try.append(os.path.join(os.getcwd(), "output", "cleaned_file_metadata.csv"))
    
    env_path = os.environ.get("DEDUP_CSV_PATH")
    if env_path:
        paths_to_try.append(env_path)
    
    print("\n" + "="*60)
    print("🔍 RECHERCHE DU FICHIER clean_file_metadata.csv")
    print("="*60)
    
    for path in paths_to_try:
        if path and os.path.exists(path):
            print(f"✅ FICHIER TROUVÉ : {path}")
            print(f"   Taille : {os.path.getsize(path)} octets")
            return path
    
    print("\n❌ FICHIER NON TROUVÉ")
    return None

CSV_PATH = find_csv_file()

if CSV_PATH is None:
    print("\n⚠️  ATTENTION : Le fichier clean_file_metadata.csv n'a pas été trouvé.")
else:
    print(f"\n✅ Utilisation du fichier : {CSV_PATH}\n")

# =========================
# SERVER SETUP
# =========================

server = flask.Flask(__name__)
app = Dash(__name__, server=server, suppress_callback_exceptions=True)
app.title = "Dedup Scanner"


def empty_df():
    """DataFrame vide avec les colonnes attendues."""
    return pd.DataFrame(columns=[
        "nom_fichier", "chemin", "chemin_dossier", "profondeur_dossier",
        "taille_octets", "taille_lisible", "categorie_taille_fichier",
        "extension", "hash_md5", "date_creation", "date_modification",
        "age_fichier", "jours_depuis_modification", "nb_occurrences",
        "a_supprimer", "rang_dans_groupe", "id_groupe_doublon",
        "statut_doublon", "type_duplication", "id_groupe", "depot",
        "unite_metier", "proprietaire", "categorie_fichier"
    ])


def load_dataframe():
    """Charge le fichier CSV en utilisant le chemin trouvé."""
    global CSV_PATH
    
    if CSV_PATH is None:
        CSV_PATH = find_csv_file()
        if CSV_PATH is None:
            return empty_df()
    
    try:
        print(f"📂 Chargement du fichier : {CSV_PATH}")
        df = pd.read_csv(CSV_PATH)
        print(f"✅ Fichier chargé : {len(df)} lignes, {len(df.columns)} colonnes")
        print(f"📊 Colonnes : {', '.join(df.columns)}")
        
        # Diagnostic
        if "a_supprimer" in df.columns:
            print(f"\n📊 Distribution de 'a_supprimer':")
            print(df["a_supprimer"].value_counts())
        else:
            print("\n⚠️  La colonne 'a_supprimer' est manquante !")
            
        return df
    except Exception as e:
        print(f"❌ Erreur lors du chargement : {e}")
        return empty_df()


def empty_figure(theme="dark", message="—"):
    """Figure Plotly vide et thémée."""
    fig = go.Figure()
    fig.update_layout(**plotly_layout_theme(theme))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=13, color="#5C6472" if theme == "dark" else "#9C9586"),
    )
    return fig


def plotly_layout_theme(theme):
    """Renvoie les kwargs de layout Plotly adaptés au thème courant."""
    if theme == "light":
        paper = "#FFFFFF"
        plot = "#FFFFFF"
        font_color = "#211D17"
        grid = "#ECE9E2"
    else:
        paper = "#11151D"
        plot = "#11151D"
        font_color = "#EDEEF0"
        grid = "#232A37"

    return dict(
        paper_bgcolor=paper,
        plot_bgcolor=plot,
        font=dict(color=font_color, family="Space Grotesk, sans-serif", size=12),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(gridcolor=grid, zerolinecolor=grid),
        yaxis=dict(gridcolor=grid, zerolinecolor=grid),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        colorway=["#C77D34", "#3D9E92", "#C9594C", "#8E96A3", "#E0A05C", "#277A70"],
    )


def style_figure(fig, theme):
    fig.update_layout(**plotly_layout_theme(theme))
    return fig


# =========================
# LAYOUT
# =========================

def kpi_card(label, kpi_id, color_var):
    return html.Div(
        [
            html.Div(label, className="kpi-label", id=f"{kpi_id}-label"),
            html.Div("0", className="kpi-value", id=kpi_id),
        ],
        className="kpi-card",
        style={"--kpi-accent": color_var},
    )


def build_dashboard(lang="fr", theme="dark"):
    return html.Div(
        className="main-content",
        id="dashboard-content",
        children=[

            # KPI Row - 4 cards : Total fichiers, Doublons, Groupes, Espace gaspillé
            html.Div(className="kpi-row", children=[
                kpi_card(t(lang, "kpi_total_files"), "kpi-total", "var(--accent-copper)"),
                kpi_card(t(lang, "kpi_duplicates"), "kpi-duplicates", "var(--accent-coral)"),
                kpi_card(t(lang, "kpi_groups"), "kpi-groups", "var(--accent-teal)"),
                kpi_card(t(lang, "kpi_space"), "kpi-space", "var(--accent-copper)"),
            ]),

            # Filter Panel - seulement Propriétaire et Catégorie
            html.Div(className="filter-panel", children=[
                html.Div(className="filter-field", children=[
                    html.Label(t(lang, "filter_proprietaire"), className="filter-label", id="label-filter-proprietaire"),
                    dcc.Dropdown(id="proprietaire_filter", multi=True, placeholder="—"),
                ]),
                html.Div(className="filter-field", children=[
                    html.Label(t(lang, "filter_categorie"), className="filter-label", id="label-filter-categorie"),
                    dcc.Dropdown(id="categorie_filter", multi=True, placeholder="—"),
                ]),
            ]),

            # Charts Row 1 : Top extensions + Status pie
            html.Div(className="chart-grid-2", children=[
                html.Div(className="chart-card", children=[
                    html.Div(t(lang, "chart_top_ext"), className="section-title", id="title-chart-ext"),
                    dcc.Graph(id="graph-extension", config={"displayModeBar": False}),
                ]),
                html.Div(className="chart-card", children=[
                    html.Div(t(lang, "chart_status"), className="section-title", id="title-chart-status"),
                    dcc.Graph(id="graph-dup", config={"displayModeBar": False}),
                ]),
            ]),

            # Charts Row 2 : Top propriétaires + Top catégories
            html.Div(className="chart-grid-2", children=[
                html.Div(className="chart-card", children=[
                    html.Div(t(lang, "chart_top_proprietaire"), className="section-title", id="title-chart-proprietaire"),
                    dcc.Graph(id="graph-proprietaire", config={"displayModeBar": False}),
                ]),
                html.Div(className="chart-card", children=[
                    html.Div(t(lang, "chart_top_categorie"), className="section-title", id="title-chart-categorie"),
                    dcc.Graph(id="graph-categorie", config={"displayModeBar": False}),
                ]),
            ]),

            # Charts Row 3 : Top groupes de doublons
            html.Div(className="chart-grid-2", children=[
                html.Div(className="chart-card", children=[
                    html.Div(t(lang, "chart_top_group"), className="section-title", id="title-chart-group"),
                    dcc.Graph(id="graph-group", config={"displayModeBar": False}),
                ]),
                html.Div(className="chart-card", children=[
                    html.Div(t(lang, "chart_niveau"), className="section-title", id="title-chart-niveau"),
                    dcc.Graph(id="graph-niveau", config={"displayModeBar": False}),
                ]),
            ]),

            # Export button
            html.Div(className="toolbar-row", children=[
                html.Button([" 📥 ", html.Span(t(lang, "btn_export"), id="label-btn-export")],
                            id="btn-export", className="control-pill-btn"),
            ]),

            dcc.Download(id="download-pdf"),

            # Table
            html.Div(className="table-card", children=[
                html.Div(t(lang, "table_title"), className="section-title", id="title-table"),
                dash_table.DataTable(
                    id="table",
                    columns=_table_columns(lang),
                    page_size=10,
                    style_table={"overflowX": "auto"},
                    style_header={"backgroundColor": "var(--bg-subtle)", "fontWeight": "600"},
                    style_cell={"padding": "12px", "backgroundColor": "var(--bg-card)", "border": "none"},
                ),
            ]),

            dcc.Store(id="refresh-trigger-store", data=0),
        ],
    )


def _table_columns(lang):
    return [
        {"name": t(lang, "col_name"), "id": "nom_fichier"},
        {"name": t(lang, "col_path"), "id": "chemin"},
        {"name": t(lang, "col_size"), "id": "taille_lisible"},
        {"name": t(lang, "col_status"), "id": "statut_doublon"},
        {"name": t(lang, "col_proprietaire"), "id": "proprietaire"},
        {"name": t(lang, "col_categorie"), "id": "categorie_fichier"},
        {"name": t(lang, "col_niveau"), "id": "profondeur_dossier"},
    ]


# =========================
# ROOT LAYOUT
# =========================

app.layout = html.Div(id="theme-root", children=[

    dcc.Store(id="lang-store", data="fr"),
    dcc.Store(id="theme-store", data="dark"),
    dcc.Store(id="lang-initialized", data=False),

    html.Div(className="app-shell", id="app-shell", children=[

        html.Div(className="topbar", children=[
            html.Div(className="brand-block", children=[
                html.Div("◎", className="brand-mark"),
                html.Div([
                    html.Div(t("fr", "app_title"), className="brand-text-title", id="brand-title"),
                    html.Div(t("fr", "app_subtitle"), className="brand-text-subtitle", id="brand-subtitle"),
                ])
            ]),
            html.Div(className="topbar-controls", children=[
                html.Button("FR / EN", id="btn-lang-toggle", className="icon-toggle-btn"),
                html.Button("🌙 Sombre", id="btn-theme-toggle", className="icon-toggle-btn"),
            ]),
        ]),

        html.Div(id="page-body", children=[
            build_dashboard("fr"),
        ]),
    ]),
])


# =========================
# CALLBACKS
# =========================

@app.callback(
    Output("lang-store", "data"),
    Output("lang-initialized", "data"),
    Input("lang-initialized", "data"),
    prevent_initial_call=False,
)
def detect_browser_language(already_init):
    if already_init:
        return no_update, no_update
    accept_language = flask.request.headers.get("Accept-Language", "")
    lang = detect_lang_from_header(accept_language)
    return lang, True


@app.callback(
    Output("lang-store", "data", allow_duplicate=True),
    Input("btn-lang-toggle", "n_clicks"),
    State("lang-store", "data"),
    prevent_initial_call=True,
)
def toggle_lang(n_clicks, current_lang):
    return "en" if current_lang == "fr" else "fr"


@app.callback(
    Output("theme-store", "data"),
    Input("btn-theme-toggle", "n_clicks"),
    State("theme-store", "data"),
    prevent_initial_call=True,
)
def toggle_theme(n_clicks, current_theme):
    return "light" if current_theme == "dark" else "dark"


app.clientside_callback(
    """
    function(theme) {
        document.documentElement.setAttribute('data-theme', theme || 'dark');
        return window.dash_clientside.no_update;
    }
    """,
    Output("theme-root", "title"),
    Input("theme-store", "data"),
)


@app.callback(
    Output("btn-theme-toggle", "children"),
    Output("btn-lang-toggle", "children"),
    Input("theme-store", "data"),
    Input("lang-store", "data"),
)
def update_toggle_labels(theme, lang):
    theme_label = ("🌙 " + t(lang, "theme_dark")) if theme == "dark" else ("☀️ " + t(lang, "theme_light"))
    lang_label = "FR 🇫🇷" if lang == "fr" else "EN 🇬🇧"
    return theme_label, lang_label


@app.callback(
    Output("brand-title", "children"),
    Output("brand-subtitle", "children"),
    Input("lang-store", "data"),
)
def update_brand_text(lang):
    return t(lang, "app_title"), t(lang, "app_subtitle")


@app.callback(
    Output("proprietaire_filter", "options"),
    Output("categorie_filter", "options"),
    Input("dashboard-content", "id"),
    prevent_initial_call=False,
)
def init_filter_options(_):
    df = load_dataframe()
    if df.empty:
        return [], []
    
    proprio_opts = [{"label": p, "value": p} for p in sorted(df["proprietaire"].dropna().unique())] if "proprietaire" in df.columns else []
    categorie_opts = [{"label": c, "value": c} for c in sorted(df["categorie_fichier"].dropna().unique())] if "categorie_fichier" in df.columns else []
    
    return proprio_opts, categorie_opts


@app.callback(
    Output("table", "data"),
    Output("table", "columns"),
    Output("kpi-total", "children"),
    Output("kpi-duplicates", "children"),
    Output("kpi-groups", "children"),
    Output("kpi-space", "children"),
    Output("graph-extension", "figure"),
    Output("graph-dup", "figure"),
    Output("graph-proprietaire", "figure"),
    Output("graph-categorie", "figure"),
    Output("graph-group", "figure"),
    Output("graph-niveau", "figure"),
    Input("proprietaire_filter", "value"),
    Input("categorie_filter", "value"),
    Input("lang-store", "data"),
    Input("theme-store", "data"),
    Input("refresh-trigger-store", "data"),
)
def update_dashboard(proprietaire, categorie, lang, theme, _refresh):
    lang = lang or "fr"
    theme = theme or "dark"
    df = load_dataframe()

    if df.empty:
        empty_fig = empty_figure(theme, t(lang, "no_duplicates"))
        return (
            [], _table_columns(lang),
            "0", "0", "0", "0 MB",
            empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
        )

    if "a_supprimer" not in df.columns:
        print("⚠️  La colonne 'a_supprimer' n'existe pas")
        empty_fig = empty_figure(theme, "Colonne 'a_supprimer' manquante")
        return (
            [], _table_columns(lang),
            "0", "0", "0", "0 MB",
            empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
        )

    dff = df.copy()

    # Appliquer les filtres
    if proprietaire and "proprietaire" in dff.columns:
        dff = dff[dff["proprietaire"].isin(proprietaire)]
    if categorie and "categorie_fichier" in dff.columns:
        dff = dff[dff["categorie_fichier"].isin(categorie)]

    # Fichiers à supprimer (doublons)
    df_dup = dff[dff["a_supprimer"] == True].copy()
    df_orig = dff[dff["a_supprimer"] == False].copy()
    
    print(f"   Originaux: {len(df_orig)}, Doublons: {len(df_dup)}")

    # KPI
    total_files = len(dff)
    total_duplicates = len(df_dup)
    groups = df_dup["id_groupe_doublon"].nunique() if len(df_dup) and "id_groupe_doublon" in df_dup.columns else 0

    if len(df_dup) and "taille_octets" in df_dup.columns:
        espace_recuperable_octets = df_dup["taille_octets"].sum()
    else:
        espace_recuperable_octets = 0
    space = espace_recuperable_octets / (1024 * 1024)

    # Formatage
    total_fmt = f"{total_files:,}".replace(",", " ")
    duplicates_fmt = f"{total_duplicates:,}".replace(",", " ")
    groups_fmt = f"{groups:,}".replace(",", " ")
    space_fmt = f"{space:,.2f} MB".replace(",", " ")

    # --- Graphiques ---
    
    # 1. Top extensions
    if len(df_dup) and "extension" in df_dup.columns:
        fig_ext = px.bar(
            df_dup["extension"].value_counts().head(10),
            color_discrete_sequence=["#C77D34"]
        )
    else:
        fig_ext = empty_figure(theme, t(lang, "no_duplicates"))

    # 2. Originaux vs Doublons (Pie chart)
    if len(df_dup) > 0 or len(df_orig) > 0:
        pie_data = pd.DataFrame({
            "Statut": ["Originaux", "Doublons"],
            "Nombre": [len(df_orig), len(df_dup)]
        })
        pie_data = pie_data[pie_data["Nombre"] > 0]
        fig_dup = px.pie(
            pie_data,
            names="Statut",
            values="Nombre",
            hole=0.55,
            color="Statut",
            color_discrete_map={"Originaux": "#C77D34", "Doublons": "#3D9E92"},
        )
    else:
        fig_dup = empty_figure(theme, t(lang, "no_duplicates"))

    # 3. Top propriétaires
    if len(df_dup) and "proprietaire" in df_dup.columns:
        fig_proprio = px.bar(
            df_dup["proprietaire"].value_counts().head(10),
            color_discrete_sequence=["#C9594C"]
        )
    else:
        fig_proprio = empty_figure(theme, t(lang, "no_duplicates"))

    # 4. Top catégories
    if len(df_dup) and "categorie_fichier" in df_dup.columns:
        fig_categorie = px.bar(
            df_dup["categorie_fichier"].value_counts().head(10),
            color_discrete_sequence=["#8E96A3"]
        )
    else:
        fig_categorie = empty_figure(theme, t(lang, "no_duplicates"))

    # 5. Groupes de doublons
    if len(df_dup) and "id_groupe_doublon" in df_dup.columns:
        fig_group = px.bar(
            df_dup["id_groupe_doublon"].value_counts().head(10),
            color_discrete_sequence=["#E0A05C"]
        )
    else:
        fig_group = empty_figure(theme, t(lang, "no_duplicates"))

    # 6. Distribution par niveau (profondeur_dossier)
    if "profondeur_dossier" in dff.columns:
        # Distribution des doublons par niveau
        niveau_counts = dff.groupby("profondeur_dossier").size().reset_index(name="count")
        # Filtrer les niveaux avec des doublons
        niveau_counts = niveau_counts.sort_values("profondeur_dossier")
        
        if len(niveau_counts) > 0:
            fig_niveau = px.bar(
                niveau_counts,
                x="profondeur_dossier",
                y="count",
                color_discrete_sequence=["#277A70"],
                labels={"profondeur_dossier": t(lang, "col_niveau"), "count": t(lang, "axis_nb_files")}
            )
        else:
            fig_niveau = empty_figure(theme, t(lang, "no_duplicates"))
    else:
        # Si profondeur_dossier n'existe pas, essayer de l'extraire du chemin
        if "chemin" in dff.columns:
            dff["profondeur_calc"] = dff["chemin"].apply(lambda x: len(str(x).split("/")) - 1 if pd.notna(x) else 0)
            niveau_counts = dff.groupby("profondeur_calc").size().reset_index(name="count")
            niveau_counts = niveau_counts.sort_values("profondeur_calc")
            
            if len(niveau_counts) > 0:
                fig_niveau = px.bar(
                    niveau_counts,
                    x="profondeur_calc",
                    y="count",
                    color_discrete_sequence=["#277A70"],
                    labels={"profondeur_calc": t(lang, "col_niveau"), "count": t(lang, "axis_nb_files")}
                )
            else:
                fig_niveau = empty_figure(theme, t(lang, "no_duplicates"))
        else:
            fig_niveau = empty_figure(theme, "Colonne 'profondeur_dossier' manquante")

    # Appliquer le style
    fig_ext = style_figure(fig_ext, theme)
    fig_dup = style_figure(fig_dup, theme)
    fig_proprio = style_figure(fig_proprio, theme)
    fig_categorie = style_figure(fig_categorie, theme)
    fig_group = style_figure(fig_group, theme)
    fig_niveau = style_figure(fig_niveau, theme)

    # Ajuster les bar charts
    for fig in (fig_ext, fig_proprio, fig_categorie, fig_group, fig_niveau):
        fig.update_traces(marker_line_width=0)
        fig.update_layout(showlegend=False, bargap=0.35, yaxis_title=None, xaxis_title=None)

    # Pie chart légende
    fig_dup.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5))

    return (
        df_dup.to_dict("records") if len(df_dup) else [],
        _table_columns(lang),
        total_fmt,
        duplicates_fmt,
        groups_fmt,
        space_fmt,
        fig_ext,
        fig_dup,
        fig_proprio,
        fig_categorie,
        fig_group,
        fig_niveau,
    )


@app.callback(
    Output("label-filter-proprietaire", "children"),
    Output("label-filter-categorie", "children"),
    Output("title-chart-ext", "children"),
    Output("title-chart-status", "children"),
    Output("title-chart-proprietaire", "children"),
    Output("title-chart-categorie", "children"),
    Output("title-chart-group", "children"),
    Output("title-chart-niveau", "children"),
    Output("title-table", "children"),
    Output("label-btn-export", "children"),
    Output("kpi-total-label", "children"),
    Output("kpi-duplicates-label", "children"),
    Output("kpi-groups-label", "children"),
    Output("kpi-space-label", "children"),
    Input("lang-store", "data"),
)
def update_dashboard_labels(lang):
    lang = lang or "fr"
    return (
        t(lang, "filter_proprietaire"),
        t(lang, "filter_categorie"),
        t(lang, "chart_top_ext"),
        t(lang, "chart_status"),
        t(lang, "chart_top_proprietaire"),
        t(lang, "chart_top_categorie"),
        t(lang, "chart_top_group"),
        t(lang, "chart_niveau"),
        t(lang, "table_title"),
        t(lang, "btn_export"),
        t(lang, "kpi_total_files"),
        t(lang, "kpi_duplicates"),
        t(lang, "kpi_groups"),
        t(lang, "kpi_space"),
    )


@app.callback(
    Output("download-pdf", "data"),
    Input("btn-export", "n_clicks"),
    State("proprietaire_filter", "value"),
    State("categorie_filter", "value"),
    prevent_initial_call=True,
)
def export_pdf(n_clicks, proprietaire, categorie):
    df = load_dataframe()
    if df.empty or "a_supprimer" not in df.columns:
        return no_update

    dff = df.copy()

    if proprietaire and "proprietaire" in dff.columns:
        dff = dff[dff["proprietaire"].isin(proprietaire)]
    if categorie and "categorie_fichier" in dff.columns:
        dff = dff[dff["categorie_fichier"].isin(categorie)]

    df_dup = dff[dff["a_supprimer"] == True]

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    width, height = letter
    y = height - 40

    pdf.drawString(30, y, "Export doublons")
    y -= 20

    cols = ["nom_fichier", "chemin", "taille_lisible"]
    if "proprietaire" in df_dup.columns:
        cols.append("proprietaire")
    if "categorie_fichier" in df_dup.columns:
        cols.append("categorie_fichier")
    if "profondeur_dossier" in df_dup.columns:
        cols.append("profondeur_dossier")

    for _, row in df_dup.head(100).iterrows():
        line = " | ".join([str(row[c])[:30] for c in cols if c in row.index])
        pdf.drawString(30, y, line)
        y -= 15

        if y < 40:
            pdf.showPage()
            y = height - 40

    pdf.save()
    buffer.seek(0)

    return dcc.send_bytes(buffer.read(), "doublons.pdf")


# =========================
# RUN
# =========================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 LANCEMENT DU DASHBOARD")
    print("="*60)
    print(f"📁 Répertoire du script : {os.path.dirname(os.path.abspath(__file__))}")
    print(f"📁 Répertoire de travail : {os.getcwd()}")
    print(f"📄 Fichier CSV : {CSV_PATH if CSV_PATH else 'NON TROUVÉ'}")
    print("="*60 + "\n")
    
    debug_mode = os.environ.get("DEDUP_DEBUG", "0") == "1"
    app.run(debug=debug_mode, host="0.0.0.0", port=8050, use_reloader=False)