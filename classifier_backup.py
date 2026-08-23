"""
=========================================================
DocAI Morocco
Machine Learning + OCR Document Classifier
=========================================================

Classification hybride :

    1. Random Forest
    2. Analyse OCR / mots-clés
    3. Fusion des scores

Classes :
    - cin
    - permis
    - passport
    - rc
=========================================================
"""

from pathlib import Path
import re

import joblib
import pandas as pd

from config import MODEL_DIR


class DocumentClassifier:

    # =====================================================
    # INITIALISATION
    # =====================================================

    def __init__(self):

        self.model_path = (
            Path(MODEL_DIR)
            / "classifier.pkl"
        )

        self.encoder_path = (
            Path(MODEL_DIR)
            / "label_encoder.pkl"
        )

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Modèle introuvable : {self.model_path}"
            )

        if not self.encoder_path.exists():
            raise FileNotFoundError(
                f"Label encoder introuvable : {self.encoder_path}"
            )

        # -------------------------------------------------
        # Chargement Random Forest
        # -------------------------------------------------

        bundle = joblib.load(
            self.model_path
        )

        self.model = bundle["model"]

        self.feature_names = bundle[
            "features"
        ]

        self.encoder = joblib.load(
            self.encoder_path
        )

        print("[INFO] Modèle ML chargé.")
        print(
            "[INFO] Features :",
            len(self.feature_names)
        )

    # =====================================================
    # FEATURE EXTRACTION
    # =====================================================

    def build_features(
        self,
        fingerprint
    ):

        distribution = fingerprint.get(
            "distribution",
            {}
        )

        features = {

            "word_count":
                fingerprint.get(
                    "word_count",
                    0
                ),

            "text_blocks":
                fingerprint.get(
                    "text_blocks",
                    0
                ),

            "average_confidence":
                fingerprint.get(
                    "average_confidence",
                    0
                ),

            "average_word_width":
                fingerprint.get(
                    "average_word_width",
                    0
                ),

            "average_word_height":
                fingerprint.get(
                    "average_word_height",
                    0
                ),

            "top_ratio":
                distribution.get(
                    "top_ratio",
                    0
                ),

            "middle_ratio":
                distribution.get(
                    "middle_ratio",
                    0
                ),

            "bottom_ratio":
                distribution.get(
                    "bottom_ratio",
                    0
                ),

            "left_ratio":
                distribution.get(
                    "left_ratio",
                    0
                ),

            "center_ratio":
                distribution.get(
                    "center_ratio",
                    0
                ),

            "right_ratio":
                distribution.get(
                    "right_ratio",
                    0
                ),

            "text_density":
                fingerprint.get(
                    "text_density",
                    0
                ),

            "mrz":
                int(
                    bool(
                        fingerprint.get(
                            "mrz",
                            False
                        )
                    )
                ),

            "photo":
                int(
                    bool(
                        fingerprint.get(
                            "photo",
                            False
                        )
                    )
                )
        }

        # -------------------------------------------------
        # Respecter exactement l'ordre
        # du modèle entraîné
        # -------------------------------------------------

        vector = {
            feature:
                features.get(
                    feature,
                    0
                )
            for feature in self.feature_names
        }

        return vector

    # =====================================================
    # NORMALISATION OCR
    # =====================================================

    @staticmethod
    def normalize_text(text):

        if not text:
            return ""

        text = str(text).upper()

        # Remplacer caractères problématiques
        replacements = {
            "É": "E",
            "È": "E",
            "Ê": "E",
            "Ë": "E",
            "À": "A",
            "Â": "A",
            "Ä": "A",
            "Ù": "U",
            "Û": "U",
            "Ü": "U",
            "Ô": "O",
            "Ö": "O",
            "Î": "I",
            "Ï": "I",
            "Ç": "C",
            "—": "-",
            "–": "-"
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    # =====================================================
    # EXTRACTION TEXTE OCR
    # =====================================================

    def get_ocr_text(
        self,
        ocr_result
    ):

        if not ocr_result:
            return ""

        text = ocr_result.get(
            "text",
            ""
        )

        if text:
            return self.normalize_text(
                text
            )

        words = ocr_result.get(
            "words",
            []
        )

        texts = []

        for word in words:

            value = word.get(
                "text",
                ""
            )

            if value:
                texts.append(
                    str(value)
                )

        return self.normalize_text(
            " ".join(texts)
        )

    # =====================================================
    # KEYWORDS
    # =====================================================

    def keyword_scores(
        self,
        ocr_result,
        fingerprint=None
    ):

        text = self.get_ocr_text(
            ocr_result
        )

        scores = {
            "cin": 0.0,
            "permis": 0.0,
            "passport": 0.0,
            "rc": 0.0
        }

        matched = {
            "cin": [],
            "permis": [],
            "passport": [],
            "rc": []
        }

        # =================================================
        # CIN
        # =================================================

        cin_keywords = {

            "CARTE": 0.25,
            "NATIONALE": 0.35,
            "IDENTITE": 0.35,
            "ROYAUME": 0.15,
            "MAROC": 0.15,
            "MOROCCO": 0.15,

        }

        for keyword, weight in cin_keywords.items():

            if keyword in text:

                scores["cin"] += weight

                matched["cin"].append(
                    keyword
                )

        # -------------------------------------------------
        # Numéro CIN marocain
        # Exemple : BW43417
        # -------------------------------------------------

        cin_matches = re.findall(
            r"\b[A-Z]{1,3}\d{5,8}\b",
            text
        )

        if cin_matches:

            scores["cin"] += 0.35

            matched["cin"].append(
                "CIN_NUMBER"
            )

        # =================================================
        # PERMIS
        # =================================================

        permis_keywords = {

            "PERMIS": 0.55,
            "CONDUIRE": 0.35,
            "DRIVING": 0.30,
            "DRIVER": 0.25

        }

        for keyword, weight in permis_keywords.items():

            if keyword in text:

                scores["permis"] += weight

                matched["permis"].append(
                    keyword
                )

        # =================================================
        # PASSPORT
        # =================================================

        passport_keywords = {

            "PASSPORT": 0.60,
            "PASSEPORT": 0.60,
            "PASSPORT": 0.60,
            "MRZ": 0.40

        }

        for keyword, weight in passport_keywords.items():

            if keyword in text:

                scores["passport"] += weight

                matched["passport"].append(
                    keyword
                )

        # -------------------------------------------------
        # MRZ
        # -------------------------------------------------

        if re.search(
            r"P<[A-Z]{3}",
            text
        ):

            scores["passport"] += 0.80

            matched["passport"].append(
                "MRZ_PATTERN"
            )

        # Si fingerprint indique MRZ
        if fingerprint:

            if fingerprint.get(
                "mrz",
                False
            ):

                scores["passport"] += 0.60

                matched["passport"].append(
                    "MRZ_FEATURE"
                )

        # =================================================
        # RC
        # =================================================

        rc_keywords = {

            "REGISTRE": 0.35,
            "COMMERCE": 0.40,
            "SOCIETE": 0.20,
            "ENTREPRISE": 0.20,
            "ICE": 0.35,
            "RC": 0.30

        }

        for keyword, weight in rc_keywords.items():

            if keyword in text:

                scores["rc"] += weight

                matched["rc"].append(
                    keyword
                )

        # -------------------------------------------------
        # Normalisation des scores
        # -------------------------------------------------

        max_score = max(
            scores.values()
        )

        if max_score > 0:

            normalized = {

                label:
                    min(
                        value / max_score,
                        1.0
                    )

                for label, value
                in scores.items()
            }

        else:

            normalized = scores

        return normalized, matched

    # =====================================================
    # CLASSIFICATION
    # =====================================================

    def classify(
        self,
        ocr_result,
        fingerprint
    ):

        # =================================================
        # 1. RANDOM FOREST
        # =================================================

        feature_vector = self.build_features(
            fingerprint
        )

        X = pd.DataFrame(
            [feature_vector],
            columns=self.feature_names
        )

        probabilities = self.model.predict_proba(
            X
        )[0]

        # -------------------------------------------------
        # Scores ML
        # -------------------------------------------------

        ml_scores = {}

        for index, probability in enumerate(
            probabilities
        ):

            label = self.encoder.inverse_transform(
                [index]
            )[0]

            ml_scores[label] = float(
                probability
            )

        # =================================================
        # 2. OCR KEYWORDS
        # =================================================

        ocr_scores, matched_keywords = (
            self.keyword_scores(
                ocr_result,
                fingerprint
            )
        )

        # =================================================
        # 3. FUSION
        # =================================================

        final_scores = {}

        labels = [
            "cin",
            "permis",
            "passport",
            "rc"
        ]

        for label in labels:

            ml = ml_scores.get(
                label,
                0.0
            )

            ocr = ocr_scores.get(
                label,
                0.0
            )

            # ------------------------------------------------
            # Le ML reste majoritaire.
            #
            # 70% ML
            # 30% OCR
            # ------------------------------------------------

            final_scores[label] = (
                0.70 * ml
                +
                0.30 * ocr
            )

        # =================================================
        # 4. RÈGLE FORTE OCR
        # =================================================

        # Si un mot-clé extrêmement spécifique
        # est détecté, on renforce la classe.

        if "PERMIS" in matched_keywords["permis"]:

            final_scores["permis"] += 0.10

        if "PASSEPORT" in matched_keywords["passport"]:

            final_scores["passport"] += 0.10

        if "PASSPORT" in matched_keywords["passport"]:

            final_scores["passport"] += 0.10

        if "MRZ_PATTERN" in matched_keywords["passport"]:

            final_scores["passport"] += 0.20

        if "COMMERCE" in matched_keywords["rc"]:

            final_scores["rc"] += 0.10

        # =================================================
        # 5. NORMALISATION FINALE
        # =================================================

        total = sum(
            final_scores.values()
        )

        if total > 0:

            final_scores = {

                label:
                    value / total

                for label, value
                in final_scores.items()
            }

        # =================================================
        # 6. MEILLEURE CLASSE
        # =================================================

        document_type = max(
            final_scores,
            key=final_scores.get
        )

        confidence = final_scores[
            document_type
        ]

        # =================================================
        # 7. SCORE PAR DOCUMENT
        # =================================================

        scores = {

            label:
                round(
                    float(
                        final_scores.get(
                            label,
                            0
                        )
                    ),
                    4
                )

            for label in labels
        }

        # =================================================
        # 8. AFFICHAGE DEBUG
        # =================================================

        print(
            f"[INFO] Classification ML : "
            f"{max(ml_scores, key=ml_scores.get)} "
            f"({max(ml_scores.values()):.3f})"
        )

        print(
            f"[INFO] Classification OCR : "
            f"{max(ocr_scores, key=ocr_scores.get)} "
            f"({max(ocr_scores.values()):.3f})"
        )

        print(
            f"[INFO] Classification finale : "
            f"{document_type} "
            f"({confidence:.3f})"
        )

        if matched_keywords.get(
            document_type
        ):

            print(
                "[INFO] Mots-clés détectés :",
                matched_keywords[
                    document_type
                ]
            )

        # =================================================
        # 9. RESULTAT
        # =================================================

        return {

            "document_type":
                document_type,

            "confidence":
                round(
                    float(confidence),
                    3
                ),

            "scores":
                scores,

            "matched_keywords":
                matched_keywords,

            "method":
                "random_forest + ocr_keywords"

        }