import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd

# =========================
# 1. CHARGEMENT
# =========================
fichier = "cleaned_file_metadata.csv"
df = pd.read_csv(fichier)

print("✅ Fichier chargé")
print(f"Taille initiale : {df.shape}")

# =========================
# 2. DÉTECTION DES DOUBLONS
# =========================

cles_doublons = ["hash_md5", "taille_octets"]

df["nb_occurrences"] = df.groupby(cles_doublons)["hash_md5"].transform("count")
df["est_doublon_exact"] = df["nb_occurrences"] > 1

df = df.sort_values("date_creation")

df["rang_dans_groupe"] = df.groupby(cles_doublons).cumcount() + 1

df["id_groupe_doublon"] = -1
mask = df["est_doublon_exact"]
df.loc[mask, "id_groupe_doublon"] = df[mask].groupby(cles_doublons).ngroup()

# =========================
# 3. STATUT LISIBLE
# =========================

df["statut_doublon"] = "Unique"
df.loc[mask & (df["rang_dans_groupe"] == 1), "statut_doublon"] = "Original"
df.loc[mask & (df["rang_dans_groupe"] > 1), "statut_doublon"] = (
    "Doublon #" + (df["rang_dans_groupe"] - 1).astype(str)
)


df["utilisateur"] = "user_1"


df["a_supprimer"] = df["rang_dans_groupe"] > 1

# =========================
# ✅ 4. AJOUT MINIMAL IMPORTANT
# =========================

# Type duplication
df["type_duplication"] = "Aucun"
df.loc[mask, "type_duplication"] = "Exact"

# ID groupe lisible
df["id_groupe"] = ""
df.loc[mask, "id_groupe"] = "EXACT_" + df["id_groupe_doublon"].astype(str)

print(f"✅ Dataset mis à jour : {df.shape}")

# =========================
# 5. ÉCRASEMENT DU FICHIER
# =========================

df.to_csv(fichier, index=False)

print("\n✅ Fichier CSV mis à jour directement")

# =========================
# 6. RÉSUMÉ
# =========================

print("\n✅ Résumé")
print(f"   → Fichiers uniques     : {(df['statut_doublon'] == 'Unique').sum()}")
print(f"   → Originaux            : {(df['statut_doublon'] == 'Original').sum()}")
print(f"   → Doublons exacts      : {df['est_doublon_exact'].sum() - (df['statut_doublon'] == 'Original').sum()}")
print(f"   → Groupes de doublons  : {df[df['est_doublon_exact']]['id_groupe_doublon'].nunique()}")