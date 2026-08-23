from pathlib import Path

from utils.image_utils import load_image
from ocr_engine import OCREngine
from layout import LayoutAnalyzer
from classifier import DocumentClassifier


# =========================================================
# CONFIGURATION
# =========================================================

DATASET_DIR = Path("datasets")


DOCUMENT_TYPES = [
    "cin",
    "permis",
    "passport",
    "rc"
]


# =========================================================
# INITIALISATION
# =========================================================

print("=" * 70)
print("              DOC AI - TEST DU MODÈLE")
print("=" * 70)

print()

ocr = OCREngine()

layout = LayoutAnalyzer()

classifier = DocumentClassifier()


# =========================================================
# STATISTIQUES
# =========================================================

total = 0

correct = 0

results = []


# =========================================================
# TEST
# =========================================================

for document_type in DOCUMENT_TYPES:

    folder = (
        DATASET_DIR
        / document_type
        / "images"
    )

    if not folder.exists():

        print(
            f"[WARNING] Dossier absent : {folder}"
        )

        continue

    images = []

    for extension in [
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.webp",
        "*.bmp"
    ]:

        images.extend(
            folder.glob(extension)
        )

    print()
    print("-" * 70)

    print(
        f"[DOCUMENT] {document_type.upper()}"
    )

    print("-" * 70)

    for image_path in sorted(images):

        total += 1

        print()
        print(
            f"[TEST] {image_path.name}"
        )

        # -------------------------------------------------
        # IMAGE
        # -------------------------------------------------

        image = load_image(
            str(image_path)
        )

        # -------------------------------------------------
        # OCR
        # -------------------------------------------------

        ocr_result = ocr.extract(
            image
        )

        # -------------------------------------------------
        # LAYOUT
        # -------------------------------------------------

        fingerprint = layout.build(
            image,
            ocr_result
        )

        # -------------------------------------------------
        # CLASSIFICATION
        # -------------------------------------------------

        prediction = classifier.classify(
            ocr_result,
            fingerprint
        )

        predicted_type = prediction[
            "document_type"
        ]

        confidence = prediction[
            "confidence"
        ]

        # -------------------------------------------------
        # CORRECT ?
        # -------------------------------------------------

        is_correct = (
            predicted_type
            ==
            document_type
        )

        if is_correct:

            correct += 1

            status = "✓"

        else:

            status = "✗"

        # -------------------------------------------------
        # AFFICHAGE
        # -------------------------------------------------

        print(
            f"   Attendu     : {document_type}"
        )

        print(
            f"   Prédit      : {predicted_type}"
        )

        print(
            f"   Confiance   : "
            f"{confidence * 100:.2f}%"
        )

        print(
            f"   Résultat    : {status}"
        )

        # -------------------------------------------------
        # SCORES
        # -------------------------------------------------

        print(
            "   Scores      :"
        )

        for label, score in sorted(
            prediction["scores"].items(),
            key=lambda x: x[1],
            reverse=True
        ):

            print(
                f"      {label:<10} "
                f"{score * 100:.2f}%"
            )

        results.append({

            "file":
                image_path.name,

            "expected":
                document_type,

            "predicted":
                predicted_type,

            "confidence":
                confidence,

            "correct":
                is_correct

        })


# =========================================================
# FINAL RESULT
# =========================================================

print()
print("=" * 70)
print("                    RÉSULTAT FINAL")
print("=" * 70)

print()

print(
    f"Documents testés : {total}"
)

print(
    f"Prédictions correctes : {correct}"
)

print(
    f"Prédictions incorrectes : "
    f"{total - correct}"
)

if total > 0:

    accuracy = (
        correct
        /
        total
    )

    print()

    print(
        f"Accuracy : "
        f"{accuracy * 100:.2f}%"
    )

print()

print("=" * 70)