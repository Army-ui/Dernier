import os
import hashlib
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# =========================
# CONFIGURATION
# =========================
# - Définit le dossier cible (répertoire utilisateur)
# - Configure le nombre de threads pour le traitement parallèle
# - Liste des dossiers à exclure (système / inutiles)

DOSSIER_CIBLE = os.path.expanduser("~")
NB_THREADS = 4
EXCLUSIONS = ["AppData", "Program Files", "Windows", ".git", "__pycache__"]

# =========================
# FONCTION MD5
# =========================
# - Calcule le hash MD5 d’un fichier
# - Lecture en blocs (4 Ko) pour éviter de charger tout en mémoire
# - Retourne None en cas d’erreur

def calculer_md5(chemin):
    try:
        hash_md5 = hashlib.md5()
        with open(chemin, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return None

# =========================
# TRAITEMENT D'UN FICHIER
# =========================
# - Récupère les métadonnées d’un fichier
# - Inclut : nom, chemin, taille, extension, hash, dates
# - Gère les erreurs d’accès sans arrêter le programme

def traiter_fichier(chemin_complet):
    try:
        return {
            "nom_fichier": os.path.basename(chemin_complet),
            "chemin": chemin_complet,
            "taille_octets": os.path.getsize(chemin_complet),
            "extension": os.path.splitext(chemin_complet)[1],
            "hash_md5": calculer_md5(chemin_complet),
            "date_creation": datetime.fromtimestamp(
                os.path.getctime(chemin_complet)
            ).strftime("%Y-%m-%d %H:%M:%S"),
            "date_modification": datetime.fromtimestamp(
                os.path.getmtime(chemin_complet)
            ).strftime("%Y-%m-%d %H:%M:%S")
        }
    except (PermissionError, FileNotFoundError, OSError):
        return None

# =========================
# COLLECTE DES FICHIERS
# =========================
# - Parcourt récursivement les dossiers avec os.walk
# - Exclut certains dossiers
# - Construit une liste complète des fichiers à traiter

print(f"Debut du scan du dossier : {DOSSIER_CIBLE}")

liste_fichiers = []

for dossier, sous_dossiers, fichiers in os.walk(DOSSIER_CIBLE):
    sous_dossiers[:] = [
        d for d in sous_dossiers
        if not any(ex in d for ex in EXCLUSIONS)
    ]

    for fichier in fichiers:
        liste_fichiers.append(os.path.join(dossier, fichier))

print(f"Nombre de fichiers detectes : {len(liste_fichiers)}")
print("Debut du traitement en parallele")

# =========================
# TRAITEMENT PARALLÈLE
# =========================
# - Utilise ThreadPoolExecutor pour accélérer le traitement
# - Soumet chaque fichier comme tâche
# - Récupère les résultats au fur et à mesure
# - Affiche la progression

donnees = []

with ThreadPoolExecutor(max_workers=NB_THREADS) as executor:
    futures = []

    for f in liste_fichiers:
        try:
            future = executor.submit(traiter_fichier, f)
            futures.append(future)
        except Exception as e:
            print(f"Impossible de soumettre le fichier {f} : {e}")

    for i, future in enumerate(as_completed(futures)):
        try:
            resultat = future.result()
            if resultat:
                donnees.append(resultat)
        except Exception as e:
            print(f"Erreur : {e}")

        if i % 1000 == 0:
            print(f"{i} fichiers traites")

print("Traitement termine")
print(f"Nombre de donnees collecte : {len(donnees)}")

# =========================
# EXPORT DES DONNÉES
# =========================
# - Conversion en DataFrame pandas
# - Export en CSV
# - Affichage d’un aperçu

df = pd.DataFrame(donnees)
df.to_csv("raw_file_metadata.csv", index=False)

print(f"{len(df)} fichiers scannés sur tous les dépôts !")
print(df.head())