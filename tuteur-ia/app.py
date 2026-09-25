import streamlit as st
from google import genai
from google.genai import types
import json
import re
import stripe
import io
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ============================================================
# CHARGEMENT DES TRADUCTIONS (AVANT set_page_config)
# ============================================================
@st.cache_data
def charger_traductions():
    chemin_script = os.path.dirname(os.path.abspath(__file__))
    chemin_fichier = os.path.join(chemin_script, "translations.json")
    with open(chemin_fichier, "r", encoding="utf-8") as f:
        return json.load(f)

TRADUCTIONS = charger_traductions()

LANGUES = {
    "🇫🇷 Français": "fr",
    "🇬🇧 English": "en",
    "🇩🇪 Deutsch": "de",
    "🇪🇸 Español": "es",
    "🇮🇹 Italiano": "it",
    "🇸🇦 العربية": "ar"
}

# ============================================================
# DÉTECTION AUTOMATIQUE DE LA LANGUE DU NAVIGATEUR
# ============================================================
def detecter_langue_navigateur():
    """
    Lit l'en-tête HTTP 'Accept-Language' envoyé par le navigateur.
    Ex: 'en-US,en;q=0.9,fr;q=0.8' → retourne 'en'
    Fallback : 'en' si rien n'est détecté.
    Nécessite Streamlit >= 1.37 pour st.context.headers.
    """
    langues_supportees = {"fr", "en", "de", "es", "it", "ar"}
    try:
        accept_lang = st.context.headers.get("Accept-Language", "")
        for part in accept_lang.split(","):
            code = part.split(";")[0].strip().lower()[:2]
            if code in langues_supportees:
                return code
    except Exception:
        pass
    return "en"

if "langue" not in st.session_state:
    st.session_state.langue = detecter_langue_navigateur()

# ============================================================
# CONFIGURATION DE LA PAGE (titre dynamique selon langue)
# ============================================================
st.set_page_config(
    page_title=TRADUCTIONS[st.session_state.langue].get("page_title", "Math Coach"),
    page_icon="📐",
    layout="centered"
)

# ============================================================
# SÉLECTEUR DE LANGUE (dans la sidebar)
# ============================================================
with st.sidebar:
    st.markdown("### 🌍 Language / Langue / Sprache / Idioma / Lingua / اللغة")
    choix = st.selectbox(
        "Choisissez votre langue :",
        options=list(LANGUES.keys()),
        index=list(LANGUES.values()).index(st.session_state.langue),
        label_visibility="collapsed"
    )
    st.session_state.langue = LANGUES[choix]

# ============================================================
# CSS POUR L'ARABE (droite à gauche)
# ============================================================
def injecter_css(langue):
    if langue == "ar":
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
        html, body, [class*="css"], .stApp {
            direction: rtl;
            text-align: right;
            font-family: 'Cairo', sans-serif;
        }
        .stTextArea textarea, .stTextInput input {
            direction: rtl;
            text-align: right;
        }
        .stMarkdown, .stMarkdown p, .stMarkdown li,
        h1, h2, h3, h4, h5, h6 {
            direction: rtl;
            text-align: right;
        }
        [data-testid="stSidebar"] {
            direction: rtl;
            text-align: right;
        }
        .stButton > button, .stDownloadButton > button {
            direction: rtl;
        }
        .katex, .MathJax, .katex-display {
            direction: ltr !important;
        }
        </style>
        """, unsafe_allow_html=True)

injecter_css(st.session_state.langue)

# ============================================================
# FONCTION DE TRADUCTION
# ============================================================
def t(cle, **kwargs):
    """Fonction de traduction avec interpolation."""
    texte = TRADUCTIONS[st.session_state.langue].get(cle, cle)
    if kwargs:
        try:
            return texte.format(**kwargs)
        except (KeyError, IndexError):
            return texte
    return texte

# ============================================================
# RÉCUPÉRATION DES SECRETS
# ============================================================
try:
    if "CLE_API" in st.secrets:
        cle_pour_ia = st.secrets["CLE_API"]
    else:
        cle_pour_ia = st.secrets["GEMINI_API_KEY"]
    client_ia = genai.Client(api_key=cle_pour_ia)
except Exception as e:
    st.error(t("ai_init_error", error=str(e)))

stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
ID_PRIX_UNIQUE = st.secrets["STRIPE_PRICE_ID"]
URL_APP = st.secrets["MON_URL_STREAMLIT"]

# ============================================================
# VÉRIFICATION ANTI-FRAUDE
# ============================================================
query_params = st.query_params
est_abonne = False
email_eleve = ""
est_rembourse = False

if "session_id" in query_params:
    try:
        session = stripe.checkout.Session.retrieve(
            query_params["session_id"],
            expand=['payment_intent']
        )
        email_eleve = session.customer_details.email if session.customer_details else ""
        payment_intent = session.payment_intent
        if payment_intent and payment_intent.get("amount_refunded", 0) > 0:
            est_rembourse = True
        if session.payment_status == "paid" and not est_rembourse:
            est_abonne = True
    except Exception:
        st.error(t("verif_error"))

# ============================================================
# FONCTION PDF (avec support arabe)
# ============================================================
def generer_pdf(texte_correction, enonce_exercice):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40,
        title=t("pdf_title")
    )
    styles = getSampleStyleSheet()

    # Détection de la langue arabe
    langue = st.session_state.get("langue", "fr")
    est_arabe = (langue == "ar")

    # Police adaptée
    police = "Helvetica"
    if est_arabe:
        chemin_police = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "NotoNaskhArabic-Regular.ttf"
        )
        if os.path.exists(chemin_police):
            pdfmetrics.registerFont(TTFont("Arabic", chemin_police))
            police = "Arabic"

    alignement = TA_RIGHT if est_arabe else TA_JUSTIFY

    style_titre = ParagraphStyle('TitrePDF', parent=styles['Heading1'],
        fontName=police, fontSize=22, leading=26,
        textColor='#1E3A8A', alignment=TA_CENTER, spaceAfter=20)
    style_sous_titre = ParagraphStyle('SousTitrePDF', parent=styles['Heading2'],
        fontName=police, fontSize=14, leading=18,
        textColor='#10B981', spaceBefore=15, spaceAfter=10,
        alignment=alignement)
    style_corps = ParagraphStyle('CorpsPDF', parent=styles['BodyText'],
        fontName=police, fontSize=11, leading=16,
        textColor='#374151', alignment=alignement, spaceAfter=10)
    style_enonce = ParagraphStyle('EnoncePDF', parent=styles['Italic'],
        fontName=police, fontSize=10, leading=14,
        textColor='#6B7280', spaceAfter=15, alignment=alignement)
    style_footer = ParagraphStyle('FooterPDF', parent=styles['Normal'],
        fontName=police, fontSize=8, leading=10,
        textColor='#9CA3AF', alignment=TA_CENTER, spaceBefore=30)

    histoire = []
    histoire.append(Paragraph(t("pdf_title"), style_titre))
    histoire.append(Spacer(1, 10))
    histoire.append(Paragraph(t("pdf_enonce"), style_sous_titre))
    histoire.append(Paragraph(enonce_exercice.replace('\n', '<br/>'), style_enonce))
    histoire.append(Spacer(1, 10))
    histoire.append(Paragraph(t("pdf_resolution"), style_sous_titre))
    texte_propre = texte_correction.replace('\n', '<br/>')
    texte_propre = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texte_propre)
    texte_propre = re.sub(r'\*(.*?)\*', r'<i>\1</i>', texte_propre)
    histoire.append(Paragraph(texte_propre, style_corps))
    histoire.append(Spacer(1, 20))
    histoire.append(Paragraph(
        "This document is for informational purposes only. Responses may include mistakes.",
        style_footer
    ))
    doc.build(histoire)
    buffer.seek(0)
    return buffer

# ============================================================
# INTERFACE
# ============================================================

# Cas 1 : Remboursé -> Bloqué
if est_rembourse:
    st.error(t("access_revoked"))
    st.subheader(t("access_revoked_msg", email=email_eleve))
    st.write(t("access_revoked_sub"))
    st.stop()

# Cas 2 : Non payé -> Page de vente
elif not est_abonne:
    st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>{t('hero_title')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; font-size: 1.2em; color: #4B5563;'>{t('hero_subtitle')}</p>", unsafe_allow_html=True)
    st.write("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**{t('feature1_title')}**")
        st.caption(t("feature1_desc"))
    with col2:
        st.markdown(f"**{t('feature2_title')}**")
        st.caption(t("feature2_desc"))
    with col3:
        st.markdown(f"**{t('feature3_title')}**")
        st.caption(t("feature3_desc"))

    st.write("---")
    st.markdown(
        f"""
        <div style="background-color: #F3F4F6; padding: 20px; border-radius: 10px; border-left: 5px solid #10B981; margin-bottom: 20px;">
            <h4 style="margin: 0; color: #111827;">{t('offer_title')}</h4>
            <p style="font-size: 1.8em; font-weight: bold; margin: 10px 0; color: #10B981;">{t('offer_price')} <span style="font-size: 0.5em; color: #6B7280; font-weight: normal;">{t('offer_price_sub')}</span></p>
            <ul style="margin-bottom: 0; padding-left: 20px; color: #374151;">
                <li>{t('offer_bullet1')}</li>
                <li>{t('offer_bullet2')}</li>
                <li>{t('offer_bullet3')}</li>
                <li>{t('offer_bullet4')}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True
    )

    if st.button(t("button_pay"), use_container_width=True, type="primary"):
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[{'price': ID_PRIX_UNIQUE, 'quantity': 1}],
                mode='payment',
                success_url=f"{URL_APP}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=URL_APP,
            )
            st.markdown(f"### [{t('button_pay_link')}]({checkout_session.url})")
            st.caption(t("stripe_secure"))
            st.markdown(
                f"<p style='font-size: 0.8em; color: #9CA3AF; text-align: center; margin-top: 10px;'>{t('legal_notice')}</p>",
                unsafe_allow_html=True
            )
        except Exception as e:
            st.error(t("stripe_error", error=str(e)))

    st.write("---")
    st.markdown(f"##### {t('testimonials_title')}")
    st.info(t("testimonial_text"))

# Cas 3 : Payé -> Accès débloqué
else:
    st.markdown(f"<h1 style='text-align: center; color: #10B981;'>{t('premium_activated')}</h1>", unsafe_allow_html=True)
    st.success(t("premium_msg", email=email_eleve))

    exercice = st.text_area(t("textarea_label"), height=150)

    if st.button(t("button_correct"), type="primary", use_container_width=True):
        if not exercice.strip():
            st.warning(t("warning_empty"))
        else:
            with st.spinner(t("spinner")):
                try:
                    noms_langues = {
                        "fr": "français",
                        "en": "anglais",
                        "de": "allemand",
                        "es": "espagnol",
                        "it": "italien",
                        "ar": "arabe",
                    }
                    nom_langue = noms_langues.get(st.session_state.langue, "anglais")

                    instructions = (
                        f"Tu es un coach privé de mathématiques hautement qualifié, pédagogue et bienveillant. "
                        f"Réponds IMPÉRATIVEMENT en {nom_langue}. "
                        "Ton but est d'aider l'élève à comprendre son exercice, pas seulement de lui donner la réponse brute. "
                        "1. Salue brièvement l'élève de manière encourageante.\n"
                        "2. Rappelle brièvement les propriétés ou formules mathématiques nécessaires.\n"
                        "3. Propose une correction extrêmement détaillée, rédigée étape par étape.\n"
                        "4. Utilise un langage clair, accessible et structure tes calculs avec une mise en forme soignée.\n"
                        "5. Termine par un petit conseil ou un mot d'encouragement pour ses révisions.\n"
                    )

                    if st.session_state.langue == "ar":
                        instructions += (
                            "IMPORTANT pour l'arabe : utilise des formules LaTeX entre $ ... $ pour les maths inline "
                            "et $$ ... $$ pour les formules en bloc. Rédige tout le texte explicatif en arabe standard moderne."
                        )

                    reponse_ia = client_ia.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=exercice,
                        config=types.GenerateContentConfig(
                            system_instruction=instructions,
                            temperature=0.3
                        )
                    )

                    st.session_state['derniere_correction'] = reponse_ia.text
                    st.session_state['dernier_enonce'] = exercice

                except Exception as api_error:
                    st.error(f"Erreur lors de la génération : {api_error}")

    # Affichage de la correction + bouton PDF
    if 'derniere_correction' in st.session_state:
        st.write("---")
        st.markdown(st.session_state['derniere_correction'])

        pdf_buffer = generer_pdf(
            st.session_state['derniere_correction'],
            st.session_state['dernier_enonce']
        )
        st.download_button(
            label=t("button_download_pdf"),
            data=pdf_buffer,
            file_name="correction_coach_math.pdf",
            mime="application/pdf",
            use_container_width=True
        )
