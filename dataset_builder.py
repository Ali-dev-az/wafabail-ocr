"""
=========================================================
WAFABAIL
Real Document Dataset Builder
=========================================================

Parcourt les documents réels présents dans datasets/
et construit leurs fingerprints structurels.

CIN
PERMIS
PASSPORT
RC

Sortie :
    outputs/features.csv
=========================================================
"""

import csv
import json
from pathlib import Path

from config import DATASET_DIR, OUTPUT_DIR, SUPPORTED_FORMATS
from utils.image_utils import load_image
from ocr_engine import OCREngine
from layout import LayoutAnalyzer


# =========================================================
# CONFIGURATION
# =========================================================

DOCUMENT_TYPES = [
    "cin",
    "permis",
    "passport",
    "rc"
]


# =========================================================
# DATASET BUILDER
# =========================================================

class DatasetBuilder:

    def __init__(self):

        print("=" * 60)
        print("        DOC AI - DATASET BUILDER")
        print("=" * 60)

        print("\n[INFO] Initialisation OCR...")

        self.ocr = OCREngine()

        print("[INFO] Initialisation Layout Analyzer...")

        self.layout = LayoutAnalyzer()

    # =====================================================
    # RECHERCHE DES IMAGES
    # =====================================================

    def find_images(self):

        images = []

        for document_type in DOCUMENT_TYPES:

            image_dir = (
                DATASET_DIR
                / document_type
                / "images"
            )

            if not image_dir.exists():

                print(
                    f"[WARNING] Dossier absent : "
                    f"{image_dir}"
                )

                continue

            for file in sorted(
                image_dir.iterdir()
            ):

                if not file.is_file():
                    continue

                extension = (
                    file.suffix.lower()
                )

                if extension not in SUPPORTED_FORMATS:
                    continue

                images.append(
                    (
                        document_type,
                        file
                    )
                )

        return images

    # =====================================================
    # EXTRACTION D'UNE IMAGE
    # =====================================================

    def process_image(
        self,
        document_type,
        image_path
    ):

        print("\n" + "-" * 60)

        print(
            f"[DOCUMENT] {document_type}"
        )

        print(
            f"[IMAGE] {image_path.name}"
        )

        # -------------------------------------------------
        # Chargement
        # -------------------------------------------------

        image = load_image(
            str(image_path)
        )

        if image is None:

            print(
                "[ERROR] Impossible de charger "
                "l'image."
            )

            return None

        # -------------------------------------------------
        # OCR
        # -------------------------------------------------

        print("[INFO] OCR...")

        ocr_result = self.ocr.extract(
            image
        )

        # -------------------------------------------------
        # Layout
        # -------------------------------------------------

        print("[INFO] Analyse du layout...")

        fingerprint = self.layout.build(
            image,
            ocr_result
        )

        # -------------------------------------------------
        # Résultat
        # -------------------------------------------------

        result = {

            "filename":
                image_path.name,

            "path":
                str(image_path),

            "document_type":
                document_type,

            "ocr":
                ocr_result,

            "fingerprint":
                fingerprint
        }

        print(
            f"[OK] {image_path.name}"
        )

        print(
            f"     Words : "
            f"{fingerprint.get('word_count', 0)}"
        )

        print(
            f"     Density : "
            f"{fingerprint.get('text_density', 0)}"
        )

        print(
            f"     MRZ : "
            f"{fingerprint.get('mrz', False)}"
        )

        return result

    # =====================================================
    # CONVERSION FINGERPRINT → CSV
    # =====================================================

    def fingerprint_to_row(
        self,
        result
    ):

        fingerprint = result[
            "fingerprint"
        ]

        zones = fingerprint.get(
            "zones",
            {}
        )

        distribution = fingerprint.get(
            "distribution",
            {}
        )

        return {

            "filename":
                result["filename"],

            "document_type":
                result["document_type"],

            # ---------------------------------------------
            # OCR
            # ---------------------------------------------

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

            # ---------------------------------------------
            # Dimensions
            # ---------------------------------------------

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

            # ---------------------------------------------
            # Density
            # ---------------------------------------------

            "text_density":
                fingerprint.get(
                    "text_density",
                    0
                ),

            # ---------------------------------------------
            # Vertical zones
            # ---------------------------------------------

            "top_count":
                zones.get(
                    "top",
                    0
                ),

            "middle_count":
                zones.get(
                    "middle",
                    0
                ),

            "bottom_count":
                zones.get(
                    "bottom",
                    0
                ),

            # ---------------------------------------------
            # Horizontal zones
            # ---------------------------------------------

            "left_count":
                zones.get(
                    "left",
                    0
                ),

            "center_count":
                zones.get(
                    "center",
                    0
                ),

            "right_count":
                zones.get(
                    "right",
                    0
                ),

            # ---------------------------------------------
            # Ratios
            # ---------------------------------------------

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

            # ---------------------------------------------
            # MRZ
            # ---------------------------------------------

            "mrz":
                int(
                    fingerprint.get(
                        "mrz",
                        False
                    )
                ),

            # ---------------------------------------------
            # PHOTO
            # ---------------------------------------------

            "photo":
                int(
                    fingerprint.get(
                        "photo",
                        False
                    )
                )
        }

    # =====================================================
    # CONSTRUCTION DU DATASET
    # =====================================================

    def build(self):

        images = self.find_images()

        if not images:

            print(
                "\n[ERROR] "
                "Aucune image trouvée."
            )

            return

        print(
            f"\n[INFO] "
            f"{len(images)} image(s) trouvée(s)."
        )

        results = []

        # -------------------------------------------------
        # Traitement
        # -------------------------------------------------

        for document_type, image_path in images:

            try:

                result = self.process_image(
                    document_type,
                    image_path
                )

                if result is not None:

                    results.append(
                        result
                    )

            except Exception as error:

                print(
                    f"[ERROR] "
                    f"{image_path.name}"
                )

                print(
                    f"        {error}"
                )

        if not results:

            print(
                "\n[ERROR] "
                "Aucun document traité."
            )

            return

        # =================================================
        # SAUVEGARDE JSON
        # =================================================

        json_path = (
            OUTPUT_DIR
            / "fingerprints.json"
        )

        with open(
            json_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
    results,
    file,
    indent=4,
    ensure_ascii=False,
    default=lambda obj: obj.item()
    if hasattr(obj, "item")
    else str(obj)
)

        print(
            f"\n[OK] Fingerprints sauvegardés : "
            f"{json_path}"
        )

        # =================================================
        # SAUVEGARDE CSV
        # =================================================

        rows = [

            self.fingerprint_to_row(
                result
            )

            for result in results

        ]

        csv_path = (
            OUTPUT_DIR
            / "features.csv"
        )

        if rows:

            fieldnames = list(
                rows[0].keys()
            )

            with open(
                csv_path,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.DictWriter(
                    file,
                    fieldnames=fieldnames
                )

                writer.writeheader()

                writer.writerows(
                    rows
                )

        print(
            f"[OK] Features sauvegardées : "
            f"{csv_path}"
        )

        # =================================================
        # RESUME
        # =================================================

        print("\n" + "=" * 60)

        print(
            "             DATASET TERMINÉ"
        )

        print("=" * 60)

        print(
            f"Documents traités : "
            f"{len(results)}"
        )

        for document_type in DOCUMENT_TYPES:

            count = sum(
                1
                for result in results
                if result["document_type"]
                == document_type
            )

            print(
                f"{document_type:<12} : "
                f"{count}"
            )

        print("=" * 60)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    builder = DatasetBuilder()

    builder.build()