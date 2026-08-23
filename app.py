"""
=========================================================
WAFABAIL
Main Application
=========================================================

Pipeline complet :

1. Chargement image
2. OCR
3. Analyse du layout
4. Classification
5. Extraction
6. Validation
7. Sauvegarde JSON
=========================================================
"""

import sys
import json
from pathlib import Path

from utils.image_utils import load_image

from ocr_engine import OCREngine
from layout import LayoutAnalyzer
from classifier import DocumentClassifier
from extractor import DocumentExtractor
from validators import DocumentValidator


# =========================================================
# CONFIGURATION
# =========================================================

RESULT_FILE = Path("result.json")


# =========================================================
# DOCUMENT PIPELINE
# =========================================================

class DocumentPipeline:

    def __init__(self):

        print("[INFO] Initialisation du pipeline...")

        # -------------------------------------------------
        # OCR
        # -------------------------------------------------

        self.ocr = OCREngine()

        # -------------------------------------------------
        # Layout Analyzer
        # -------------------------------------------------

        self.layout = LayoutAnalyzer()

        # -------------------------------------------------
        # Classifier
        # -------------------------------------------------

        self.classifier = DocumentClassifier()

        # -------------------------------------------------
        # Extractor
        # -------------------------------------------------

        self.extractor = DocumentExtractor()

        # -------------------------------------------------
        # Validator
        # -------------------------------------------------

        self.validators = DocumentValidator()

        print("[INFO] Pipeline prêt.")

    # =====================================================
    # PROCESS DOCUMENT
    # =====================================================

    def process(self, image_path):

        # -------------------------------------------------
        # CHARGEMENT IMAGE
        # -------------------------------------------------

        print(
            f"\n[INFO] Chargement image : {image_path}"
        )

        image = load_image(
            image_path
        )

        if image is None:

            raise ValueError(
                "Impossible de charger l'image."
            )

        # -------------------------------------------------
        # OCR
        # -------------------------------------------------

        print("[INFO] OCR...")

        ocr_result = self.ocr.extract(
            image
        )

        if not ocr_result.get(
            "success",
            False
        ):

            raise RuntimeError(
                "Échec de l'OCR."
            )

        # -------------------------------------------------
        # LAYOUT
        # -------------------------------------------------

        print("[INFO] Analyse du layout...")

        fingerprint = self.layout.build(
            image,
            ocr_result
        )

        # -------------------------------------------------
        # CLASSIFICATION
        # -------------------------------------------------

        print("[INFO] Classification...")

        classification = self.classifier.classify(
            ocr_result,
            fingerprint
        )

        document_type = classification.get(
            "document_type"
        )

        confidence = classification.get(
            "confidence",
            0
        )

        # -------------------------------------------------
        # EXTRACTION
        # -------------------------------------------------

        print(
            f"[INFO] Extraction : {document_type}"
        )

        extracted_data = self.extractor.extract(
            document_type,
            ocr_result,
            fingerprint
        )

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        print("[INFO] Validation...")

        validation = self.validators.validate(
            document_type,
            extracted_data
        )

        # -------------------------------------------------
        # RESULTAT COMPLET
        # -------------------------------------------------

        result = {

            "image":
                str(image_path),

            "document_type":
                document_type,

            "confidence":
                confidence,

            "classification":
                classification,

            "ocr":
                ocr_result,

            "fingerprint":
                fingerprint,

            "extraction":
                extracted_data,

            "validation":
                validation

        }

        return result


# =========================================================
# AFFICHAGE RESULTAT
# =========================================================

def display_result(result):

    print("\n")
    print("=" * 60)
    print("              RESULTAT DOC AI")
    print("=" * 60)

    # -----------------------------------------------------
    # TYPE DOCUMENT
    # -----------------------------------------------------

    document_type = result.get(
        "document_type"
    )

    confidence = result.get(
        "confidence",
        0
    )

    print(
        f"\nType de document : {document_type}"
    )

    print(
        f"Confiance : {confidence:.2%}"
    )

    # -----------------------------------------------------
    # SCORES
    # -----------------------------------------------------

    classification = result.get(
        "classification",
        {}
    )

    scores = classification.get(
        "scores",
        {}
    )

    print("\n--- SCORES ---")

    for document, score in scores.items():

        print(
            f"{document:<12} : {score}"
        )

    # -----------------------------------------------------
    # EXTRACTION
    # -----------------------------------------------------

    extraction = result.get(
        "extraction",
        {}
    )

    print("\n--- EXTRACTION ---")

    for key, value in extraction.items():

        print(
            f"{key:<20} : {value}"
        )

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    validation = result.get(
        "validation",
        {}
    )

    print("\n--- VALIDATION ---")

    if validation.get(
        "valid",
        False
    ):

        print(
            "Document valide ✓"
        )

    else:

        print(
            "Document à vérifier ⚠"
        )

    # -----------------------------------------------------
    # ERREURS
    # -----------------------------------------------------

    errors = validation.get(
        "errors",
        []
    )

    if errors:

        print("\nErreurs :")

        for error in errors:

            print(
                f"  - {error}"
            )

    # -----------------------------------------------------
    # AVERTISSEMENTS
    # -----------------------------------------------------

    warnings = validation.get(
        "warnings",
        []
    )

    if warnings:

        print("\nAvertissements :")

        for warning in warnings:

            print(
                f"  - {warning}"
            )

    print("\n")
    print("=" * 60)


# =========================================================
# JSON SERIALIZER
# =========================================================

def json_serializer(obj):

    """
    Conversion des types NumPy et autres
    objets non sérialisables en JSON.
    """

    # -----------------------------------------------------
    # NumPy integer / float / bool
    # -----------------------------------------------------

    if hasattr(
        obj,
        "item"
    ):

        return obj.item()

    # -----------------------------------------------------
    # NumPy array
    # -----------------------------------------------------

    if hasattr(
        obj,
        "tolist"
    ):

        return obj.tolist()

    # -----------------------------------------------------
    # Path
    # -----------------------------------------------------

    if isinstance(
        obj,
        Path
    ):

        return str(obj)

    raise TypeError(
        f"Object of type "
        f"{type(obj).__name__} "
        f"is not JSON serializable"
    )


# =========================================================
# SAVE RESULT
# =========================================================

def save_result(
    result,
    filename=RESULT_FILE
):

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            indent=4,
            ensure_ascii=False,
            default=json_serializer
        )

    print(
        f"\n[INFO] Résultat sauvegardé dans {filename}"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    # -----------------------------------------------------
    # ARGUMENT IMAGE
    # -----------------------------------------------------

    if len(sys.argv) < 2:

        print(
            "\nUsage :"
        )

        print(
            "python app.py chemin/image.jpg"
        )

        print(
            "\nExemple :"
        )

        print(
            "python app.py datasets/cin/images/CIN.jpg"
        )

        sys.exit(1)

    image_path = Path(
        sys.argv[1]
    )

    # -----------------------------------------------------
    # VERIFICATION IMAGE
    # -----------------------------------------------------

    if not image_path.exists():

        print(
            f"[ERROR] Image introuvable : "
            f"{image_path}"
        )

        sys.exit(1)

    print(
        f"[INFO] Image : {image_path}"
    )

    # -----------------------------------------------------
    # EXECUTION PIPELINE
    # -----------------------------------------------------

    try:

        pipeline = DocumentPipeline()

        result = pipeline.process(
            image_path
        )

        # -------------------------------------------------
        # AFFICHAGE
        # -------------------------------------------------

        display_result(
            result
        )

        # -------------------------------------------------
        # SAUVEGARDE
        # -------------------------------------------------

        save_result(
            result
        )

    except Exception as error:

        print(
            f"\n[ERROR] {error}"
        )

        sys.exit(1)


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    main()