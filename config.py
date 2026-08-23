"""
=========================================================
WAFABAIL
Configuration File
=========================================================
Toutes les constantes du projet sont définies ici.

Ne mettez aucune logique métier dans ce fichier.
=========================================================
"""

from pathlib import Path
import os

# =========================================================
# ROOT PROJECT
# =========================================================

ROOT_DIR = Path(__file__).resolve().parent

# =========================================================
# DIRECTORIES
# =========================================================

DATASET_DIR = ROOT_DIR / "datasets"

MODEL_DIR = ROOT_DIR / "models"

TEMPLATE_DIR = ROOT_DIR / "templates"

OUTPUT_DIR = ROOT_DIR / "outputs"

DEBUG_DIR = OUTPUT_DIR / "debug"

CROP_DIR = OUTPUT_DIR / "cropped"

JSON_DIR = OUTPUT_DIR / "json"

# =========================================================
# IMAGE CONFIGURATION
# =========================================================

IMAGE_WIDTH = 1280

IMAGE_HEIGHT = 720

MAX_IMAGE_SIZE = (IMAGE_WIDTH, IMAGE_HEIGHT)

SUPPORTED_FORMATS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp"
]

# =========================================================
# PREPROCESSING
# =========================================================

GAUSSIAN_KERNEL = (5, 5)

CANNY_THRESHOLD_1 = 75

CANNY_THRESHOLD_2 = 200

MIN_DOCUMENT_AREA = 50000

MAX_ROTATION_ANGLE = 45

# =========================================================
# OCR
# =========================================================

OCR_LANGUAGE = "fr"

USE_GPU = False

OCR_DETECTION_THRESHOLD = 0.5

OCR_BOX_THRESHOLD = 0.6

OCR_UNCLIP_RATIO = 1.5

# =========================================================
# DOCUMENT TYPES
# =========================================================

DOCUMENT_TYPES = {

    "cin": "Carte Nationale",

    "permis": "Permis de conduire",

    "passport": "Passeport",

    "rc": "Registre de Commerce"

}

# =========================================================
# KEYWORDS
# =========================================================

DOCUMENT_KEYWORDS = {

    "cin": [
        "CARTE NATIONALE",
        "ROYAUME DU MAROC",
        "NATIONALE D'IDENTITE",
        "IDENTITE",
        "CARTE D'IDENTITE"
    ],

    "permis": [
        "PERMIS",
        "PERMIS DE CONDUIRE",
        "CONDUIRE",
        "DRIVING LICENCE",
        "PERMIS DE CONDUITE"
    ],

    "passport": [
        "PASSPORT",
        "PASSEPORT",
        "KINGDOM OF MOROCCO",
        "ROYAUME DU MAROC",
        "REPUBLIC OF MOROCCO"
    ],

    "rc": [
        "REGISTRE",
        "REGISTRE DE COMMERCE",
        "REGISTRE DU COMMERCE",
        "COMMERCE",
        "ICE",
        "SOCIETE"
    ]

}

# =========================================================
# LAYOUT
# =========================================================

EXPECTED_LAYOUT = {

    "cin": {

        "photo": 1,

        "logo": 1,

        "mrz": 0

    },

    "passport": {

        "photo": 1,

        "logo": 1,

        "mrz": 1

    },

    "permis": {

        "photo": 1,

        "logo": 1,

        "mrz": 0

    },

    "rc": {

        "photo": 0,

        "logo": 1,

        "mrz": 0

    }

}

# =========================================================
# CLASSIFIER
# =========================================================

CLASSIFIER_MODEL = MODEL_DIR / "classifier.pkl"

CLASSIFIER_CONFIDENCE = 0.75

# =========================================================
# DEBUG
# =========================================================

SAVE_DEBUG_IMAGES = True

SHOW_PROCESSING_STEPS = False

# =========================================================
# API
# =========================================================

API_TITLE = "WAFABAIL"

API_VERSION = "1.0.0"

API_DESCRIPTION = "Moroccan Intelligent Document Recognition System"

# =========================================================
# RANDOM SEED
# =========================================================

RANDOM_SEED = 42

# =========================================================
# CREATE FOLDERS IF THEY DON'T EXIST
# =========================================================

for directory in [

    OUTPUT_DIR,

    DEBUG_DIR,

    CROP_DIR,

    JSON_DIR,

    MODEL_DIR

]:

    os.makedirs(directory, exist_ok=True)