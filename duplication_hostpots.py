import sys
sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd

# =========================
# 1. CHARGEMENT
# =========================

fichier = "cleaned_file_metadata.csv"

df = pd.read_csv(fichier)

print("✅ Fichier chargé")
print(f"Taille : {df.shape}")

# =========================
# 2. SEGMENTATION
# =========================

def extraire_segment(chemin, position, defaut="Inconnu"):
    segments = [s for s in str(chemin).split("/") if s]

    if len(segments) > position:
        return segments[position]

    return defaut


# Structure attendue :
# depot/unite_metier/proprietaire/fichier.ext

df["proprietaire"] = df["chemin"].apply(
    lambda x: extraire_segment(x, 2)
)

print("✅ Colonne propriétaire créée")

# =========================
# 3. CATEGORIE FICHIER
# =========================

def categoriser_fichier(extension):

    ext = str(extension).lower().strip().replace(".", "")

    if ext in [
        "doc", "docx", "txt", "rtf", "odt"
    ]:
        return "Documents"

    elif ext in [
        "pdf"
    ]:
        return "PDF"

    elif ext in [
        "ppt", "pptx", "odp"
    ]:
        return "Presentations"

    elif ext in [
        "xls", "xlsx", "csv", "ods"
    ]:
        return "Tableurs"

    elif ext in [
        "jpg", "jpeg", "png",
        "gif", "bmp", "tiff",
        "svg", "webp"
    ]:
        return "Images"

    elif ext in [
        "zip", "rar", "7z",
        "tar", "gz"
    ]:
        return "Archives"

    elif ext in [
        "mp4", "avi", "mov",
        "wmv", "mkv"
    ]:
        return "Videos"

    elif ext in [
        "mp3", "wav",
        "aac", "flac"
    ]:
        return "Audio"

    else:
        return "Autres"


df["categorie_fichier"] = (
    df["extension"]
    .fillna("")
    .apply(categoriser_fichier)
)

print("✅ Colonne categorie_fichier créée")

# =========================
# 4. DOUBLONS REELS
# =========================

if "a_supprimer" not in df.columns:
    raise Exception(
        "❌ La colonne 'a_supprimer' est absente. "
        "Exécute d'abord detect_duplicates.py"
    )

df_doublons = df[
    df["a_supprimer"] == True
].copy()

print(f"✅ Nombre de doublons : {len(df_doublons)}")

# =========================
# 5. KPI
# =========================

nb_total_fichiers = len(df)

nb_total_doublons = len(df_doublons)

nb_originaux = (
    nb_total_fichiers
    - nb_total_doublons
)

espace_total_octets = (
    df["taille_octets"].sum()
)

espace_gaspille_octets = (
    df_doublons["taille_octets"].sum()
)

espace_gaspille_mb = round(
    espace_gaspille_octets / (1024 * 1024),
    2
)

taux_gaspillage = round(
    (
        espace_gaspille_octets
        / espace_total_octets
        * 100
    ),
    2
) if espace_total_octets > 0 else 0

kpis = {
    "Nombre total de fichiers":
        nb_total_fichiers,

    "Nombre total de fichiers dupliqués":
        nb_total_doublons,

    "Espace gaspillé (MB)":
        espace_gaspille_mb,

    "Taux de gaspillage (%)":
        taux_gaspillage
}

# =========================
# 6. PIE CHART
# ORIGINAUX VS DOUBLONS
# =========================

pie_doublons = pd.DataFrame({
    "Categorie": [
        "Originaux",
        "Doublons"
    ],
    "Nombre": [
        nb_originaux,
        nb_total_doublons
    ]
})

# =========================
# 7. TOP EXTENSIONS
# =========================

top_extensions = (
    df_doublons
    .groupby("extension")
    .agg(
        nb_fichiers=("chemin", "count"),
        espace_octets=("taille_octets", "sum")
    )
    .reset_index()
)

top_extensions["espace_gaspille_mb"] = (
    top_extensions["espace_octets"]
    / (1024 * 1024)
)

top_extensions = (
    top_extensions
    .sort_values(
        "espace_gaspille_mb",
        ascending=False
    )
    .head(10)
)

# =========================
# 8. TOP PROPRIETAIRES
# =========================

top_proprietaires = (
    df_doublons
    .groupby("proprietaire")
    .agg(
        nb_fichiers=("chemin", "count"),
        espace_octets=("taille_octets", "sum")
    )
    .reset_index()
)

top_proprietaires["espace_gaspille_mb"] = (
    top_proprietaires["espace_octets"]
    / (1024 * 1024)
)

top_proprietaires = (
    top_proprietaires
    .sort_values(
        "espace_gaspille_mb",
        ascending=False
    )
    .head(10)
)

# =========================
# 9. TOP CATEGORIES
# =========================

top_categories = (
    df_doublons
    .groupby("categorie_fichier")
    .agg(
        nb_fichiers=("chemin", "count"),
        espace_octets=("taille_octets", "sum")
    )
    .reset_index()
)

top_categories["espace_gaspille_mb"] = (
    top_categories["espace_octets"]
    / (1024 * 1024)
)

top_categories = (
    top_categories
    .sort_values(
        "espace_gaspille_mb",
        ascending=False
    )
)

# =========================
# 10. RESUME CONSOLE
# =========================

print("\n===== KPI =====")

for cle, valeur in kpis.items():
    print(f"{cle}: {valeur}")

print("\n===== ORIGINAUX VS DOUBLONS =====")
print(pie_doublons)

print("\n===== TOP 10 EXTENSIONS =====")
print(
    top_extensions[
        [
            "extension",
            "nb_fichiers",
            "espace_gaspille_mb"
        ]
    ]
)

print("\n===== TOP 10 PROPRIETAIRES =====")
print(
    top_proprietaires[
        [
            "proprietaire",
            "nb_fichiers",
            "espace_gaspille_mb"
        ]
    ]
)

print("\n===== TOP CATEGORIES =====")
print(
    top_categories[
        [
            "categorie_fichier",
            "nb_fichiers",
            "espace_gaspille_mb"
        ]
    ]
)

# =========================
# 11. MISE A JOUR DU DATASET
# =========================

df.to_csv(
    fichier,
    index=False
)

print("\n✅ cleaned_file_metadata.csv mis à jour")

print("✅ Colonnes ajoutées :")
print("   - proprietaire")
print("   - categorie_fichier")

print(f"\n✅ Nombre total de fichiers : {nb_total_fichiers}")
print(f"✅ Nombre total de doublons : {nb_total_doublons}")
print(f"✅ Espace gaspillé (MB) : {espace_gaspille_mb}")
print(f"✅ Taux de gaspillage (%) : {taux_gaspillage}")