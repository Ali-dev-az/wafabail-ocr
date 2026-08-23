"""
=========================================================
WAFABAIL
Image Preprocessing
=========================================================

Responsable de préparer une image avant
la détection du document.

Pipeline :

Image
    ↓
Resize
    ↓
Gray
    ↓
Denoise
    ↓
CLAHE
    ↓
Gaussian Blur
    ↓
Canny
"""

import cv2
import numpy as np

from config import (
    IMAGE_WIDTH,
    IMAGE_HEIGHT,
    GAUSSIAN_KERNEL,
    CANNY_THRESHOLD_1,
    CANNY_THRESHOLD_2
)

from utils.image_utils import (
    resize,
    to_gray
)


class ImagePreprocessor:

    def __init__(self):

        pass

    # --------------------------------------------------

    def resize_image(self, image):

        """
        Redimensionne l'image.
        """

        return resize(image, width=IMAGE_WIDTH)

    # --------------------------------------------------

    def grayscale(self, image):

        """
        Convertit en niveaux de gris.
        """

        return to_gray(image)

    # --------------------------------------------------

    def denoise(self, image):

        """
        Réduction du bruit.
        """

        return cv2.fastNlMeansDenoising(
            image,
            None,
            10,
            7,
            21
        )

    # --------------------------------------------------

    def enhance_contrast(self, image):

        """
        CLAHE améliore énormément
        les documents photographiés.
        """

        clahe = cv2.createCLAHE(
            clipLimit=2.0,
            tileGridSize=(8,8)
        )

        return clahe.apply(image)

    # --------------------------------------------------

    def blur(self, image):

        """
        Lissage.
        """

        return cv2.GaussianBlur(
            image,
            GAUSSIAN_KERNEL,
            0
        )

    # --------------------------------------------------

    def detect_edges(self, image):

        """
        Détection des contours.
        """

        return cv2.Canny(
            image,
            CANNY_THRESHOLD_1,
            CANNY_THRESHOLD_2
        )

    # --------------------------------------------------

    def process(self, image):

        """
        Pipeline complet.
        """

        resized = self.resize_image(image)

        gray = self.grayscale(resized)

        denoised = self.denoise(gray)

        contrast = self.enhance_contrast(denoised)

        blurred = self.blur(contrast)

        edges = self.detect_edges(blurred)

        return {

            "original": image,

            "resized": resized,

            "gray": gray,

            "denoised": denoised,

            "contrast": contrast,

            "blurred": blurred,

            "edges": edges

        }