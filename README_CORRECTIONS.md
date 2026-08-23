# WAFABAIL — version corrigée

## Corrections principales

1. **Classification**
   - Les signatures textuelles OCR passent avant le Random Forest.
   - Passeport = MRZ/PASSEPORT prioritaire.
   - Permis = PERMIS + CONDUIRE.
   - RC = REGISTRE + COMMERCE / CERTIFICAT + IMMATRICULATION / ICE.
   - CIN = CARTE + NATIONALE + IDENTITE.
   - Le Random Forest ne sert plus qu'en fallback lorsque l'OCR est ambigu.

2. **OCR**
   - Le choix de la meilleure variante n'est plus biaisé par les mots de la CIN.
   - Les coordonnées des boîtes OCR sont remises dans le repère de l'image originale après agrandissement x2.
   - Fallback Tesseract si EasyOCR n'est pas disponible.

3. **Extraction**
   - Extraction textuelle prioritaire autour des labels pour éviter que le champ suivant soit aspiré.
   - RC : société, forme juridique, capital, adresse, dénomination, activité, RC, ICE et date d'inscription.
   - Permis : numéro, prénom, nom, date de naissance et date de délivrance.
   - Passeport : numéro et informations MRZ.
   - CIN : numéro et informations personnelles avec correction des dates futures.

4. **Pipeline**
   - Correction d'un bug important : l'extracteur recevait `ocr_result["text"]` (une chaîne) au lieu de `ocr_result` (le dictionnaire OCR complet).

## Lancer l'interface

```bash
cd DocAi
python3 -m pip install -r requirements.txt
streamlit run ui.py
```

Si EasyOCR/PyTorch pose problème sur la machine, Tesseract peut servir de fallback :

```bash
brew install tesseract
brew install tesseract-lang
```

Puis relancer :

```bash
streamlit run ui.py
```

## Test CLI

```bash
python3 app.py datasets/cin/images/CIN_1.png
```

ou :

```bash
python3 -m py_compile *.py extractors/*.py utils/*.py
```

## Important

Le dataset fourni contient seulement 12 images (3 par classe). Le modèle Random Forest ne doit donc pas être considéré comme la source principale de vérité. Pour une version production, ajouter beaucoup plus d'exemples par classe, avec plusieurs qualités, angles, éclairages et arrière-plans.


## Mode de secours très rapide

Si l'installation EasyOCR/PyTorch bloque sur Mac M1, installez uniquement :

```bash
python3 -m pip install -r requirements_fallback.txt
brew install tesseract
brew install tesseract-lang
streamlit run ui.py
```

Le moteur OCR détecte automatiquement l'absence d'EasyOCR et bascule vers Tesseract.
