"""
WAFABAIL - OCR Engine robuste.

Objectif:
- utiliser plusieurs variantes d'image sans favoriser un type de document;
- conserver les coordonnées dans le repère de l'image originale;
- choisir le résultat OCR sur des critères génériques (confiance + quantité de texte).
"""
import re
try:
    import easyocr
except ImportError:
    easyocr = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

import numpy as np
import cv2


class OCREngine:
    def __init__(self):
        self.reader = None
        if easyocr is not None:
            print("[INFO] Initialisation EasyOCR...")
            self.reader = easyocr.Reader(["fr", "en"], gpu=False)
            print("[INFO] EasyOCR prêt.")
        elif pytesseract is not None:
            print("[WARNING] EasyOCR indisponible -> fallback Tesseract.")
        else:
            raise ImportError(
                "Ni EasyOCR ni pytesseract ne sont disponibles."
            )

    @staticmethod
    def center(box):
        return (
            float(np.mean([p[0] for p in box])),
            float(np.mean([p[1] for p in box])),
        )

    @staticmethod
    def preprocess(image):
        h, w = image.shape[:2]
        enlarged = cv2.resize(
            image, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC
        )
        gray = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)

        threshold = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 31, 11
        )

        # image, scale_to_original
        # Trois variantes suffisent dans la majorité des cas et
        # évitent de multiplier inutilement le temps OCR.
        return [
            (image, 1.0),
            (enlarged, 2.0),
            (sharpened, 2.0),
        ]

    @staticmethod
    def clean_box(box, scale=1.0):
        return [[float(p[0]) / scale, float(p[1]) / scale] for p in box]

    def run_ocr(self, image):
        if self.reader is not None:
            return self.reader.readtext(
                image,
                detail=1,
                paragraph=False,
                width_ths=0.55,
                height_ths=0.55,
                text_threshold=0.35,
                low_text=0.20,
                link_threshold=0.25,
                mag_ratio=1.0,
            )

        # Fallback Tesseract -> même format que EasyOCR.
        data = pytesseract.image_to_data(
            image,
            lang="fra+eng",
            config="--psm 6",
            output_type=pytesseract.Output.DICT,
        )
        detections = []
        for i, value in enumerate(data["text"]):
            value = str(value).strip()
            if not value:
                continue
            try:
                confidence = max(0.0, float(data["conf"][i]) / 100.0)
            except Exception:
                confidence = 0.0
            x = int(data["left"][i])
            y = int(data["top"][i])
            w = int(data["width"][i])
            h = int(data["height"][i])
            box = [[x,y],[x+w,y],[x+w,y+h],[x,y+h]]
            detections.append((box, value, confidence))
        return detections

    def convert_results(self, detections, scale=1.0):
        words, full_text = [], []
        for box, text, confidence in detections:
            if not text or not str(text).strip():
                continue
            box = self.clean_box(box, scale)
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            words.append({
                "text": str(text).strip(),
                "confidence": float(confidence),
                "bbox": box,
                "center": self.center(box),
                "x": float(min(xs)),
                "y": float(min(ys)),
                "width": float(max(xs)-min(xs)),
                "height": float(max(ys)-min(ys)),
            })
            full_text.append(str(text).strip())

        return {
            "success": True,
            "text": " ".join(full_text),
            "words": words,
            "count": len(words),
        }

    @staticmethod
    def score_result(result):
        words = result.get("words", [])
        text = result.get("text", "")
        if not words or not text.strip():
            return -1.0

        avg_conf = sum(float(w.get("confidence", 0)) for w in words) / len(words)
        alnum = sum(c.isalnum() for c in text)
        useful_ratio = alnum / max(len(text), 1)

        # Aucun mot-clé de document ici: le choix OCR ne doit jamais
        # favoriser CIN, passeport, permis ou RC.
        return (
            min(len(words), 80) * 0.18
            + avg_conf * 12.0
            + useful_ratio * 4.0
        )

    def extract(self, image):
        variants = self.preprocess(image)
        best_result, best_score = None, -1e9

        print(f"[INFO] OCR de {len(variants)} variantes...")

        for index, (variant, scale) in enumerate(variants):
            try:
                detections = self.run_ocr(variant)
                result = self.convert_results(detections, scale=scale)
                score = self.score_result(result)
                print(
                    f"[INFO] Variante OCR {index+1}/{len(variants)} : "
                    f"{result['count']} mots, score={score:.2f}"
                )
                if score > best_score:
                    best_score, best_result = score, result
            except Exception as e:
                print(f"[WARNING] OCR variante {index+1} échouée : {e}")

        if best_result is None:
            return {
                "success": False, "text": "", "words": [], "count": 0,
                "error": "OCR impossible",
            }

        best_result["ocr_score"] = float(best_score)
        print(f"[INFO] Meilleur résultat OCR : score={best_score:.2f}")
        return best_result
