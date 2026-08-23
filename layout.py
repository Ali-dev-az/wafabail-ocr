"""
=========================================================
WAFABAIL
Document Layout Analyzer
=========================================================

Analyse structurelle du document à partir des résultats OCR.

Features extraites :
    - dimensions image
    - nombre de mots/blocs OCR
    - confiance moyenne
    - largeur/hauteur moyenne des mots
    - distribution verticale
    - distribution horizontale
    - densité textuelle
    - MRZ
    - présence potentielle d'une photo
=========================================================
"""

import re
import cv2
import numpy as np


class LayoutAnalyzer:

    def __init__(self):
        pass

    # =====================================================
    # SAFE NUMBER
    # =====================================================

    def safe_float(self, value):

        try:
            return float(value)

        except (TypeError, ValueError):

            return 0.0

    # =====================================================
    # BBOX
    # =====================================================

    def extract_bbox(self, word):

        bbox = word.get("bbox")

        if not bbox:
            return None

        try:

            points = np.array(
                bbox,
                dtype=float
            )

            x_min = float(
                np.min(points[:, 0])
            )

            x_max = float(
                np.max(points[:, 0])
            )

            y_min = float(
                np.min(points[:, 1])
            )

            y_max = float(
                np.max(points[:, 1])
            )

            return (
                x_min,
                y_min,
                x_max,
                y_max
            )

        except Exception:

            return None

    # =====================================================
    # MRZ
    # =====================================================

    def detect_mrz(self, text):
        """
        Détection volontairement stricte.
        Une simple longue chaîne alphanumérique ne suffit pas:
        sinon les numéros de permis sont pris pour une MRZ.
        """
        if not text:
            return False

        text = str(text).upper().replace(" ", "")
        text = text.replace("«", "<").replace("‹", "<")

        patterns = [
            r"P<[A-Z]{3}",
            r"P<<[A-Z<]{3,}",
            r"[A-Z0-9<]{25,}<<[A-Z0-9<]{5,}",
        ]
        return any(re.search(p, text) for p in patterns)

    # =====================================================
    # PHOTO
    # =====================================================

    def detect_photo(self, image, words):
        """
        Détection conservatrice d'une zone portrait.
        L'ancien algorithme retournait True sur presque tous les
        documents parce qu'une zone vide existe toujours à gauche.
        """
        if image is None:
            return False

        h, w = image.shape[:2]
        if h < 100 or w < 100:
            return False

        # Un portrait est une zone rectangulaire relativement grande
        # et peu couverte par les boîtes OCR. On ne l'affirme que si
        # plusieurs critères sont réunis.
        for x1, x2 in [
            (0.04 * w, 0.42 * w),
            (0.08 * w, 0.50 * w),
        ]:
            y1, y2 = 0.15 * h, 0.82 * h
            area = (x2-x1) * (y2-y1)
            if area <= 0:
                continue

            covered = 0.0
            for word in words:
                bbox = self.extract_bbox(word)
                if bbox is None:
                    continue
                bx1, by1, bx2, by2 = bbox
                ix1, iy1 = max(bx1, x1), max(by1, y1)
                ix2, iy2 = min(bx2, x2), min(by2, y2)
                if ix2 > ix1 and iy2 > iy1:
                    covered += (ix2-ix1) * (iy2-iy1)

            occupation = covered / area

            # Vérification visuelle simple: variation de gris suffisante.
            crop = image[int(y1):int(y2), int(x1):int(x2)]
            if crop.size == 0:
                continue
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.ndim == 3 else crop
            std = float(np.std(gray))

            if occupation < 0.055 and std > 22:
                return True

        return False

    # =====================================================
    # BUILD FINGERPRINT
    # =====================================================

    def build(
        self,
        image,
        ocr_result
    ):

        # =================================================
        # IMAGE
        # =================================================

        if image is None:

            return {

                "image_width": 0,

                "image_height": 0,

                "word_count": 0,

                "text_blocks": 0,

                "average_confidence": 0,

                "average_word_width": 0,

                "average_word_height": 0,

                "zones": {},

                "distribution": {},

                "text_density": 0,

                "mrz": False,

                "photo": False,

                "raw_text": ""

            }

        image_height, image_width = (
            image.shape[:2]
        )

        # =================================================
        # OCR WORDS
        # =================================================

        words = ocr_result.get(
            "words",
            []
        )

        # Sécurité si OCR retourne None

        if words is None:

            words = []

        # =================================================
        # TEXTE
        # =================================================

        raw_text = ocr_result.get(
            "text",
            ""
        )

        # =================================================
        # COMPTE
        # =================================================

        word_count = len(words)

        text_blocks = len(words)

        # =================================================
        # VARIABLES
        # =================================================

        confidences = []

        widths = []

        heights = []

        centers_x = []

        centers_y = []

        # =================================================
        # ZONES
        # =================================================

        zones = {

            "top": 0,

            "middle": 0,

            "bottom": 0,

            "left": 0,

            "center": 0,

            "right": 0

        }

        # =================================================
        # PARCOURS OCR
        # =================================================

        for word in words:

            # ---------------------------------------------
            # Confidence
            # ---------------------------------------------

            confidence = self.safe_float(
                word.get(
                    "confidence",
                    0
                )
            )

            confidences.append(
                confidence
            )

            # ---------------------------------------------
            # BBOX
            # ---------------------------------------------

            bbox = self.extract_bbox(
                word
            )

            if bbox is None:

                continue

            x1, y1, x2, y2 = bbox

            width = max(
                0,
                x2 - x1
            )

            height = max(
                0,
                y2 - y1
            )

            center_x = (
                x1 + x2
            ) / 2

            center_y = (
                y1 + y2
            ) / 2

            widths.append(
                width
            )

            heights.append(
                height
            )

            centers_x.append(
                center_x
            )

            centers_y.append(
                center_y
            )

            # =============================================
            # VERTICAL
            # =============================================

            relative_y = (
                center_y
                /
                image_height
            )

            if relative_y < 1 / 3:

                zones["top"] += 1

            elif relative_y < 2 / 3:

                zones["middle"] += 1

            else:

                zones["bottom"] += 1

            # =============================================
            # HORIZONTAL
            # =============================================

            relative_x = (
                center_x
                /
                image_width
            )

            if relative_x < 1 / 3:

                zones["left"] += 1

            elif relative_x < 2 / 3:

                zones["center"] += 1

            else:

                zones["right"] += 1

        # =================================================
        # MOYENNES
        # =================================================

        if confidences:

            average_confidence = (
                sum(confidences)
                /
                len(confidences)
            )

        else:

            average_confidence = 0

        if widths:

            average_word_width = (
                sum(widths)
                /
                len(widths)
            )

        else:

            average_word_width = 0

        if heights:

            average_word_height = (
                sum(heights)
                /
                len(heights)
            )

        else:

            average_word_height = 0

        # =================================================
        # DISTRIBUTION
        # =================================================

        if word_count > 0:

            distribution = {

                "top_ratio":
                    zones["top"]
                    /
                    word_count,

                "middle_ratio":
                    zones["middle"]
                    /
                    word_count,

                "bottom_ratio":
                    zones["bottom"]
                    /
                    word_count,

                "left_ratio":
                    zones["left"]
                    /
                    word_count,

                "center_ratio":
                    zones["center"]
                    /
                    word_count,

                "right_ratio":
                    zones["right"]
                    /
                    word_count

            }

        else:

            distribution = {

                "top_ratio": 0,

                "middle_ratio": 0,

                "bottom_ratio": 0,

                "left_ratio": 0,

                "center_ratio": 0,

                "right_ratio": 0

            }

        # =================================================
        # TEXT DENSITY
        # =================================================

        image_area = (
            image_width
            *
            image_height
        )

        text_area = 0

        for width, height in zip(
            widths,
            heights
        ):

            text_area += (
                width
                *
                height
            )

        if image_area > 0:

            text_density = (
                text_area
                /
                image_area
            )

        else:

            text_density = 0

        # =================================================
        # MRZ
        # =================================================

        mrz = self.detect_mrz(
            raw_text
        )

        # =================================================
        # PHOTO
        # =================================================

        photo = self.detect_photo(
            image,
            words
        )

        # =================================================
        # FINGERPRINT
        # =================================================

        fingerprint = {

            "image_width":
                int(image_width),

            "image_height":
                int(image_height),

            "word_count":
                int(word_count),

            "text_blocks":
                int(text_blocks),

            "average_confidence":
                float(
                    average_confidence
                ),

            "average_word_width":
                float(
                    average_word_width
                ),

            "average_word_height":
                float(
                    average_word_height
                ),

            "zones": {

                key: int(value)

                for key, value
                in zones.items()

            },

            "distribution": {

                key: float(value)

                for key, value
                in distribution.items()

            },

            "text_density":
                float(text_density),

            "mrz":
                bool(mrz),

            "photo":
                bool(photo),

            "raw_text":
                str(raw_text)

        }

        return fingerprint