# WAFABAIL — Intelligent Document Processing

> **Automatisation de la classification et de l'extraction intelligente des documents administratifs grâce à l'OCR et au Machine Learning.**

---

## 📌 Présentation du projet

**WAFABAIL-OCR** est une solution intelligente de traitement automatisé de documents conçue pour **identifier, analyser et extraire automatiquement les informations importantes présentes dans différents documents administratifs**.

Le projet répond à un problème concret : le traitement manuel de documents tels que les cartes d'identité, passeports, permis de conduire et documents du registre de commerce demande du temps, nécessite une intervention humaine et peut être source d'erreurs.

L'objectif de WAFABAIL est donc de transformer ce processus manuel en un **pipeline automatisé capable de comprendre un document à partir d'une simple image ou d'un fichier PDF**.

Le système prend un document en entrée et réalise automatiquement :

```text
Document
   │
   ▼
Prétraitement de l'image
   │
   ▼
OCR
   │
   ▼
Classification du document
   │
   ▼
Extraction des informations
   │
   ▼
Validation des données
   │
   ▼
Résultat structuré
```

---

# 🎯 Pourquoi WAFABAIL a été créé ?

Dans de nombreux processus administratifs et financiers, les collaborateurs doivent traiter quotidiennement différents types de documents.

Par exemple :

* Carte d'identité nationale (CIN)
* Passeport
* Permis de conduire
* Registre de commerce (RC)

Traditionnellement, l'opérateur doit :

1. ouvrir le document ;
2. identifier manuellement son type ;
3. rechercher les informations importantes ;
4. recopier les données ;
5. vérifier leur exactitude ;
6. enregistrer les informations dans un système.

Cette méthode présente plusieurs problèmes :

* ⏱️ perte de temps ;
* ✍️ saisie manuelle répétitive ;
* ❌ risque d'erreurs humaines ;
* 📄 difficulté à traiter un grand nombre de documents ;
* 🔄 absence d'automatisation ;
* 📊 difficulté à standardiser les données extraites.

**WAFABAIL a donc été conçu pour automatiser ces différentes étapes.**

L'utilisateur fournit simplement un document et le système tente automatiquement de déterminer :

> **Quel est le type du document ?**

puis :

> **Quelles sont les informations importantes présentes dans ce document ?**

---

# 🧠 Objectifs du projet

Les principaux objectifs de WAFABAIL sont :

### 1. Classification automatique

Identifier automatiquement le type du document parmi quatre catégories :

| Classe     | Document                   |
| ---------- | -------------------------- |
| `CIN`      | Carte d'Identité Nationale |
| `PASSPORT` | Passeport                  |
| `PERMIS`   | Permis de conduire         |
| `RC`       | Registre de Commerce       |

---

### 2. Extraction automatique

Une fois le document identifié, WAFABAIL utilise l'OCR afin de récupérer automatiquement les informations importantes.

Par exemple :

**CIN**

* Nom
* Prénom
* Date de naissance
* Numéro CIN
* Lieu de naissance

**Passeport**

* Nom
* Prénom
* Numéro de passeport
* Date de naissance
* Nationalité
* Date d'expiration

**Permis**

* Nom
* Prénom
* Numéro du permis
* Date de naissance
* Date de délivrance
* Catégories

**RC**

* Dénomination sociale
* Forme juridique
* Capital
* Adresse
* Numéro RC
* ICE
* Date d'inscription

---

# 🏗️ Architecture du système

WAFABAIL est organisé sous forme de plusieurs étapes indépendantes.

```text
                         ┌─────────────────────┐
                         │       DOCUMENT      │
                         │   Image / PDF       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   PREPROCESSING     │
                         │                     │
                         │ • Resize            │
                         │ • Deskew             │
                         │ • Denoising         │
                         │ • Contrast           │
                         │ • Thresholding       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │        OCR          │
                         │                     │
                         │ EasyOCR / Tesseract │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   CLASSIFICATION    │
                         │                     │
                         │ CIN                 │
                         │ Passport            │
                         │ Permis              │
                         │ RC                  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     EXTRACTION      │
                         │                     │
                         │ Extracteur adapté   │
                         │ au type de document │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     VALIDATION      │
                         │                     │
                         │ Regex               │
                         │ règles métier       │
                         │ cohérence           │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       OUTPUT        │
                         │                     │
                         │ JSON / Interface    │
                         └─────────────────────┘
```

---

# 🔍 Fonctionnement détaillé

## Étape 1 — Upload du document

L'utilisateur importe une image ou un document compatible depuis l'interface Streamlit.

Formats typiquement utilisés :

```text
.jpg
.jpeg
.png
.pdf
```

---

## Étape 2 — Prétraitement

Les documents réels peuvent être :

* inclinés ;
* sombres ;
* flous ;
* bruités ;
* photographiés avec un téléphone ;
* mal éclairés ;
* de résolution différente.

Avant de lancer l'OCR, l'image passe donc par une étape de prétraitement.

Les opérations peuvent inclure :

* redimensionnement ;
* correction de l'inclinaison ;
* amélioration du contraste ;
* réduction du bruit ;
* binarisation ;
* amélioration de la lisibilité.

L'objectif est simple :

> **Fournir à l'OCR une image aussi lisible que possible.**

---

# 🔤 OCR — Optical Character Recognition

L'OCR signifie :

**Optical Character Recognition**

ou en français :

**Reconnaissance Optique de Caractères.**

Son rôle est de transformer les caractères présents dans l'image en texte exploitable par le programme.

Par exemple, une image contenant :

```text
ROYAUME DU MAROC

CARTE NATIONALE D'IDENTITE

NOM : ALAOUI
PRENOM : MOHAMMED
```

devient approximativement :

```text
ROYAUME DU MAROC
CARTE NATIONALE D'IDENTITE
NOM : ALAOUI
PRENOM : MOHAMMED
```

Ce texte peut ensuite être analysé automatiquement.

---

# 🤖 Classification des documents

La classification est une étape essentielle du projet.

WAFABAIL doit déterminer automatiquement si le document correspond à :

```text
CIN
PASSPORT
PERMIS
RC
```

La classification utilise plusieurs indices.

Par exemple :

### CIN

La présence de termes tels que :

```text
CARTE
NATIONALE
IDENTITE
NATIONAL
IDENTIFICATION
```

peut indiquer une CIN.

### Passeport

Des indices tels que :

```text
PASSPORT
PASSEPORT
MRZ
P<
```

sont particulièrement importants.

### Permis

Des mots comme :

```text
PERMIS
CONDUIRE
DRIVING
PERMIT
```

peuvent être utilisés.

### RC

Le système recherche notamment :

```text
REGISTRE
COMMERCE
RC
ICE
CERTIFICAT
IMMATRICULATION
```

---

# 🧠 Approche hybride

Une caractéristique importante de WAFABAIL est l'utilisation d'une **approche hybride**.

Le système ne dépend pas uniquement d'un modèle Machine Learning.

Il combine :

```text
OCR
+
Règles métier
+
Signatures documentaires
+
Regex
+
Machine Learning
```

Cette approche permet d'améliorer la robustesse du système lorsque le nombre de documents d'entraînement est limité.

Les signatures documentaires fortes sont utilisées en priorité lorsque cela est possible.

Le Machine Learning peut ensuite servir de mécanisme complémentaire lorsque les règles ne permettent pas de prendre une décision suffisamment claire.

---

# 📊 Machine Learning

Le projet contient également une composante de classification basée sur le Machine Learning.

Les caractéristiques extraites du document peuvent notamment être liées à :

* présence de mots-clés ;
* longueur du texte ;
* présence de certains motifs ;
* caractéristiques OCR ;
* présence de MRZ ;
* caractéristiques visuelles.

Un **Random Forest** peut ensuite être utilisé comme classifieur complémentaire.

### Pourquoi Random Forest ?

Random Forest présente plusieurs avantages :

* simple à utiliser ;
* robuste ;
* efficace sur des données tabulaires ;
* capable de gérer plusieurs caractéristiques ;
* relativement facile à interpréter.

Cependant, le dataset actuel étant volontairement limité, le modèle ML n'est pas considéré comme l'unique source de vérité.

---

# 📑 Extraction des données

Après avoir identifié le type du document, WAFABAIL utilise un extracteur spécifique.

```text
             Classification
                   │
       ┌───────────┼───────────┐
       │           │           │
      CIN      PASSPORT      PERMIS       RC
       │           │           │           │
       ▼           ▼           ▼           ▼
   CINParser   PassportParser PermitParser RCParser
```

Chaque extracteur applique des règles adaptées à la structure du document.

---

# 🪪 Extraction CIN

Pour une CIN, le système cherche notamment :

```text
Nom
Prénom
Numéro CIN
Date de naissance
Lieu de naissance
```

Les expressions régulières et les positions relatives des champs sont utilisées afin de limiter les erreurs de l'OCR.

---

# 🛂 Extraction Passeport

Les passeports présentent une caractéristique particulièrement intéressante :

## MRZ

La **Machine Readable Zone** est la zone composée de lignes de caractères située généralement au bas du passeport.

Exemple conceptuel :

```text
P<MARALAOUI<<MOHAMMED<<<<<<<<<<<<
AB1234567MAR9001011M3001012<<<<<<
```

La MRZ permet notamment de récupérer :

* numéro de passeport ;
* nom ;
* prénom ;
* nationalité ;
* date de naissance ;
* date d'expiration.

La détection de MRZ est volontairement plus stricte afin d'éviter qu'une simple chaîne alphanumérique soit considérée comme une MRZ.

---

# 🚗 Extraction Permis

Pour le permis, le système recherche notamment :

```text
Nom
Prénom
Numéro du permis
Date de naissance
Date de délivrance
Catégories
```

Une attention particulière est portée au numéro du permis et aux labels présents autour des informations.

---

# 🏢 Extraction RC

Le Registre de Commerce possède une structure différente des documents d'identité.

Le système recherche notamment :

```text
Dénomination sociale
Forme juridique
Capital
Adresse
RC
ICE
Date d'inscription
```

Les informations sont recherchées en tenant compte des labels et de leur contexte afin d'éviter de récupérer du texte voisin qui n'appartient pas au champ recherché.

---

# ✅ Validation des données

L'OCR n'est jamais parfait.

Il peut par exemple transformer :

```text
O
```

en :

```text
0
```

ou :

```text
I
```

en :

```text
1
```

WAFABAIL applique donc différentes règles de validation.

Exemples :

* validation des dates ;
* validation des numéros ;
* vérification des formats ;
* suppression de valeurs impossibles ;
* contrôle des champs obligatoires ;
* vérification de cohérence.

L'objectif est de ne pas simplement extraire du texte, mais de produire des **données structurées et exploitables**.

---

# 🖥️ Interface utilisateur

L'application utilise **Streamlit** afin de fournir une interface web simple et interactive.

L'utilisateur peut :

### 📤 1. Importer un document

Glisser-déposer une image ou un PDF.

### 🔎 2. Lancer l'analyse

Le pipeline réalise automatiquement :

```text
Preprocessing
       ↓
OCR
       ↓
Classification
       ↓
Extraction
       ↓
Validation
```

### 📊 3. Consulter le résultat

L'interface affiche notamment :

* type du document ;
* niveau de confiance ;
* informations extraites ;
* texte OCR ;
* informations de diagnostic.

### ✏️ 4. Corriger les informations

Les champs extraits peuvent être vérifiés et corrigés manuellement avant utilisation.

### 📥 5. Exporter

Les informations peuvent être exportées dans un format structuré, notamment JSON.

---

# 📁 Structure du projet

Une organisation typique du projet est :

```text
WAFABAIL/
│
├── app.py
├── ui.py
├── pipeline.py
│
├── classifier.py
├── document_classifier.py
│
├── extractor.py
├── document_extractor.py
│
├── robust_preprocess.py
├── preprocessing.py
│
├── ocr.py
├── ocr_engine.py
│
├── requirements.txt
├── requirements_fallback.txt
│
├── README.md
│
├── models/
│   └── ...
│
├── data/
│   ├── cin/
│   ├── passport/
│   ├── permis/
│   └── rc/
│
└── ...
```

> Les noms exacts des fichiers peuvent évoluer avec les versions du projet.

---

# 🛠️ Technologies utilisées

## Python

Langage principal utilisé pour développer le pipeline.

## OpenCV

Utilisé pour le traitement et l'amélioration des images.

Principales opérations :

* resize ;
* deskew ;
* denoising ;
* thresholding ;
* traitement des contours.

## EasyOCR

Moteur OCR principal permettant de reconnaître les caractères présents dans les documents.

## Tesseract OCR

Une solution alternative peut être utilisée lorsque EasyOCR n'est pas disponible ou lorsque l'environnement l'exige.

## Scikit-learn

Utilisé notamment pour la partie Machine Learning et le Random Forest.

## NumPy

Utilisé pour la manipulation des données numériques et des images.

## Pandas

Utilisé pour la manipulation et l'analyse des données lorsque nécessaire.

## Streamlit

Utilisé pour construire l'interface utilisateur interactive.

---

# ⚙️ Installation

## 1. Cloner le repository

```bash
git clone https://github.com/USERNAME/WAFABAIL.git
cd WAFABAIL
```

Remplacer `USERNAME` par le nom du compte GitHub contenant le projet.

---

## 2. Créer un environnement virtuel

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

---

## 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

# 🔧 Alternative OCR avec Tesseract

Si EasyOCR rencontre un problème d'installation ou d'exécution, Tesseract peut être utilisé comme solution alternative.

### macOS

```bash
brew install tesseract
brew install tesseract-lang
```

Puis :

```bash
pip install -r requirements_fallback.txt
```

---

# 🚀 Lancement de l'application

Lancer l'interface Streamlit :

```bash
streamlit run ui.py
```

Une adresse locale sera ensuite affichée dans le terminal.

Généralement :

```text
http://localhost:8501
```

Ouvrir cette adresse dans un navigateur.

---

# 🧪 Exemple d'utilisation

### Étape 1

L'utilisateur ouvre WAFABAIL.

### Étape 2

Il importe une CIN :

```text
cin.jpg
```

### Étape 3

WAFABAIL effectue :

```text
Image
 ↓
Preprocessing
 ↓
OCR
 ↓
Classification
```

Le système peut retourner :

```json
{
    "document_type": "CIN",
    "confidence": 0.96
}
```

### Étape 4

L'extracteur CIN récupère :

```json
{
    "nom": "ALAOUI",
    "prenom": "MOHAMMED",
    "date_naissance": "01/01/1995",
    "numero_cin": "AB123456"
}
```

### Étape 5

L'utilisateur vérifie les informations puis peut exporter le résultat.

---

# 📦 Exemple de sortie JSON

```json
{
    "document_type": "CIN",
    "confidence": 0.96,
    "fields": {
        "nom": "ALAOUI",
        "prenom": "MOHAMMED",
        "date_naissance": "01/01/1995",
        "numero_cin": "AB123456"
    }
}
```

---

# 🔐 Sécurité et confidentialité

Les documents d'identité peuvent contenir des informations personnelles sensibles.

Dans un environnement réel, il est donc recommandé de :

* ne pas stocker les documents inutilement ;
* supprimer les fichiers temporaires après traitement ;
* chiffrer les données sensibles ;
* contrôler les accès ;
* éviter de publier des documents réels dans le repository GitHub ;
* utiliser uniquement des données anonymisées pour les tests ;
* protéger les logs contenant potentiellement des informations personnelles.

### ⚠️ Important

**Ne jamais mettre de vraies CIN, passeports, permis ou documents contenant des données personnelles dans un repository GitHub public.**

Utiliser uniquement :

```text
documents anonymisés
```

ou :

```text
documents de démonstration
```

---

# 📈 Limites actuelles

WAFABAIL constitue une base fonctionnelle d'Intelligent Document Processing, mais plusieurs améliorations peuvent encore être apportées.

### Dataset

Le dataset actuel est limité.

Pour améliorer significativement la classification, il serait nécessaire d'utiliser davantage de documents pour chaque classe.

Par exemple :

```text
500+ CIN
500+ Passeports
500+ Permis
500+ RC
```

avec différentes conditions :

* qualité variable ;
* rotation ;
* éclairage différent ;
* photos prises au téléphone ;
* scans ;
* différentes générations de documents.

---

# 🚀 Améliorations futures

Plusieurs évolutions peuvent être envisagées.

## 1. Dataset plus important

Augmenter considérablement le nombre de documents d'entraînement.

---

## 2. Deep Learning

Remplacer ou compléter le Random Forest avec un modèle spécialisé en classification d'images/document.

Par exemple :

* CNN ;
* EfficientNet ;
* ResNet ;
* Vision Transformer.

---

## 3. Layout Analysis

Ajouter une véritable analyse de la structure du document afin de comprendre :

```text
LABEL → VALEUR
```

plutôt que de dépendre uniquement du texte OCR.

---

## 4. Détection automatique des champs

Utiliser les bounding boxes OCR pour déterminer automatiquement la relation spatiale entre :

```text
NOM:
```

et :

```text
ALAOUI
```

---

## 5. Support de documents supplémentaires

L'architecture peut être étendue à :

* factures ;
* relevés bancaires ;
* contrats ;
* bulletins ;
* cartes professionnelles ;
* documents fiscaux.

---

# 📊 Pourquoi utiliser une approche hybride ?

Une solution basée uniquement sur des règles peut devenir difficile à maintenir.

Une solution basée uniquement sur le Machine Learning nécessite généralement beaucoup de données.

WAFABAIL combine donc les deux approches.

```text
             OCR
              │
              ▼
       Signatures fortes ?
          │          │
         Oui        Non
          │          │
          ▼          ▼
    Classification   ML
      directe       fallback
          │          │
          └────┬─────┘
               ▼
          Extraction
               │
               ▼
           Validation
```

Cette architecture permet d'obtenir un compromis entre :

* précision ;
* simplicité ;
* rapidité ;
* interprétabilité ;
* évolutivité.

---

# 🎓 Contexte du projet

WAFABAIL a été développé dans le cadre d'un projet d'**Intelligent Document Processing**.

Le projet met en pratique plusieurs domaines de l'intelligence artificielle et du développement logiciel :

* Computer Vision ;
* OCR ;
* Machine Learning ;
* traitement d'images ;
* Natural Language Processing ;
* extraction d'informations ;
* validation de données ;
* développement d'une interface web.

L'objectif principal était de construire une solution capable de rapprocher les techniques d'intelligence artificielle d'un **cas d'utilisation réel dans le traitement documentaire**.

---

# 🏦 Cas d'utilisation potentiel

Une telle solution peut être intégrée dans des processus nécessitant la collecte automatique d'informations depuis des documents administratifs.

Par exemple :

```text
Client
  │
  ▼
Upload document
  │
  ▼
WAFABAIL
  │
  ├── Classification
  │
  ├── OCR
  │
  ├── Extraction
  │
  └── Validation
  │
  ▼
Données structurées
  │
  ▼
Système métier
```

Cela permettrait de réduire la saisie manuelle et d'accélérer le traitement documentaire.

---

# 📝 État du projet

**Statut :** 🟢 Prototype fonctionnel / Proof of Concept

Fonctionnalités principales :

* [x] Upload de documents
* [x] Prétraitement
* [x] OCR
* [x] Classification CIN
* [x] Classification Passeport
* [x] Classification Permis
* [x] Classification RC
* [x] Extraction des informations
* [x] Validation des champs
* [x] Interface Streamlit
* [x] Export des résultats
* [ ] Dataset industriel de grande taille
* [ ] Modèle Deep Learning avancé
* [ ] Déploiement cloud
* [ ] API REST de production
* [ ] Monitoring et logging avancés

---

# 👨‍💻 Auteur

Projet développé dans le cadre d'un projet d'**Intelligent Document Processing / OCR / Machine Learning**.

**WAFABAIL**

---

# 📄 Licence

Ce projet est destiné à des fins de développement, de démonstration et de recherche.

La licence peut être adaptée selon les besoins du projet et les conditions d'utilisation des modèles, bibliothèques et données utilisées.

---

# ⭐ Conclusion

**WAFABAIL** a pour objectif de transformer le traitement manuel de documents administratifs en un processus automatisé.

À partir d'un simple document, le système réalise :

```text
📄 Document
      ↓
🖼️ Prétraitement
      ↓
🔤 OCR
      ↓
🤖 Classification
      ↓
📝 Extraction
      ↓
✅ Validation
      ↓
📊 Données structurées
```

Le projet constitue ainsi une base pour développer une solution complète d'**Intelligent Document Processing**, capable à terme de traiter automatiquement un volume important de documents avec une intervention humaine minimale.
