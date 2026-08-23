"""
=========================================================
DocAI Morocco
Document Field Extractor
=========================================================

Extraction robuste des champs importants :

- CIN
- Permis de conduire
- Passeport
- Registre de Commerce

Particularités :
- tolérance aux erreurs OCR
- extraction basée sur texte + positions
- détection renforcée des numéros CIN
- filtrage des faux noms OCR
- détection améliorée des dates
- détection du lieu de naissance
=========================================================
"""

import re
from datetime import datetime


class DocumentExtractor:

    def __init__(self):

        self.extractors = {
            "cin": self.extract_cin,
            "permis": self.extract_permis,
            "passport": self.extract_passport,
            "rc": self.extract_rc
        }

    # =====================================================
    # NORMALISATION
    # =====================================================

    @staticmethod
    def normalize_text(text):

        if not text:
            return ""

        text = str(text).upper()

        replacements = {
            "—": "-",
            "–": "-",
            "_": " ",
            "|": " ",
            ":": " ",
            "\n": " "
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    # =====================================================
    # MOTS OCR
    # =====================================================

    @staticmethod
    def get_words(ocr_result):

        words = ocr_result.get(
            "words",
            []
        )

        result = []

        for word in words:

            text = word.get(
                "text",
                ""
            )

            if not text:
                continue

            try:
                confidence = float(
                    word.get(
                        "confidence",
                        0
                    )
                )
            except Exception:
                confidence = 0.0

            try:
                x = float(
                    word.get(
                        "x",
                        0
                    )
                )

                y = float(
                    word.get(
                        "y",
                        0
                    )
                )

                width = float(
                    word.get(
                        "width",
                        0
                    )
                )

                height = float(
                    word.get(
                        "height",
                        0
                    )
                )

            except Exception:

                x = 0.0
                y = 0.0
                width = 0.0
                height = 0.0

            result.append({

                "text":
                    str(text).strip(),

                "confidence":
                    confidence,

                "x":
                    x,

                "y":
                    y,

                "width":
                    width,

                "height":
                    height
            })

        return result

    # =====================================================
    # DATE
    # =====================================================

    @staticmethod
    def normalize_date(
        day,
        month,
        year
    ):

        try:

            day = int(day)
            month = int(month)
            year = int(year)

            if year < 100:
                year += 2000

            if not (
                1 <= day <= 31
                and
                1 <= month <= 12
                and
                1900 <= year <= 2100
            ):
                return None

            date = datetime(
                year,
                month,
                day
            )

            return date.strftime(
                "%d/%m/%Y"
            )

        except (
            ValueError,
            TypeError
        ):

            return None

    # =====================================================
    # VALIDATION DATE
    # =====================================================

    @staticmethod
    def is_valid_date(
        date_string
    ):

        if not date_string:
            return False

        try:

            datetime.strptime(
                date_string,
                "%d/%m/%Y"
            )

            return True

        except ValueError:

            return False

    # =====================================================
    # EXTRACTION DATE
    # =====================================================

    def extract_date(
        self,
        text
    ):

        if not text:
            return None

        text = self.normalize_text(
            text
        )

        patterns = [

            # 29/11/1978
            r"\b(\d{1,2})[\/\-.](\d{1,2})[\/\-.](\d{4})\b",

            # 29 11 1978
            r"\b(\d{1,2})\s+(\d{1,2})\s+(\d{4})\b",

            # OCR : 29 0 1978
            r"\b(\d{1,2})\s+[O0]\s+(\d{4})\b",

            # OCR : 29 O 1978
            r"\b(\d{1,2})\s+[OQ]\s+(\d{4})\b"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text
            )

            if not match:
                continue

            if len(match.groups()) == 3:

                date = self.normalize_date(
                    match.group(1),
                    match.group(2),
                    match.group(3)
                )

                if date:
                    return date

        return None

    # =====================================================
    # DATE À PARTIR DES MOTS OCR
    # =====================================================

    def extract_date_from_words(
        self,
        words,
        min_confidence=0.25
    ):

        if not words:
            return None

        valid_words = [
            w for w in words
            if w["confidence"] >= min_confidence
        ]

        if not valid_words:
            return None

        # -------------------------------------------------
        # 1. Un seul bloc
        # -------------------------------------------------

        for word in valid_words:

            date = self.extract_date(
                word["text"]
            )

            if date:
                return date

        # -------------------------------------------------
        # 2. Texte global
        # -------------------------------------------------

        global_text = " ".join(
            w["text"]
            for w in valid_words
        )

        date = self.extract_date(
            global_text
        )

        if date:
            return date

        # -------------------------------------------------
        # 3. Groupes spatiaux
        # -------------------------------------------------

        sorted_words = sorted(
            valid_words,
            key=lambda w: (
                w["y"],
                w["x"]
            )
        )

        for i, current in enumerate(
            sorted_words
        ):

            group = [
                current
            ]

            for j in range(
                i + 1,
                min(
                    i + 7,
                    len(sorted_words)
                )
            ):

                candidate = (
                    sorted_words[j]
                )

                vertical_distance = abs(
                    candidate["y"]
                    -
                    current["y"]
                )

                max_vertical = max(
                    current["height"] * 1.8,
                    70
                )

                if (
                    vertical_distance
                    >
                    max_vertical
                ):
                    continue

                horizontal_distance = abs(
                    candidate["x"]
                    -
                    current["x"]
                )

                if (
                    horizontal_distance
                    <= 800
                ):

                    group.append(
                        candidate
                    )

            group = sorted(
                group,
                key=lambda w: w["x"]
            )

            candidate_text = " ".join(
                w["text"]
                for w in group
            )

            date = self.extract_date(
                candidate_text
            )

            if date:
                return date

        # -------------------------------------------------
        # 4. Trois blocs numériques
        # -------------------------------------------------

        numeric_words = []

        for word in valid_words:

            cleaned = re.sub(
                r"[^0-9OQ]",
                "",
                word["text"].upper()
            )

            if cleaned:

                numeric_words.append(
                    (
                        word,
                        cleaned
                    )
                )

        numeric_words = sorted(
            numeric_words,
            key=lambda item: (
                item[0]["y"],
                item[0]["x"]
            )
        )

        for i in range(
            len(numeric_words)
        ):

            group = numeric_words[
                i:i + 3
            ]

            if len(group) < 3:
                continue

            parts = [
                item[1]
                for item in group
            ]

            parts = [
                part.replace(
                    "O",
                    "0"
                ).replace(
                    "Q",
                    "0"
                )
                for part in parts
            ]

            if (
                len(parts[0]) in (1, 2)
                and
                len(parts[1]) in (1, 2)
                and
                len(parts[2]) == 4
            ):

                date = self.normalize_date(
                    parts[0],
                    parts[1],
                    parts[2]
                )

                if date:
                    return date

        return None

    # =====================================================
    # CORRECTION OCR CIN
    # =====================================================

    @staticmethod
    def clean_cin_candidate(
        value
    ):

        if not value:
            return None

        value = (
            str(value)
            .upper()
            .strip()
        )

        # Supprimer espaces et séparateurs
        value = re.sub(
            r"[\s\-_/.:]",
            "",
            value
        )

        # Corrections OCR uniquement
        # dans la partie numérique
        match = re.match(
            r"^([A-Z]{1,3})(.*)$",
            value
        )

        if not match:
            return None

        letters = match.group(1)
        numbers = match.group(2)

        numbers = (
            numbers
            .replace("O", "0")
            .replace("Q", "0")
            .replace("D", "0")
            .replace("I", "1")
            .replace("L", "1")
        )

        candidate = (
            letters
            +
            numbers
        )

        return candidate

    # =====================================================
    # NUMÉRO CIN
    # =====================================================

    def extract_cin_number(
        self,
        text,
        words=None
    ):

        if not text:
            return None

        normalized = self.normalize_text(
            text
        )

        candidates = []

        # -------------------------------------------------
        # 1. Format classique
        # -------------------------------------------------

        patterns = [

            r"\b([A-Z]{1,3})\s*[- ]?\s*(\d{5,8})\b",

            r"\b([A-Z]{1,3})([0-9OQDI L]{5,10})\b"

        ]

        for pattern in patterns:

            matches = re.findall(
                pattern,
                normalized
            )

            for match in matches:

                if isinstance(
                    match,
                    tuple
                ):

                    value = (
                        match[0]
                        +
                        match[1]
                    )

                else:

                    value = match

                candidate = (
                    self.clean_cin_candidate(
                        value
                    )
                )

                if candidate is None:
                    continue

                if re.match(
                    r"^[A-Z]{1,3}\d{5,8}$",
                    candidate
                ):

                    candidates.append(
                        candidate
                    )

        # -------------------------------------------------
        # 2. Recherche dans chaque mot OCR
        # -------------------------------------------------

        if words:

            for word in words:

                raw = word.get(
                    "text",
                    ""
                )

                candidate = (
                    self.clean_cin_candidate(
                        raw
                    )
                )

                if candidate and re.match(
                    r"^[A-Z]{1,3}\d{5,8}$",
                    candidate
                ):

                    candidates.append(
                        candidate
                    )

        # -------------------------------------------------
        # 3. Séquence collée par OCR
        # -------------------------------------------------

        compact = re.sub(
            r"[^A-Z0-9]",
            "",
            normalized
        )

        matches = re.findall(
            r"[A-Z]{1,3}[0-9OQDI]{5,8}",
            compact
        )

        for match in matches:

            candidate = (
                self.clean_cin_candidate(
                    match
                )
            )

            if candidate and re.match(
                r"^[A-Z]{1,3}\d{5,8}$",
                candidate
            ):

                candidates.append(
                    candidate
                )

        # -------------------------------------------------
        # Déduplication
        # -------------------------------------------------

        unique = []

        for candidate in candidates:

            if candidate not in unique:

                unique.append(
                    candidate
                )

        if not unique:
            return None

        # Préférer un numéro contenant
        # 6 ou 7 chiffres
        unique.sort(
            key=lambda x: (
                len(re.sub(
                    r"[^0-9]",
                    "",
                    x
                )) == 7,
                len(x)
            ),
            reverse=True
        )

        return unique[0]

    # =====================================================
    # NUMÉRO PERMIS
    # =====================================================

    def extract_permis_number(
        self,
        text
    ):

        if not text:
            return None

        text = self.normalize_text(
            text
        )

        patterns = [

            r"(?:PERMIS|N[°O]|NO|NUMERO)"
            r"\s*[:\-]?\s*"
            r"([A-Z0-9]{4,15})",

            r"\b([A-Z]{1,3}\d{4,10})\b"

        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text
            )

            if match:

                value = (
                    match.group(1)
                )

                if re.search(
                    r"\d",
                    value
                ):

                    return value

        return None

    # =====================================================
    # FILTRAGE NOM
    # =====================================================

    @staticmethod
    def is_valid_name_candidate(
        word
    ):

        value = word[
            "text"
        ].strip()

        if not value:
            return False

        normalized = (
            value
            .upper()
            .strip()
        )

        # -------------------------------------------------
        # Faux noms fréquents sur CIN
        # -------------------------------------------------

        ignored = {

            "ROYAUME",
            "DU",
            "MAROC",
            "CARTE",
            "NATIONALE",
            "IDENTITE",
            "IDENTITÉ",

            "KINGDOM",
            "MOROCCO",

            "PASSEPORT",
            "PASSPORT",

            "PERMIS",
            "CONDUIRE",

            "REGISTRE",
            "COMMERCE",

            "LIEU",
            "PLACE",
            "NAISSANCE",

            "NOM",
            "PRENOM",
            "PRÉNOM",

            "DATE",
            "DAT",

            "NE",
            "NÉ",
            "LE",

            "A",
            "DE",
            "DU",
            "DES",

            "EN",

            "VALABLE",
            "JUSQUAU",
            "JUSQU",
            "SEXE",

            "M",
            "F"
        }

        if normalized in ignored:
            return False

        # Expressions composées
        if normalized in {
            "NE LE",
            "NÉ LE",
            "NEE LE",
            "NEE EN",
            "NE EN"
        }:
            return False

        # -------------------------------------------------
        # Longueur
        # -------------------------------------------------

        if len(normalized) < 4:
            return False

        if len(normalized) > 30:
            return False

        # -------------------------------------------------
        # Aucun chiffre
        # -------------------------------------------------

        if any(
            char.isdigit()
            for char in normalized
        ):
            return False

        # -------------------------------------------------
        # Lettres
        # -------------------------------------------------

        letters = sum(
            char.isalpha()
            for char in normalized
        )

        if letters < 4:
            return False

        ratio = (
            letters
            /
            max(
                len(normalized),
                1
            )
        )

        if ratio < 0.70:
            return False

        return True

    # =====================================================
    # NOM / PRÉNOM
    # =====================================================

    def extract_names(
        self,
        words
    ):

        candidates = []

        for word in words:

            if word[
                "confidence"
            ] < 0.20:
                continue

            if not self.is_valid_name_candidate(
                word
            ):
                continue

            candidates.append(
                word
            )

        if not candidates:
            return None, None

        # -------------------------------------------------
        # Tri vertical puis horizontal
        # -------------------------------------------------

        candidates = sorted(
            candidates,
            key=lambda w: (
                w["y"],
                w["x"]
            )
        )

        # -------------------------------------------------
        # Éviter les mots isolés trop faibles
        # -------------------------------------------------

        strong = [
            w for w in candidates
            if w["confidence"] >= 0.30
        ]

        if strong:
            candidates = strong

        # -------------------------------------------------
        # Recherche de deux mots proches
        # -------------------------------------------------

        for i in range(
            len(candidates) - 1
        ):

            first = candidates[i]
            second = candidates[i + 1]

            vertical_distance = abs(
                first["y"]
                -
                second["y"]
            )

            horizontal_distance = abs(
                first["x"]
                -
                second["x"]
            )

            max_height = max(
                first["height"],
                second["height"],
                1
            )

            if (
                vertical_distance
                <= max_height * 1.8
                and
                horizontal_distance
                <= 900
            ):

                name = (
                    first["text"]
                    .strip()
                )

                surname = (
                    second["text"]
                    .strip()
                )

                # Ne jamais retourner
                # "Né le" comme nom
                if (
                    name.upper()
                    in {
                        "NE",
                        "NÉ",
                        "LE"
                    }
                ):
                    continue

                if (
                    surname.upper()
                    in {
                        "NE",
                        "NÉ",
                        "LE"
                    }
                ):
                    continue

                return (
                    name,
                    surname
                )

        # -------------------------------------------------
        # Si un seul candidat fiable
        # -------------------------------------------------

        if len(candidates) == 1:

            return (
                candidates[0]["text"].strip(),
                None
            )

        return None, None

    # =====================================================
    # LIEU DE NAISSANCE
    # =====================================================

    def extract_birth_place(
        self,
        text,
        words
    ):

        normalized = self.normalize_text(
            text
        )

        # -------------------------------------------------
        # Texte après "LIEU DE NAISSANCE"
        # -------------------------------------------------

        patterns = [

            r"LIEU\s+DE\s+NAISSANCE\s*[:\-]?\s*([A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ ]{3,40})",

            r"PLACE\s+OF\s+BIRTH\s*[:\-]?\s*([A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ ]{3,40})",

            r"NAISSANCE\s*[:\-]?\s*([A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ ]{3,40})"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                normalized
            )

            if match:

                value = (
                    match.group(1)
                    .strip()
                )

                value = re.sub(
                    r"\s+",
                    " ",
                    value
                )

                # Couper si on rencontre
                # une information suivante
                value = re.split(
                    r"\b(?:NOM|PRENOM|NE|NÉ|DATE|SEXE)\b",
                    value
                )[0].strip()

                if (
                    len(value) >= 2
                    and
                    len(value) <= 40
                ):

                    return value

        # -------------------------------------------------
        # Recherche spatiale après un mot
        # "naissance"
        # -------------------------------------------------

        for i, word in enumerate(
            words
        ):

            current = (
                word["text"]
                .upper()
            )

            if (
                "NAISSANCE"
                not in current
            ):
                continue

            nearby = []

            for candidate in words[
                i + 1:
            ]:

                if (
                    candidate["y"]
                    <
                    word["y"]
                ):
                    continue

                distance = (
                    candidate["y"]
                    -
                    word["y"]
                )

                if distance > 400:
                    break

                if self.is_valid_name_candidate(
                    candidate
                ):

                    nearby.append(
                        candidate["text"]
                    )

                if len(nearby) >= 3:
                    break

            if nearby:

                return " ".join(
                    nearby
                )

        return None

    # =====================================================
    # CIN
    # =====================================================

    def extract_cin(
        self,
        ocr_result,
        fingerprint=None
    ):

        text = ocr_result.get(
            "text",
            ""
        )

        words = self.get_words(
            ocr_result
        )

        cin_number = (
            self.extract_cin_number(
                text,
                words
            )
        )

        name, surname = (
            self.extract_names(
                words
            )
        )

        birth_date = (
            self.extract_date_from_words(
                words,
                min_confidence=0.20
            )
        )

        birth_place = (
            self.extract_birth_place(
                text,
                words
            )
        )

        result = {

            "document_type":
                "cin",

            "cin_number":
                cin_number,

            "name":
                name,

            "surname":
                surname,

            "birth_date":
                birth_date,

            "birth_place":
                birth_place
        }

        return result

    # =====================================================
    # PERMIS
    # =====================================================

    def extract_permis(
        self,
        ocr_result,
        fingerprint=None
    ):

        text = ocr_result.get(
            "text",
            ""
        )

        words = self.get_words(
            ocr_result
        )

        name, surname = (
            self.extract_names(
                words
            )
        )

        return {

            "document_type":
                "permis",

            "permis_number":
                self.extract_permis_number(
                    text
                ),

            "name":
                name,

            "surname":
                surname,

            "birth_date":
                self.extract_date_from_words(
                    words,
                    min_confidence=0.20
                )
        }

    # =====================================================
    # PASSPORT
    # =====================================================

    def extract_passport(
        self,
        ocr_result,
        fingerprint=None
    ):

        text = ocr_result.get(
            "text",
            ""
        )

        words = self.get_words(
            ocr_result
        )

        name, surname = (
            self.extract_names(
                words
            )
        )

        result = {

            "document_type":
                "passport",

            "passport_number":
                None,

            "name":
                name,

            "surname":
                surname,

            "birth_date":
                self.extract_date_from_words(
                    words,
                    min_confidence=0.20
                ),

            "mrz":
                False
        }

        patterns = [

            r"\b([A-Z]{1,2}\d{6,9})\b",

            r"(?:PASSPORT|PASSEPORT)"
            r"\s*[:\-]?\s*"
            r"([A-Z0-9]{6,12})"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text.upper()
            )

            if match:

                result[
                    "passport_number"
                ] = match.group(1)

                break

        normalized = self.normalize_text(
            text
        )

        if re.search(
            r"P<[A-Z]{3}",
            normalized
        ):

            result["mrz"] = True

        if fingerprint and fingerprint.get(
            "mrz",
            False
        ):

            result["mrz"] = True

        return result

    # =====================================================
    # REGISTRE DE COMMERCE
    # =====================================================

    def extract_rc(
        self,
        ocr_result,
        fingerprint=None
    ):

        text = ocr_result.get(
            "text",
            ""
        )

        result = {

            "document_type":
                "rc",

            "rc_number":
                None,

            "ice":
                None,

            "company_name":
                None
        }

        patterns = [

            r"(?:RC|REGISTRE)"
            r"\s*(?:N[°O])?"
            r"\s*[:\-]?\s*"
            r"([A-Z0-9]{3,15})"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text.upper()
            )

            if match:

                result[
                    "rc_number"
                ] = match.group(1)

                break

        match = re.search(
            r"\bICE\s*[:\-]?\s*(\d{10,20})\b",
            text.upper()
        )

        if match:

            result["ice"] = (
                match.group(1)
            )

        return result

    # =====================================================
    # MÉTHODE PRINCIPALE
    # =====================================================

    def extract(
        self,
        document_type,
        ocr_result,
        fingerprint=None
    ):

        document_type = (
            document_type.lower()
            if document_type
            else ""
        )

        extractor = self.extractors.get(
            document_type
        )

        if extractor is None:

            return {

                "document_type":
                    document_type,

                "error":
                    "Type de document inconnu"
            }

        return extractor(
            ocr_result,
            fingerprint
        )