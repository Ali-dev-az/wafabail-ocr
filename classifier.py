"""
=========================================================
WAFABAIL
Machine Learning + OCR Document Classifier
=========================================================

Classification hybride robuste :

    1. Signatures documentaires fortes
    2. Analyse OCR tolérante aux erreurs
    3. Random Forest
    4. Fusion contrôlée

Classes :
    - cin
    - permis
    - passport
    - rc
=========================================================
"""

from pathlib import Path
import re
from difflib import SequenceMatcher

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

        fingerprint = (
            fingerprint
            if isinstance(fingerprint, dict)
            else {}
        )

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
        # Respecter exactement les features du modèle
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

            "Œ": "OE",
            "Æ": "AE",

            "—": "-",
            "–": "-"
        }

        for old, new in replacements.items():
            text = text.replace(
                old,
                new
            )

        text = re.sub(
            r"[^A-Z0-9<>\-/ ]+",
            " ",
            text
        )

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
    # MOTS OCR
    # =====================================================

    def get_ocr_words(
        self,
        ocr_result
    ):

        words = []

        for word in (
            ocr_result.get(
                "words",
                []
            )
            if ocr_result
            else []
        ):

            value = word.get(
                "text",
                ""
            )

            if not value:
                continue

            words.append(
                self.normalize_text(
                    value
                )
            )

        return [
            w
            for w in words
            if w
        ]

    # =====================================================
    # SIMILARITE OCR
    # =====================================================

    @staticmethod
    def similarity(
        a,
        b
    ):

        a = str(a).upper()
        b = str(b).upper()

        if not a or not b:
            return 0.0

        return SequenceMatcher(
            None,
            a,
            b
        ).ratio()

    # =====================================================
    # MOT EXACT OU OCR APPROCHANT
    # =====================================================

    def fuzzy_word_match(
        self,
        words,
        target,
        threshold=0.72
    ):

        target = self.normalize_text(
            target
        )

        best_score = 0.0
        best_word = None

        for word in words:

            score = self.similarity(
                word,
                target
            )

            if score > best_score:

                best_score = score
                best_word = word

        return (
            best_score >= threshold,
            best_score,
            best_word
        )

    # =====================================================
    # PHRASE APPROXIMATIVE
    # =====================================================

    def fuzzy_phrase_score(
        self,
        text,
        phrase
    ):

        text_words = self.normalize_text(
            text
        ).split()

        phrase_words = self.normalize_text(
            phrase
        ).split()

        if not text_words:
            return 0.0

        if not phrase_words:
            return 0.0

        scores = []

        for target in phrase_words:

            best = 0.0

            for word in text_words:

                score = self.similarity(
                    word,
                    target
                )

                if score > best:
                    best = score

            scores.append(
                best
            )

        return sum(scores) / len(scores)

    # =====================================================
    # SIGNATURES DOCUMENTAIRES
    # =====================================================

    def detect_strong_signature(
        self,
        ocr_result,
        fingerprint=None
    ):

        text = self.get_ocr_text(
            ocr_result
        )

        words = self.get_ocr_words(
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

        carte_ok, carte_score, _ = (
            self.fuzzy_word_match(
                words,
                "CARTE",
                0.70
            )
        )

        identite_ok, identite_score, _ = (
            self.fuzzy_word_match(
                words,
                "IDENTITE",
                0.62
            )
        )

        nationale_ok, nationale_score, _ = (
            self.fuzzy_word_match(
                words,
                "NATIONALE",
                0.60
            )
        )

        # Phrase globale
        cin_phrase_score = max(
            self.fuzzy_phrase_score(
                text,
                "CARTE NATIONALE IDENTITE"
            ),
            self.fuzzy_phrase_score(
                text,
                "CARTE NATIONALE D IDENTITE"
            )
        )

        if carte_ok:

            scores["cin"] += 0.40

            matched["cin"].append(
                f"CARTE~{carte_score:.2f}"
            )

        if identite_ok:

            scores["cin"] += 0.50

            matched["cin"].append(
                f"IDENTITE~{identite_score:.2f}"
            )

        if nationale_ok:

            scores["cin"] += 0.30

            matched["cin"].append(
                f"NATIONALE~{nationale_score:.2f}"
            )

        if cin_phrase_score >= 0.62:

            scores["cin"] += 0.70

            matched["cin"].append(
                "CIN_PHRASE"
            )

        # Numéro CIN comme élément complémentaire
        cin_matches = re.findall(
            r"\b[A-Z]{1,3}\d{5,8}\b",
            text
        )

        if cin_matches:

            scores["cin"] += 0.20

            matched["cin"].append(
                "CIN_NUMBER"
            )

        # =================================================
        # PERMIS
        # =================================================

        permis_ok, permis_score, _ = (
            self.fuzzy_word_match(
                words,
                "PERMIS",
                0.68
            )
        )

        conduire_ok, conduire_score, _ = (
            self.fuzzy_word_match(
                words,
                "CONDUIRE",
                0.65
            )
        )

        if permis_ok:

            scores["permis"] += 0.80

            matched["permis"].append(
                f"PERMIS~{permis_score:.2f}"
            )

        if conduire_ok:

            scores["permis"] += 0.60

            matched["permis"].append(
                f"CONDUIRE~{conduire_score:.2f}"
            )

        permis_phrase_score = max(
            self.fuzzy_phrase_score(
                text,
                "PERMIS DE CONDUIRE"
            ),
            self.fuzzy_phrase_score(
                text,
                "PERMIS CONDUIRE"
            )
        )

        if permis_phrase_score >= 0.65:

            scores["permis"] += 0.90

            matched["permis"].append(
                "PERMIS_PHRASE"
            )

        # =================================================
        # PASSPORT
        # =================================================

        passport_ok, passport_score, _ = (
            self.fuzzy_word_match(
                words,
                "PASSEPORT",
                0.68
            )
        )

        passport_en_ok, passport_en_score, _ = (
            self.fuzzy_word_match(
                words,
                "PASSPORT",
                0.68
            )
        )

        if passport_ok:

            scores["passport"] += 1.00

            matched["passport"].append(
                f"PASSEPORT~{passport_score:.2f}"
            )

        if passport_en_ok:

            scores["passport"] += 1.00

            matched["passport"].append(
                f"PASSPORT~{passport_en_score:.2f}"
            )

        # -------------------------------------------------
        # MRZ
        # -------------------------------------------------

        mrz_pattern = re.search(
            r"(?:P<[A-Z]{3}|[A-Z]{1,2}<[A-Z]{2})",
            text
        )

        if mrz_pattern:

            scores["passport"] += 1.50

            matched["passport"].append(
                "MRZ_PATTERN"
            )

        if fingerprint:

            if fingerprint.get(
                "mrz",
                False
            ):

                scores["passport"] += 1.00

                matched["passport"].append(
                    "MRZ_FEATURE"
                )

        # =================================================
        # RC
        # =================================================

        registre_ok, registre_score, _ = (
            self.fuzzy_word_match(
                words,
                "REGISTRE",
                0.65
            )
        )

        commerce_ok, commerce_score, _ = (
            self.fuzzy_word_match(
                words,
                "COMMERCE",
                0.65
            )
        )

        certificat_ok, certificat_score, _ = (
            self.fuzzy_word_match(
                words,
                "CERTIFICAT",
                0.65
            )
        )

        immatriculation_ok, immatriculation_score, _ = (
            self.fuzzy_word_match(
                words,
                "IMMATRICULATION",
                0.58
            )
        )

        if registre_ok:

            scores["rc"] += 0.80

            matched["rc"].append(
                f"REGISTRE~{registre_score:.2f}"
            )

        if commerce_ok:

            scores["rc"] += 0.80

            matched["rc"].append(
                f"COMMERCE~{commerce_score:.2f}"
            )

        if certificat_ok:

            scores["rc"] += 0.45

            matched["rc"].append(
                f"CERTIFICAT~{certificat_score:.2f}"
            )

        if immatriculation_ok:

            scores["rc"] += 0.55

            matched["rc"].append(
                f"IMMATRICULATION~{immatriculation_score:.2f}"
            )

        rc_phrase_score = max(
            self.fuzzy_phrase_score(
                text,
                "REGISTRE DU COMMERCE"
            ),
            self.fuzzy_phrase_score(
                text,
                "CERTIFICAT D IMMATRICULATION"
            )
        )

        if rc_phrase_score >= 0.62:

            scores["rc"] += 1.00

            matched["rc"].append(
                "RC_PHRASE"
            )

        # -------------------------------------------------
        # Mots spécifiques RC
        # -------------------------------------------------

        rc_specific = [
            "SOCIETE",
            "ENTREPRISE",
            "DENOMINATION",
            "CAPITAL",
            "JURIDIQUE",
            "CHRONOLOGIQUE",
            "ANALYTIQUE",
            "ICE"
        ]

        for target in rc_specific:

            ok, score, _ = (
                self.fuzzy_word_match(
                    words,
                    target,
                    0.68
                )
            )

            if ok:

                scores["rc"] += 0.12

                matched["rc"].append(
                    f"{target}~{score:.2f}"
                )

        return (
            scores,
            matched
        )

    # =====================================================
    # KEYWORDS CLASSIQUES
    # =====================================================

    def keyword_scores(
        self,
        ocr_result,
        fingerprint=None
    ):

        text = self.get_ocr_text(
            ocr_result
        )

        words = self.get_ocr_words(
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
            "MRZ": 0.40
        }

        for keyword, weight in passport_keywords.items():

            if keyword in text:

                scores["passport"] += weight

                matched["passport"].append(
                    keyword
                )

        if re.search(
            r"P<[A-Z]{3}",
            text
        ):

            scores["passport"] += 0.80

            matched["passport"].append(
                "MRZ_PATTERN"
            )

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
            "RC": 0.30,
            "CERTIFICAT": 0.30,
            "IMMATRICULATION": 0.30
        }

        for keyword, weight in rc_keywords.items():

            if keyword in text:

                scores["rc"] += weight

                matched["rc"].append(
                    keyword
                )

        return (
            scores,
            matched
        )

    # =====================================================
    # CLASSIFICATION
    # =====================================================

    def classify(self, ocr_result, fingerprint):
        """
        Classification prioritaire par signatures textuelles.
        Le Random Forest reste un fallback uniquement lorsque l'OCR
        ne fournit pas assez d'indices fiables.
        """
        text = self.get_ocr_text(ocr_result)
        words = self.get_ocr_words(ocr_result)
        joined = " ".join(words)

        def has(target, threshold=0.82):
            ok, score, _ = self.fuzzy_word_match(words, target, threshold)
            return ok

        def phrase(target, threshold=0.78):
            return self.fuzzy_phrase_score(text, target) >= threshold

        scores = {"cin": 0.0, "permis": 0.0, "passport": 0.0, "rc": 0.0}
        matches = {k: [] for k in scores}

        # Passport: MRZ / PASSPORT sont les indices les plus discriminants.
        mrz = bool(fingerprint.get("mrz", False)) if fingerprint else False
        passport_direct = has("PASSPORT", .70) or has("PASSEPORT", .70)
        passport_phrase = phrase("PASSPORT", .72) or phrase("PASSEPORT", .72)
        if passport_direct:
            scores["passport"] += 0.85; matches["passport"].append("PASSPORT")
        if passport_phrase:
            scores["passport"] += 0.40; matches["passport"].append("PASSEPORT_PHRASE")
        if mrz or re.search(r"P\s*[<«‹]\s*[A-Z]{2,3}", text):
            scores["passport"] += 1.25; matches["passport"].append("MRZ")

        # Permis.
        permis = has("PERMIS", .70)
        conduire = has("CONDUIRE", .70)
        if permis:
            scores["permis"] += 0.80; matches["permis"].append("PERMIS")
        if conduire:
            scores["permis"] += 0.70; matches["permis"].append("CONDUIRE")
        if phrase("PERMIS DE CONDUIRE", .68) or phrase("PERMIS CONDUIRE", .68):
            scores["permis"] += 0.80; matches["permis"].append("PERMIS_DE_CONDUIRE")

        # RC.
        registre = has("REGISTRE", .68)
        commerce = has("COMMERCE", .68)
        certificat = has("CERTIFICAT", .70)
        immat = has("IMMATRICULATION", .68)
        ice = bool(re.search(r"\bICE\b", text))
        if registre:
            scores["rc"] += 0.75; matches["rc"].append("REGISTRE")
        if commerce:
            scores["rc"] += 0.75; matches["rc"].append("COMMERCE")
        if certificat:
            scores["rc"] += 0.35; matches["rc"].append("CERTIFICAT")
        if immat:
            scores["rc"] += 0.45; matches["rc"].append("IMMATRICULATION")
        if ice:
            scores["rc"] += 0.35; matches["rc"].append("ICE")
        if phrase("REGISTRE DU COMMERCE", .68) or phrase("CERTIFICAT D IMMATRICULATION", .68):
            scores["rc"] += 0.75; matches["rc"].append("RC_PHRASE")

        # CIN.
        carte = has("CARTE", .70)
        nationale = has("NATIONALE", .70)
        identite = has("IDENTITE", .68)
        if carte:
            scores["cin"] += 0.40; matches["cin"].append("CARTE")
        if nationale:
            scores["cin"] += 0.35; matches["cin"].append("NATIONALE")
        if identite:
            scores["cin"] += 0.45; matches["cin"].append("IDENTITE")
        if (carte and identite) or phrase("CARTE NATIONALE IDENTITE", .68):
            scores["cin"] += 0.85; matches["cin"].append("CARTE_NATIONALE_IDENTITE")

        # Contexte marocain: ROYAUME/MAROC n'est jamais suffisant à lui seul,
        # car il apparaît aussi sur les passeports et permis.
        if "ROYAUME" in text or "MAROC" in text:
            if scores["cin"] > 0:
                scores["cin"] += 0.10
            if scores["passport"] > 0:
                scores["passport"] += 0.10

        # Exclusion forte: une MRZ + PASSPORT doit battre les signatures communes.
        if scores["passport"] >= 1.0 and (mrz or passport_direct):
            chosen = "passport"
            confidence = min(0.995, 0.86 + 0.08 * min(scores["passport"] / 2.5, 1))
            method = "ocr_signature_passport"
        else:
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            best_label, best_score = ranked[0]
            second_score = ranked[1][1]

            # Une signature métier suffisamment forte prend la priorité.
            strong_thresholds = {
                "cin": 1.25, "permis": 1.35, "rc": 1.35, "passport": 1.0
            }
            if best_score >= strong_thresholds[best_label]:
                chosen = best_label
                margin = best_score - second_score
                confidence = min(0.98, 0.72 + 0.18 * min(margin / 1.0, 1))
                method = "ocr_signature"
            else:
                # Fallback ML uniquement si l'OCR est ambigu.
                feature_vector = self.build_features(fingerprint)
                X = pd.DataFrame([feature_vector], columns=self.feature_names)
                probabilities = self.model.predict_proba(X)[0]
                ml_scores = {}
                for index, probability in enumerate(probabilities):
                    label = self.encoder.inverse_transform([index])[0]
                    ml_scores[label] = float(probability)

                # Petit apport OCR; surtout pas 45% ML comme avant.
                combined = {
                    label: 0.70 * scores[label] + 0.30 * ml_scores.get(label, 0.0)
                    for label in scores
                }
                total = sum(combined.values())
                if total > 0:
                    combined = {k: v / total for k, v in combined.items()}
                chosen = max(combined, key=combined.get)
                confidence = float(combined[chosen]) if combined else 0.0
                method = "ocr_ml_fallback"

                scores = combined

        final_scores = {k: 0.0 for k in scores}
        if chosen in final_scores:
            final_scores[chosen] = float(confidence)

        print("[DEBUG] OCR normalisé :", text[:500])
        print("[INFO] Classification finale :", chosen, f"({confidence:.3f})")
        print("[INFO] Méthode :", method)
        if matches.get(chosen):
            print("[INFO] Signatures :", matches[chosen])

        return {
            "document_type": chosen,
            "confidence": round(float(confidence), 3),
            "scores": {k: round(float(v), 4) for k, v in final_scores.items()},
            "matched_keywords": matches,
            "strong_signatures": matches,
            "method": method,
        }
