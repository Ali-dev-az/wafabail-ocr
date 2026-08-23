"""
=========================================================
WAFABAIL
Complete Document Processing Pipeline
=========================================================
"""

from utils.image_utils import load_image

from detector import DocumentDetector
from ocr_engine import OCREngine
from layout import LayoutAnalyzer
from classifier import DocumentClassifier
from extractor import DocumentExtractor
from validators import DocumentValidator


class DocumentPipeline:

    def __init__(self):

        print("[INFO] Initialisation du pipeline...")

        self.detector = DocumentDetector()

        self.ocr = OCREngine()

        self.layout = LayoutAnalyzer()

        self.classifier = DocumentClassifier()

        self.extractor = DocumentExtractor()

        self.validator = DocumentValidator()

        print("[INFO] Pipeline prêt.")

    # --------------------------------------------------

    def process(self, image_path):

        # ==============================================
        # 1. LOAD
        # ==============================================

        image = load_image(image_path)

        # ==============================================
        # 2. DOCUMENT DETECTION
        # ==============================================

        detection = self.detector.detect(image)

        if detection["success"]:

            document_image = detection["cropped"]

        else:

            # Si le contour n'est pas trouvé,
            # on travaille quand même sur l'image originale.

            document_image = image

        # ==============================================
        # 3. OCR
        # ==============================================

        ocr_result = self.ocr.extract(
            document_image
        )

        # ==============================================
        # 4. LAYOUT
        # ==============================================

        fingerprint = self.layout.build(
            document_image,
            ocr_result
        )

        # ==============================================
        # 5. CLASSIFICATION
        # ==============================================

        classification = self.classifier.classify(
            ocr_result,
            fingerprint
        )

        document_type = classification[
            "document_type"
        ]

        # ==============================================
        # 6. EXTRACTION
        # ==============================================

        extracted = self.extractor.extract(
            document_type,
            ocr_result,
            fingerprint
        )

        # ==============================================
        # 7. VALIDATION
        # ==============================================

        validation = self.validator.validate(
            document_type,
            extracted
        )

        # ==============================================
        # FINAL RESULT
        # ==============================================

        return {

            "success": True,

            "document_type": document_type,

            "confidence":
                classification["confidence"],

            "classification":
                classification,

            "fingerprint":
                fingerprint,

            "extraction":
                extracted,

            "validation":
                validation,

            "ocr":
                ocr_result
        }