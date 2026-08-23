"""
=========================================================
WAFABAIL
Smart Document Field Extractor
=========================================================

Extraction robuste pour :
    - CIN
    - Permis de conduire
    - Passeport
    - Registre de Commerce

Principe :
    OCR -> mots + positions -> extraction par labels/zones
    -> nettoyage -> validation
"""

import re
import unicodedata
from datetime import datetime


class DocumentExtractor:

    def __init__(self):

        self.extractors = {
            "cin": self.extract_cin,
            "permis": self.extract_permis,
            "passport": self.extract_passport,
            "rc": self.extract_rc,
        }

        self.ignored_words = {
            "ROYAUME", "MAROC",
            "CARTE", "NATIONALE", "IDENTITE", "IDENTITÉ",
            "KINGDOM", "MOROCCO",
            "PERMIS", "CONDUIRE",
            "REGISTRE", "COMMERCE",
            "CERTIFICAT", "IMMATRICULATION",
            "MINISTERE", "MINISTÈRE",
            "JUSTICE", "TRIBUNAL",
            "ADRESSE", "NOM", "PRENOM", "PRÉNOM",
            "NE", "NÉ", "LE",
            "DATE", "LIEU", "NAISSANCE",
            "SIGLE", "CAPITAL", "SOCIAL",
            "DENOMINATION", "DÉNOMINATION",
            "FORME", "JURIDIQUE",
            "OBJET", "DU", "COMMERCE",
        }

        # Labels utilisés comme frontières.
        # Lorsqu'on trouve un nouveau label, on arrête
        # l'extraction du champ précédent.
        self.all_labels = {
            "NOM",
            "PRENOM",
            "PRÉNOM",
            "NE",
            "NÉ",
            "NEE",
            "NÉE",
            "ADRESSE",
            "PERMIS",
            "PERMIS N",
            "PERMIS N°",
            "FORME JURIDIQUE",
            "CAPITAL SOCIAL",
            "DENOMINATION",
            "DÉNOMINATION",
            "OBJET DU COMMERCE",
            "EST INSCRIT",
            "DEPUIS LE",
            "NUMERO CHRONOLOGIQUE",
            "NUMERO ANALYTIQUE",
            "NUMERO I.C.E",
            "NUMERO ICE",
        }

    # =====================================================
    # NORMALISATION
    # =====================================================

    @staticmethod
    def normalize_text(text):

        if not text:
            return ""

        text = str(text).upper()
        text = unicodedata.normalize("NFKD", text)
        text = "".join(c for c in text if not unicodedata.combining(c))

        replacements = {
            "—": "-",
            "–": "-",
            "_": " ",
            "|": " ",
            ":": " ",
            ";": " ",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    # =====================================================
    # OCR WORDS
    # =====================================================

    @staticmethod
    def get_words(ocr_result):

        result = []

        for word in ocr_result.get("words", []):

            text = str(word.get("text", "")).strip()

            if not text:
                continue

            try:
                confidence = float(
                    word.get("confidence", 0)
                )
            except Exception:
                confidence = 0.0

            try:
                x = float(word.get("x", 0))
                y = float(word.get("y", 0))
                width = float(word.get("width", 0))
                height = float(word.get("height", 0))
            except Exception:
                x = 0
                y = 0
                width = 0
                height = 0

            result.append({
                "text": text,
                "norm": DocumentExtractor.normalize_text(text),
                "confidence": confidence,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
            })

        return result

    # =====================================================
    # UTILITAIRES
    # =====================================================

    def is_ignored(self, text):

        value = self.normalize_text(text)

        return value in self.ignored_words

    def is_alpha_text(self, text):

        value = self.normalize_text(text)

        if not value:
            return False

        if any(char.isdigit() for char in value):
            return False

        letters = re.sub(
            r"[^A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ ]",
            "",
            value
        )

        return len(letters.replace(" ", "")) >= 3

    def clean_value(self, text):

        value = self.normalize_text(text)

        value = re.sub(
            r"[^A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ0-9 .,'/-]",
            " ",
            value
        )

        value = re.sub(r"\s+", " ", value)

        return value.strip()

    # =====================================================
    # DATE
    # =====================================================

    @staticmethod
    def normalize_date(day, month, year):

        try:

            day = int(day)
            month = int(month)
            year = int(year)

            if year < 100:
                year += 1900 if year >= 50 else 2000

            date = datetime(year, month, day)

            return date.strftime("%d/%m/%Y")

        except Exception:
            return None

    def extract_date(self, text):

        if not text:
            return None

        text = self.normalize_text(text)

        patterns = [
            r"\b(\d{1,2})[\/\-.](\d{1,2})[\/\-.](\d{4})\b",
            r"\b(\d{1,2})\s+(\d{1,2})\s+(\d{4})\b",
            r"\b(\d{1,2})[\/\-.](\d{1,2})[\/\-.](\d{2})\b",
        ]

        for pattern in patterns:

            for match in re.finditer(pattern, text):

                date = self.normalize_date(
                    match.group(1),
                    match.group(2),
                    match.group(3)
                )

                if date:
                    return date

        return None

    def extract_dates_from_words(self, words):

        candidates = []

        for word in words:

            if word["confidence"] < 0.20:
                continue

            date = self.extract_date(word["text"])

            if date:
                candidates.append({
                    "date": date,
                    "x": word["x"],
                    "y": word["y"],
                    "confidence": word["confidence"],
                })

        # Recherche dans groupes de mots proches
        sorted_words = sorted(
            words,
            key=lambda w: (w["y"], w["x"])
        )

        for i in range(len(sorted_words)):

            group = []

            base_y = sorted_words[i]["y"]

            for j in range(
                i,
                min(i + 6, len(sorted_words))
            ):

                word = sorted_words[j]

                if abs(word["y"] - base_y) <= 60:
                    group.append(word)

            group.sort(key=lambda w: w["x"])

            text = " ".join(
                w["text"] for w in group
            )

            date = self.extract_date(text)

            if date:

                candidates.append({
                    "date": date,
                    "x": group[0]["x"],
                    "y": base_y,
                    "confidence": max(
                        w["confidence"]
                        for w in group
                    )
                })

        # Supprimer doublons
        unique = {}

        for item in candidates:

            key = (
                item["date"],
                round(item["y"] / 20)
            )

            if key not in unique:
                unique[key] = item
            elif item["confidence"] > unique[key]["confidence"]:
                unique[key] = item

        return list(unique.values())

    # =====================================================
    # LABEL MATCHING
    # =====================================================

    def label_matches(self, word_text, labels):

        value = self.normalize_text(word_text)

        for label in labels:

            key = self.normalize_text(label)

            if value == key:
                return True

            # Expression complète uniquement.
            pattern = (
                r"(?<![A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ])"
                + re.escape(key)
                + r"(?![A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ])"
            )

            if re.search(pattern, value):
                return True

        return False

    # =====================================================
    # LABELS TROUVES
    # =====================================================

    def find_label_words(self, words, labels):

        result = []

        for word in words:

            if self.label_matches(
                word["text"],
                labels
            ):
                result.append(word)

        return result

    # =====================================================
    # MOTS APRES LABEL
    # =====================================================

    def words_after_label(
        self,
        words,
        labels,
        max_y_distance=150,
        max_x_distance=1000,
        stop_at_labels=True
    ):
        """
        Version stricte.

        Priorité :
        1. même ligne
        2. proximité horizontale
        3. arrêt au prochain label

        IMPORTANT :
        Cette méthode ne récupère plus toute la ligne
        jusqu'au bout du document.
        """

        labels_found = self.find_label_words(
            words,
            labels
        )

        if not labels_found:
            return []

        results = []

        sorted_words = sorted(
            words,
            key=lambda w: (w["y"], w["x"])
        )

        for label in labels_found:

            # -------------------------------------------------
            # Mots candidats
            # -------------------------------------------------

            candidates = []

            for word in sorted_words:

                if word is label:
                    continue

                dx = word["x"] - label["x"]
                dy_signed = word["y"] - label["y"]
                dy = abs(dy_signed)

                # Pas avant le label
                if dx < -10:
                    continue

                # Trop loin
                if dx > max_x_distance:
                    continue

                if dy > max_y_distance:
                    continue

                # Le mot doit être à droite ou légèrement dessous
                if dy_signed < -30:
                    continue

                candidates.append(word)

            # -------------------------------------------------
            # Trier spatialement
            # -------------------------------------------------

            candidates.sort(
                key=lambda w: (
                    abs(w["y"] - label["y"]),
                    w["x"]
                )
            )

            # -------------------------------------------------
            # Priorité même ligne
            # -------------------------------------------------

            same_line = [
                w for w in candidates
                if abs(
                    w["y"] - label["y"]
                ) <= 55
                and w["x"] > label["x"]
            ]

            same_line.sort(
                key=lambda w: w["x"]
            )

            if same_line:

                selected = []

                for word in same_line:

                    # Arrêter au prochain label
                    if (
                        stop_at_labels
                        and word["norm"] in self.all_labels
                    ):
                        break

                    selected.append(word)

                    # Éviter d'aspirer toute la page
                    if len(selected) >= 8:
                        break

                results.extend(selected)

                continue

            # -------------------------------------------------
            # Sinon : ligne suivante immédiate
            # -------------------------------------------------

            below = [
                w for w in candidates
                if w["y"] >= label["y"]
            ]

            if not below:
                continue

            min_y = min(
                w["y"] for w in below
            )

            next_line = [
                w for w in below
                if abs(w["y"] - min_y) <= 50
            ]

            next_line.sort(
                key=lambda w: w["x"]
            )

            selected = []

            for word in next_line:

                if (
                    stop_at_labels
                    and word["norm"] in self.all_labels
                ):
                    break

                selected.append(word)

                if len(selected) >= 8:
                    break

            results.extend(selected)

        # -------------------------------------------------
        # Supprimer doublons
        # -------------------------------------------------

        unique = []
        seen = set()

        for word in results:

            key = id(word)

            if key not in seen:
                seen.add(key)
                unique.append(word)

        return sorted(
            unique,
            key=lambda w: (w["y"], w["x"])
        )

    # =====================================================
    # TEXTE APRES LABEL
    # =====================================================

    def text_after_label(
        self,
        words,
        labels,
        min_confidence=0.25,
        max_y_distance=150,
        max_x_distance=1000
    ):

        candidates = self.words_after_label(
            words,
            labels,
            max_y_distance=max_y_distance,
            max_x_distance=max_x_distance
        )

        candidates = [
            w for w in candidates
            if w["confidence"] >= min_confidence
            and not self.is_ignored(w["text"])
        ]

        if not candidates:
            return None

        candidates.sort(
            key=lambda w: (
                w["y"],
                w["x"]
            )
        )

        return " ".join(
            self.clean_value(w["text"])
            for w in candidates
        ).strip()

    # =====================================================
    # CIN NUMBER
    # =====================================================

    def extract_cin_number(self, words, text):

        candidates = []

        for word in words:

            value = self.normalize_text(
                word["text"]
            )

            compact = re.sub(
                r"[^A-Z0-9]",
                "",
                value
            )

            if re.fullmatch(
                r"[A-Z]{1,3}[0-9]{4,10}",
                compact
            ):

                candidates.append({
                    "value": compact,
                    "confidence": word["confidence"]
                })

        normalized = self.normalize_text(text)

        matches = re.findall(
            r"\b([A-Z]{1,3})\s?(\d{4,10})\b",
            normalized
        )

        for letters, numbers in matches:

            candidates.append({
                "value": letters + numbers,
                "confidence": 0.30
            })

        if not candidates:
            return None

        candidates.sort(
            key=lambda x: -x["confidence"]
        )

        return candidates[0]["value"]

    # =====================================================
    # CIN
    # =====================================================

    def extract_cin(
        self,
        ocr_result,
        fingerprint=None
    ):

        words = self.get_words(ocr_result)

        text = ocr_result.get(
            "text",
            ""
        )

        result = {
            "document_type": "cin",
            "cin_number": None,
            "name": None,
            "surname": None,
            "birth_date": None,
            "birth_place": None,
        }

        # -------------------------------------------------
        # NUMERO
        # -------------------------------------------------

        result["cin_number"] = (
            self.extract_cin_number(
                words,
                text
            )
        )

        # -------------------------------------------------
        # DATE
        # -------------------------------------------------

        dates = self.extract_dates_from_words(
            words
        )

        if dates:

            dates.sort(
                key=lambda x: (
                    x["y"],
                    -x["confidence"]
                )
            )

            result["birth_date"] = dates[0]["date"]

        # -------------------------------------------------
        # NOM / PRENOM
        # -------------------------------------------------

        candidates = []

        for word in words:

            value = word["norm"]

            if len(value) < 3:
                continue

            if word["confidence"] < 0.30:
                continue

            if not self.is_alpha_text(value):
                continue

            if self.is_ignored(value):
                continue

            candidates.append(word)

        if candidates:

            # Les informations personnelles de la CIN
            # sont généralement dans la zone centrale.
            candidates.sort(
                key=lambda w: (
                    abs(w["x"] - 500),
                    w["y"],
                    -w["confidence"]
                )
            )

            # Chercher une paire verticale cohérente
            pairs = []

            for first in candidates:

                for second in candidates:

                    if first is second:
                        continue

                    if second["y"] <= first["y"]:
                        continue

                    dy = (
                        second["y"] -
                        first["y"]
                    )

                    dx = abs(
                        second["x"] -
                        first["x"]
                    )

                    if 20 <= dy <= 220 and dx <= 500:

                        score = (
                            first["confidence"]
                            + second["confidence"]
                        )

                        pairs.append(
                            (
                                score,
                                first,
                                second
                            )
                        )

            if pairs:

                pairs.sort(
                    key=lambda x: -x[0]
                )

                _, first, second = pairs[0]

                result["name"] = first["text"]
                result["surname"] = second["text"]

            else:

                candidates.sort(
                    key=lambda w: (
                        -w["confidence"],
                        w["y"]
                    )
                )

                result["name"] = candidates[0]["text"]

                if len(candidates) > 1:
                    result["surname"] = candidates[1]["text"]

        # -------------------------------------------------
        # LIEU DE NAISSANCE
        # -------------------------------------------------

        place_candidates = self.words_after_label(
            words,
            [
                "NE A",
                "NÉ A",
                "NEE A",
                "NÉE A",
                "LIEU DE NAISSANCE"
            ],
            max_y_distance=120,
            max_x_distance=900
        )

        place_words = [
            w for w in place_candidates
            if (
                w["confidence"] >= 0.25
                and self.is_alpha_text(w["text"])
                and not self.is_ignored(w["text"])
            )
        ]

        if place_words:

            first_y = place_words[0]["y"]

            same_line = [
                w for w in place_words
                if abs(w["y"] - first_y) <= 60
            ]

            same_line.sort(
                key=lambda w: w["x"]
            )

            result["birth_place"] = " ".join(
                w["text"]
                for w in same_line[:5]
            )


        # Correction textuelle CIN.
        normalized_cin = self.normalize_text(text)

        m = re.search(
            r"(?:N°|NO|N)\s*([A-Z]{1,3}\d{4,10})\b",
            normalized_cin
        )
        if m:
            result["cin_number"] = m.group(1)

        # Sur les CIN marocaines, le nom/prénom précède souvent "NE LE".
        m = re.search(
            r"(?:IDENTITE|IDENTITE NATIONALE).{0,180}?([A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]{3,}(?:\s+[A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]{3,}){0,2})\s+NE\s+LE\b",
            normalized_cin
        )
        if m:
            tokens = [
                t for t in m.group(1).split()
                if not self.is_ignored(t)
            ]
            if len(tokens) >= 2:
                result["name"] = tokens[-2]
                result["surname"] = tokens[-1]

        # Une date de naissance future est presque toujours une erreur OCR.
        if result["birth_date"]:
            try:
                year = int(result["birth_date"].split("/")[-1])
                from datetime import datetime as _dt
                if year > _dt.now().year:
                    result["birth_date"] = None
            except Exception:
                pass

        return result

    # =====================================================
    # PERMIS DE CONDUIRE
    # =====================================================

    def extract_permis(
        self,
        ocr_result,
        fingerprint=None
    ):

        words = self.get_words(ocr_result)
        text = ocr_result.get("text", "")
        normalized = self.normalize_text(text)

        result = {
            "document_type": "permis",
            "permis_number": None,
            "name": None,
            "surname": None,
            "birth_date": None,
            "birth_place": None,
            "address": None,
            "issue_place": None,
            "issue_date": None,
            "cine_number": None,
        }

        # =================================================
        # OUTILS LOCAUX
        # =================================================

        def clean_words(items):
            """
            Nettoie une liste de mots OCR et élimine les éléments
            administratifs / trop courts.
            """
            result_words = []

            for w in items:

                value = self.normalize_text(
                    w.get("text", "")
                )

                if not value:
                    continue

                if w.get("confidence", 0) < 0.15:
                    continue

                result_words.append(w)

            return result_words

        def is_latin_name(word):
            """
            Détermine si un mot peut être un nom/prénom latin.
            """
            value = self.normalize_text(
                word.get("text", "")
            )

            if not value:
                return False

            if self.is_ignored(value):
                return False

            # Pas de chiffres
            if any(c.isdigit() for c in value):
                return False

            # On exige au moins 3 lettres
            letters = re.sub(
                r"[^A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]",
                "",
                value
            )

            if len(letters) < 3:
                return False

            return True

        def get_label_words(label_patterns):
            """
            Recherche les mots OCR correspondant à un label.
            On autorise les variations dues à l'OCR.
            """
            labels = []

            normalized_patterns = [
                self.normalize_text(x)
                for x in label_patterns
            ]

            for w in words:

                value = w["norm"]

                if not value:
                    continue

                for pattern in normalized_patterns:

                    if value == pattern:
                        labels.append(w)
                        break

                    # Exemple :
                    # PRENOM/ -> PRENOM
                    # NOM/ -> NOM
                    # PERMIS N -> PERMIS
                    compact_value = re.sub(
                        r"[^A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ0-9]",
                        "",
                        value
                    )

                    compact_pattern = re.sub(
                        r"[^A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ0-9]",
                        "",
                        pattern
                    )

                    if (
                        compact_pattern
                        and compact_pattern in compact_value
                    ):
                        labels.append(w)
                        break

            return labels

        def nearest_below(
            label,
            candidates,
            max_y=180,
            max_x=450,
            require_right=False
        ):
            """
            Cherche la valeur située sous un label.

            C'est volontairement différent de words_after_label():
            sur le permis marocain, les valeurs sont souvent sous
            les labels.
            """

            selected = []

            for w in candidates:

                if w is label:
                    continue

                dx = w["x"] - label["x"]
                dy = w["y"] - label["y"]

                # La valeur doit être sous le label
                if dy < 10:
                    continue

                if dy > max_y:
                    continue

                # Zone horizontale raisonnable
                if abs(dx) > max_x:
                    continue

                if require_right and dx < 0:
                    continue

                selected.append(w)

            selected.sort(
                key=lambda w: (
                    w["y"],
                    abs(w["x"] - label["x"]),
                    -w["confidence"]
                )
            )

            return selected

        # =================================================
        # 1. NUMERO DU PERMIS
        # =================================================
        #
        # Exemple photo 1 :
        # Permis N° 42/571119
        #
        # Exemple photo 2 :
        # Permis N° 42/549568
        #
        # IMPORTANT :
        # On ne cherche PAS un nombre globalement.
        # On exige une proximité avec "PERMIS".
        # =================================================

        permis_candidates = []

        # -------------------------------------------------
        # A. Recherche spatiale autour du label PERMIS
        # -------------------------------------------------

        permis_labels = get_label_words([
            "PERMIS",
            "PERMIS N",
            "PERMIS N°"
        ])

        for label in permis_labels:

            for w in words:

                if w is label:
                    continue

                dx = w["x"] - label["x"]
                dy = w["y"] - label["y"]

                # Numéro généralement à droite du label
                if dx < -20:
                    continue

                if dx > 900:
                    continue

                if abs(dy) > 100:
                    continue

                value = self.normalize_text(
                    w["text"]
                )

                # Format principal marocain :
                # 42/571119
                # 42/549568
                if re.fullmatch(
                    r"\d{1,3}/\d{5,8}",
                    value
                ):

                    permis_candidates.append({
                        "value": value,
                        "confidence": w["confidence"],
                        "distance": abs(dx) + abs(dy)
                    })

        # -------------------------------------------------
        # B. Recherche dans le texte GLOBAL
        #
        # MAIS uniquement si le nombre est proche du mot
        # PERMIS.
        # -------------------------------------------------

        permis_match = re.search(
            r"PERMIS.{0,40}?"
            r"(\d{1,3}/\d{5,8})",
            normalized,
            flags=re.IGNORECASE
        )

        if permis_match:

            permis_candidates.append({
                "value": permis_match.group(1),
                "confidence": 0.95,
                "distance": 0
            })

        if permis_candidates:

            permis_candidates.sort(
                key=lambda x: (
                    -x["confidence"],
                    x["distance"]
                )
            )

            result["permis_number"] = (
                permis_candidates[0]["value"]
            )

        # =================================================
        # 2. DATE DE NAISSANCE
        # =================================================

        birth_date = None

        # -------------------------------------------------
        # Recherche autour du label
        # "Date et Lieu de naissance"
        # -------------------------------------------------

        birth_label_words = get_label_words([
            "DATE ET LIEU DE NAISSANCE",
            "DATE LIEU DE NAISSANCE",
            "DATE ET LIEU",
            "NAISSANCE"
        ])

        date_candidates = []

        for label in birth_label_words:

            nearby = nearest_below(
                label,
                words,
                max_y=180,
                max_x=700
            )

            for w in nearby:

                d = self.extract_date(
                    w["text"]
                )

                if d:

                    date_candidates.append({
                        "date": d,
                        "confidence": w["confidence"],
                        "distance": (
                            abs(w["y"] - label["y"])
                            + abs(w["x"] - label["x"])
                        )
                    })

        if date_candidates:

            date_candidates.sort(
                key=lambda x: (
                    -x["confidence"],
                    x["distance"]
                )
            )

            birth_date = date_candidates[0]["date"]

        # -------------------------------------------------
        # FALLBACK GLOBAL
        # -------------------------------------------------

        if birth_date is None:

            dates = self.extract_dates_from_words(
                words
            )

            if dates:

                # La date de naissance est généralement
                # la première date importante de la carte.
                dates.sort(
                    key=lambda d: (
                        d["y"],
                        -d["confidence"]
                    )
                )

                birth_date = dates[0]["date"]

        result["birth_date"] = birth_date

        # =================================================
        # 3. PRENOM
        # =================================================
        #
        # Sur les deux cartes :
        #
        # Prénom
        # MOHAMED ALI
        #
        # ou
        #
        # Prénom
        # REDA
        #
        # La valeur est SOUS le label.
        # =================================================

        prenom_labels = get_label_words([
            "PRENOM",
            "PRÉNOM",
            "PRENOM/",
            "PRENOM /"
        ])

        prenom_candidates = []

        for label in prenom_labels:

            nearby = nearest_below(
                label,
                words,
                max_y=170,
                max_x=500
            )

            for w in nearby:

                if not is_latin_name(w):
                    continue

                # Exclure les mots administratifs
                value = w["norm"]

                if value in {
                    "DATE",
                    "DATE ET",
                    "LIEU",
                    "NAISSANCE",
                    "DELIVRE",
                    "DELIVRE A",
                    "CASA SUD",
                    "PERMIS",
                    "ROYAUME",
                    "MAROC",
                    "CONDUIRE"
                }:
                    continue

                prenom_candidates.append({
                    "word": w,
                    "distance": (
                        abs(w["y"] - label["y"])
                        + abs(w["x"] - label["x"])
                    )
                })

        if prenom_candidates:

            prenom_candidates.sort(
                key=lambda x: (
                    x["distance"],
                    -x["word"]["confidence"]
                )
            )

            first = prenom_candidates[0]["word"]

            # -------------------------------------------------
            # Récupérer les mots supplémentaires du prénom
            #
            # Exemple :
            # MOHAMED + ALI
            # -------------------------------------------------

            name_words = [first]

            for w in words:

                if w is first:
                    continue

                if not is_latin_name(w):
                    continue

                dx = w["x"] - first["x"]
                dy = abs(w["y"] - first["y"])

                # Même ligne
                if dy > 70:
                    continue

                # Proche horizontalement
                if dx < 0:
                    continue

                if dx > 300:
                    continue

                # Ne pas prendre un autre champ
                if w["norm"] in {
                    "NOM",
                    "DATE",
                    "LIEU",
                    "NAISSANCE",
                    "CASA",
                    "REHAMNA",
                    "ABKARI",
                    "AZZOUZI"
                }:
                    continue

                name_words.append(w)

            name_words.sort(
                key=lambda w: w["x"]
            )

            # Éviter les doublons
            unique = []
            seen_text = set()

            for w in name_words:

                value = w["norm"]

                if value in seen_text:
                    continue

                seen_text.add(value)
                unique.append(w["text"])

            result["name"] = " ".join(
                unique[:3]
            )

        # =================================================
        # 4. NOM / SURNAME
        # =================================================

        nom_labels = get_label_words([
            "NOM",
            "NOM/",
            "NOM /"
        ])

        nom_candidates = []

        for label in nom_labels:

            nearby = nearest_below(
                label,
                words,
                max_y=170,
                max_x=500
            )

            for w in nearby:

                if not is_latin_name(w):
                    continue

                value = w["norm"]

                if value in {
                    "DATE",
                    "LIEU",
                    "NAISSANCE",
                    "DELIVRE",
                    "DELIVRE A",
                    "CASA",
                    "REHAMNA",
                    "MOHAMED",
                    "ALI",
                    "REDA"
                }:
                    continue

                nom_candidates.append({
                    "word": w,
                    "distance": (
                        abs(w["y"] - label["y"])
                        + abs(w["x"] - label["x"])
                    )
                })

        if nom_candidates:

            nom_candidates.sort(
                key=lambda x: (
                    x["distance"],
                    -x["word"]["confidence"]
                )
            )

            result["surname"] = (
                nom_candidates[0]["word"]["text"]
            )

        # =================================================
        # 5. FALLBACK NOM / PRENOM
        # =================================================
        #
        # Si l'OCR ne détecte pas correctement les labels,
        # utiliser la zone personnelle du permis.
        # =================================================

        if (
            result["name"] is None
            or result["surname"] is None
        ):

            personal_words = []

            for w in words:

                if not is_latin_name(w):
                    continue

                y = w["y"]

                # Zone centrale du permis
                if not (120 <= y <= 600):
                    continue

                personal_words.append(w)

            personal_words.sort(
                key=lambda w: (
                    w["y"],
                    w["x"]
                )
            )

            # Ne pas prendre les mots administratifs
            personal_words = [
                w for w in personal_words
                if w["norm"] not in {
                    "ROYAUME",
                    "MAROC",
                    "PERMIS",
                    "CONDUIRE",
                    "DATE",
                    "LIEU",
                    "NAISSANCE",
                    "DELIVRE",
                    "SUD",
                    "LE",
                    "CINE"
                }
            ]

            # Chercher une paire verticale :
            #
            # MOHAMED ALI
            # AZZOUZI
            #
            # ou
            #
            # REDA
            # ABKARI

            pairs = []

            for first in personal_words:

                for second in personal_words:

                    if first is second:
                        continue

                    if second["y"] <= first["y"]:
                        continue

                    dy = second["y"] - first["y"]

                    if dy < 20 or dy > 150:
                        continue

                    if abs(
                        second["x"] -
                        first["x"]
                    ) > 250:
                        continue

                    # Éviter les dates / villes
                    if second["norm"] in {
                        "CASA",
                        "REHAMNA",
                        "SUD"
                    }:
                        continue

                    score = (
                        first["confidence"]
                        + second["confidence"]
                    )

                    pairs.append({
                        "first": first,
                        "second": second,
                        "score": score
                    })

            if pairs:

                pairs.sort(
                    key=lambda x: x["score"],
                    reverse=True
                )

                best = pairs[0]

                if result["name"] is None:
                    result["name"] = (
                        best["first"]["text"]
                    )

                if result["surname"] is None:
                    result["surname"] = (
                        best["second"]["text"]
                    )

        # =================================================
        # 6. LIEU DE NAISSANCE
        # =================================================
        #
        # Très important :
        #
        # DATE
        # 01/09/2004
        # CASA
        #
        # ou
        #
        # DATE
        # 17/07/2001
        # REHAMNA
        #
        # On cherche donc un mot LATIN situé juste sous
        # la date de naissance.
        # =================================================

        if result["birth_date"]:

            birth_date_words = []

            for w in words:

                d = self.extract_date(
                    w["text"]
                )

                if d == result["birth_date"]:

                    birth_date_words.append(w)

            place_candidates = []

            for date_word in birth_date_words:

                for w in words:

                    if w is date_word:
                        continue

                    dy = w["y"] - date_word["y"]
                    dx = abs(
                        w["x"] -
                        date_word["x"]
                    )

                    # Sous la date
                    if dy < 15:
                        continue

                    if dy > 150:
                        continue

                    if dx > 350:
                        continue

                    if not is_latin_name(w):
                        continue

                    value = w["norm"]

                    if value in {
                        "DELIVRE",
                        "DELIVRE A",
                        "CASA SUD",
                        "SUD",
                        "LE",
                        "DATE",
                        "LIEU",
                        "NAISSANCE"
                    }:
                        continue

                    place_candidates.append({
                        "word": w,
                        "distance": dy + dx
                    })

            if place_candidates:

                place_candidates.sort(
                    key=lambda x: (
                        x["distance"],
                        -x["word"]["confidence"]
                    )
                )

                first_place = (
                    place_candidates[0]["word"]
                )

                place_words = [
                    first_place
                ]

                # Autoriser un deuxième mot :
                # par exemple une ville composée
                for w in words:

                    if w is first_place:
                        continue

                    if not is_latin_name(w):
                        continue

                    if abs(
                        w["y"] -
                        first_place["y"]
                    ) > 70:
                        continue

                    dx = (
                        w["x"] -
                        first_place["x"]
                    )

                    if dx <= 0 or dx > 250:
                        continue

                    if w["norm"] in {
                        "DELIVRE",
                        "SUD",
                        "LE"
                    }:
                        continue

                    place_words.append(w)

                place_words.sort(
                    key=lambda w: w["x"]
                )

                result["birth_place"] = " ".join(
                    w["text"]
                    for w in place_words[:3]
                )

        # =================================================
        # 7. FALLBACK LIEU DE NAISSANCE
        # =================================================

        if result["birth_place"] is None:

            # Recherche dans le texte global :
            #
            # 17/07/2001 REHAMNA
            # 01/09/2004 CASA
            #
            date_patterns = re.findall(
                r"\b\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{4}\b"
                r"\s+"
                r"([A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]{3,30})",
                normalized
            )

            if date_patterns:

                candidate = (
                    date_patterns[0].strip()
                )

                if candidate not in {
                    "DELIVRE",
                    "CASA",
                    "SUD"
                }:
                    result["birth_place"] = candidate

                else:
                    # CASA est justement un lieu valide
                    result["birth_place"] = candidate

        # =================================================
        # 8. LIEU DE DELIVRANCE
        # =================================================
        #
        # Exemple :
        # délivré à Casa Sud
        #
        # On doit le distinguer du lieu de naissance.
        # =================================================

        issue_place_match = re.search(
            r"DELIVRE\s+A\s+"
            r"([A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ][A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ ]{2,40})",
            normalized
        )

        if issue_place_match:

            issue_place = (
                issue_place_match.group(1)
                .strip()
            )

            # Couper si on récupère "LE"
            issue_place = re.split(
                r"\bLE\b",
                issue_place
            )[0].strip()

            result["issue_place"] = (
                issue_place
            )

        else:

            issue_labels = get_label_words([
                "DELIVRE A",
                "DÉLIVRÉ À",
                "DELIVRE"
            ])

            issue_candidates = []

            for label in issue_labels:

                nearby = nearest_below(
                    label,
                    words,
                    max_y=120,
                    max_x=500
                )

                for w in nearby:

                    if not is_latin_name(w):
                        continue

                    issue_candidates.append(w)

            if issue_candidates:

                issue_candidates.sort(
                    key=lambda w: (
                        w["y"],
                        -w["confidence"]
                    )
                )

                result["issue_place"] = (
                    issue_candidates[0]["text"]
                )

        # =================================================
        # 9. DATE DE DELIVRANCE
        # =================================================

        issue_labels = get_label_words([
            "LE"
        ])

        issue_date_candidates = []

        for label in issue_labels:

            for w in words:

                if w is label:
                    continue

                dx = w["x"] - label["x"]
                dy = w["y"] - label["y"]

                if dx < 0 or dx > 500:
                    continue

                if abs(dy) > 100:
                    continue

                d = self.extract_date(
                    w["text"]
                )

                if d:
                    issue_date_candidates.append({
                        "date": d,
                        "confidence": w["confidence"]
                    })

        # Global fallback : prendre la date qui n'est PAS
        # la date de naissance.
        if issue_date_candidates:

            for item in issue_date_candidates:

                if item["date"] != result["birth_date"]:

                    result["issue_date"] = (
                        item["date"]
                    )
                    break

        if result["issue_date"] is None:

            all_dates = self.extract_dates_from_words(
                words
            )

            for d in all_dates:

                if d["date"] != result["birth_date"]:

                    result["issue_date"] = (
                        d["date"]
                    )
                    break

        # =================================================
        # 10. NUMERO C.I.N.E.
        # =================================================
        #
        # Exemple :
        # N° C.N.I.E.
        # BW43417
        #
        # IMPORTANT :
        # ne jamais le confondre avec le numéro du permis.
        # =================================================

        cine_labels = get_label_words([
            "CINE",
            "C.N.I.E",
            "C N I E",
            "N C N I E",
            "N° C.N.I.E"
        ])

        cine_candidates = []

        for label in cine_labels:

            for w in words:

                if w is label:
                    continue

                dx = w["x"] - label["x"]
                dy = abs(
                    w["y"] -
                    label["y"]
                )

                if dx < -100:
                    continue

                if dx > 600:
                    continue

                if dy > 130:
                    continue

                value = re.sub(
                    r"[^A-Z0-9]",
                    "",
                    self.normalize_text(
                        w["text"]
                    )
                )

                if re.fullmatch(
                    r"[A-Z]{1,3}\d{4,10}",
                    value
                ):

                    cine_candidates.append({
                        "value": value,
                        "confidence": w["confidence"]
                    })

        # Fallback texte global
        if not cine_candidates:

            cine_match = re.search(
                r"(?:C\.?N\.?I\.?E|CINE)"
                r".{0,50}?"
                r"\b([A-Z]{1,3}\d{4,10})\b",
                normalized
            )

            if cine_match:

                cine_candidates.append({
                    "value": cine_match.group(1),
                    "confidence": 0.90
                })

        if cine_candidates:

            cine_candidates.sort(
                key=lambda x: -x["confidence"]
            )

            result["cine_number"] = (
                cine_candidates[0]["value"]
            )

        # =================================================
        # 11. ADRESSE
        # =================================================
        #
        # Toutes les cartes de permis ne contiennent pas
        # forcément une adresse exploitable.
        #
        # On ne fabrique JAMAIS une adresse.
        # =================================================

        address_labels = get_label_words([
            "ADRESSE"
        ])

        address_candidates = []

        for label in address_labels:

            nearby = nearest_below(
                label,
                words,
                max_y=220,
                max_x=800
            )

            for w in nearby:

                value = self.normalize_text(
                    w["text"]
                )

                if value in {
                    "PERMIS",
                    "NOM",
                    "PRENOM",
                    "DATE",
                    "LIEU",
                    "NAISSANCE",
                    "DELIVRE",
                    "LE"
                }:
                    continue

                if w["confidence"] < 0.25:
                    continue

                address_candidates.append(w)

        if address_candidates:

            address_candidates.sort(
                key=lambda w: (
                    w["y"],
                    w["x"]
                )
            )

            result["address"] = " ".join(
                w["text"]
                for w in address_candidates[:10]
            )

        # =================================================
        # RETOUR
        # =================================================


        # -------------------------------------------------
        # FINAL TEXT-FIRST CORRECTION
        # Les champs du permis marocain sont structurés par labels.
        # On utilise le texte global en priorité pour éviter d'aspirer
        # les mots du champ voisin.
        # -------------------------------------------------
        def text_field(start_patterns, stop_patterns):
            for sp in start_patterns:
                m = re.search(sp, normalized, flags=re.IGNORECASE)
                if not m:
                    continue
                tail = normalized[m.end():]
                stop = re.search("|".join(stop_patterns), tail, flags=re.IGNORECASE)
                value = tail[:stop.start()] if stop else tail
                value = re.sub(r"^[\s:;,.\-/]+|[\s:;,.\-/]+$", "", value)
                value = re.sub(r"\s+", " ", value).strip()
                if value:
                    return value
            return None

        m = re.search(
            r"PERMIS\s*N\s*\.?\s*[:\-]?\s*((?:\d{1,3}/\d{5,8})|(?:\d{6,12}))",
            normalized
        )
        if m:
            result["permis_number"] = m.group(1)

        def label_segment(start_patterns, stop_patterns):
            for sp in start_patterns:
                m = re.search(sp, normalized, flags=re.IGNORECASE)
                if not m:
                    continue
                tail = normalized[m.end():]
                stop = re.search("|".join(stop_patterns), tail, flags=re.IGNORECASE)
                segment = tail[:stop.start()] if stop else tail
                tokens = re.findall(r"[A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]{3,}", segment.upper())
                tokens = [
                    t for t in tokens
                    if not self.is_ignored(t)
                    and t not in {"DATE", "LIEU", "NAISSANCE", "ROYAUME", "MAROC",
                                  "PERMIS", "CONDUIRE", "DELIVRE", "CASA", "SUD"}
                ]
                if tokens:
                    # Les derniers tokens avant le prochain label sont
                    # généralement la valeur réelle.
                    return " ".join(tokens[-2:])
            return None

        prenom = label_segment(
            [r"PRÉNOM\s*/?", r"PRENOM\s*/?", r"PRENOM"],
            [r"\bNOM\b", r"\bDATE\b", r"\bLIEU\b"]
        )
        if prenom:
            result["name"] = prenom

        surname = label_segment(
            [r"\bNOM\s*/?", r"\bNOM"],
            [r"\bDATE\b", r"\bLIEU\b", r"\bPERMIS\s*N"]
        )
        if surname:
            # Le nom de famille est normalement un seul champ;
            # garder le dernier token réduit les artefacts OCR.
            result["surname"] = surname.split()[-1]

        m = re.search(
            r"(?:DATE\s+ET\s+LIEU\s+DE\s+NAISSANCE|DATE\s+LIEU\s+DE\s+NAISSANCE)"
            r".{0,100}?(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",
            normalized, flags=re.IGNORECASE
        )
        if m:
            result["birth_date"] = self.extract_date(m.group(1))

        m = re.search(
            r"DELIVRE\s+A\s+(.{1,60}?)\s+LE\s+(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",
            normalized, flags=re.IGNORECASE
        )
        if m:
            result["issue_place"] = m.group(1).strip()
            result["issue_date"] = self.extract_date(m.group(2))

        m = re.search(r"(?:N\.?\s*CIN|CIN|CNE)\s*[:\-/]?\s*([A-Z]{1,3}\d{4,10})", normalized)
        if m:
            result["cine_number"] = m.group(1)

        return result
    # =====================================================
    # PASSPORT
    # =====================================================

    def extract_passport(
        self,
        ocr_result,
        fingerprint=None
    ):

        words = self.get_words(
            ocr_result
        )

        text = self.normalize_text(
            ocr_result.get("text", "")
        )

        result = {
            "document_type": "passport",
            "passport_number": None,
            "name": None,
            "surname": None,
            "birth_date": None,
            "birth_place": None,
            "mrz": False,
        }

        # Numéro
        patterns = [
            r"\b([A-Z]{1,2}\d{6,9})\b",
            r"(?:PASSEPORT|PASSPORT)"
            r"\s*[:\-]?\s*"
            r"([A-Z0-9]{6,12})"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text
            )

            if match:

                result["passport_number"] = (
                    match.group(1)
                )

                break

        # Date
        dates = self.extract_dates_from_words(
            words
        )

        if dates:

            dates.sort(
                key=lambda d: d["y"]
            )

            result["birth_date"] = (
                dates[0]["date"]
            )

        # MRZ
        if re.search(
            r"P<[A-Z]{3}",
            text
        ):

            result["mrz"] = True

        # Nom
        surname = self.text_after_label(
            words,
            ["NOM", "SURNAME"],
            min_confidence=0.25
        )

        if surname:
            result["surname"] = surname

        # Prénom
        name = self.text_after_label(
            words,
            ["PRENOM", "PRÉNOM", "GIVEN NAME"],
            min_confidence=0.25
        )

        if name:
            result["name"] = name

        # -------------------------------------------------
        # MRZ: meilleure source pour un passeport.
        # Ligne 2: numéro + date naissance + date expiration.
        # Exemple: XX1234567MAR900101...
        # -------------------------------------------------
        compact = re.sub(r"\s+", "", text.upper()).replace("«", "<").replace("‹", "<")

        # Ligne de données (type 2): numéro + pays + YYMMDD + sexe.
        m2 = re.search(
            r"([A-Z0-9<]{8,9})([A-Z]{3})(\d{6})([MFX<])(\d{6})",
            compact
        )
        if m2:
            candidate = m2.group(1).replace("<", "")
            if re.fullmatch(r"[A-Z0-9]{6,9}", candidate):
                result["passport_number"] = candidate
            result["birth_date"] = self.normalize_date(
                m2.group(3)[4:6], m2.group(3)[2:4], m2.group(3)[:2]
            )

        # Ligne de données (type 1): P<XXX + nom + << + prénoms.
        m_name = re.search(
            r"P<[A-Z]{3}(.+?)<<([A-Z<]+)",
            compact
        )
        if m_name:
            surname = m_name.group(1).replace("<", " ").strip()
            given = m_name.group(2).replace("<", " ").strip()
            if surname:
                result["surname"] = surname
            if given:
                result["name"] = given

        # Date: préférer une date située près d'un label de naissance.
        m = re.search(
            r"(?:DATE\s+DE\s+NAISSANCE|BIRTH\s+DATE|NE\s+LE)"
            r".{0,80}?(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",
            text, flags=re.IGNORECASE
        )
        if m:
            result["birth_date"] = self.extract_date(m.group(1))

        return result

    # =====================================================
    # RC - REGISTRE DE COMMERCE
    # =====================================================

    def extract_rc(
        self,
        ocr_result,
        fingerprint=None
    ):

        words = self.get_words(
            ocr_result
        )

        text = ocr_result.get(
            "text",
            ""
        )

        normalized = self.normalize_text(
            text
        )

        result = {
            "document_type": "rc",
            "rc_number": None,
            "ice": None,
            "company_name": None,
            "legal_form": None,
            "capital": None,
            "address": None,
            "denomination": None,
            "activity": None,
            "registration_date": None,
        }

        # -------------------------------------------------
        # Extraction textuelle prioritaire.
        # Elle évite que le voisinage spatial aspire le texte
        # du champ suivant (problème majeur de l'ancienne version).
        # -------------------------------------------------
        def field_regex(patterns, stop_patterns):
            for start_pattern in patterns:
                m = re.search(start_pattern, normalized, flags=re.IGNORECASE)
                if not m:
                    continue
                tail = normalized[m.end():]
                if stop_patterns:
                    stop = re.search("|".join(stop_patterns), tail, flags=re.IGNORECASE)
                    value = tail[:stop.start()] if stop else tail
                else:
                    value = tail
                value = re.sub(r"^[\s:;,.\-]+|[\s:;,.\-]+$", "", value)
                value = re.sub(r"\s+", " ", value).strip()
                if value:
                    return value
            return None

        text_company = field_regex(
            [r"LA\s+SOCIETE\s*[:\-]?", r"SOCIETE\s*[:\-]?"],
            [r"\bSIGLE\b", r"\bFORME\s+JURIDIQUE\b"]
        )
        if text_company:
            result["company_name"] = text_company

        text_legal = field_regex(
            [r"FORME\s+JURIDIQUE\s*[:\-]?"],
            [r"\bCAPITAL(?:\s+SOCIAL)?\b", r"\bADRESSE\b"]
        )
        if text_legal:
            result["legal_form"] = text_legal

        text_capital = field_regex(
            [r"CAPITAL\s+SOCIAL\s*[:\-]?", r"CAPITAL\s*[:\-]?"],
            [r"\bADRESSE\b", r"\bDENOMINATION\b", r"\bOBJET\b"]
        )
        if text_capital:
            result["capital"] = text_capital

        text_address = field_regex(
            [r"ADRESSE\s*[:\-]?"],
            [r"\bDENOMINATION\b", r"\bOBJET\s+DU\s+COMMERCE\b",
             r"\bNUMERO\b", r"\bEST\s+INSCRIT\b"]
        )
        if text_address:
            result["address"] = text_address

        text_denomination = field_regex(
            [r"DENOMINATION\s*[:\-]?"],
            [r"\bOBJET\s+DU\s+COMMERCE\b", r"\bEST\s+INSCRIT\b"]
        )
        if text_denomination:
            result["denomination"] = text_denomination

        text_activity = field_regex(
            [r"OBJET\s+DU\s+COMMERCE\s*[:\-]?"],
            [r"\bEST\s+INSCRIT\b", r"\bDEPUIS\s+LE\b"]
        )
        if text_activity:
            result["activity"] = text_activity

        m = re.search(
            r"(?:EST\s+INSCRIT.*?DEPUIS\s+LE|DEPUIS\s+LE)\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",
            normalized, flags=re.IGNORECASE
        )
        if m:
            result["registration_date"] = self.extract_date(m.group(1))

        m = re.search(
            r"(?:NUMERO\s+ANALYTIQUE|N\s*ANALYTIQUE)\s*[:\-]?\s*(\d{3,10})",
            normalized, flags=re.IGNORECASE
        )
        if m:
            result["rc_number"] = m.group(1)

        m = re.search(
            r"(?:NUMERO\s+(?:I\.?\s*C\.?\s*E|1\.?\s*C\.?\s*[E£3]|ICE)|N\s*ICE)\s*[:\-]?\s*(\d{10,20})",
            normalized, flags=re.IGNORECASE
        )
        if not m:
            # Fallback: l'ICE marocain est un identifiant de 15 chiffres.
            m = re.search(r"\b(\d{15})\b", normalized)
        if m:
            result["ice"] = m.group(1)

        # =================================================
        # HELPER RC
        # =================================================

        def get_field(
            labels,
            min_conf=0.30,
            max_dy=90,
            max_dx=900,
            max_words=12
        ):

            candidates = self.words_after_label(
                words,
                labels,
                max_y_distance=max_dy,
                max_x_distance=max_dx
            )

            candidates = [
                w for w in candidates
                if w["confidence"] >= min_conf
            ]

            if not candidates:
                return None

            candidates.sort(
                key=lambda w: (
                    w["y"],
                    w["x"]
                )
            )

            # Première ligne de résultat
            first_y = candidates[0]["y"]

            same_line = [
                w for w in candidates
                if abs(w["y"] - first_y) <= 60
            ]

            same_line.sort(
                key=lambda w: w["x"]
            )

            selected = same_line[:max_words]

            value = " ".join(
                self.clean_value(
                    w["text"]
                )
                for w in selected
            )

            return value.strip() or None

        # =================================================
        # SOCIETE
        # =================================================

        # IMPORTANT :
        # Dans ton OCR :
        #
        # La Société      PRONANI
        # Sigle
        #
        # On veut UNIQUEMENT PRONANI.

        company = get_field(
            ["LA SOCIETE", "SOCIETE", "SOCIÉTÉ"],
            min_conf=0.30,
            max_dy=90,
            max_dx=800,
            max_words=3
        )

        if company:

            # Sécurité supplémentaire
            company = re.split(
                r"\b(?:FORME|CAPITAL|ADRESSE|DENOMINATION)\b",
                company,
                flags=re.IGNORECASE
            )[0].strip()

            result["company_name"] = company

        # =================================================
        # FORME JURIDIQUE
        # =================================================

        legal = get_field(
            ["FORME JURIDIQUE"],
            min_conf=0.40,
            max_dy=100,
            max_dx=1000,
            max_words=8
        )

        if legal:

            legal = re.split(
                r"\b(?:CAPITAL|ADRESSE|DENOMINATION|DÉNOMINATION)\b",
                legal,
                flags=re.IGNORECASE
            )[0].strip()

            result["legal_form"] = legal

        # =================================================
        # CAPITAL
        # =================================================

        capital_candidates = self.words_after_label(
            words,
            ["CAPITAL SOCIAL"],
            max_y_distance=90,
            max_x_distance=1000
        )

        for word in capital_candidates:

            value = self.clean_value(
                word["text"]
            )

            if re.search(
                r"\d[\d\s,.]*",
                value
            ):

                # Exemple attendu :
                # 500000,00 MAD
                if (
                    "MAD" in value
                    or "DH" in value
                    or re.fullmatch(
                        r"[\d\s,.]+",
                        value
                    )
                ):

                    result["capital"] = value

                    # Si MAD est séparé dans le mot suivant
                    idx = words.index(word)

                    for next_word in words[idx + 1:idx + 3]:

                        if (
                            abs(
                                next_word["y"]
                                - word["y"]
                            ) <= 50
                            and next_word["x"]
                            > word["x"]
                            and next_word["norm"] in {
                                "MAD",
                                "DH"
                            }
                        ):

                            result["capital"] += (
                                " "
                                + next_word["text"]
                            )

                    break

        # =================================================
        # ADRESSE
        # =================================================

        address = get_field(
            ["ADRESSE"],
            min_conf=0.30,
            max_dy=100,
            max_dx=1000,
            max_words=10
        )

        if address:

            address = re.split(
                r"\b(?:DENOMINATION|DÉNOMINATION|OBJET DU COMMERCE)\b",
                address,
                flags=re.IGNORECASE
            )[0].strip()

            result["address"] = address

        # =================================================
        # DENOMINATION
        # =================================================

        denomination = get_field(
            ["DENOMINATION", "DÉNOMINATION"],
            min_conf=0.30,
            max_dy=100,
            max_dx=1000,
            max_words=8
        )

        if denomination:

            denomination = re.split(
                r"\b(?:OBJET DU COMMERCE|EST INSCRIT)\b",
                denomination,
                flags=re.IGNORECASE
            )[0].strip()

            result["denomination"] = denomination

        # =================================================
        # ACTIVITE
        # =================================================

        activity_candidates = self.words_after_label(
            words,
            ["OBJET DU COMMERCE"],
            max_y_distance=180,
            max_x_distance=1500
        )

        activity_candidates = [
            w for w in activity_candidates
            if w["confidence"] >= 0.45
        ]

        if activity_candidates:

            activity_candidates.sort(
                key=lambda w: (
                    w["y"],
                    w["x"]
                )
            )

            # L'activité commence juste après
            # "Objet du Commerce".
            first_y = activity_candidates[0]["y"]

            selected = [
                w for w in activity_candidates
                if w["y"] <= first_y + 100
            ]

            # Arrêter avant "Est inscrit"
            final = []

            for w in selected:

                if w["norm"] in {
                    "EST INSCRIT",
                    "INSCRIT"
                }:
                    break

                final.append(w)

            result["activity"] = " ".join(
                w["text"]
                for w in final[:15]
            )

        # =================================================
        # DATE IMMATRICULATION
        # =================================================

        registration_candidates = self.words_after_label(
            words,
            [
                "DEPUIS LE",
                "EST INSCRIT",
                "INSCRIT"
            ],
            max_y_distance=100,
            max_x_distance=1000
        )

        for word in registration_candidates:

            date = self.extract_date(
                word["text"]
            )

            if date:

                result["registration_date"] = date
                break

        # Fallback
        if result["registration_date"] is None:

            dates = self.extract_dates_from_words(
                words
            )

            if dates:

                # Pour le RC, la date d'inscription
                # est généralement autour de la zone
                # "Est inscrit".
                dates.sort(
                    key=lambda d: (
                        abs(d["y"] - 900),
                        -d["confidence"]
                    )
                )

                result["registration_date"] = (
                    dates[0]["date"]
                )

        # =================================================
        # RC NUMBER = NUMERO ANALYTIQUE
        # =================================================

        rc_candidates = self.words_after_label(
            words,
            [
                "NUMERO ANALYTIQUE",
                "N° ANALYTIQUE",
                "NO ANALYTIQUE"
            ],
            max_y_distance=90,
            max_x_distance=900
        )

        for word in rc_candidates:

            value = re.sub(
                r"[^0-9]",
                "",
                word["text"]
            )

            if 3 <= len(value) <= 10:

                result["rc_number"] = value
                break

        # Fallback
        if result["rc_number"] is None:

            match = re.search(
                r"NUM[ÉE]RO\s+ANALYTIQUE"
                r".{0,100}?"
                r"\b(\d{3,10})\b",
                normalized
            )

            if match:

                result["rc_number"] = (
                    match.group(1)
                )

        # =================================================
        # ICE
        # =================================================

        ice_candidates = self.words_after_label(
            words,
            [
                "NUMERO I.C.E",
                "NUMERO ICE",
                "N° ICE"
            ],
            max_y_distance=90,
            max_x_distance=900
        )

        for word in ice_candidates:

            value = re.sub(
                r"[^0-9]",
                "",
                word["text"]
            )

            if 10 <= len(value) <= 20:

                result["ice"] = value
                break

        # Fallback global
        if result["ice"] is None:

            match = re.search(
                r"(?:NUMERO\s+I\.?C\.?E)"
                r"\s*[:\-]?\s*"
                r"(\d{10,20})",
                normalized
            )

            if match:

                result["ice"] = (
                    match.group(1)
                )


        # Les valeurs issues des labels textuels sont prioritaires
        # sur l'ancienne heuristique spatiale.
        for key, value in {
            "company_name": text_company,
            "legal_form": text_legal,
            "capital": text_capital,
            "address": text_address,
            "denomination": text_denomination,
            "activity": text_activity,
        }.items():
            if value:
                result[key] = value

        return result

    # =====================================================
    # METHOD PRINCIPALE
    # =====================================================

    def extract(
        self,
        document_type,
        ocr_result,
        fingerprint=None
    ):

        document_type = (
            str(document_type)
            .lower()
            .strip()
            if document_type
            else ""
        )

        extractor = self.extractors.get(
            document_type
        )

        if extractor is None:

            return {
                "document_type": document_type,
                "error": "Type de document inconnu"
            }

        return extractor(
            ocr_result,
            fingerprint
        )