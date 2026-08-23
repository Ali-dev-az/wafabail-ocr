"""
=========================================================
WAFABAIL
Document Detector
=========================================================

Détecte automatiquement un document sur une photo,
le recadre et corrige la perspective.
"""

import cv2
import numpy as np

from preprocessing import ImagePreprocessor
from config import MIN_DOCUMENT_AREA


class DocumentDetector:

    def __init__(self):

        self.preprocessor = ImagePreprocessor()

    # -----------------------------------------------------

    @staticmethod
    def order_points(points):
        """
        Ordonne les 4 coins :
        haut-gauche
        haut-droite
        bas-droite
        bas-gauche
        """

        rect = np.zeros((4, 2), dtype="float32")

        s = points.sum(axis=1)

        rect[0] = points[np.argmin(s)]
        rect[2] = points[np.argmax(s)]

        diff = np.diff(points, axis=1)

        rect[1] = points[np.argmin(diff)]
        rect[3] = points[np.argmax(diff)]

        return rect

    # -----------------------------------------------------

    @staticmethod
    def four_point_transform(image, points):

        rect = DocumentDetector.order_points(points)

        (tl, tr, br, bl) = rect

        widthA = np.linalg.norm(br - bl)
        widthB = np.linalg.norm(tr - tl)

        maxWidth = max(int(widthA), int(widthB))

        heightA = np.linalg.norm(tr - br)
        heightB = np.linalg.norm(tl - bl)

        maxHeight = max(int(heightA), int(heightB))

        destination = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")

        matrix = cv2.getPerspectiveTransform(rect, destination)

        warped = cv2.warpPerspective(
            image,
            matrix,
            (maxWidth, maxHeight)
        )

        return warped

    # -----------------------------------------------------

    def find_document_contour(self, edges):

        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_LIST,
            cv2.CHAIN_APPROX_SIMPLE
        )

        contours = sorted(
            contours,
            key=cv2.contourArea,
            reverse=True
        )

        for contour in contours:

            area = cv2.contourArea(contour)

            if area < MIN_DOCUMENT_AREA:
                continue

            perimeter = cv2.arcLength(contour, True)

            approximation = cv2.approxPolyDP(
                contour,
                0.02 * perimeter,
                True
            )

            if len(approximation) == 4:
                return approximation

        return None

    # -----------------------------------------------------

    def detect(self, image):

        processed = self.preprocessor.process(image)

        edges = processed["edges"]

        contour = self.find_document_contour(edges)

        if contour is None:

            return {
                "success": False,
                "message": "Document introuvable",
                "cropped": None,
                "contour": None,
                "processed": processed
            }

        warped = self.four_point_transform(
            processed["resized"],
            contour.reshape(4, 2)
        )

        return {

            "success": True,

            "cropped": warped,

            "contour": contour,

            "processed": processed

        }

    # -----------------------------------------------------

    @staticmethod
    def draw_contour(image, contour):

        img = image.copy()

        cv2.drawContours(
            img,
            [contour],
            -1,
            (0, 255, 0),
            3
        )

        return img