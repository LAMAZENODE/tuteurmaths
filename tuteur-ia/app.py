import urllib.parse
import streamlit as st
from google import genai
from google.genai import types
import json
import re
import stripe
import io
import os
import time
import random
import datetime
if "sujet_genere" not in st.session_state:
    st.session_state.sujet_genere = ""
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
        "coach_question": "As-tu compris cette étape ? Veux-tu que nous passions à la suite ?",
        "coach_yes": "Oui, j'ai compris",
        "coach_no": "Non, explique autrement",
        "coach_finish": "J'ai terminé, montre-moi le récapitulatif",
        "coach_done": "🎉 Bravo ! Tu as terminé toutes les étapes.",
        "coach_step": "Étape",
        "coach_restart": "🔄 Recommencer un nouvel exercice",
        "coach_summary": "📋 Récapitulatif de ta progression",
        "button_download_pdf": "📥 Télécharger la correction en PDF",
        "spinner": "⏳ Génération de l'étape...",
        "warning_empty": "⚠️ Merci de saisir un énoncé.",
        "ai_init_error": "Erreur d'initialisation IA : {error}",
        "verif_error": "Erreur de vérification du paiement.",
        "pdf_title": "Ma Correction Personnalisée",
        "pdf_enonce": "📌 Énoncé soumis :",
        "pdf_resolution": "📝 Résolution pas à pas :",
        "preambule_title": "📖 Rappel de cours",
        "exemple_concret_title": "💡 Exemple concret",
        "exemple_theorique_title": "🧮 Exemple théorique",
        
        "retry_button": "🔄 Réessayer",
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
        "coach_question": "Did you understand this step? Shall we move on?",
        "coach_yes": "Yes, I understood",
        "coach_no": "No, explain differently",
        "coach_finish": "I'm done, show me the summary",
        "coach_done": "🎉 Well done! You completed all the steps.",
        "coach_step": "Step",
        "coach_restart": "🔄 Start a new exercise",
        "coach_summary": "📋 Summary of your progression",
        "button_download_pdf": "📥 Download correction as PDF",
        "spinner": "⏳ Generating step...",
        "warning_empty": "⚠️ Please enter a statement.",
        "ai_init_error": "AI initialization error: {error}",
        "verif_error": "Payment verification error.",
        "pdf_title": "My Personalized Correction",
        "pdf_enonce": "📌 Submitted statement:",
        "pdf_resolution": "📝 Step-by-step resolution:",
        "preambule_title": "📖 Course reminder",
        "exemple_concret_title": "💡 Concrete example",
        "exemple_theorique_title": "🧮 Theoretical example",
        "retry_button": "🔄 Retry",
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
        "coach_question": "Hast du diesen Schritt verstanden? Wollen wir weitermachen?",
        "coach_yes": "Ja, ich habe verstanden",
        "coach_no": "Nein, anders erklären",
        "coach_finish": "Ich bin fertig, zeig mir die Zusammenfassung",
        "coach_done": "🎉 Gut gemacht! Du hast alle Schritte abgeschlossen.",
        "coach_step": "Schritt",
        "coach_restart": "🔄 Neue Übung starten",
        "coach_summary": "📋 Zusammenfassung deines Fortschritts",
        "button_download_pdf": "📥 Korrektur als PDF herunterladen",
        "spinner": "⏳ Schritt wird generiert...",
        "warning_empty": "⚠️ Bitte geben Sie eine Aufgabe ein.",
        "ai_init_error": "KI-Initialisierungsfehler: {error}",
        "verif_error": "Fehler bei der Zahlungsüberprüfung.",
        "pdf_title": "Meine personalisierte Korrektur",
        "pdf_enonce": "📌 Eingereichte Aufgabe:",
        "pdf_resolution": "📝 Schritt-für-Schritt-Lösung:",
        "preambule_title": "📖 Kurserinnerung",
        "exemple_concret_title": "💡 Konkretes Beispiel",
        "exemple_theorique_title": "🧮 Theoretisches Beispiel",
        "retry_button": "🔄 Erneut versuchen",
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
        "coach_question": "¿Has entendido este paso? ¿Pasamos al siguiente?",
        "coach_yes": "Sí, lo he entendido",
        "coach_no": "No, explica de otra forma",
        "coach_finish": "He terminado, muéstrame el resumen",
        "coach_done": "🎉 ¡Bien hecho! Has completado todos los pasos.",
        "coach_step": "Paso",
        "coach_restart": "🔄 Empezar un nuevo ejercicio",
        "coach_summary": "📋 Resumen de tu progreso",
        "button_download_pdf": "📥 Descargar corrección en PDF",
        "spinner": "⏳ Generando paso...",
        "warning_empty": "⚠️ Por favor, introduce un enunciado.",
        "ai_init_error": "Error de inicialización IA: {error}",
        "verif_error": "Error de verificación del pago.",
        "pdf_title": "Mi Corrección Personalizada",
        "pdf_enonce": "📌 Enunciado enviado:",
        "pdf_resolution": "📝 Resolución paso a paso:",
        "preambule_title": "📖 Recordatorio del curso",
        "exemple_concret_title": "💡 Ejemplo concreto",
        "exemple_theorique_title": "🧮 Ejemplo teórico",
        "retry_button": "🔄 Reintentar",
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
        "coach_question": "Hai capito questo passaggio? Passiamo al prossimo?",
        "coach_yes": "Sì, ho capito",
        "coach_no": "No, spiega in modo diverso",
        "coach_finish": "Ho finito, mostrami il riepilogo",
        "coach_done": "🎉 Bravo! Hai completato tutti i passaggi.",
        "coach_step": "Passo",
        "coach_restart": "🔄 Inizia un nuovo esercizio",
        "coach_summary": "📋 Riepilogo dei tuoi progressi",
        "button_download_pdf": "📥 Scarica la correzione in PDF",
        "spinner": "⏳ Generazione del passaggio...",
        "warning_empty": "⚠️ Inserisci un enunciato.",
        "ai_init_error": "Errore di inizializzazione IA: {error}",
        "verif_error": "Errore di verifica del pagamento.",
        "pdf_title": "La Mia Correzione Personalizzata",
        "pdf_enonce": "📌 Enunciato inviato:",
        "pdf_resolution": "📝 Risoluzione passo dopo passo:",
        "preambule_title": "📖 Promemoria del corso",
        "exemple_concret_title": "💡 Esempio concreto",
        "exemple_theorique_title": "🧮 Esempio teorico",
        "retry_button": "🔄 Riprova",
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
        "coach_question": "هل فهمت هذه الخطوة؟ هل ننتقل إلى التالية؟",
        "coach_yes": "نعم، لقد فهمت",
        "coach_no": "لا، اشرح بطريقة أخرى",
        "coach_finish": "لقد انتهيت، أرني الملخص",
        "coach_done": "🎉 أحسنت! لقد أكملت جميع الخطوات.",
        "coach_step": "الخطوة",
        "coach_restart": "🔄 ابدأ تمرينًا جديدًا",
        "coach_summary": "📋 ملخص تقدمك",
        "button_download_pdf": "📥 تحميل التصحيح بصيغة PDF",
        "spinner": "⏳ جارٍ إنشاء الخطوة...",
        "warning_empty": "⚠️ يرجى إدخال نص التمرين.",
        "ai_init_error": "خطأ في تهيئة الذكاء الاصطناعي: {error}",
        "verif_error": "خطأ في التحقق من الدفع.",
        "pdf_title": "تصحيحي المخصص",
        "pdf_enonce": "📌 النص المرسل:",
        "pdf_resolution": "📝 الحل خطوة بخطوة:",
        "preambule_title": "📖 تذكير بالدرس",
        "exemple_concret_title": "💡 مثال ملموس",
        "exemple_theorique_title": "🧮 مثال نظري",
        "retry_button": "🔄 إعادة المحاولة",
    },
}

@st.cache_data
def charger_traductions():
    chemin_script = os.path.dirname(os.path.abspath(__file__))
    chemin_fichier = os.path.join(chemin_script, "translations.json")
    try:
        with open(chemin_fichier, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return TRADUCTIONS_SECOURS

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
# COOKIE MANAGER
# ============================================================
if COOKIES_DISPONIBLES:
    cookie_manager = stx.CookieManager(key="cookie_manager_math")
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
    st.stop()

try:
    stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
    ID_PRIX_UNIQUE = st.secrets["STRIPE_PRICE_ID"]
    URL_APP = st.secrets["MON_URL_STREAMLIT"]
except Exception as e:
    st.error(f"Erreur de configuration Stripe : {e}")
    st.stop()

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
# FONCTION PDF (CORRIGÉE — MULTILINGUE)
# ============================================================
def generer_pdf(texte_correction, enonce_exercice):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40,
        title=t("pdf_title")
    )
    styles = getSampleStyleSheet()

    langue = st.session_state.get("langue", "fr")
    est_arabe = (langue == "ar")

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

    # --------------------------------------------------------
    # NETTOYAGE DU TEXTE POUR REPORTLAB
    # --------------------------------------------------------
    def nettoyer_pour_pdf(texte):
        if not texte:
            return ""

        # ============================================================
        # ÉTAPE 0 : SUPPRESSION DU LATEX / KATEX
        # ============================================================
        texte = re.sub(r'\$\$(.+?)\$\$', r'\1', texte, flags=re.DOTALL)
        texte = re.sub(r'\$(.+?)\$', r'\1', texte, flags=re.DOTALL)
        texte = re.sub(r'\\\[(.+?)\\\]', r'\1', texte, flags=re.DOTALL)
        texte = re.sub(r'\\\((.+?)\\\)', r'\1', texte, flags=re.DOTALL)

        texte = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', r'(\1)/(\2)', texte)

        texte = texte.replace(r'\times', '×')
        texte = texte.replace(r'\cdot', '·')
        texte = texte.replace(r'\leq', '≤')
        texte = texte.replace(r'\geq', '≥')
        texte = texte.replace(r'\neq', '≠')
        texte = texte.replace(r'\infty', '∞')
        texte = texte.replace(r'\pi', 'π')
        texte = texte.replace(r'\alpha', 'α')
        texte = texte.replace(r'\beta', 'β')
        texte = texte.replace(r'\Delta', 'Δ')
        texte = texte.replace(r'\mathbb{R}', 'ℝ')

        texte = re.sub(r'_1', '₁', texte)
        texte = re.sub(r'_2', '₂', texte)
        texte = re.sub(r'_3', '₃', texte)

        texte = re.sub(r'\^2', '²', texte)
        texte = re.sub(r'\^3', '³', texte)

        texte = re.sub(r'\\[a-zA-Z]+', '', texte)
        texte = texte.replace('{', '').replace('}', '')

        # ============================================================
        # ÉTAPE 0bis : SUPPRESSION DES 'n' PARASITES
        # ============================================================
        texte = re.sub(r'^-n\s+', '', texte)
        texte = re.sub(r'(^|\n)\s*n\s+', r'\1', texte)
        texte = re.sub(r'(\w)-n\s+', r'\1 ', texte)
        texte = re.sub(r'(\w)n\s+([A-ZÉÈÀÊÎÔÛ])', r'\1 \2', texte)
        texte = re.sub(r'(\d)n\b', r'\1', texte)
        texte = re.sub(r'(\w)n([A-ZÉÈÀÊÎÔÛ])', r'\1 \2', texte)

        # ============================================================
        # ÉTAPE 1 : NORMALISATION
        # ============================================================
        texte = texte.replace('\r\n', '\n').replace('\r', '\n')
        texte = texte.replace('\\n', '\n')
        texte = re.sub(r'(\S)\n(\S)', r'\1\2', texte)

        # ============================================================
        # ÉTAPE 2 : ÉCHAPPEMENT XML POUR REPORTLAB
        # ============================================================
        texte = texte.replace('&', '&amp;')
        texte = texte.replace('<', '&lt;').replace('>', '&gt;')
        texte = texte.replace('&lt;br/&gt;', '<br/>')

        # ============================================================
        # ÉTAPE 3 : MARKDOWN → HTML REPORTLAB
        # ============================================================
        texte = re.sub(r'^###\s+(.*)$', r'<b>\1</b>', texte, flags=re.MULTILINE)
        texte = re.sub(r'^##\s+(.*)$',  r'<b><font size="13">\1</font></b>', texte, flags=re.MULTILINE)
        texte = re.sub(r'^#\s+(.*)$',   r'<b><font size="15">\1</font></b>', texte, flags=re.MULTILINE)

        # Saut de ligne après les titres Markdown
        texte = re.sub(r'(<b><font size="1[35]">.*?</font></b>)([A-ZÉÈÀÊÎÔÛ])', r'\1<br/>\2', texte)
        texte = re.sub(r'(<b>.*?</b>)([A-ZÉÈÀÊÎÔÛ])', r'\1<br/>\2', texte)

        # ============================================================
        # TITRES DANS TOUTES LES LANGUES
        # ============================================================
        titres_connus = [
            # Français
            "Rappel de cours", "Rappel théorique", "Exemple concret",
            "Exemple théorique", "Application à l'exercice",
            "Rappel :", "Concret :", "Théorique :", "Application :",
            "Conclusion :", "Définition :", "Situation :", "Tarif :",
            "Fonction :", "Énoncé :",
            # Anglais
            "Course reminder", "Theoretical reminder", "Concrete example",
            "Theoretical example", "Application to the exercise",
            "Reminder:", "Real-life example:", "Theory:",
            # Allemand
            "Kurserinnerung", "Theoretische Erinnerung", "Konkretes Beispiel",
            "Theoretisches Beispiel", "Anwendung auf die Übung",
            # Espagnol
            "Recordatorio del curso", "Recordatorio teórico", "Ejemplo concreto",
            "Ejemplo teórico", "Aplicación al ejercicio",
            # Italien
            "Promemoria del corso", "Promemoria teorico", "Esempio concreto",
            "Esempio teorico", "Applicazione all'esercizio",
            # Arabe
            "تذكير بالدرس", "تذكير نظري", "مثال ملموس", "مثال نظري",
            "تطبيق على التمرين",
        ]
        for titre in titres_connus:
            for lettre in "ABCDEFGHIJKLMNOPQRSTUVWXYZÉÈÀÊÎÔÛ":
                texte = texte.replace(titre + lettre, titre + "<br/>" + lettre)
            texte = texte.replace(titre + " ", titre + "<br/>")

        # Listes Markdown
        texte = re.sub(r'^\s*[-*]\s+(.*)$', r'• \1', texte, flags=re.MULTILINE)

        # Gras / italique
        texte = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', texte)
        texte = re.sub(r'\*(.+?)\*',     r'<i>\1</i>', texte)

        # Séparateurs
        texte = re.sub(r'^\s*---\s*$', '<br/>', texte, flags=re.MULTILINE)

        # ============================================================
        # ÉTAPE 4 : SAUTS DE LIGNE FINAUX
        # ============================================================
        texte = texte.replace('\n', '<br/>')
        texte = re.sub(r'(<br/>){3,}', '<br/><br/>', texte)

        return texte

    # --------------------------------------------------------
    # CONSTRUCTION DU PDF
    # --------------------------------------------------------
    histoire = []
    histoire.append(Paragraph(t("pdf_title"), style_titre))
    histoire.append(Spacer(1, 10))

    histoire.append(Paragraph(t("pdf_enonce"), style_sous_titre))
    enonce_propre = nettoyer_pour_pdf(enonce_exercice)
    histoire.append(Paragraph(enonce_propre, style_enonce))
    histoire.append(Spacer(1, 10))

    histoire.append(Paragraph(t("pdf_resolution"), style_sous_titre))
    corps_propre = nettoyer_pour_pdf(texte_correction)

    blocs = corps_propre.split('<br/><br/>')
    for bloc in blocs:
        bloc = bloc.strip()
        if not bloc:
            continue
        try:
            histoire.append(Paragraph(bloc, style_corps))
        except Exception:
            bloc_secours = re.sub(r'<[^>]+>', '', bloc)
            histoire.append(Paragraph(bloc_secours, style_corps))

    histoire.append(Spacer(1, 20))
    histoire.append(Paragraph(
        "This document is for informational purposes only. Responses may include mistakes.",
        style_footer
    ))

    doc.build(histoire)
    buffer.seek(0)
    return buffer

# ============================================================
# MODÈLES DISPONIBLES (fallback)
# ============================================================
MODELES_DISPONIBLES = [
    'gemini-3.5-flash-lite',
    'gemini-3.1-flash-lite',
    'gemini-2.5-flash-lite',
]

def _appeler_gemini(instructions, contenu="Génère l'étape demandée."):
    derniere_erreur = None
    for modele in MODELES_DISPONIBLES:
        try:
            reponse = client_ia.models.generate_content(
                model=modele,
                contents=contenu,
                config=types.GenerateContentConfig(system_instruction=instructions)
            )
            return reponse.text
        except Exception as e:
            derniere_erreur = e
            msg = str(e)
            if "404" in msg or "NOT_FOUND" in msg:
                continue
            if "503" in msg or "UNAVAILABLE" in msg:
                time.sleep(2 + random.uniform(0, 1))
                continue
            raise
    raise derniere_erreur

# ============================================================
# GÉNÉRATION D'UNE ÉTAPE (MULTILINGUE)
# ============================================================
def generer_etape(exercice, etape_numero, historique_explications=None, mode="standard"):
    noms_langues = {
        "fr": "français", "en": "anglais", "de": "allemand",
        "es": "espagnol", "it": "italien", "ar": "arabe",
    }
    nom_langue = noms_langues.get(st.session_state.langue, "anglais")

    # Titres traduits
    titres = {
        "fr": {"rappel": "Rappel théorique", "concret": "Exemple concret",
               "theorique": "Exemple théorique", "application": "Application à l'exercice"},
        "en": {"rappel": "Theoretical reminder", "concret": "Concrete example",
               "theorique": "Theoretical example", "application": "Application to the exercise"},
        "de": {"rappel": "Theoretische Erinnerung", "concret": "Konkretes Beispiel",
               "theorique": "Theoretisches Beispiel", "application": "Anwendung auf die Übung"},
        "es": {"rappel": "Recordatorio teórico", "concret": "Ejemplo concreto",
               "theorique": "Ejemplo teórico", "application": "Aplicación al ejercicio"},
        "it": {"rappel": "Promemoria teorico", "concret": "Esempio concreto",
               "theorique": "Esempio teorico", "application": "Applicazione all'esercizio"},
        "ar": {"rappel": "تذكير نظري", "concret": "مثال ملموس",
               "theorique": "مثال نظري", "application": "تطبيق على التمرين"},
    }
    titres_langue = titres.get(st.session_state.langue, titres["en"])

    historique_txt = ""
    if historique_explications:
        historique_txt = "\n".join(
            f"Étape {i+1} déjà validée : {exp}"
            for i, exp in enumerate(historique_explications)
        )

    if mode == "standard":
        instructions = (
            f"You are a private math coach. Answer ONLY in {nom_langue}.\n"
            f"The student is working on this exercise:\n{exercice}\n\n"
            f"{historique_txt}\n\n"
            f"STRICT RULES:\n"
            f"1. Explain ONLY step {etape_numero} (not the following ones, not the final answer).\n"
            f"2. Use simple words adapted to a high school student.\n"
            f"3. MANDATORY STRUCTURE of your answer (in this order):\n"
            f"   📖 **{titres_langue['rappel']}** : the rule/definition/formula used\n"
            f"   💡 **{titres_langue['concret']}** : a daily life situation (money, distances, pizza...)\n"
            f"   🧮 **{titres_langue['theorique']}** : a small fully solved example with DIFFERENT numbers\n"
            f"   🎯 **{titres_langue['application']}** : what we concretely do here\n"
            f"4. NEVER give the complete solution or the final result of the student's exercise.\n"
            f"5. End with an encouraging tone.\n"
            f"6. Maximum 15 lines.\n"
            f"7. IMPORTANT: Write the titles EXACTLY as given above, in {nom_langue}, NOT in French.\n"
        )
    else:
        instructions = (
            f"You are a private math coach. Answer ONLY in {nom_langue}.\n"
            f"The student is working on: {exercice}\n"
            f"{historique_txt}\n\n"
            f"The student did NOT UNDERSTAND step {etape_numero}. You must REFORMULATE it:\n"
            f"- Use EVEN SIMPLER words.\n"
            f"- OR propose ANOTHER METHOD (diagram, decomposition, analogy).\n"
            f"- OR give a CONCRETE example from daily life.\n"
            f"- Keep the structure: 📖 {titres_langue['rappel']} / 💡 {titres_langue['concret']} "
            f"/ 🧮 {titres_langue['theorique']} / 🎯 {titres_langue['application']}\n"
            f"- Still do NOT give the final answer.\n"
            f"- Maximum 15 lines.\n"
            f"- IMPORTANT: Write the titles in {nom_langue}, NOT in French.\n"
        )

    return _appeler_gemini(instructions, contenu="Génère l'étape demandée.")

# ============================================================
# PRÉAMBULE THÉORIQUE (MULTILINGUE)
# ============================================================
def generer_preambule_theorique(exercice):
    noms_langues = {
        "fr": "français", "en": "anglais", "de": "allemand",
        "es": "espagnol", "it": "italien", "ar": "arabe",
    }
    nom_langue = noms_langues.get(st.session_state.langue, "français")

    # Titres traduits
    titres = {
        "fr": {"rappel": "Rappel de cours", "concret": "Exemple concret",
               "theorique": "Exemple théorique"},
        "en": {"rappel": "Course reminder", "concret": "Concrete example",
               "theorique": "Theoretical example"},
        "de": {"rappel": "Kurserinnerung", "concret": "Konkretes Beispiel",
               "theorique": "Theoretisches Beispiel"},
        "es": {"rappel": "Recordatorio del curso", "concret": "Ejemplo concreto",
               "theorique": "Ejemplo teórico"},
        "it": {"rappel": "Promemoria del corso", "concret": "Esempio concreto",
               "theorique": "Esempio teorico"},
        "ar": {"rappel": "تذكير بالدرس", "concret": "مثال ملموس",
               "theorique": "مثال نظري"},
    }
    titres_langue = titres.get(st.session_state.langue, titres["en"])

    instructions = (
        f"You are a math coach. Answer ONLY in {nom_langue}.\n"
        f"The student submitted: {exercice}\n\n"
        f"Generate a STRUCTURED PREAMBLE (max 25 lines):\n\n"
        f"## 📖 {titres_langue['rappel']}\n"
        f"- Necessary definition(s) and formula(s)\n"
        f"- Important properties to know\n\n"
        f"## 💡 {titres_langue['concret']}\n"
        f"- A daily life situation illustrating the concept\n"
        f"- Simple and explicit numbers\n\n"
        f"## 🧮 {titres_langue['theorique']}\n"
        f"- A small numerical example DIFFERENT from the student's exercise\n"
        f"- Fully solved step by step\n\n"
        f"Be clear, pedagogical, structured with Markdown titles.\n"
        f"IMPORTANT: Write the titles in {nom_langue}, NOT in French.\n"
        f"IMPORTANT: Always put a line break after each title."
    )

    try:
        return _appeler_gemini(instructions, contenu="Génère le préambule théorique.")
    except Exception as e:
        return f"_(Préambule indisponible : {e})_"

# ============================================================
# GESTION DE L'ÉTAT PÉDAGOGIQUE
# ============================================================
def initialiser_session_pedago(exercice):
    st.session_state.etape_actuelle = 1
    st.session_state.historique_explications = []
    st.session_state.explication_en_cours = None
    st.session_state.dernier_enonce = exercice
    st.session_state.correction_terminee = False
    st.session_state.mode_explication = "standard"
    st.session_state.preambule_theorique = None
    st.session_state.video_query = exercice[:80]
def reinitialiser_session_pedago():
    for k in ["etape_actuelle", "historique_explications",
              "explication_en_cours", "correction_terminee",
              "mode_explication", "derniere_correction",
              "preambule_theorique"]:
        st.session_state.pop(k, None)

# ============================================================
# AFFICHAGE DU COACH INTERACTIF
# ============================================================
def afficher_video(exercice, etape=None):
    """Affiche un bouton qui ouvre YouTube sur le bon concept."""
    with st.expander("📺 Voir une vidéo explicative", expanded=False):
        # Utilise la requête préparée par l'IA, sinon le début de l'exercice
        query = st.session_state.get("video_query") or exercice[:80]
        if not query:
            st.info("Pas de vidéo disponible.")
            return
        
        lien = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
        st.markdown(f"### [{query}]({lien})")
        st.caption("Clique sur le lien pour voir les vidéos YouTube.")

def afficher_coach_interactif(exercice):
    if "video_query" not in st.session_state:
        st.session_state.video_query = exercice[:80]

    if st.session_state.etape_actuelle > 15:
        st.session_state.correction_terminee = True
        st.rerun()

    if st.session_state.explication_en_cours is None:
        with st.spinner(t("spinner")):
            try:
                explication = generer_etape(
                    exercice,
                    st.session_state.etape_actuelle,
                    st.session_state.historique_explications,
                    mode=st.session_state.mode_explication
                )
                st.session_state.explication_en_cours = explication
            except Exception as api_error:
                afficher_erreur_ia(api_error)
                if st.button("🔄 " + t("retry_button"),
                             key=f"retry_{st.session_state.etape_actuelle}"):
                    st.session_state.explication_en_cours = None
                    st.rerun()
                return

    st.progress(
        min(st.session_state.etape_actuelle / 10, 1.0),
        text=f"{t('coach_step')} {st.session_state.etape_actuelle}"
    )

    st.markdown(f"### 📘 {t('coach_step')} {st.session_state.etape_actuelle}")
    st.markdown(st.session_state.explication_en_cours)

    afficher_video(st.session_state.dernier_enonce)

    st.write("---")

    st.markdown(f"**{t('coach_question')}**")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ " + t("coach_yes"), use_container_width=True,
                     type="primary", key=f"yes_{st.session_state.etape_actuelle}"):
            st.session_state.historique_explications.append(
                st.session_state.explication_en_cours
            )
            st.session_state.etape_actuelle += 1
            st.session_state.explication_en_cours = None
            st.session_state.mode_explication = "standard"
            st.rerun()

    with col2:
        if st.button("🔄 " + t("coach_no"), use_container_width=True,
                     key=f"no_{st.session_state.etape_actuelle}"):
            st.session_state.mode_explication = "alternative"
            st.session_state.explication_en_cours = None
            st.rerun()

    if st.session_state.etape_actuelle >= 3:
        if st.button("🎉 " + t("coach_finish"), use_container_width=True,
                     key=f"finish_{st.session_state.etape_actuelle}"):
            st.session_state.correction_terminee = True
            st.rerun()
# ============================================================
# AFFICHAGE RÉCAPITULATIF FINAL + PDF
# ============================================================
def afficher_recapitulatif_final(nom_fichier="correction_coach_math.pdf"):
    st.success(t("coach_done"))

    exercice = st.session_state.get('dernier_enonce', '')

    if st.session_state.get("preambule_theorique") is None:
        with st.spinner("📖 Génération du rappel de cours..."):
            preambule = generer_preambule_theorique(exercice)
            st.session_state.preambule_theorique = preambule

    preambule = st.session_state.preambule_theorique

    resolution = "\n\n".join(
        f"### {t('coach_step')} {i+1}\n{exp}"
        for i, exp in enumerate(st.session_state.get("historique_explications", []))
    )

    recapitulatif_complet = (
        f"# 📖 {t('preambule_title')}\n\n{preambule}\n\n"
        f"---\n\n# 📝 {t('pdf_resolution')}\n\n{resolution}"
    )
    st.session_state['derniere_correction'] = recapitulatif_complet

    st.write("---")
    st.markdown(f"#### {t('coach_summary')}")
    st.markdown(recapitulatif_complet)

    pdf_buffer = generer_pdf(recapitulatif_complet, exercice)
    st.download_button(
        label=t("button_download_pdf"),
        data=pdf_buffer,
        file_name=nom_fichier,
        mime="application/pdf",
        use_container_width=True
    )

    if st.button(t("coach_restart"), use_container_width=True, key="restart_btn"):
        reinitialiser_session_pedago()
        st.rerun()

# ============================================================
# GESTION D'ERREUR IA LISIBLE
# ============================================================
def afficher_erreur_ia(api_error):
    message = str(api_error)
    if "401" in message or "UNAUTHENTICATED" in message or "API_KEY_INVALID" in message:
        st.error("🔑 Problème d'authentification avec l'API. Vérifiez votre clé API dans les secrets Streamlit.")
    elif "404" in message or "NOT_FOUND" in message:
        st.error("🤖 Le modèle demandé n'est pas disponible avec votre clé API. Vérifiez la région ou le nom du modèle.")
    elif "503" in message or "UNAVAILABLE" in message:
        st.error("⏳ Le service est momentanément surchargé. Merci de réessayer dans quelques instants.")
    elif "429" in message or "RESOURCE_EXHAUSTED" in message:
        st.error("⏳ Trop de requêtes envoyées. Merci de patienter une minute avant de réessayer.")
    else:
        st.error(f"Erreur lors de la génération : {api_error}")
# ============================================================
# GÉNÉRATEUR DE SUJETS D'ÉVALUATION ET DE CONCOURS
# ============================================================








def generer_pdf_sujet(texte_sujet):
    import io
    import re
    from xml.sax.saxutils import escape

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import (
        getSampleStyleSheet, ParagraphStyle
    )
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        HRFlowable,
        KeepTogether
    )

    # Création du PDF en mémoire
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.7 * cm,
        leftMargin=1.7 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    styles = getSampleStyleSheet()

    bleu = colors.HexColor("#17365D")
    gris = colors.HexColor("#D9E2F3")

    titre = ParagraphStyle(
        "TitreSujet",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=22,
        alignment=TA_CENTER,
        textColor=bleu,
        spaceAfter=14
    )

    exercice = ParagraphStyle(
        "TitreExercice",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=bleu,
        spaceBefore=12,
        spaceAfter=7,
        keepWithNext=True
    )

    normal = ParagraphStyle(
        "TexteNormal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        spaceAfter=5
    )

    question = ParagraphStyle(
        "Question",
        parent=normal,
        leftIndent=7,
        spaceBefore=3,
        spaceAfter=7
    )

    informations = ParagraphStyle(
        "Informations",
        parent=normal,
        fontSize=9,
        leading=15,
        spaceAfter=5
    )

    consigne = ParagraphStyle(
        "Consigne",
        parent=normal,
        leftIndent=5,
        spaceAfter=5
    )

    story = []

    # Normalisation du texte
    texte = str(texte_sujet or "")
    texte = texte.replace("\r\n", "\n").replace("\r", "\n")

    # Réunir les notations géométriques coupées
    texte = re.sub(
        r"\(\s*\n\s*([A-Za-z])\s*\)",
        r"(\1)",
        texte
    )

    # Séparer les questions collées
    lignes = texte.split("\n")
    lignes_propres = []

    for ligne in lignes:

        ligne = ligne.strip()

        # Séparer les questions numérotées
        ligne = re.sub(
            r"(?<!\w)(?=\d+\.\s)",
            "\n",
            ligne
        )

        # Séparer les sous-questions a), b), c), d)
        ligne = re.sub(
            r"(?<!\w)(?=[a-d]\)\s)",
            "\n",
            ligne
        )

        # Séparer Réponse et Justification
        ligne = re.sub(
            r"\s+(?=Justification\s*:)",
            "\n",
            ligne,
            flags=re.IGNORECASE
        )

        # Séparer les consignes de notation collées
        ligne = re.sub(
            r"\s+-\s+(?=La droite|Le segment|La demi-droite)",
            "\n",
            ligne
        )

        lignes_propres.extend(ligne.split("\n"))

    lignes = lignes_propres

    premier_titre = True

    for ligne in lignes:

        ligne = ligne.strip()

        if not ligne:
            story.append(Spacer(1, 4))
            continue

        # Nettoyage du Markdown
        ligne = ligne.replace("**", "")
        ligne = ligne.replace("__", "")

        # Nettoyage des délimiteurs LaTeX
        ligne = re.sub(r"\\\(|\\\)", "", ligne)
        ligne = re.sub(r"\\\[|\\\]", "", ligne)
        ligne = ligne.replace("$", "")

        # Conversion des notations mathématiques
        remplacements = {
            r"\in": "appartient à",
            r"\notin": "n'appartient pas à",
            r"\leq": "≤",
            r"\geq": "≥",
            r"\neq": "≠",
            r"\times": "x",
            r"\div": "/",
            r"\approx": "environ",
            r"\parallel": "parallèle à",
            r"\perp": "perpendiculaire à",
            r"\Delta": "Delta",
            r"\delta": "delta",
            r"\pi": "pi",
            r"\sqrt": "racine"
        }

        for ancien, nouveau in remplacements.items():
            ligne = ligne.replace(ancien, nouveau)

        # Nettoyage des indices géométriques
        ligne = re.sub(
            r"_\{?([0-9]+)\}?",
            r"\1",
            ligne
        )

        # Titre principal
        if premier_titre and (
            "SUJET D'ÉVALUATION" in ligne.upper()
            or "SUJET D'EVALUATION" in ligne.upper()
            or "SUJET D'ÉVALUATION / CONCOURS" in ligne.upper()
        ):
            story.append(
                Paragraph(escape(ligne), titre)
            )

            story.append(
                HRFlowable(
                    width="100%",
                    thickness=1.2,
                    color=bleu,
                    spaceAfter=12
                )
            )

            premier_titre = False
            continue

        # Titres des exercices
        if re.match(
            r"Exercice\s+\d+",
            ligne,
            re.IGNORECASE
        ):
            story.append(
                KeepTogether([
                    Spacer(1, 5),
                    Paragraph(escape(ligne), exercice),
                    HRFlowable(
                        width="100%",
                        thickness=0.6,
                        color=gris,
                        spaceAfter=7
                    )
                ])
            )
            continue

        # Consignes générales
        if ligne.lower().startswith("consignes générales"):
            story.append(
                Paragraph(
                    "<b>Consignes générales</b>",
                    normal
                )
            )
            continue

        # Informations de l'élève
        if re.match(
            r"^(Nom|Prénom|Classe|Date|Chapitre|Niveau|Durée|Barème)",
            ligne,
            re.IGNORECASE
        ):
            story.append(
                Paragraph(escape(ligne), informations)
            )
            continue

        # Réponses et justifications
        if re.match(
            r"^(Réponse|Justification)\s*:",
            ligne,
            re.IGNORECASE
        ):
            story.append(
                Paragraph(escape(ligne), question)
            )
            continue

        # Questions et sous-questions
        if re.match(
            r"^(\d+\.|[a-d]\))",
            ligne
        ):
            story.append(
                Paragraph(escape(ligne), question)
            )
            continue

# Remplacer les pointillés par des traits continus
ligne = re.sub(
    r"\.{5,}",
    lambda m: "_" * len(m.group()),
    ligne
)
        
        # Schémas textuels
        if re.search(r"[.=_-]{5,}", ligne):
            schema = ParagraphStyle(
                "SchemaGeometrique",
                fontName="Courier",
                fontSize=9,
                leading=14,
                leftIndent=8
            )

            story.append(
                Paragraph(escape(ligne), schema)
            )
            continue

        # Texte ordinaire
        story.append(
            Paragraph(escape(ligne), consigne)
        )

    # Construction du document
    doc.build(story)

    buffer.seek(0)

    return buffer





def afficher_generateur_sujet():

    if "ouvrir_generateur_sujet" not in st.session_state:
        st.session_state.ouvrir_generateur_sujet = False

    if "sujet_genere" not in st.session_state:
        st.session_state.sujet_genere = ""

    if "correction_sujet" not in st.session_state:
        st.session_state.correction_sujet = ""

    # Bouton toujours accessible
    if st.button(
        "📝 Je peux vous proposer un sujet d'évaluation ou de concours",
        use_container_width=True,
        key="btn_ouvrir_generateur_sujet"
    ):
        st.session_state.ouvrir_generateur_sujet = (
            not st.session_state.ouvrir_generateur_sujet
        )
        st.rerun()

    if not st.session_state.ouvrir_generateur_sujet:
        return

    st.markdown("---")
    st.markdown("### 📚 Création de votre sujet")

    with st.form(
        key="form_sujet_evaluation_principal",
        clear_on_submit=False
    ):

        niveau = st.selectbox(
            "Choisissez votre niveau :",
            [
                "6ème", "5ème", "4ème", "3ème",
                "Seconde", "Première", "Terminale",
                "Concours"
            ]
        )

        type_sujet = st.selectbox(
            "Type de sujet :",
            ["Évaluation", "Concours", "Brevet", "Baccalauréat"]
        )

        chapitre = st.text_input(
            "Chapitre ou thème souhaité :",
            placeholder="Exemple : Théorème de Pythagore"
        )

        difficulte = st.selectbox(
            "Niveau de difficulté :",
            ["Facile", "Moyen", "Difficile"]
        )

        duree = st.selectbox(
            "Durée du sujet :",
            ["30 minutes", "1 heure", "1 heure 30", "2 heures"]
        )

        generer = st.form_submit_button(
            "🚀 Générer mon sujet",
            use_container_width=True
        )

    if generer:

        if not chapitre.strip():
            st.warning("Veuillez indiquer un chapitre ou un thème.")

        else:
            with st.spinner("⏳ Création de votre sujet..."):

                try:
                
                    
                    instructions = f"""
Tu es un professeur de mathématiques expérimenté,
spécialisé dans la création de sujets d'évaluation
et de concours scolaires.

Crée un sujet de {type_sujet} en mathématiques.

INFORMATIONS :
Niveau : {niveau}
Chapitre : {chapitre}
Difficulté : {difficulte}
Durée : {duree}

PRÉSENTATION DU SUJET :

1. Un seul titre principal.
2. Une seule zone pour le nom, le prénom, la classe et la date.
3. Indique clairement le chapitre, le niveau, la durée
   et le barème total.
4. Ajoute des consignes générales courtes et précises.
5. Organise les exercices du plus simple au plus difficile.
6. Attribue un barème à chaque exercice.
7. Le total des points doit être exactement égal à 20.

RÈGLES OBLIGATOIRES DE QUALITÉ :


- Le titre principal doit apparaître une seule fois.
- Les informations Nom, Prénom, Classe et Date
  doivent apparaître une seule fois.
- Ne crée pas une deuxième zone d'identification.
- Si une question propose plusieurs mots à utiliser,
  vérifie qu'il y a assez de phrases pour les employer.
- Pour chaque exercice, vérifie que le nombre de points
  correspond exactement à son contenu.
- Ne crée pas de schéma ASCII si sa lecture risque
  d'être ambiguë.
- Pour les constructions géométriques, indique clairement
  quand l'élève doit utiliser une feuille séparée.
- Termine toujours toutes les consignes et tous les exercices.
- Ne coupe jamais le sujet au milieu d'une phrase.

- Chaque question doit être complète et compréhensible.
- Aucune phrase ne doit être coupée ou inachevée.
- Vérifie que toutes les questions ont une réponse possible.
- Vérifie la cohérence mathématique de chaque exercice.
- Ne pose jamais une question qui dépend d'une figure absente.
- Si une figure est nécessaire, fournis-la directement
  sous forme de schéma ASCII simple et lisible.
- Ne demande jamais à l'élève d'observer une figure
  qui n'est pas présente dans le sujet.
- Les points, droites et segments doivent être correctement
  nommés et utilisés.
- Les longueurs représentées doivent être cohérentes
  avec les questions posées.
- Ne demande pas de citer un point extérieur à une droite
  si tous les points proposés appartiennent à cette droite.
- Prévois suffisamment de lignes pour les réponses.
- Pour les constructions, précise clairement le matériel
  et les consignes.
- Ne répète pas les informations d'identification.
- N'utilise pas de séparateurs inutiles comme -- ou ___.
- N'ajoute aucun texte technique ou commentaire destiné
  au développeur.

VÉRIFICATION AVANT DE TERMINER :

Relis tout le sujet.
Vérifie les calculs, les figures, les notations,
les consignes et le total des points.
Corrige toute contradiction avant de répondre.

FORMAT DE SORTIE :

Utilise des titres clairs :
SUJET D'ÉVALUATION
Exercice 1
Exercice 2
Exercice 3, etc.

Utilise une numérotation simple.
Utilise une notation mathématique lisible.
Laisse des espaces pour les réponses.

IMPORTANT :
Ne fournis aucune correction ni réponse.
Réponds uniquement avec le sujet final en français.
"""


                    sujet = _appeler_gemini(
                        instructions,
                        contenu="Génère le sujet demandé."
                    )

                    if sujet:
                        st.session_state.sujet_genere = sujet
                        st.session_state.correction_sujet = ""

                except Exception as e:
                    st.error(f"Erreur de génération : {e}")

    # Affichage et téléchargement du sujet
    if st.session_state.sujet_genere:

        st.markdown("---")
        st.markdown("### 📄 Sujet d'évaluation")

        st.markdown(st.session_state.sujet_genere)

        pdf_sujet = generer_pdf_sujet(
            st.session_state.sujet_genere
        )

        st.download_button(
            "📥 Télécharger le sujet en PDF",
            data=pdf_sujet.getvalue(),
            file_name="sujet_evaluation.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="download_sujet_evaluation"
        )

        st.markdown("---")
        st.markdown("### 🔐 Correction réservée à l'enseignant")

    
          
        if st.button(    
            "✏️ Générer la correction détaillée",
            use_container_width=True,
            key="btn_correction_sujet"
        ):

            with st.spinner("⏳ Préparation du corrigé enseignant..."):

                try:
                    prompt = f"""
Tu es un professeur expérimenté de mathématiques.

Voici le sujet à corriger :

{st.session_state.sujet_genere}

Produis un corrigé enseignant complet.

Pour chaque exercice :
1. Rappelle la question.
2. Détaille chaque calcul.
3. Explique les méthodes utilisées.
4. Donne la réponse finale.
5. Indique le barème de chaque question.

Vérifie la cohérence des résultats.
Réponds en français.
"""

                    response = _appeler_gemini(
                        prompt,
                        contenu="Génère la correction détaillée du sujet."
                    )

                    st.session_state.correction_sujet = response or ""

                    if not st.session_state.correction_sujet:
                        st.error("La correction n'a pas pu être générée.")

                except Exception as e:
                    st.error(f"Erreur de correction : {e}")

        # Affichage et téléchargement du corrigé
        if st.session_state.correction_sujet:

            st.success("✅ Le corrigé enseignant est prêt.")

            pdf_correction = generer_pdf_sujet(
                st.session_state.correction_sujet
            )

            st.download_button(
                "📘 Télécharger le corrigé enseignant en PDF",
                data=pdf_correction.getvalue(),
                file_name="corrige_enseignant.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_correction_enseignant"
            )
# ============================================================
# INTERFACE
# ============================================================


        
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

    if "ouvrir_generateur_sujet" not in st.session_state:
        st.session_state.ouvrir_generateur_sujet = False

    # Vérification du cookie
    if not st.session_state.free_question_used and cookie_manager is not None:
        try:
            cookie_val = cookie_manager.get(cookie="free_question_used")
            if cookie_val == "1":
                st.session_state.free_question_used = True
        except Exception:
            pass

    # Présentation
    st.markdown(
        f"<h1 style='text-align: center; color: #1E3A8A;'>{t('hero_title')}</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        f"<p style='text-align: center; font-size: 1.2em; color: #4B5563;'>{t('hero_subtitle')}</p>",
        unsafe_allow_html=True
    )

    st.write("---")

    # Fonction d'affichage de l'offre Premium
    def afficher_offre_premium():

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
            <div style="background-color: #F3F4F6;
            padding: 20px; border-radius: 10px;
            border-left: 5px solid #10B981;
            margin-bottom: 20px;">
                <h4 style="margin: 0; color: #111827;">
                    {t('offer_title')}
                </h4>
                <p style="font-size: 1.8em; font-weight: bold;
                margin: 10px 0; color: #10B981;">
                    {t('offer_price')}
                    <span style="font-size: 0.5em;
                    color: #6B7280; font-weight: normal;">
                        {t('offer_price_sub')}
                    </span>
                </p>
                <ul style="margin-bottom: 0;
                padding-left: 20px; color: #374151;">
                    <li>{t('offer_bullet1')}</li>
                    <li>{t('offer_bullet2')}</li>
                    <li>{t('offer_bullet3')}</li>
                    <li>{t('offer_bullet4')}</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            t("button_pay"),
            use_container_width=True,
            type="primary",
            key="btn_pay"
        ):
            try:
                checkout_session = stripe.checkout.Session.create(
                    line_items=[
                        {'price': ID_PRIX_UNIQUE, 'quantity': 1}
                    ],
                    mode='payment',
                    success_url=f"{URL_APP}?session_id={{CHECKOUT_SESSION_ID}}",
                    cancel_url=URL_APP,
                )

                st.markdown(
                    f"### [{t('button_pay_link')}]({checkout_session.url})"
                )
                st.caption(t("stripe_secure"))

                st.markdown(
                    f"<p style='font-size: 0.8em; color: #9CA3AF; "
                    f"text-align: center; margin-top: 10px;'>"
                    f"{t('legal_notice')}</p>",
                    unsafe_allow_html=True
                )

            except Exception as e:
                st.error(t("stripe_error", error=str(e)))

        st.write("---")
        st.markdown(f"##### {t('testimonials_title')}")
        st.info(t("testimonial_text"))
            # Générateur toujours accessible après vérification de l'email
    if st.session_state.get("email_verifie"):
        afficher_generateur_sujet()

    # Cas A : Une correction est déjà en cours
    if "etape_actuelle" in st.session_state:

        if st.session_state.get("correction_terminee"):
            afficher_recapitulatif_final("correction_gratuite.pdf")

            st.success(t("free_question_used"))
            st.markdown(t("free_question_used_msg"))

            afficher_offre_premium()

        else:
            afficher_coach_interactif(
                st.session_state["dernier_enonce"]
            )

    # Cas B : Question gratuite déjà utilisée
    elif st.session_state.free_question_used:

        st.success(t("free_question_used"))
        st.markdown(t("free_question_used_msg"))

        afficher_offre_premium()

    # Cas C : Première visite, demande d'email
    elif not st.session_state.email_verifie:

        st.info("Veuillez saisir votre adresse e-mail pour continuer.")

        email_saisi = st.text_input(
            t("email_label"),
            key="email_saisi"
        )

        if st.button(
            t("email_continue_btn"),
            type="primary",
            use_container_width=True,
            key="btn_email"
        ):

            email_clean = email_saisi.strip().lower()

            if not email_valide(email_clean):
                st.error(t("email_invalid"))

            elif email_deja_utilise(email_clean):
                st.error(t("email_already_used"))

            else:
                st.session_state.email_verifie = email_clean
                st.session_state.ouvrir_generateur_sujet = False
                st.rerun()

    # Cas D : Email vérifié, accès gratuit
    else:

        st.success(t("email_verified"))


        # Afficher la question gratuite si le générateur est fermé
        if not st.session_state.get("ouvrir_generateur_sujet", False):

            st.markdown(f"#### {t('question_step_title')}")

            st.info(t("free_question_remaining"))
            st.write("---")

            exercice_gratuit = st.text_area(
                t("free_question_label"),
                height=150,
                key="free_question_input"
            )

            if st.button(
                t("free_question_button"),
                type="primary",
                use_container_width=True,
                key="btn_free"
            ):

                if not exercice_gratuit.strip():
                    st.warning(t("warning_empty"))

                else:
                    sauvegarder_email(
                        st.session_state.email_verifie
                    )

                    st.session_state.free_question_used = True

                    if cookie_manager is not None:
                        try:
                            cookie_manager.set(
                                "free_question_used",
                                "1",
                                expires_at=datetime.datetime.now()
                                + datetime.timedelta(days=365)
                            )
                        except Exception:
                            pass

                    initialiser_session_pedago(exercice_gratuit)
                    st.rerun()




      


# Cas 3 : Payé
else:
    st.markdown(
        f"<h1 style='text-align: center; color: #10B981;'>{t('premium_activated')}</h1>",
        unsafe_allow_html=True
    )

    st.success(t("premium_msg", email=email_eleve))

    if "etape_actuelle" not in st.session_state:
        exercice = st.text_area(
            t("textarea_label"),
            height=150,
            key="premium_input"
        )

        if st.button(
            t("button_correct"),
            type="primary",
            use_container_width=True,
            key="btn_correct"
        ):
            if not exercice.strip():
                st.warning(t("warning_empty"))
            else:
                initialiser_session_pedago(exercice)
                st.rerun()

    else:
        if st.session_state.get("correction_terminee"):
            afficher_recapitulatif_final("correction_coach_math.pdf")
        else:
            afficher_coach_interactif(
                st.session_state['dernier_enonce']
            )

