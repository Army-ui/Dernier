# -*- coding: utf-8 -*-
"""
Dashboard de visualisation des doublons — version simplifiée.
Lecture directe du fichier clean_file_metadata.csv
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
        
        if "a_supprimer" in df.columns:
            print(f"📊 Doublons : {len(df[df['a_supprimer'] == True])}")
            
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

            # KPI Row - 4 cards
            html.Div(className="kpi-row", children=[
                kpi_card(t(lang, "kpi_total_files"), "kpi-total", "var(--accent-copper)"),
                kpi_card(t(lang, "kpi_duplicates"), "kpi-duplicates", "var(--accent-coral)"),
                kpi_card(t(lang, "kpi_waste_percent"), "kpi-waste-percent", "var(--accent-teal)"),
                kpi_card(t(lang, "kpi_space"), "kpi-space", "var(--accent-copper)"),
            ]),

            # Filter Panel - Seulement Catégorie
            html.Div(className="filter-panel", children=[
                html.Div(className="filter-field", children=[
                    html.Label(t(lang, "filter_categorie"), className="filter-label", id="label-filter-categorie"),
                    dcc.Dropdown(id="categorie_filter", multi=True, placeholder="—"),
                ]),
            ]),

            # Charts Row 1 : Status pie + Top catégories
            html.Div(className="chart-grid-2", children=[
                html.Div(className="chart-card", children=[
                    html.Div(t(lang, "chart_status"), className="section-title", id="title-chart-status"),
                    dcc.Graph(id="graph-dup", config={"displayModeBar": False}),
                ]),
                html.Div(className="chart-card", children=[
                    html.Div(t(lang, "chart_top_categorie"), className="section-title", id="title-chart-categorie"),
                    dcc.Graph(id="graph-categorie", config={"displayModeBar": False}),
                ]),
            ]),

            # Charts Row 2 : Top propriétaires + Top dossiers impactés
            html.Div(className="chart-grid-2", children=[
                html.Div(className="chart-card", children=[
                    html.Div(t(lang, "chart_top_proprietaire"), className="section-title", id="title-chart-proprietaire"),
                    dcc.Graph(id="graph-proprietaire", config={"displayModeBar": False}),
                ]),
                html.Div(className="chart-card", children=[
                    html.Div(t(lang, "chart_top_folders"), className="section-title", id="title-chart-folders"),
                    dcc.Graph(id="graph-folders", config={"displayModeBar": False}),
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
    Output("categorie_filter", "options"),
    Input("dashboard-content", "id"),
    prevent_initial_call=False,
)
def init_filter_options(_):
    df = load_dataframe()
    if df.empty:
        return []
    
    categorie_opts = [{"label": c, "value": c} for c in sorted(df["categorie_fichier"].dropna().unique())] if "categorie_fichier" in df.columns else []
    
    return categorie_opts


@app.callback(
    Output("table", "data"),
    Output("table", "columns"),
    Output("kpi-total", "children"),
    Output("kpi-duplicates", "children"),
    Output("kpi-waste-percent", "children"),
    Output("kpi-space", "children"),
    Output("graph-dup", "figure"),
    Output("graph-categorie", "figure"),
    Output("graph-proprietaire", "figure"),
    Output("graph-folders", "figure"),
    Input("categorie_filter", "value"),
    Input("lang-store", "data"),
    Input("theme-store", "data"),
    Input("refresh-trigger-store", "data"),
)
def update_dashboard(categorie, lang, theme, _refresh):
    lang = lang or "fr"
    theme = theme or "dark"
    df = load_dataframe()

    if df.empty:
        empty_fig = empty_figure(theme, t(lang, "no_duplicates"))
        return (
            [], _table_columns(lang),
            "0", "0", "0%", "0 MB",
            empty_fig, empty_fig, empty_fig, empty_fig,
        )

    if "a_supprimer" not in df.columns:
        empty_fig = empty_figure(theme, "Colonne 'a_supprimer' manquante")
        return (
            [], _table_columns(lang),
            "0", "0", "0%", "0 MB",
            empty_fig, empty_fig, empty_fig, empty_fig,
        )

    dff = df.copy()

    # Appliquer le filtre catégorie
    if categorie and "categorie_fichier" in dff.columns:
        dff = dff[dff["categorie_fichier"].isin(categorie)]

    # Fichiers à supprimer (doublons)
    df_dup = dff[dff["a_supprimer"] == True].copy()
    df_orig = dff[dff["a_supprimer"] == False].copy()

    # KPI
    total_files = len(dff)
    total_duplicates = len(df_dup)
    
    # Pourcentage d'espace gaspillé
    total_space = dff["taille_octets"].sum() if "taille_octets" in dff.columns else 0
    wasted_space = df_dup["taille_octets"].sum() if "taille_octets" in df_dup.columns else 0
    waste_percent = (wasted_space / total_space * 100) if total_space > 0 else 0

    if len(df_dup) and "taille_octets" in df_dup.columns:
        espace_recuperable_octets = df_dup["taille_octets"].sum()
    else:
        espace_recuperable_octets = 0
    space = espace_recuperable_octets / (1024 * 1024)

    # Formatage
    total_fmt = f"{total_files:,}".replace(",", " ")
    duplicates_fmt = f"{total_duplicates:,}".replace(",", " ")
    waste_percent_fmt = f"{waste_percent:.1f}%"
    space_fmt = f"{space:,.2f} MB".replace(",", " ")

    # --- Graphiques ---
    
    # 1. Originaux vs Doublons (Pie chart)
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

    # 2. Top catégories
    if len(df_dup) and "categorie_fichier" in df_dup.columns:
        fig_categorie = px.bar(
            df_dup["categorie_fichier"].value_counts().head(10),
            color_discrete_sequence=["#8E96A3"]
        )
    else:
        fig_categorie = empty_figure(theme, t(lang, "no_duplicates"))

    # 3. Top propriétaires
    if len(df_dup) and "proprietaire" in df_dup.columns:
        fig_proprietaire = px.bar(
            df_dup["proprietaire"].value_counts().head(10),
            color_discrete_sequence=["#C9594C"]
        )
    else:
        fig_proprietaire = empty_figure(theme, t(lang, "no_duplicates"))

    # 4. Top dossiers impactés (avec le plus de gaspillage)
    if len(df_dup) and "chemin_dossier" in df_dup.columns:
        folder_waste = df_dup.groupby("chemin_dossier").agg({
            "taille_octets": "sum",
            "nom_fichier": "count"
        }).reset_index()
        folder_waste.columns = ["chemin_dossier", "waste_bytes", "file_count"]
        folder_waste["waste_mb"] = folder_waste["waste_bytes"] / (1024 * 1024)
        folder_waste = folder_waste.sort_values("waste_bytes", ascending=False).head(10)
        
        folder_waste["folder_short"] = folder_waste["chemin_dossier"].apply(
            lambda x: x.split("/")[-1] if "/" in str(x) else str(x)[:30]
        )
        
        fig_folders = px.bar(
            folder_waste,
            x="folder_short",
            y="waste_mb",
            color_discrete_sequence=["#277A70"],
            labels={"folder_short": t(lang, "col_folder"), "waste_mb": "MB"}
        )
    else:
        if len(df_dup) and "chemin" in df_dup.columns:
            df_dup["chemin_dossier"] = df_dup["chemin"].apply(
                lambda x: "/".join(str(x).split("/")[:-1]) if "/" in str(x) else str(x)
            )
            folder_waste = df_dup.groupby("chemin_dossier").agg({
                "taille_octets": "sum",
                "nom_fichier": "count"
            }).reset_index()
            folder_waste.columns = ["chemin_dossier", "waste_bytes", "file_count"]
            folder_waste["waste_mb"] = folder_waste["waste_bytes"] / (1024 * 1024)
            folder_waste = folder_waste.sort_values("waste_bytes", ascending=False).head(10)
            
            folder_waste["folder_short"] = folder_waste["chemin_dossier"].apply(
                lambda x: x.split("/")[-1] if "/" in str(x) else str(x)[:30]
            )
            
            fig_folders = px.bar(
                folder_waste,
                x="folder_short",
                y="waste_mb",
                color_discrete_sequence=["#277A70"],
                labels={"folder_short": t(lang, "col_folder"), "waste_mb": "MB"}
            )
        else:
            fig_folders = empty_figure(theme, "Colonne 'chemin_dossier' manquante")

    # Appliquer le style
    fig_dup = style_figure(fig_dup, theme)
    fig_categorie = style_figure(fig_categorie, theme)
    fig_proprietaire = style_figure(fig_proprietaire, theme)
    fig_folders = style_figure(fig_folders, theme)

    # Ajuster les bar charts
    for fig in (fig_categorie, fig_proprietaire, fig_folders):
        fig.update_traces(marker_line_width=0)
        fig.update_layout(showlegend=False, bargap=0.35, yaxis_title=None, xaxis_title=None)

    # Pie chart légende
    fig_dup.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5))

    return (
        df_dup.to_dict("records") if len(df_dup) else [],
        _table_columns(lang),
        total_fmt,
        duplicates_fmt,
        waste_percent_fmt,
        space_fmt,
        fig_dup,
        fig_categorie,
        fig_proprietaire,
        fig_folders,
    )


@app.callback(
    Output("label-filter-categorie", "children"),
    Output("title-chart-status", "children"),
    Output("title-chart-categorie", "children"),
    Output("title-chart-proprietaire", "children"),
    Output("title-chart-folders", "children"),
    Output("title-table", "children"),
    Output("label-btn-export", "children"),
    Output("kpi-total-label", "children"),
    Output("kpi-duplicates-label", "children"),
    Output("kpi-waste-percent-label", "children"),
    Output("kpi-space-label", "children"),
    Input("lang-store", "data"),
)
def update_dashboard_labels(lang):
    lang = lang or "fr"
    return (
        t(lang, "filter_categorie"),
        t(lang, "chart_status"),
        t(lang, "chart_top_categorie"),
        t(lang, "chart_top_proprietaire"),
        t(lang, "chart_top_folders"),
        t(lang, "table_title"),
        t(lang, "btn_export"),
        t(lang, "kpi_total_files"),
        t(lang, "kpi_duplicates"),
        t(lang, "kpi_waste_percent"),
        t(lang, "kpi_space"),
    )


@app.callback(
    Output("download-pdf", "data"),
    Input("btn-export", "n_clicks"),
    State("categorie_filter", "value"),
    prevent_initial_call=True,
)
def export_pdf(n_clicks, categorie):
    df = load_dataframe()
    if df.empty or "a_supprimer" not in df.columns:
        return no_update

    dff = df.copy()

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
