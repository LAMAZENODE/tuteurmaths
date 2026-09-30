import streamlit as st
from google import genai
from google.genai import types
import json
import re
import time
import stripe
import io
import os
import datetime
import base64
from weasyprint import HTML
from supabase import create_client, Client

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
        "correction_title": "Votre correction",
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
        "correction_title": "Your correction",
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
        "correction_title": "Ihre Korrektur",
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
        "correction_title": "Tu corrección",
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
        "correction_title": "La tua correzione",
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
        "correction_title": "التصحيح",
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

        /* Détection automatique de la direction par paragraphe */
        .stMarkdown p, .stMarkdown li {
            unicode-bidi: plaintext !important;
        }

        /* Formules et code : LTR */
        code, pre, .stCode, .katex, .MathJax, .katex-display {
            direction: ltr !important;
            text-align: left !important;
            unicode-bidi: isolate !important;
        }

        span[dir="ltr"] {
            display: inline !important;
            direction: ltr !important;
            unicode-bidi: isolate !important;
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
# COOKIE MANAGER
# ============================================================
if COOKIES_DISPONIBLES:
    cookie_manager = stx.CookieManager(key="cookie_manager_math")
    cookie_manager.get_all(key="init_cookies")
else:
    cookie_manager = None

# ============================================================
# GESTION DES EMAILS — SUPABASE
# ============================================================
@st.cache_resource
def init_supabase() -> Client:
    """Initialise la connexion Supabase (une seule fois)."""
    url = st.secrets["supabase"]["SUPABASE_URL"]
    key = st.secrets["supabase"]["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()


def charger_emails_utilises():
    """Récupère tous les emails utilisés depuis Supabase."""
    try:
        response = supabase.table("emails_utilises").select("email").execute()
        return [row["email"] for row in response.data]
    except Exception as e:
        st.error(f"Erreur Supabase (chargement) : {e}")
        return []


def sauvegarder_email(email):
    """Sauvegarde un email dans Supabase."""
    email_clean = email.lower().strip()
    try:
        existing = supabase.table("emails_utilises") \
            .select("id") \
            .eq("email", email_clean) \
            .execute()
        if existing.data:
            return
        supabase.table("emails_utilises").insert({
            "email": email_clean
        }).execute()
    except Exception as e:
        st.error(f"Erreur Supabase (sauvegarde) : {e}")


def retirer_email(email):
    """Retire un email de Supabase (si la génération échoue)."""
    email_clean = email.lower().strip()
    try:
        supabase.table("emails_utilises") \
            .delete() \
            .eq("email", email_clean) \
            .execute()
    except Exception as e:
        st.error(f"Erreur Supabase (retrait) : {e}")


def email_deja_utilise(email):
    """Vérifie si l'email existe déjà dans Supabase."""
    email_clean = email.lower().strip()
    try:
        response = supabase.table("emails_utilises") \
            .select("id") \
            .eq("email", email_clean) \
            .execute()
        return len(response.data) > 0
    except Exception as e:
        st.error(f"Erreur Supabase (vérification) : {e}")
        return False


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
# OUTILS PDF — NETTOYAGE ARABE
# ============================================================
def _convertir_latex_simple(texte):
    """Convertit les formules LaTeX en texte simple."""
    texte = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', r'(\1)/(\2)', texte)
    remplacements = {
        r'\times': ' × ', r'\cdot': ' · ',
        r'\leq': ' ≤ ', r'\geq': ' ≥ ', r'\neq': ' ≠ ',
        r'\approx': ' ≈ ', r'\infty': ' ∞ ', r'\pm': ' ± ',
        r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ',
        r'\pi': 'π', r'\theta': 'θ',
    }
    for k, v in remplacements.items():
        texte = texte.replace(k, v)
    texte = re.sub(r'\\sqrt\{([^{}]+)\}', r'√(\1)', texte)
    texte = re.sub(r'\^\{([^{}]+)\}', r'^\1', texte)
    texte = re.sub(r'_\{([^{}]+)\}', r'_\1', texte)
    texte = re.sub(r'\$\$(.+?)\$\$', r'\1', texte, flags=re.DOTALL)
    texte = re.sub(r'\$(.+?)\$', r'\1', texte)
    return texte


def _normaliser_espaces(texte):
    """Convertit TOUS les espaces Unicode en espace normal."""
    remplacements = [
        ("\u00A0", " "), ("\u1680", " "),
        ("\u2000", " "), ("\u2001", " "), ("\u2002", " "), ("\u2003", " "),
        ("\u2004", " "), ("\u2005", " "), ("\u2006", " "), ("\u2007", " "),
        ("\u2008", " "), ("\u2009", " "), ("\u200A", " "),
        ("\u202F", " "), ("\u205F", " "), ("\u3000", " "),
        ("\u200B", ""), ("\uFEFF", ""),
    ]
    for k, v in remplacements:
        texte = texte.replace(k, v)
    return texte


def _nettoyer_arabe(ligne):
    """Nettoie les espaces parasites et les accents arabes (version ULTRA)."""
    ligne = _normaliser_espaces(ligne)

    for c in ["\u200C", "\u200D", "\u200E", "\u200F",
              "\u202A", "\u202B", "\u202C", "\u202D", "\u202E",
              "\u2066", "\u2067", "\u2068", "\u2069"]:
        ligne = ligne.replace(c, "")

    for _ in range(5):
        ligne = re.sub(
            r'[\s\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000]+'
            r'([\u064B-\u0652\u0670\u06D6-\u06ED])',
            r'\1',
            ligne
        )

    for _ in range(3):
        ligne = re.sub(
            r'[\s\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000]+([.,،؟!؛:])',
            r'\1',
            ligne
        )

    ligne = re.sub(r' {2,}', ' ', ligne)
    return ligne


def _est_ligne_formule(ligne):
    """Détecte si la ligne est majoritairement latine/mathématique."""
    stripped = ligne.strip()
    if not stripped:
        return False
    compte_latin = sum(
        1 for c in stripped
        if c.isascii() and (c.isalnum() or c in "()+-=/*^_.,' ")
    )
    return compte_latin / max(len(stripped), 1) > 0.6


def _markdown_vers_html(contenu, est_arabe=False):
    """Convertit un texte Markdown en HTML structuré."""
    lignes_html = []
    for ligne in contenu.split("\n"):
        l = ligne.rstrip()
        if not l.strip():
            lignes_html.append("<br>")
            continue

        l = _convertir_latex_simple(l)

        if est_arabe:
            if _est_ligne_formule(l):
                l = f'<span dir="ltr">{l.strip()}</span>'
            else:
                l = _nettoyer_arabe(l)

        if l.startswith("### "):
            lignes_html.append(f"<h3>{l[4:]}</h3>")
        elif l.startswith("## "):
            lignes_html.append(f"<h2>{l[3:]}</h2>")
        elif l.startswith("# "):
            lignes_html.append(f"<h1>{l[2:]}</h1>")
        elif l.lstrip().startswith(("- ", "* ")):
            texte_puce = l.lstrip()[2:]
            texte_puce = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', texte_puce)
            texte_puce = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', texte_puce)
            classe = "puce-ar" if est_arabe else "puce"
            lignes_html.append(f'<p class="{classe}">• {texte_puce}</p>')
        else:
            l = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', l)
            l = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', l)
            lignes_html.append(f"<p>{l}</p>")

    return "\n".join(lignes_html)


# ============================================================
# GÉNÉRATION PDF — WEASYPRINT
# ============================================================
@st.cache_resource(show_spinner=False)
def _charger_police_base64():
    """Charge la police arabe en base64."""
    try:
        chemin = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "NotoNaskhArabic-Regular.ttf"
        )
        with open(chemin, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return None


def generer_pdf(texte_correction, enonce_exercice):
    """Génère le PDF avec WeasyPrint (RTL natif, ligatures correctes)."""
    langue = st.session_state.get("langue", "fr")
    est_arabe = (langue == "ar")

    direction = "rtl" if est_arabe else "ltr"
    align = "right" if est_arabe else "left"

    titre_pdf = t("pdf_title")
    titre_enonce = t("pdf_enonce")
    titre_resolution = t("pdf_resolution")

    corps_enonce = _markdown_vers_html(enonce_exercice, est_arabe=est_arabe)
    corps_correction = _markdown_vers_html(texte_correction, est_arabe=est_arabe)

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
            @page {{ margin: 2cm; size: A4; }}
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
            p {{ margin: 6px 0; unicode-bidi: plaintext; }}
            .puce-ar {{ padding-right: 22px; text-indent: -14px; margin: 4px 0; }}
            .puce {{ padding-left: 22px; text-indent: -14px; margin: 4px 0; }}
            span[dir="ltr"] {{
                display: inline-block;
                direction: ltr;
                unicode-bidi: isolate;
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
    return io.BytesIO(pdf_bytes)

# ============================================================
# GÉNÉRATION DE CORRECTION (avec retry automatique)
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
            "IMPORTANT pour l'arabe :\n"
            "- Rédige tout le texte explicatif en arabe standard moderne.\n"
            "- Utilise des formules LaTeX entre $ ... $ pour les maths inline "
            "et $$ ... $$ pour les formules en bloc.\n"
            "- ⚠️ N'ajoute JAMAIS d'espace avant les accents arabes "
            "(أهلاً، حقاً، دائماً — PAS أهال ً، حقا ً، دائما ً).\n"
            "- ⚠️ Colle toujours les accents au caractère qui les précède.\n"
            "- ⚠️ Ne mets jamais d'espace avant la ponctuation (. ، ؟ !).\n"
            "- ⚠️ N'utilise JAMAIS deux alifs consécutifs dans un mot "
            "(écris الاستيعاب، الأساسية — PAS االستيعاب، األساسية)."
        )

    modeles = [
        "gemini-3.6-flash",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-flash-latest",
    ]

    derniere_erreur = None

    for mod in modeles:
        for tentative in range(3):
            try:
                reponse_ia = client_ia.models.generate_content(
                    model=mod,
                    contents=exercice,
                    config=types.GenerateContentConfig(
                        system_instruction=instructions,
                        temperature=0.3
                    )
                )
                if reponse_ia and reponse_ia.text:
                    return reponse_ia.text
            except Exception as e:
                derniere_erreur = str(e)
                if "503" in derniere_erreur or "UNAVAILABLE" in derniere_erreur:
                    time.sleep(2 + tentative * 2)
                    continue
                if "404" in derniere_erreur or "NOT_FOUND" in derniere_erreur:
                    break
                time.sleep(1)
                continue

    if "503" in str(derniere_erreur) or "UNAVAILABLE" in str(derniere_erreur):
        return (
            "⏳ Le service est momentanément surchargé. "
            "Merci de réessayer dans 1 à 2 minutes. "
            "Votre question gratuite n'a PAS été consommée."
        )

    return f"❌ Erreur : {derniere_erreur}"

# ============================================================
# AFFICHAGE CORRECTION + PDF
# ============================================================
def afficher_correction_et_pdf(nom_fichier="correction_coach_math.pdf"):
    if 'derniere_correction' in st.session_state:
        try:
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
        except Exception as e:
            st.warning(f"PDF indisponible : {e}")

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
    if "free_question_used" not in st.session_state:
        st.session_state.free_question_used = False
    if "email_verifie" not in st.session_state:
        st.session_state.email_verifie = None

    if not st.session_state.free_question_used and cookie_manager is not None:
        try:
            cookie_val = cookie_manager.get(cookie="free_question_used")
            if cookie_val == "1":
                st.session_state.free_question_used = True
        except Exception:
            pass

    st.markdown(
        f"<h1 style='text-align: center; color: #1E3A8A;'>{t('hero_title')}</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<p style='text-align: center; font-size: 1.2em; color: #4B5563;'>{t('hero_subtitle')}</p>",
        unsafe_allow_html=True
    )
    st.write("---")

    # ---------- BLOC : ÉTAPE 1 (email) ----------
    if st.session_state.email_verifie is None and not st.session_state.free_question_used:
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

    # ---------- BLOC : ÉTAPE 2 (question gratuite) ----------
    elif not st.session_state.free_question_used:
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
                # ✅ Sauvegarder l'email AVANT la génération
                sauvegarder_email(st.session_state.email_verifie)

                with st.spinner(t("spinner")):
                    try:
                        correction = generer_correction(exercice_gratuit)

                        if correction.startswith("❌") or correction.startswith("⏳"):
                            # En cas d'échec technique, on retire l'email
                            # pour ne pas pénaliser l'utilisateur
                            retirer_email(st.session_state.email_verifie)
                            st.warning(correction)
                        else:
                            st.session_state.free_question_used = True
                            st.session_state['derniere_correction'] = correction
                            st.session_state['dernier_enonce'] = exercice_gratuit
                            if cookie_manager is not None:
                                try:
                                    cookie_manager.set(
                                        "free_question_used", "1",
                                        expires_at=datetime.datetime.now() + datetime.timedelta(days=365),
                                        secure=True,
                                        same_site="strict"
                                    )
                                except Exception:
                                    pass
                            st.rerun()
                    except Exception as api_error:
                        retirer_email(st.session_state.email_verifie)
                        st.error(f"Erreur lors de la génération : {api_error}")

    # ---------- BLOC : AFFICHAGE DE LA CORRECTION GRATUITE ----------
    else:
        st.success(t("free_question_used"))
        st.write("---")

        if 'derniere_correction' in st.session_state:
            st.markdown(f"### ✨ {t('correction_title')}")
            st.markdown(st.session_state['derniere_correction'])
            st.write("---")
            afficher_correction_et_pdf("correction_gratuite.pdf")

        st.write("---")
        st.info(t("free_question_used_msg"))

    # ---------- BLOC : OFFRE PAYANTE ----------
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

                    if correction.startswith("❌") or correction.startswith("⏳"):
                        st.warning(correction)
                    else:
                        st.session_state['derniere_correction'] = correction
                        st.session_state['dernier_enonce'] = exercice
                        st.rerun()
                except Exception as api_error:
                    st.error(f"Erreur lors de la génération : {api_error}")

    if 'derniere_correction' in st.session_state:
        st.markdown(f"### ✨ {t('correction_title')}")
        st.markdown(st.session_state['derniere_correction'])
        st.write("---")
        afficher_correction_et_pdf("correction_coach_math.pdf")
