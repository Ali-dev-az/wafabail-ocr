"""
=========================================================
WAFABAIL
ML Classifier Training
=========================================================

Entraînement d'un modèle de classification documentaire
à partir des features extraites des documents réels.

Classes :
    - cin
    - permis
    - passport
    - rc
=========================================================
"""

from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

from config import MODEL_DIR


# =========================================================
# PATHS
# =========================================================

FEATURES_FILE = (
    Path("outputs")
    / "features.csv"
)

MODEL_FILE = MODEL_DIR / "classifier.pkl"

LABEL_ENCODER_FILE = MODEL_DIR / "label_encoder.pkl"


# =========================================================
# FEATURES
# =========================================================

FEATURE_COLUMNS = [

    "image_width",
    "image_height",

    "word_count",
    "text_blocks",

    "average_confidence",

    "average_word_width",
    "average_word_height",

    "top_ratio",
    "middle_ratio",
    "bottom_ratio",

    "left_ratio",
    "center_ratio",
    "right_ratio",

    "text_density",

    "mrz",
    "photo"

]


# =========================================================
# LOAD DATASET
# =========================================================

def load_dataset():

    print("=" * 60)
    print("        DOC AI - MODEL TRAINING")
    print("=" * 60)

    print()
    print("[INFO] Chargement du dataset...")

    if not FEATURES_FILE.exists():

        raise FileNotFoundError(
            f"Dataset introuvable : {FEATURES_FILE}"
        )

    df = pd.read_csv(
        FEATURES_FILE
    )

    print(
        f"[INFO] {len(df)} document(s) chargé(s)."
    )

    print()

    print("[INFO] Colonnes disponibles :")

    for column in df.columns:

        print(
            f"   - {column}"
        )

    return df


# =========================================================
# PREPARE DATA
# =========================================================

def prepare_data(df):

    print()
    print("[INFO] Préparation des features...")

    # -----------------------------------------------------
    # Vérification label
    # -----------------------------------------------------

    possible_labels = [

        "document_type",
        "label",
        "type"

    ]

    label_column = None

    for column in possible_labels:

        if column in df.columns:

            label_column = column
            break

    if label_column is None:

        raise ValueError(
            "Impossible de trouver la colonne "
            "contenant le type de document."
        )

    print(
        f"[INFO] Label utilisé : {label_column}"
    )

    # -----------------------------------------------------
    # Features réellement disponibles
    # -----------------------------------------------------

    available_features = [

        column

        for column in FEATURE_COLUMNS

        if column in df.columns

    ]

    if not available_features:

        raise ValueError(
            "Aucune feature compatible trouvée "
            "dans features.csv"
        )

    print()
    print("[INFO] Features utilisées :")

    for feature in available_features:

        print(
            f"   ✓ {feature}"
        )

    X = df[
        available_features
    ].copy()

    y = df[
        label_column
    ].astype(str)

    # -----------------------------------------------------
    # Nettoyage
    # -----------------------------------------------------

    X = X.replace(
        [float("inf"), float("-inf")],
        0
    )

    X = X.fillna(0)

    # -----------------------------------------------------
    # Booléens
    # -----------------------------------------------------

    for column in [
        "mrz",
        "photo"
    ]:

        if column in X.columns:

            X[column] = (
                X[column]
                .astype(int)
            )

    # -----------------------------------------------------
    # Label encoder
    # -----------------------------------------------------

    encoder = LabelEncoder()

    y_encoded = encoder.fit_transform(
        y
    )

    print()
    print("[INFO] Classes détectées :")

    for index, label in enumerate(
        encoder.classes_
    ):

        print(
            f"   {index} → {label}"
        )

    return (
        X,
        y_encoded,
        encoder,
        available_features
    )


# =========================================================
# TRAIN
# =========================================================

def train_model(
    X,
    y
):

    print()
    print("[INFO] Entraînement Random Forest...")

    model = RandomForestClassifier(

        n_estimators=200,

        max_depth=8,

        min_samples_leaf=1,

        random_state=42,

        class_weight="balanced"

    )

    model.fit(
        X,
        y
    )

    print(
        "[OK] Modèle entraîné."
    )

    return model


# =========================================================
# FEATURE IMPORTANCE
# =========================================================

def show_feature_importance(
    model,
    feature_names
):

    print()
    print("=" * 60)
    print("        IMPORTANCE DES FEATURES")
    print("=" * 60)

    importances = model.feature_importances_

    ranking = sorted(

        zip(
            feature_names,
            importances
        ),

        key=lambda x: x[1],

        reverse=True

    )

    for feature, importance in ranking:

        print(
            f"{feature:<25} "
            f"{importance:.4f}"
        )


# =========================================================
# SAVE MODEL
# =========================================================

def save_model(
    model,
    encoder,
    feature_names
):

    print()
    print("[INFO] Sauvegarde du modèle...")

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # -----------------------------------------------------
    # Modèle
    # -----------------------------------------------------

    joblib.dump(
        {
            "model": model,
            "features": feature_names
        },
        MODEL_FILE
    )

    # -----------------------------------------------------
    # Encoder
    # -----------------------------------------------------

    joblib.dump(
        encoder,
        LABEL_ENCODER_FILE
    )

    print()
    print(
        f"[OK] Modèle : {MODEL_FILE}"
    )

    print(
        f"[OK] Encoder : {LABEL_ENCODER_FILE}"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    df = load_dataset()

    (
        X,
        y,
        encoder,
        feature_names

    ) = prepare_data(
        df
    )

    model = train_model(
        X,
        y
    )

    show_feature_importance(
        model,
        feature_names
    )

    save_model(
        model,
        encoder,
        feature_names
    )

    print()
    print("=" * 60)
    print("        ENTRAÎNEMENT TERMINÉ")
    print("=" * 60)

    print()
    print(
        "Le modèle est maintenant disponible dans :"
    )

    print(
        f"   {MODEL_FILE}"
    )

    print()


# =========================================================

if __name__ == "__main__":

    main()