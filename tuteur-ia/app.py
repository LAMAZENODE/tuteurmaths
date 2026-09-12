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
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

# ============================================================
# CONFIGURATION DE LA PAGE
# ============================================================
st.set_page_config(page_title="AI Math Tutor", page_icon="📐", layout="centered")

# ============================================================
# CHARGEMENT DES TRADUCTIONS
# ============================================================
@st.cache_data
def charger_traductions():
    chemin_script = os.path.dirname(os.path.abspath(__file__))
    chemin_fichier = os.path.join(chemin_script, "translations.json")
    with open(chemin_fichier, "r", encoding="utf-8") as f:
        return json.load(f)
   
TRADUCTIONS = charger_traductions()

# Sélecteur de langue dans la sidebar
LANGUES = {
    "🇫🇷 Français": "fr",
    "🇬🇧 English": "en",
    "🇩🇪 Deutsch": "de",
    "🇪🇸 Español": "es",
    "🇮🇹 Italiano": "it"
}

if "langue" not in st.session_state:
    st.session_state.langue = "fr"

with st.sidebar:
    st.markdown("### 🌍 Language / Langue / Sprache / Idioma / Lingua")
    choix = st.selectbox(
        "Choisissez votre langue :",
        options=list(LANGUES.keys()),
        index=list(LANGUES.values()).index(st.session_state.langue),
        label_visibility="collapsed"
    )
    st.session_state.langue = LANGUES[choix]

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
# FONCTION PDF
# ============================================================
def generer_pdf(texte_correction, enonce_exercice):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40,
        title="AI Math Tutor Correction"
    )
    styles = getSampleStyleSheet()
    style_titre = ParagraphStyle('TitrePDF', parent=styles['Heading1'],
        fontSize=22, leading=26, textColor='#1E3A8A', alignment=TA_CENTER, spaceAfter=20)
    style_sous_titre = ParagraphStyle('SousTitrePDF', parent=styles['Heading2'],
        fontSize=14, leading=18, textColor='#10B981', spaceBefore=15, spaceAfter=10)
    style_corps = ParagraphStyle('CorpsPDF', parent=styles['BodyText'],
        fontSize=11, leading=16, textColor='#374151', alignment=TA_JUSTIFY, spaceAfter=10)
    style_enonce = ParagraphStyle('EnoncePDF', parent=styles['Italic'],
        fontSize=10, leading=14, textColor='#6B7280', spaceAfter=15)
    style_footer = ParagraphStyle('FooterPDF', parent=styles['Normal'],
        fontSize=8, leading=10, textColor='#9CA3AF', alignment=TA_CENTER, spaceBefore=30)

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
    histoire.append(Paragraph("This is for informational purposes only. AI responses may include mistakes.", style_footer))
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
                    # Instructions multilingues pour l'IA
                    instructions = (
                        f"Tu es un tuteur privé de mathématiques hautement qualifié, pédagogue et bienveillant. "
                        f"Réponds IMPÉRATIVEMENT dans la langue suivante : {st.session_state.langue}. "
                        "Ton but est d'aider l'élève à comprendre son exercice, pas seulement de lui donner la réponse brute. "
                        "1. Salue brièvement l'élève de manière encourageante.\n"
                        "2. Rappelle brièvement les propriétés ou formules mathématiques nécessaires.\n"
                        "3. Propose une correction extrêmement détaillée, rédigée étape par étape.\n"
                        "4. Utilise un langage clair, accessible et structure tes calculs avec une mise en forme soignée.\n"
                        "5. Termine par un petit conseil ou un mot d'encouragement pour ses révisions."
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
            label="📥 Télécharger la correction en PDF",
            data=pdf_buffer,
            file_name="correction_tuteur_math.pdf",
            mime="application/pdf",
            use_container_width=True
        )
























