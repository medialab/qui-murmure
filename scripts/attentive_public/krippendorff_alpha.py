import csv
import pandas as pd
import numpy as np
import krippendorff
from itertools import combinations
from sklearn.model_selection import train_test_split

RANDOM_SEED = 1234567
# =========================
# 1. Charger et nettoyer
# =========================

df = pd.read_csv(
    "../data/Annotation_attentive_users_all_coders.csv", dtype={"user_id": int}
)
df.replace("", np.nan, inplace=True)
label_to_id = {
    "Commentateur·ice d'actualité": 0,
    "Pseudo - médias": 1,
    "Anonyme": 2,
    "Ne sait pas": 2,
}
id_to_label = {
    0.0: "Commentateur·ice d'actualité",
    1.0: "Pseudo - médias",
    2.0: "Anonyme",
}

df["Catégorie"] = df["Catégorie"].replace(label_to_id)
label_to_id_positionnement = {"Non": 0, "Oui": 1}
df["Positionnement"] = df["Positionnement"].replace(label_to_id_positionnement)

ITEM_COL = "user_id"
ANNOTATOR_COL = "coder"
VARIABLES = ["Catégorie", "Positionnement"]

# =========================
# 2. Fonction Krippendorff
# =========================


def compute_kripp_alpha(df, variable):
    df_var = df.dropna(subset=[variable])
    matrix = df_var.pivot(index=ANNOTATOR_COL, columns=ITEM_COL, values=variable)
    reliability_data = matrix.to_numpy()

    alpha = krippendorff.alpha(
        reliability_data=reliability_data, level_of_measurement="nominal"
    )

    return alpha


print("\n=== Krippendorff's Alpha (global) ===")
for var in VARIABLES:
    print(f"{var} :", compute_kripp_alpha(df, var))


# =========================
# 3. Alpha 2 à 2
# =========================


def pairwise_alpha(df, variable):
    annotators = df[ANNOTATOR_COL].unique()
    matrix_results = pd.DataFrame(index=annotators, columns=annotators)

    for a1, a2 in combinations(annotators, 2):
        df_pair = df[df[ANNOTATOR_COL].isin([a1, a2])]
        df_pair = df_pair.dropna(subset=[variable])

        pivot = df_pair.pivot(index=ANNOTATOR_COL, columns=ITEM_COL, values=variable)

        if pivot.shape[1] > 0:
            alpha = krippendorff.alpha(
                reliability_data=pivot.to_numpy(), level_of_measurement="nominal"
            )
        else:
            alpha = np.nan

        matrix_results.loc[a1, a2] = alpha
        matrix_results.loc[a2, a1] = alpha

    np.fill_diagonal(matrix_results.values, 1)

    return matrix_results


print("\n=== Matrice Krippendorff 2 à 2 (Catégorie) ===")
print(pairwise_alpha(df, "Catégorie"))

print("\n=== Matrice Krippendorff 2 à 2 (Positionnement) ===")
print(pairwise_alpha(df, "Positionnement"))


# =========================
# 4. Alpha par modalité
# =========================


def alpha_by_modality(df, variable):
    df_var = df.dropna(subset=[variable])
    modalities = df_var[variable].unique()

    results = []

    for modality in modalities:
        df_mod = df_var.copy()
        df_mod["binary"] = (df_mod[variable] == modality).astype(int)

        pivot = df_mod.pivot(index=ANNOTATOR_COL, columns=ITEM_COL, values="binary")

        alpha = krippendorff.alpha(
            reliability_data=pivot.to_numpy(), level_of_measurement="nominal"
        )

        results.append(
            {"Variable": variable, "Modalité": modality, "Krippendorff_Alpha": alpha}
        )

    return pd.DataFrame(results)


alpha_by_category = alpha_by_modality(df, "Catégorie")
alpha_by_category["Modalité"] = alpha_by_category["Modalité"].replace(id_to_label)
print("\n=== Alpha par modalité (Catégorie) ===")
print(alpha_by_category.sort_values("Krippendorff_Alpha"))

print("\n=== Alpha par modalité (Positionnement) ===")
print(alpha_by_modality(df, "Positionnement"))

# =========================
# 5. Nombre d’annotateurs par user
# =========================

# nombre d’annotateurs distincts par user
annotated_df = df.dropna(subset=["Catégorie"])
print("Nombre de users annotés: ", annotated_df[ITEM_COL].nunique())

annot_counts = annotated_df.groupby(ITEM_COL)[ANNOTATOR_COL].nunique()

nb_1_annotateur = (annot_counts == 1).sum()
nb_2_annotateurs = (annot_counts == 2).sum()

print("Users annotés par 1 personne :", nb_1_annotateur)
print("Users annotés par 2 personnes :", nb_2_annotateurs)

# =========================
# 6. Cas d’accord (Catégorie)
# =========================

# On garde seulement les users avec exactement 2 annotateurs
df_2 = annotated_df[annotated_df[ITEM_COL].isin(annot_counts[annot_counts == 2].index)]

# Pivot pour comparer les deux annotations
pivot = df_2.pivot(index=ITEM_COL, columns=ANNOTATOR_COL, values="Catégorie")

# Trouver les deux plus grandes valeurs (soient celles qui ne sont pas NaN)
vals = pivot.values
max_index = np.argsort(-vals, axis=1)
max_index_vals = vals[np.arange(len(pivot.index))[:, None], max_index][:, :2]

# Compter les lignes où ces deux valeurs sont égales
agreement = max_index_vals[:, 0] == max_index_vals[:, 1]
print("Nombre de cas d'accord chez les doubles annotations :", agreement.sum())


# =========================
# 7. On ajoute les cas déjà double-annotés par Antoine et moi
# =========================
df_double = pd.read_csv(
    "../data/Annotation attentive users - tests.csv",
    usecols=list(range(0, 17)),
    dtype={"user_id": int},
)
df_double["Catégorie"] = df_double["Catégorie"].replace(label_to_id)
df_double["Positionnement"] = df_double["Positionnement"].replace(
    label_to_id_positionnement
)

all_annotated = pd.concat([annotated_df, df_double])
deduplicated = all_annotated.drop_duplicates(["user_id"])

print("=== Répartition par modalité ===")
print(deduplicated.replace(id_to_label).value_counts("Catégorie"))
print(deduplicated.replace(id_to_label).value_counts("Catégorie", normalize=True))

X_train, X_test, _, _ = train_test_split(
    deduplicated, deduplicated["Catégorie"], test_size=0.25, random_state=RANDOM_SEED
)

# =========================
# 8. On retire du jeu d'entraînement et du jeu de dev les cas de désaccord
# =========================
X_train = X_train[~X_train[ITEM_COL].isin(pivot[~agreement].index)]

print("")
print("=== Jeu d'entraînement (on a retiré les cas de désaccord) ===")
print(len(X_train), "unique users")
print(X_train.replace(id_to_label).value_counts("Catégorie"))
print(X_train.replace(id_to_label).value_counts("Catégorie", normalize=True))

X_train.to_csv("../data/public_attentif_train_set.csv", index=False)

print("")
print("=== Jeu de validation (on a retiré les cas de désaccord) ===")
X_val, X_test, _, _ = train_test_split(
    X_test, X_test["Catégorie"], test_size=0.5, random_state=RANDOM_SEED
)
X_val = X_val[~X_val[ITEM_COL].isin(pivot[~agreement].index)]
print(len(X_val), "unique users")
print(X_val.replace(id_to_label).value_counts("Catégorie"))
print(X_val.replace(id_to_label).value_counts("Catégorie", normalize=True))
X_val.to_csv("../data/public_attentif_val_set.csv", index=False)

# =========================
# 9. Pour le jeu de test, on garde un score qui est la moyenne des deux annotations
# (1.0 si accord pour oui, 0.5 si désaccord, 0.0 si accord pour non)
# =========================
print("")
print("=== Jeu de test (on garde les valeurs en désaccord) ===")
test_with_duplicates = all_annotated[all_annotated.user_id.isin(X_test.user_id)]

fieldnames = [
    "user_name",
    "user_screen_name",
    "user_id",
    "user_description",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "Commentateur·ice d'actualité",
    "Anonyme",
    "Pseudo - médias",
]


def compare_rows(previous_row, writer, row={"user_id": None}):
    if dict(previous_row):
        if previous_row["user_id"] == row["user_id"]:
            for cat_id, cat_label in id_to_label.items():
                row[cat_label] = (row[cat_label] + previous_row[cat_label]) / 2
            writer.writerow(row)
            return {}
        writer.writerow(previous_row)
    return row


def stats_with_disagreement(file_path, nb_users):
    min_max_count = {key: {"min": 0, "max": 0} for key in id_to_label.values()}
    with open(file_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for cat_label in min_max_count:
                if float(row[cat_label]) == 1.0:
                    min_max_count[cat_label]["min"] += 1
                    min_max_count[cat_label]["max"] += 1
                elif float(row[cat_label]) == 0.5:
                    min_max_count[cat_label]["max"] += 1

    print(pd.DataFrame(min_max_count).transpose().sort_values("max", ascending=False))
    print(
        (
            pd.DataFrame(min_max_count).transpose().sort_values("max", ascending=False)
            / nb_users
        ).round(2)
    )


previous_row = {}
with open("../data/public_attentif_test_set.csv", "w") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for i, row in test_with_duplicates.sort_values("user_id").iterrows():
        for cat_id, cat_label in id_to_label.items():
            row[cat_label] = float(row["Catégorie"] == cat_id)
        previous_row = compare_rows(previous_row, writer, row)
    compare_rows(previous_row, writer)


stats_with_disagreement(
    "../data/public_attentif_test_set.csv",
    len(test_with_duplicates.drop_duplicates("user_id")),
)