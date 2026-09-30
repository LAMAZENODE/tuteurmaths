import streamlit as st
from google import genai
from google.genai import types
import json
import re
import stripe
import io
import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Cookie manager (optionnel)
try:
    import extra_streamlit_components as stx
    COOKIES_DISPONIBLES = True
except ImportError:
    COOKIES_DISPONIBLES = False

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

# ============================================================
# TRADUCTIONS DE SECOURS
# ============================================================
TRADUCTIONS_SECOURS = {
    "fr": {
        "free_question_title": "🎁 Votre première question est offerte",
        "free_question_subtitle": "Posez votre question gratuitement et découvrez la qualité de la correction. Aucune carte bancaire requise.",
        "free_question_used": "✅ Vous avez utilisé votre question gratuite",
        "free_question_used_msg": "Pour continuer à recevoir des corrections illimitées, débloquez l'accès complet pour seulement 5€ (paiement unique).",
        "free_question_remaining": "Il vous reste 1 question gratuite.",
        "free_question_label": "Posez votre question de maths :",
        "free_question_button": "Obtenir ma correction gratuite",
        "free_question_cta": "🚀 Débloquer l'accès illimité pour 5€",
        "email_label": "📧 Votre adresse email",
        "email_placeholder": "exemple@email.com",
        "email_help": "Nous utilisons votre email uniquement pour vérifier que vous n'avez pas déjà utilisé votre question gratuite.",
        "email_invalid": "⚠️ Veuillez saisir une adresse email valide.",
        "email_already_used": "❌ Cette adresse email a déjà utilisé sa question gratuite. Débloquez l'accès complet pour 5€ pour continuer.",
        "email_step_title": "Étape 1 : Identifiez-vous",
        "question_step_title": "Étape 2 : Posez votre question",
        "email_continue_btn": "Continuer vers ma question gratuite →",
        "email_verified": "✅ Email vérifié. Vous pouvez maintenant poser votre question gratuite.",
    },
    "en": {
        "free_question_title": "🎁 Your first question is free",
        "free_question_subtitle": "Ask your question for free and discover the quality of the correction. No credit card required.",
        "free_question_used": "✅ You have used your free question",
        "free_question_used_msg": "To keep receiving unlimited corrections, unlock full access for only €5 (one-time payment).",
        "free_question_remaining": "You have 1 free question left.",
        "free_question_label": "Ask your math question:",
        "free_question_button": "Get my free correction",
        "free_question_cta": "🚀 Unlock unlimited access for €5",
        "email_label": "📧 Your email address",
        "email_placeholder": "example@email.com",
        "email_help": "We use your email only to verify that you haven't already used your free question.",
        "email_invalid": "⚠️ Please enter a valid email address.",
        "email_already_used": "❌ This email has already used its free question. Unlock full access for €5 to continue.",
        "email_step_title": "Step 1: Identify yourself",
        "question_step_title": "Step 2: Ask your question",
        "email_continue_btn": "Continue to my free question →",
        "email_verified": "✅ Email verified. You can now ask your free question.",
    },
    "de": {
        "free_question_title": "🎁 Ihre erste Frage ist kostenlos",
        "free_question_subtitle": "Stellen Sie Ihre Frage kostenlos und entdecken Sie die Qualität der Korrektur. Keine Kreditkarte erforderlich.",
        "free_question_used": "✅ Sie haben Ihre kostenlose Frage verwendet",
        "free_question_used_msg": "Um weiterhin unbegrenzte Korrekturen zu erhalten, schalten Sie den Vollzugang für nur 5€ frei (Einmalzahlung).",
        "free_question_remaining": "Sie haben noch 1 kostenlose Frage.",
        "free_question_label": "Stellen Sie Ihre Mathefrage:",
        "free_question_button": "Kostenlose Korrektur erhalten",
        "free_question_cta": "🚀 Unbegrenzten Zugang für 5€ freischalten",
        "email_label": "📧 Ihre E-Mail-Adresse",
        "email_placeholder": "beispiel@email.com",
        "email_help": "Wir verwenden Ihre E-Mail nur, um zu prüfen, ob Sie Ihre kostenlose Frage bereits verwendet haben.",
        "email_invalid": "⚠️ Bitte geben Sie eine gültige E-Mail-Adresse ein.",
        "email_already_used": "❌ Diese E-Mail hat ihre kostenlose Frage bereits verwendet. Schalten Sie den Vollzugang für 5€ frei.",
        "email_step_title": "Schritt 1: Identifizieren Sie sich",
        "question_step_title": "Schritt 2: Stellen Sie Ihre Frage",
        "email_continue_btn": "Weiter zu meiner kostenlosen Frage →",
        "email_verified": "✅ E-Mail verifiziert. Sie können jetzt Ihre kostenlose Frage stellen.",
    },
    "es": {
        "free_question_title": "🎁 Tu primera pregunta es gratis",
        "free_question_subtitle": "Haz tu pregunta gratis y descubre la calidad de la corrección. No se requiere tarjeta de crédito.",
        "free_question_used": "✅ Has usado tu pregunta gratuita",
        "free_question_used_msg": "Para seguir recibiendo correcciones ilimitadas, desbloquea el acceso completo por solo 5€ (pago único).",
        "free_question_remaining": "Te queda 1 pregunta gratuita.",
        "free_question_label": "Haz tu pregunta de matemáticas:",
        "free_question_button": "Obtener mi corrección gratuita",
        "free_question_cta": "🚀 Desbloquear acceso ilimitado por 5€",
        "email_label": "📧 Tu dirección de correo",
        "email_placeholder": "ejemplo@email.com",
        "email_help": "Usamos tu correo solo para verificar que no hayas usado ya tu pregunta gratuita.",
        "email_invalid": "⚠️ Por favor, introduce un correo válido.",
        "email_already_used": "❌ Este correo ya ha usado su pregunta gratuita. Desbloquea el acceso completo por 5€.",
        "email_step_title": "Paso 1: Identifícate",
        "question_step_title": "Paso 2: Haz tu pregunta",
        "email_continue_btn": "Continuar a mi pregunta gratuita →",
        "email_verified": "✅ Correo verificado. Ya puedes hacer tu pregunta gratuita.",
    },
    "it": {
        "free_question_title": "🎁 La tua prima domanda è gratuita",
        "free_question_subtitle": "Fai la tua domanda gratuitamente e scopri la qualità della correzione. Nessuna carta di credito richiesta.",
        "free_question_used": "✅ Hai usato la tua domanda gratuita",
        "free_question_used_msg": "Per continuare a ricevere correzioni illimitate, sblocca l'accesso completo per soli 5€ (pagamento unico).",
        "free_question_remaining": "Ti resta 1 domanda gratuita.",
        "free_question_label": "Fai la tua domanda di matematica:",
        "free_question_button": "Ottieni la mia correzione gratuita",
        "free_question_cta": "🚀 Sblocca l'accesso illimitato per 5€",
        "email_label": "📧 Il tuo indirizzo email",
        "email_placeholder": "esempio@email.com",
        "email_help": "Usiamo la tua email solo per verificare che tu non abbia già usato la domanda gratuita.",
        "email_invalid": "⚠️ Inserisci un indirizzo email valido.",
        "email_already_used": "❌ Questa email ha già usato la sua domanda gratuita. Sblocca l'accesso completo per 5€.",
        "email_step_title": "Passo 1: Identificati",
        "question_step_title": "Passo 2: Fai la tua domanda",
        "email_continue_btn": "Continua verso la mia domanda gratuita →",
        "email_verified": "✅ Email verificata. Ora puoi fare la tua domanda gratuita.",
    },
    "ar": {
        "free_question_title": "🎁 سؤالك الأول مجاني",
        "free_question_subtitle": "اطرح سؤالك مجانًا واكتشف جودة التصحيح. لا حاجة لبطاقة بنكية.",
        "free_question_used": "✅ لقد استخدمت سؤالك المجاني",
        "free_question_used_msg": "لمواصلة تلقي تصحيحات غير محدودة، افتح الوصول الكامل مقابل 5 يورو فقط (دفعة واحدة).",
        "free_question_remaining": "يتبقى لك سؤال واحد مجاني.",
        "free_question_label": "اطرح سؤال الرياضيات:",
        "free_question_button": "احصل على تصحيحي المجاني",
        "free_question_cta": "🚀 افتح الوصول غير المحدود مقابل 5 يورو",
        "email_label": "📧 بريدك الإلكتروني",
        "email_placeholder": "example@email.com",
        "email_help": "نستخدم بريدك فقط للتحقق من أنك لم تستخدم سؤالك المجاني من قبل.",
        "email_invalid": "⚠️ يرجى إدخال بريد إلكتروني صالح.",
        "email_already_used": "❌ هذا البريد استخدم سؤاله المجاني بالفعل. افتح الوصول الكامل مقابل 5 يورو.",
        "email_step_title": "الخطوة 1: عرّف بنفسك",
        "question_step_title": "الخطوة 2: اطرح سؤالك",
        "email_continue_btn": "تابع إلى سؤالي المجاني ←",
        "email_verified": "✅ تم التحقق من البريد. يمكنك الآن طرح سؤالك المجاني.",
    },
}

LANGUES = {
    "🇫🇷 Français": "fr",
    "🇬🇧 English": "en",
    "🇩🇪 Deutsch": "de",
    "🇪🇸 Español": "es",
    "🇮🇹 Italiano": "it",
    "🇸🇦 العربية": "ar"
}

# ============================================================
# DÉTECTION AUTOMATIQUE DE LA LANGUE
# ============================================================
def detecter_langue_navigateur():
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
# CONFIGURATION DE LA PAGE
# ============================================================
st.set_page_config(
    page_title=TRADUCTIONS[st.session_state.langue].get("page_title", "Math Coach"),
    page_icon="📐",
    layout="centered"
)

# ============================================================
# SÉLECTEUR DE LANGUE
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
# CSS ARABE
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
# TRADUCTION
# ============================================================
def t(cle, **kwargs):
    texte = TRADUCTIONS[st.session_state.langue].get(cle)
    if texte is None:
        texte = TRADUCTIONS_SECOURS.get(st.session_state.langue, {}).get(cle, cle)
    if kwargs:
        try:
            return texte.format(**kwargs)
        except (KeyError, IndexError):
            return texte
    return texte

# ============================================================
# COOKIE MANAGER (PAS de @st.cache_resource !)
# ============================================================
if COOKIES_DISPONIBLES:
    cookie_manager = stx.CookieManager(key="cookie_manager_math")
    # Force l'initialisation au premier run
    cookie_manager.get_all(key="init_cookies")
else:
    cookie_manager = None

# ============================================================
# GESTION DES EMAILS UTILISÉS
# ============================================================
CHEMIN_EMAILS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "emails_utilises.json"
)

def charger_emails_utilises():
    if not os.path.exists(CHEMIN_EMAILS):
        return []
    try:
        with open(CHEMIN_EMAILS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def sauvegarder_email(email):
    emails = charger_emails_utilises()
    if email not in emails:
        emails.append(email)
        try:
            with open(CHEMIN_EMAILS, "w", encoding="utf-8") as f:
                json.dump(emails, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

def email_deja_utilise(email):
    return email.lower().strip() in [e.lower().strip() for e in charger_emails_utilises()]

def email_valide(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email.strip()) is not None

# ============================================================
# SECRETS
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
# VÉRIFICATION ANTI-FRAUDE (Stripe)
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
import base64
from weasyprint import HTML


def _convertir_latex_simple(texte):
    """
    Convertit les formules LaTeX en texte simple (WeasyPrint ne rend pas LaTeX).
    Ex: \\frac{a}{b} -> (a)/(b),  $$x$$ -> x
    """
    # \frac{a}{b} -> (a)/(b)
    texte = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', r'(\1)/(\2)', texte)

    # Symboles simples
    remplacements = {
        r'\times': ' × ',
        r'\cdot': ' · ',
        r'\leq': ' ≤ ',
        r'\geq': ' ≥ ',
        r'\neq': ' ≠ ',
        r'\approx': ' ≈ ',
        r'\infty': ' ∞ ',
        r'\pm': ' ± ',
        r'\alpha': 'α',
        r'\beta': 'β',
        r'\gamma': 'γ',
        r'\pi': 'π',
        r'\theta': 'θ',
    }
    for k, v in remplacements.items():
        texte = texte.replace(k, v)

    # \sqrt{x} -> √(x)
    texte = re.sub(r'\\sqrt\{([^{}]+)\}', r'√(\1)', texte)

    # x^{2} -> x^2 ; x_{1} -> x_1
    texte = re.sub(r'\^\{([^{}]+)\}', r'^\1', texte)
    texte = re.sub(r'_\{([^{}]+)\}', r'_\1', texte)

    # Retirer les balises $$ ... $$ et $ ... $
    texte = re.sub(r'\$\$(.+?)\$\$', r'\1', texte, flags=re.DOTALL)
    texte = re.sub(r'\$(.+?)\$', r'\1', texte)

    return texte


@st.cache_resource(show_spinner=False)
def _charger_police_base64():
    """Charge la police arabe en base64 pour l'intégrer dans le HTML."""
    try:
        chemin = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "NotoNaskhArabic-Regular.ttf"
        )
        with open(chemin, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return None


def _markdown_vers_html(contenu, est_arabe=False):
    """Convertit une correction Markdown en HTML structuré."""
    lignes_html = []
    for ligne in contenu.split("\n"):
        l = ligne.rstrip()

        if not l.strip():
            lignes_html.append("<br>")
            continue

        # Convertir LaTeX en texte simple
        l = _convertir_latex_simple(l)

        if est_arabe:
            # Corriger les espaces avant les accents arabes
            for k, v in {
                " ً": "ً", " ٍ": "ٍ", " ٌ": "ٌ",
                " َ": "َ", " ِ": "ِ", " ُ": "ُ",
                " ْ": "ْ", " ّ": "ّ",
                " .": ".", " ،": "،", " ؟": "؟",
            }.items():
                l = l.replace(k, v)

        if l.startswith("### "):
            lignes_html.append(f"<h3>{l[4:]}</h3>")
        elif l.startswith("## "):
            lignes_html.append(f"<h2>{l[3:]}</h2>")
        elif l.startswith("# "):
            lignes_html.append(f"<h1>{l[2:]}</h1>")
        elif l.lstrip().startswith(("- ", "* ")):
            texte_puce = l.lstrip()[2:]
            # Gras / italique Markdown
            texte_puce = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', texte_puce)
            texte_puce = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', texte_puce)
            classe = "puce-ar" if est_arabe else "puce"
            lignes_html.append(f'<p class="{classe}">• {texte_puce}</p>')
        else:
            # Gras / italique Markdown
            l = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', l)
            l = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', l)
            lignes_html.append(f"<p>{l}</p>")

    return "\n".join(lignes_html)


def generer_pdf(texte_correction, enonce_exercice):
    """
    Génère le PDF de correction avec WeasyPrint (RTL natif + ligatures arabes).
    """
    langue = st.session_state.get("langue", "fr")
    est_arabe = (langue == "ar")

    direction = "rtl" if est_arabe else "ltr"
    align = "right" if est_arabe else "left"

    # --- Récupère les textes traduits ---
    titre_pdf = t("pdf_title")
    titre_enonce = t("pdf_enonce")
    titre_resolution = t("pdf_resolution")

    # --- Convertit le contenu en HTML ---
    corps_enonce = _markdown_vers_html(enonce_exercice, est_arabe=est_arabe)
    corps_correction = _markdown_vers_html(texte_correction, est_arabe=est_arabe)

    # --- Charge la police arabe en base64 ---
    police_b64 = _charger_police_base64()
    font_face = ""
    if police_b64:
        font_face = f"""
        @font-face {{
            font-family: 'NotoArabicEmbedded';
            src: url(data:font/ttf;base64,{police_b64}) format('truetype');
        }}
        """
        police_css = "'NotoArabicEmbedded', 'DejaVu Sans', Arial, sans-serif"
    else:
        police_css = "'Noto Naskh Arabic', 'Amiri', 'DejaVu Sans', Arial, sans-serif"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            {font_face}
            @page {{
                margin: 2cm;
                size: A4;
            }}
            body {{
                font-family: {police_css};
                direction: {direction};
                text-align: {align};
                font-size: 11pt;
                line-height: 1.7;
                color: #374151;
            }}
            h1 {{
                font-size: 20pt;
                color: #1E3A8A;
                text-align: center;
                margin-bottom: 20px;
                margin-top: 0;
            }}
            h2 {{
                font-size: 14pt;
                color: #10B981;
                margin-top: 20px;
                margin-bottom: 10px;
                border-bottom: 1px solid #e5e7eb;
                padding-bottom: 4px;
            }}
            h3 {{
                font-size: 12pt;
                color: #6b21a8;
                margin-top: 14px;
                margin-bottom: 6px;
            }}
            p {{
                margin: 6px 0;
            }}
            .puce-ar {{
                padding-right: 22px;
                text-indent: -14px;
                margin: 4px 0;
            }}
            .puce {{
                padding-left: 22px;
                text-indent: -14px;
                margin: 4px 0;
            }}
            .footer {{
                margin-top: 40px;
                font-size: 8pt;
                color: #9CA3AF;
                text-align: center;
                border-top: 1px solid #e5e7eb;
                padding-top: 10px;
            }}
            .enonce {{
                background-color: #F9FAFB;
                padding: 12px;
                border-radius: 6px;
                margin-bottom: 20px;
                color: #4B5563;
                font-style: italic;
            }}
        </style>
    </head>
    <body>
        <h1>{titre_pdf}</h1>

        <h2>{titre_enonce}</h2>
        <div class="enonce">{corps_enonce}</div>

        <h2>{titre_resolution}</h2>
        {corps_correction}

        <div class="footer">
            This document is for informational purposes only. Responses may include mistakes.
        </div>
    </body>
    </html>
    """

    pdf_bytes = HTML(string=html).write_pdf()

    # Retourne un BytesIO pour compatibilité avec st.download_button
    return io.BytesIO(pdf_bytes)

# ============================================================
# GÉNÉRATION DE CORRECTION
# ============================================================
def generer_correction(exercice):
    noms_langues = {
        "fr": "français", "en": "anglais", "de": "allemand",
        "es": "espagnol", "it": "italien", "ar": "arabe",
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
    return reponse_ia.text

# ============================================================
# AFFICHAGE CORRECTION + PDF
# ============================================================
def afficher_correction_et_pdf(nom_fichier="correction_coach_math.pdf"):
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
            file_name=nom_fichier,
            mime="application/pdf",
            use_container_width=True
        )

# ============================================================
# INTERFACE
# ============================================================

# Cas 1 : Remboursé
if est_rembourse:
    st.error(t("access_revoked"))
    st.subheader(t("access_revoked_msg", email=email_eleve))
    st.write(t("access_revoked_sub"))
    st.stop()

# Cas 2 : Non payé
elif not est_abonne:
    # --- Initialisation de l'état ---
    if "free_question_used" not in st.session_state:
        st.session_state.free_question_used = False

    if "email_verifie" not in st.session_state:
        st.session_state.email_verifie = None

    # --- Vérification du cookie ---
    if not st.session_state.free_question_used and cookie_manager is not None:
        try:
            cookie_val = cookie_manager.get(cookie="free_question_used")
            if cookie_val == "1":
                st.session_state.free_question_used = True
        except Exception:
            pass

    # --- TITRE DE MARQUE (à son emplacement d'origine, toujours affiché) ---
    st.markdown(
        f"<h1 style='text-align: center; color: #1E3A8A;'>{t('hero_title')}</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<p style='text-align: center; font-size: 1.2em; color: #4B5563;'>{t('hero_subtitle')}</p>",
        unsafe_allow_html=True
    )
    st.write("---")

    # --- Si la question gratuite n'a PAS encore été utilisée ---
    if not st.session_state.free_question_used:

        # ÉTAPE 1 : Saisie de l'email
        if st.session_state.email_verifie is None:
            st.markdown(f"#### {t('email_step_title')}")

            email_saisi = st.text_input(
                t("email_label"),
                placeholder=t("email_placeholder"),
                help=t("email_help"),
                key="email_input"
            )

            if st.button(t("email_continue_btn"), type="primary", use_container_width=True, key="btn_email"):
                email_clean = email_saisi.strip().lower()
                if not email_valide(email_clean):
                    st.error(t("email_invalid"))
                elif email_deja_utilise(email_clean):
                    st.error(t("email_already_used"))
                    st.info(t("free_question_used_msg"))
                else:
                    st.session_state.email_verifie = email_clean
                    st.rerun()

        # ÉTAPE 2 : Question gratuite
        else:
            st.success(t("email_verified"))
            st.markdown(f"#### {t('question_step_title')}")
            st.info(t("free_question_remaining"))
            st.write("---")

            exercice_gratuit = st.text_area(
                t("free_question_label"),
                height=150,
                key="free_question_input"
            )

            if st.button(t("free_question_button"), type="primary", use_container_width=True, key="btn_free"):
                if not exercice_gratuit.strip():
                    st.warning(t("warning_empty"))
                else:
                    with st.spinner(t("spinner")):
                        try:
                            correction = generer_correction(exercice_gratuit)

                            # Sauvegarder l'email comme utilisé
                            sauvegarder_email(st.session_state.email_verifie)

                            # Marquer comme utilisée
                            st.session_state.free_question_used = True
                            st.session_state['derniere_correction'] = correction
                            st.session_state['dernier_enonce'] = exercice_gratuit

                            if cookie_manager is not None:
                                try:
                                    cookie_manager.set(
                                        "free_question_used", "1",
                                        expires_at=datetime.datetime.now() + datetime.timedelta(days=365)
                                    )
                                except Exception:
                                    pass

                            st.rerun()
                        except Exception as api_error:
                            st.error(f"Erreur lors de la génération : {api_error}")

            # Affichage de la correction gratuite si déjà générée
            if st.session_state.free_question_used and 'derniere_correction' in st.session_state:
                afficher_correction_et_pdf("correction_gratuite.pdf")
                st.write("---")
                st.success(t("free_question_used"))
                st.markdown(t("free_question_used_msg"))

    # --- Si la question gratuite a DÉJÀ été utilisée ---
    else:
        st.info(t("free_question_used_msg"))
        st.write("---")

    # --- Bloc de vente (toujours affiché) ---
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

    if st.button(t("button_pay"), use_container_width=True, type="primary", key="btn_pay"):
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

# Cas 3 : Payé
else:
    st.markdown(f"<h1 style='text-align: center; color: #10B981;'>{t('premium_activated')}</h1>", unsafe_allow_html=True)
    st.success(t("premium_msg", email=email_eleve))

    exercice = st.text_area(t("textarea_label"), height=150, key="premium_input")

    if st.button(t("button_correct"), type="primary", use_container_width=True, key="btn_correct"):
        if not exercice.strip():
            st.warning(t("warning_empty"))
        else:
            with st.spinner(t("spinner")):
                try:
                    correction = generer_correction(exercice)
                    st.session_state['derniere_correction'] = correction
                    st.session_state['dernier_enonce'] = exercice
                except Exception as api_error:
                    st.error(f"Erreur lors de la génération : {api_error}")

    afficher_correction_et_pdf("correction_coach_math.pdf")
