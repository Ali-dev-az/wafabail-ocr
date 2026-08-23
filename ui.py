"""
WAFABAIL - Intelligent Document Processing
Interface Streamlit interactive pour classification, OCR, extraction et validation.

Lancer avec:
    streamlit run ui.py
"""

import copy
import json
import tempfile
from pathlib import Path

import streamlit as st
from PIL import Image

from pipeline import DocumentPipeline


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="WAFABAIL | Intelligent Document Processing",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# STYLE
# =========================================================

st.markdown(
    """
    <style>
    .stApp {
        background: #f5f7fb;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #102a43 0%, #173f5f 100%);
    }

    [data-testid="stSidebar"] * {
        color: white !important;
    }

    .brand {
        padding: 18px 20px;
        border-radius: 16px;
        background: linear-gradient(135deg, #0b1f33, #176b87);
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 8px 25px rgba(16, 42, 67, .18);
    }

    .brand h1 {
        margin: 0;
        font-size: 28px;
        letter-spacing: .5px;
    }

    .brand p {
        margin: 6px 0 0 0;
        opacity: .85;
        font-size: 13px;
    }

    .hero {
        padding: 28px 30px;
        border-radius: 20px;
        background: linear-gradient(135deg, #ffffff 0%, #edf5fa 100%);
        border: 1px solid #dbe5ed;
        box-shadow: 0 8px 30px rgba(16, 42, 67, .07);
        margin-bottom: 22px;
    }

    .hero h1 {
        margin: 0 0 7px 0;
        color: #102a43;
        font-size: 34px;
    }

    .hero p {
        margin: 0;
        color: #52606d;
    }

    .upload-card {
        padding: 8px 0;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e1e8ef;
        border-radius: 14px;
        padding: 12px;
        box-shadow: 0 4px 16px rgba(16, 42, 67, .05);
    }

    .status-ok {
        padding: 12px 16px;
        border-radius: 12px;
        background: #e8f7ef;
        color: #176b45;
        border: 1px solid #bfe7d0;
        font-weight: 600;
    }

    .status-warning {
        padding: 12px 16px;
        border-radius: 12px;
        background: #fff7e6;
        color: #8a5a00;
        border: 1px solid #f3d28a;
        font-weight: 600;
    }

    .field-label {
        font-size: 12px;
        color: #627d98;
        margin-bottom: 2px;
    }

    .footer {
        text-align: center;
        color: #829ab1;
        font-size: 12px;
        padding: 28px 0 8px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HELPERS
# =========================================================

@st.cache_resource(show_spinner=False)
def get_pipeline():
    return DocumentPipeline()


def confidence_label(value):
    value = float(value or 0)
    if value >= 0.85:
        return "Élevée"
    if value >= 0.65:
        return "Moyenne"
    return "Faible"


def flatten_fields(data, prefix=""):
    """Retourne les champs éditables sous forme de tuples (chemin, valeur)."""
    rows = []
    if not isinstance(data, dict):
        return rows
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            rows.extend(flatten_fields(value, path))
        elif isinstance(value, list):
            rows.append((path, ", ".join(map(str, value))))
        else:
            rows.append((path, "" if value is None else str(value)))
    return rows


def set_nested_value(data, path, value):
    parts = path.split(".")
    current = data
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value


def pretty_name(path):
    label = path.split(".")[-1].replace("_", " ")
    return label[:1].upper() + label[1:]


def clean_result_for_download(result):
    """Évite de mettre les très grosses données de fingerprint dans l'export UI."""
    export = copy.deepcopy(result)
    export.pop("fingerprint", None)
    return export


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <h1>WAFABAIL</h1>
            <p>Intelligent Document Processing</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 📌 Types supportés")
    st.markdown("- 🪪 CIN")
    st.markdown("- 🛂 Passeport")
    st.markdown("- 🚗 Permis")
    st.markdown("- 🏢 Registre de Commerce (RC)")

    st.markdown("---")
    st.markdown("### ⚙️ Pipeline")
    st.caption("Détection → OCR → Classification → Extraction → Validation")

    if st.session_state.get("result"):
        st.markdown("---")
        if st.button("🗑️ Nouvelle analyse", use_container_width=True):
            st.session_state.pop("result", None)
            st.session_state.pop("edited_extraction", None)
            st.rerun()


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="hero">
        <h1>📄 WAFABAIL Document Intelligence</h1>
        <p>Classification automatique, OCR et extraction intelligente des documents.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# UPLOAD AREA
# =========================================================

left, right = st.columns([1.7, 1], gap="large")

with left:
    st.markdown("### 📤 Importer un document")
    uploaded = st.file_uploader(
        "Glissez-déposez votre document ici ou cliquez pour parcourir",
        type=["jpg", "jpeg", "png", "webp", "bmp"],
        help="Formats acceptés : JPG, JPEG, PNG, WEBP et BMP",
    )

with right:
    st.markdown("### ℹ️ Fonctionnement")
    st.info(
        "Le document est d'abord détecté et prétraité, puis analysé par OCR. "
        "Le moteur identifie ensuite son type et extrait les champs pertinents."
    )


if uploaded is not None:
    try:
        image = Image.open(uploaded)
    except Exception as exc:
        st.error(f"Impossible de lire le document : {exc}")
        st.stop()

    st.markdown("### 👁️ Aperçu")
    preview_col, action_col = st.columns([1.8, 1], gap="large")

    with preview_col:
        st.image(image, caption=uploaded.name, use_container_width=True)

    with action_col:
        st.markdown("#### Prêt pour l'analyse")
        st.write(f"**Fichier :** {uploaded.name}")
        st.write(f"**Format :** {image.format or 'Image'}")
        st.write(f"**Dimensions :** {image.width} × {image.height}")

        analyze = st.button(
            "🚀 ANALYSER LE DOCUMENT",
            type="primary",
            use_container_width=True,
        )

        if analyze:
            suffix = Path(uploaded.name).suffix or ".png"
            tmp_path = None

            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded.getbuffer())
                    tmp_path = tmp.name

                progress = st.progress(0, text="Initialisation du pipeline…")
                status = st.empty()

                status.info("🔍 Détection et prétraitement du document…")
                progress.progress(20)

                pipeline = get_pipeline()

                status.info("🔤 OCR et analyse de la structure…")
                progress.progress(45)

                result = pipeline.process(tmp_path)

                status.info("🧠 Classification et extraction des informations…")
                progress.progress(75)

                st.session_state["result"] = result
                st.session_state["edited_extraction"] = copy.deepcopy(
                    result.get("extraction", {})
                )

                progress.progress(100, text="Analyse terminée")
                status.success("✅ Document analysé avec succès")

            except Exception as exc:
                st.error(f"❌ Erreur pendant l'analyse : {exc}")
            finally:
                if tmp_path:
                    Path(tmp_path).unlink(missing_ok=True)


# =========================================================
# RESULTS
# =========================================================

result = st.session_state.get("result")

if result:
    st.markdown("---")
    st.markdown("## 📊 Résultats de l'analyse")

    document_type = str(result.get("document_type", "inconnu")).upper()
    confidence = float(result.get("confidence", 0) or 0)
    validation = result.get("validation", {}) or {}

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📄 Type détecté", document_type)
    m2.metric("🎯 Confiance", f"{confidence * 100:.1f}%")
    m3.metric("🧠 Niveau", confidence_label(confidence))
    m4.metric("✅ Validation", "Valide" if validation.get("valid") else "À vérifier")

    st.markdown("### 🔎 Statut")
    if validation.get("valid"):
        st.markdown(
            '<div class="status-ok">✓ Le document respecte les règles de validation.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="status-warning">⚠️ Certaines informations doivent être vérifiées.</div>',
            unsafe_allow_html=True,
        )

    tab_extract, tab_class, tab_ocr, tab_debug = st.tabs(
        ["📝 Données extraites", "🧠 Classification", "🔤 OCR", "🔧 Diagnostic"]
    )

    # -----------------------------------------------------
    # EXTRACTION / EDITABLE
    # -----------------------------------------------------
    with tab_extract:
        st.caption("Les champs peuvent être corrigés manuellement avant l'export.")

        extraction = st.session_state.get("edited_extraction", {})
        fields = flatten_fields(extraction)

        if fields:
            cols = st.columns(2)
            for index, (path, value) in enumerate(fields):
                with cols[index % 2]:
                    new_value = st.text_input(
                        pretty_name(path),
                        value=value,
                        key=f"field_{path}",
                    )
                    set_nested_value(extraction, path, new_value)

            st.session_state["edited_extraction"] = extraction
        else:
            st.warning("Aucune donnée structurée n'a été extraite.")

        st.markdown("#### Résultat JSON")
        result_for_export = clean_result_for_download(result)
        result_for_export["extraction"] = extraction

        st.code(
            json.dumps(extraction, ensure_ascii=False, indent=2),
            language="json",
        )

        st.download_button(
            "⬇️ Télécharger les données extraites (JSON)",
            data=json.dumps(result_for_export, ensure_ascii=False, indent=2),
            file_name="WAFABAIL_document_result.json",
            mime="application/json",
            use_container_width=True,
        )

    # -----------------------------------------------------
    # CLASSIFICATION
    # -----------------------------------------------------
    with tab_class:
        classification = result.get("classification", {}) or {}
        st.json(classification)

        scores = classification.get("scores") or classification.get("probabilities")
        if isinstance(scores, dict):
            st.markdown("#### Scores par type")
            for label, score in scores.items():
                try:
                    numeric = float(score)
                except (TypeError, ValueError):
                    continue
                st.write(f"**{str(label).upper()}** — {numeric * 100:.1f}%")
                st.progress(min(max(numeric, 0.0), 1.0))

    # -----------------------------------------------------
    # OCR
    # -----------------------------------------------------
    with tab_ocr:
        ocr = result.get("ocr", {}) or {}
        text = ocr.get("text", "")
        st.text_area(
            "Texte détecté par OCR",
            value=text,
            height=420,
        )

        if ocr:
            with st.expander("Métadonnées OCR"):
                st.json({k: v for k, v in ocr.items() if k != "text"})

    # -----------------------------------------------------
    # DIAGNOSTIC
    # -----------------------------------------------------
    with tab_debug:
        errors = validation.get("errors", []) or []
        warnings = validation.get("warnings", []) or []

        if errors:
            st.error("Erreurs de validation")
            for error in errors:
                st.write(f"• {error}")

        if warnings:
            st.warning("Avertissements")
            for warning in warnings:
                st.write(f"• {warning}")

        with st.expander("Voir le résultat technique complet"):
            st.json(clean_result_for_download(result))


st.markdown(
    '<div class="footer">WAFABAIL · Intelligent Document Processing · CIN · Passeport · Permis · RC</div>',
    unsafe_allow_html=True,
)
