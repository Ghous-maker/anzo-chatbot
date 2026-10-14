import os
import re
import csv
import smtplib
from email.message import EmailMessage
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="ANG | AI Business Consultant",
    page_icon="💬",
    layout="centered"
)

# ---------------------------------------------------------------------------
# THEME  (palette: #fefefe #f4eff7 #f3e5ec #d6cdd1 #b2a3a4 #565656
#         + charcoal #404040 for icons, coral #e8957f for the Send button)
# ---------------------------------------------------------------------------


def svg_uri(inner: str) -> str:
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
        'viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round">' + inner + "</svg>"
    )
    return "data:image/svg+xml;utf8," + quote(svg)


# Card icons (white line icons on charcoal squares)
ICON_LEADS = svg_uri('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>')
ICON_AUTOMATION = svg_uri('<path d="M21 12a9 9 0 0 0-15-6.7L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 15 6.7L21 16"/><path d="M16 16h5v5"/>')
ICON_SYSTEM = svg_uri('<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>')
ICON_SEND = svg_uri('<path d="M7 17 17 7"/><path d="M8 7h9v9"/>')

LOGO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24" '
    'fill="none" stroke="#fefefe" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'
    '<path d="M9 9.5h6"/><path d="M9 12.5h3.5"/></svg>'
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --c-white: #fefefe;
    --c-lavender: #f4eff7;
    --c-pink: #f3e5ec;
    --c-line: #d6cdd1;
    --c-muted: #b2a3a4;
    --c-text: #565656;
    --c-dark: #404040;
    --c-ink: #2f2c2e;
    --c-coral: #e8957f;
    --c-coral-2: #f0a894;
}

html, body, [class*="css"], .stApp {
    font-family: Inter, Arial, sans-serif;
    color-scheme: light !important;
}

.stApp {
    background:
        radial-gradient(900px 650px at 8% 0%, #ebe8fa 0%, rgba(235,232,250,0) 62%),
        radial-gradient(900px 650px at 95% 25%, #f9e6ed 0%, rgba(249,230,237,0) 62%),
        radial-gradient(800px 520px at 0% 100%, #f4e6e1 0%, rgba(244,230,225,0) 62%),
        radial-gradient(800px 520px at 100% 100%, #efe0f4 0%, rgba(239,224,244,0) 62%),
        #f4eff7 !important;
}

#MainMenu, footer, header { visibility: hidden !important; }
.stDeployButton, .stAppDeployButton { display: none !important; }
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stHeader"],
[data-testid="stToolbarActions"],
[data-testid="stAppToolbar"],
[data-testid="manage-app-button"] { display: none !important; }
.stApp > header { display: none !important; }

.block-container {
    padding: 1.4rem 1rem 7.5rem 1rem !important;
    max-width: 900px;
}

/* ---------- Shell (the page container itself is the card) ---------- */
.block-container {
    background: linear-gradient(160deg, rgba(244,239,247,0.80), rgba(243,229,236,0.70)) !important;
    border: 1px solid rgba(214, 205, 209, 0.85);
    border-radius: 34px;
    box-shadow: 0 20px 50px rgba(86, 86, 86, 0.07);
    margin: 1.2rem auto 7rem auto !important;
    padding: 1.4rem 1.6rem 1.8rem 1.6rem !important;
}
.ang-top {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 26px;
}
.ang-mark {
    width: 38px;
    height: 38px;
    border-radius: 12px;
    background: var(--c-dark);
    color: var(--c-white);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 16px;
}
.ang-brand {
    color: var(--c-dark);
    font-weight: 500;
    font-size: 17px;
}

/* ---------- Hero ---------- */
.ang-hero {
    text-align: center;
    width: 100%;
    padding: 10px 10px 0 10px;
}
.ang-logo {
    width: 76px;
    height: 76px;
    margin: 0 auto 22px auto;
    border-radius: 22px;
    background: linear-gradient(145deg, #4d4d4d, #343434);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 14px 30px rgba(64, 64, 64, 0.25), inset 0 1px 0 rgba(255,255,255,0.15);
}
div.ang-hello {
    margin: 0;
    color: #b2a3a4 !important;
    font-size: 30px !important;
    font-weight: 600 !important;
    line-height: 1.25 !important;
}
div.ang-title {
    margin: 2px 0 0 0;
    color: #565656 !important;
    font-size: 38px !important;
    font-weight: 700 !important;
    line-height: 1.15 !important;
    letter-spacing: -0.5px;
}
div.ang-sub {
    max-width: 480px;
    margin: 14px auto 0 auto;
    color: #8f8588 !important;
    font-size: 15px !important;
    line-height: 1.6 !important;
}

/* ---------- Suggestion cards ---------- */
div[data-testid="stHorizontalBlock"] button {
    background: rgba(254, 254, 254, 0.88) !important;
    color: var(--c-ink) !important;
    border: 1px solid rgba(255, 255, 255, 0.95) !important;
    border-radius: 22px !important;
    min-height: 175px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    justify-content: flex-start !important;
    text-align: left !important;
    padding: 18px !important;
    box-shadow: 0 10px 28px rgba(86, 86, 86, 0.08) !important;
    transition: transform .15s ease, box-shadow .15s ease;
}
div[data-testid="stHorizontalBlock"] button::before {
    content: "";
    display: block;
    order: 0;
    width: 48px;
    height: 48px;
    border-radius: 14px;
    background-color: var(--c-dark);
    background-position: center;
    background-repeat: no-repeat;
    background-size: 24px;
    margin-bottom: 18px;
    flex-shrink: 0;
}
div[data-testid="stHorizontalBlock"] button > div,
div[data-testid="stHorizontalBlock"] button [data-testid="stMarkdownContainer"] {
    order: 1;
    display: block !important;
    width: 100% !important;
    text-align: left !important;
}
div[data-testid="stHorizontalBlock"] button p {
    display: block !important;
    margin: 0 !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
    text-align: left !important;
    color: var(--c-ink) !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    line-height: 1.35 !important;
}
div[data-testid="stHorizontalBlock"] button::after {
    order: 2;
    display: block;
    margin-top: 6px;
    color: #8f8588;
    font-size: 12.5px;
    font-weight: 400;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(1) button::before { background-image: url("__ICON_LEADS__"); }
div[data-testid="stHorizontalBlock"] > div:nth-child(2) button::before { background-image: url("__ICON_AUTOMATION__"); }
div[data-testid="stHorizontalBlock"] > div:nth-child(3) button::before { background-image: url("__ICON_SYSTEM__"); }
div[data-testid="stHorizontalBlock"] > div:nth-child(1) button::after { content: "WhatsApp & website inquiries"; }
div[data-testid="stHorizontalBlock"] > div:nth-child(2) button::after { content: "Automation & follow-ups"; }
div[data-testid="stHorizontalBlock"] > div:nth-child(3) button::after { content: "Dashboards, apps & systems"; }
div[data-testid="stHorizontalBlock"] button:hover {
    transform: translateY(-2px);
    box-shadow: 0 16px 34px rgba(86, 86, 86, 0.13) !important;
    border-color: var(--c-line) !important;
}

/* ---------- Chat messages ---------- */
[data-testid="stChatMessage"] {
    background: rgba(254, 254, 254, 0.88) !important;
    border: 1px solid rgba(214, 205, 209, 0.7);
    border-radius: 20px;
    padding: 12px 14px !important;
    margin: 10px 0 !important;
    box-shadow: 0 8px 22px rgba(86, 86, 86, 0.06);
}
[data-testid="stChatMessage"] p,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {
    color: var(--c-ink) !important;
    line-height: 1.6;
}
[data-testid="stChatMessageAvatarAssistant"],
[data-testid="stChatMessageAvatarUser"] {
    background: var(--c-dark) !important;
    color: var(--c-white) !important;
    border-radius: 12px !important;
}

/* ---------- Contact expander + form ---------- */
[data-testid="stExpander"] {
    background: rgba(254, 254, 254, 0.8) !important;
    border: 1px solid rgba(214, 205, 209, 0.8) !important;
    border-radius: 18px !important;
}
.stTextInput label, .stTextArea label,
[data-testid="stExpander"] p, [data-testid="stExpander"] span {
    color: var(--c-text) !important;
}
.stTextInput input, .stTextArea textarea {
    background: var(--c-lavender) !important;
    color: var(--c-ink) !important;
    border: 1px solid var(--c-line) !important;
    border-radius: 14px !important;
}

/* ---------- Buttons (form) ---------- */
.stButton > button,
.stFormSubmitButton button {
    background: linear-gradient(135deg, var(--c-coral) 0%, var(--c-coral-2) 100%) !important;
    color: var(--c-white) !important;
    border: 0 !important;
    border-radius: 999px !important;
    font-weight: 600 !important;
    padding: 0.55rem 1.3rem !important;
    box-shadow: 0 8px 18px rgba(232, 149, 127, 0.35) !important;
}

/* ---------- Chat input (pill + coral send) ---------- */
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] {
    background: transparent !important;
}
[data-testid="stChatInput"] {
    background: rgba(254, 254, 254, 0.9) !important;
    border: 1px solid rgba(255, 255, 255, 0.95) !important;
    border-radius: 999px !important;
    box-shadow: 0 10px 28px rgba(86, 86, 86, 0.10) !important;
    padding: 4px !important;
}
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] div[data-baseweb="textarea"],
[data-testid="stChatInput"] div[data-baseweb="base-input"] {
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: var(--c-ink) !important;
    border: 0 !important;
    padding-left: 18px !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--c-muted) !important; }
[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, var(--c-coral), var(--c-coral-2)) !important;
    color: var(--c-white) !important;
    border: 0 !important;
    border-radius: 999px !important;
    box-shadow: 0 6px 14px rgba(232, 149, 127, 0.4) !important;
}
[data-testid="stChatInput"] button svg { fill: var(--c-white) !important; color: var(--c-white) !important; }
</style>
"""

CSS = (
    CSS.replace("__ICON_LEADS__", ICON_LEADS)
    .replace("__ICON_AUTOMATION__", ICON_AUTOMATION)
    .replace("__ICON_SYSTEM__", ICON_SYSTEM)
)
st.markdown(CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

PRIMARY_MODEL = "openai/gpt-oss-20b"
FALLBACK_MODELS = [
    PRIMARY_MODEL,
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]
LEADS_FILE = Path("ang_leads.csv")

SYSTEM_PROMPT = """
You are ANG's AI business consultant.

ANG is an AI automation and software agency. Understand the visitor's
business problem first, then recommend a suitable ANG solution, then
qualify serious prospects.

You are NOT a FAQ bot, service menu, or the visitor.

IDENTITY LOCK:
- Always speak as ANG's consultant.
- Never speak as the visitor.
- Never invent the visitor's lead volume, tools, budget, process, or results.
- If the visitor did not say a fact, do not pretend it exists.

ANG capabilities, not a fixed menu:
- AI chatbots and AI agents
- AI voice / call agents
- Customer support, sales, and lead qualification agents
- WhatsApp AI and automation
- Business process automation
- Lead management and automated follow-ups
- Email, CRM, Google Sheets, data, reporting, and notification automation
- Website development
- Web applications, dashboards, portals, and custom software
- Mobile apps for Android and iOS

CONSULTING METHOD:
1. Understand the goal.
2. Identify the real problem.
3. Ask about the current process only if still unknown.
4. Recommend a connected ANG solution.
5. Ask exactly one next question.

RESPONSE SHAPE:
- First reply to a new problem: 4 short sentences.
  Sentence 1 restates the visitor's problem without adding facts.
  Sentence 2 recommends the ANG solution and what it would do.
  Sentence 3 gives the business benefit without fake percentages, case studies, or guarantees.
  Sentence 4 is exactly one short question.
- Later replies: 2 to 3 short sentences, answer what the visitor said, then exactly one question.

LANGUAGE:
- Match the visitor's latest message.
- Roman Urdu / Hinglish in, Roman Urdu / Hinglish out.
- English in, English out.
- Keep product names in English: WhatsApp, CRM, Excel, Google Sheets.

QUESTION RULE:
- Ask exactly one question.
- Ask for only one piece of information.
- Never join two requests with and, or, aur, ya, or a comma list.
- Never use more than one question mark.

QUALIFICATION AND NEXT STEP:
- After the problem and goal are clear, learn one thing at a time: business type, current tools or process, what they want built, timeline.
- Never ask for the same information twice. Use what the visitor already said.
- If the visitor asks about price, timeline, how to start, or shows clear interest, or after about 3 exchanges, tell them they can share their name and WhatsApp or email in the "Contact ANG team" section below the chat so the ANG team can review and follow up. Then end with exactly one question such as whether they would like the ANG team to contact them.
- Never promise results, pricing, timelines, or capabilities that were not confirmed.

NO INVENTED PROOF:
- Never say ANG has helped, built, delivered, or worked with any client, clinic, agency, industry, or project. ANG has no confirmed case studies or results you can mention.
- If asked for case studies, portfolio, past work, or clients, say you cannot share confirmed examples in this chat and the ANG team can discuss relevant work.
- Describe solutions as what ANG can design, never as guaranteed features. Details are confirmed after the ANG team reviews requirements.
- For clinics and healthcare: talk about answering inquiries, appointment requests, and reminders. Never promise collecting, storing, or handling medical or health information.

PRICING / TIMELINE:
- Never invent a price or deadline.
- Say ANG confirms cost and timeline after reviewing scope.

GOOD EXAMPLE
Visitor: Meri real estate agency hai. Website aur WhatsApp se leads aati hain, lekin meri team late reply karti hai aur kai leads miss ho jati hain.
You: Aapki asl problem yeh hai ke website aur WhatsApp ki leads ka jawab late milta hai, is liye potential clients nikal jate hain. ANG iske liye WhatsApp aur website ka connected AI lead agent bana sakta hai jo turant jawab de, zaroori details le, qualify kare, aur serious leads aapki team tak bheje. Is se missed follow-ups kam ho sakte hain aur team ko sirf ready conversations milengi. Abhi yeh leads aap kahan save karte hain?
"""

WELCOME_MESSAGE = (
    "I'm ANG's AI business consultant. Tell me what you want to build, "
    "automate, or improve in your business — or where your team is losing "
    "time or missing leads."
)

# (card title, small subtitle, message sent to the bot)
SUGGESTIONS = [
    (
        "Missed leads & late replies",
        "WhatsApp & website inquiries",
        "Website and WhatsApp leads come in, but my team replies late and we miss customers.",
    ),
    (
        "Repetitive manual work",
        "Automation & follow-ups",
        "My team spends too much time on repetitive manual work and follow-ups.",
    ),
    (
        "Custom website or software",
        "Dashboards, apps & systems",
        "I need a custom website, dashboard, or software for my business, but I am not sure what to build first.",
    ),
]

ROMAN_MARKERS = {
    "hai", "hain", "kya", "kyun", "mujhe", "mera", "meri", "mere", "aap",
    "aapki", "apki", "hum", "hamari", "lekin", "magar", "nahi", "nahin",
    "chahiye", "karna", "karte", "karti", "hota", "hoti", "wala", "wali",
    "yeh", "ye", "woh", "wo", "abhi", "kitna", "kitni", "kaise", "kaisa",
    "batao", "bataen", "se", "ko", "ka", "ki", "ke", "mein",
    "aur", "ya", "liye", "baad", "pehle",
}

ROLE_LEAK = re.compile(
    r"^\s*(mujhe|hamari agency|meri agency|mujh ko)\b",
    re.IGNORECASE
)


def get_secret(name: str, default: str = "") -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        return str(st.secrets.get(name, default)).strip()
    except Exception:
        return default


GENERIC_QUESTION = {
    "english": "Could you tell me a bit more about the main problem you want to solve in your business?",
    "roman_urdu": "Aap apne business ka woh main masla bata sakte hain jo aap hal karna chahte hain?",
    "urdu": "کیا آپ اپنے کاروبار کا وہ بنیادی مسئلہ بتا سکتے ہیں جسے آپ حل کرنا چاہتے ہیں؟",
}
ERROR_MESSAGE = {
    "english": "Sorry, I cannot reply right now. Please try again in a moment or use the Contact ANG team section below.",
    "roman_urdu": "Maaf kijiye, abhi jawab nahi de sakta. Thori der baad try karein ya neeche Contact ANG team section use karein.",
    "urdu": "معذرت، ابھی جواب نہیں دے سکتا۔ تھوڑی دیر بعد کوشش کریں یا نیچے Contact ANG team استعمال کریں۔",
}


def get_api_key() -> str:
    return get_secret("GROQ_API_KEY")


def detect_language(text: str) -> str:
    if re.search(r"[\u0600-\u06FF]", text or ""):
        return "urdu"
    words = re.findall(r"[A-Za-z]+", (text or "").lower())
    if not words:
        return "english"
    hits = sum(1 for w in words if w in ROMAN_MARKERS)
    if hits >= 2 or hits / max(len(words), 1) >= 0.18:
        return "roman_urdu"
    return "english"


def language_instruction(lang: str) -> str:
    if lang == "roman_urdu":
        return (
            "The visitor wrote in Roman Urdu / Hinglish. "
            "Reply in simple Roman Urdu / Hinglish. "
            "You are ANG's consultant, not the visitor. "
            "Ask exactly one short question."
        )
    if lang == "urdu":
        return (
            "The visitor wrote in Urdu. Reply in simple Urdu. "
            "You are ANG's consultant, not the visitor. "
            "Ask exactly one short question."
        )
    return (
        "The visitor wrote in English. Reply in clear English. "
        "You are ANG's consultant, not the visitor. "
        "Ask exactly one short question."
    )


def looks_like_roman_urdu(text: str) -> bool:
    words = re.findall(r"[A-Za-z]+", (text or "").lower())
    if not words:
        return False
    hits = sum(1 for w in words if w in ROMAN_MARKERS)
    return hits >= 2


def enforce_one_question(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return text
    sentences = [x for x in re.split(r"(?<=[.!?؟])\s+", text) if x]
    questions = [x for x in sentences if x.rstrip().endswith(("?", "؟"))]
    if len(questions) <= 1:
        return text
    statements = [x for x in sentences if x not in questions]
    return " ".join(statements + [questions[-1]]).strip()


CLAIM_RE = re.compile(
    r"\b(we\W?ve|we have|we helped|ang has|ang have|our clients?|our customers?|"
    r"previous clients?|past clients?|hum ne|humne|hamare clients?|hamare customers?|"
    r"ang ne)\b[^.!?؟]{0,60}\b(help|helped|built|build|delivered|worked|done|improv|"
    r"increase|reduc|kiya|kiye|banaya|banaye|madad)",
    re.IGNORECASE,
)

PROOF_RE = re.compile(
    r"case stud|portfolio|past work|previous work|past project|previous project|"
    r"your clients|any client|examples? of|testimonial|success stor|"
    r"pichle (kaam|project|client)|purane (kaam|project|client)|"
    r"koi example|kaam dikha",
    re.IGNORECASE,
)

INTENT_RE = re.compile(
    r"\b(price|pricing|cost|quote|budget|charges?|fees?|timeline|how long|deadline|"
    r"start|hire|meeting|call me|contact|kitna|kitne|qeemat|keemat|rate|kab tak|kab)\b",
    re.IGNORECASE,
)

PROOF_REPLY = {
    "english": "I can't share confirmed case studies or past results in this chat, but the ANG team can discuss relevant work with you directly.",
    "roman_urdu": "Main is chat mein confirmed case studies ya pichle results share nahi kar sakta, lekin ANG team aap se relevant kaam ke baare mein direct baat kar sakti hai.",
    "urdu": "میں اس چیٹ میں تصدیق شدہ کیس اسٹڈیز یا پچھلے نتائج شیئر نہیں کر سکتا، لیکن ANG ٹیم آپ سے متعلقہ کام کے بارے میں براہ راست بات کر سکتی ہے۔",
}

NUDGE = {
    "english": "You can share your name and WhatsApp or email in the Contact ANG team section below, and the team will follow up.",
    "roman_urdu": "Aap neeche Contact ANG team section mein apna naam aur WhatsApp ya email share kar dein, ANG team follow up karegi.",
    "urdu": "آپ نیچے Contact ANG team سیکشن میں اپنا نام اور WhatsApp یا ای میل شیئر کر دیں، ANG ٹیم رابطہ کرے گی۔",
}


def split_sentences(text: str) -> list:
    return [x for x in re.split(r"(?<=[.!?؟])\s+", (text or "").strip()) if x]


def strip_unconfirmed_claims(text: str) -> str:
    kept = [x for x in split_sentences(text) if not CLAIM_RE.search(x)]
    return " ".join(kept).strip()


def add_nudge(text: str, lang: str) -> str:
    line = NUDGE[lang]
    if "contact ang" in text.lower():
        return text
    sentences = split_sentences(text)
    if sentences and sentences[-1].rstrip().endswith(("?", "؟")):
        return " ".join(sentences[:-1] + [line, sentences[-1]]).strip()
    return (text + " " + line).strip()


def get_client(api_key: str) -> OpenAI:
    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )


def call_model(client: OpenAI, messages: list, temperature: float = 0.2) -> str:
    last_error = None
    tried = []
    for model in FALLBACK_MODELS:
        if not model or model in tried:
            continue
        tried.append(model)
        kwargs = dict(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=1200,
        )
        try:
            if "gpt-oss" in model:
                try:
                    response = client.chat.completions.create(
                        extra_body={"reasoning_effort": "low"}, **kwargs
                    )
                except Exception:
                    response = client.chat.completions.create(**kwargs)
            else:
                response = client.chat.completions.create(**kwargs)
            text = (response.choices[0].message.content or "").strip()
            if text:
                return text
            continue
        except Exception as error:
            last_error = error
            continue
    raise RuntimeError(str(last_error) if last_error else "No model available")


def polish_reply(client: OpenAI, text: str, lang: str, user_message: str) -> str:
    needs_language_fix = lang == "roman_urdu" and not looks_like_roman_urdu(text)
    needs_role_fix = bool(ROLE_LEAK.search(text or ""))
    if not needs_language_fix and not needs_role_fix:
        return text
    instructions = [
        "Rewrite this ANG consultant reply.",
        "Keep the same meaning. Do not add prices, timelines, results, or new facts.",
        "Speak as ANG's consultant, never as the client.",
        "Keep exactly one question.",
        f"Visitor message: {user_message}",
    ]
    if lang == "roman_urdu":
        instructions.append("Write in simple Roman Urdu / Hinglish.")
    elif lang == "urdu":
        instructions.append("Write in simple Urdu.")
    else:
        instructions.append("Write in clear English.")
    messages = [
        {"role": "system", "content": " ".join(instructions)},
        {"role": "user", "content": text},
    ]
    rewritten = call_model(client, messages, temperature=0.1)
    return rewritten or text


def save_lead(data: dict) -> None:
    is_new = not LEADS_FILE.exists()
    fieldnames = ["timestamp", "name", "company", "email", "phone", "problem", "notes"]
    with LEADS_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if is_new:
            writer.writeheader()
        writer.writerow(data)


def notify_team(data: dict) -> bool:
    """Email the ANG team when a new lead arrives. Returns True if sent."""
    host = get_secret("SMTP_HOST", "smtp.gmail.com")
    port = int(get_secret("SMTP_PORT", "587") or 587)
    user = get_secret("SMTP_USER")
    password = get_secret("SMTP_PASSWORD")
    to_email = get_secret("NOTIFY_EMAIL") or user
    if not (user and password and to_email):
        return False

    msg = EmailMessage()
    msg["Subject"] = f"New ANG lead: {data.get('name') or data.get('company') or 'Website visitor'}"
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(
        "A new lead was submitted through the ANG chatbot.\n\n"
        f"Time: {data.get('timestamp')}\n"
        f"Name: {data.get('name')}\n"
        f"Company: {data.get('company')}\n"
        f"Email: {data.get('email')}\n"
        f"Phone / WhatsApp: {data.get('phone')}\n"
        f"Main problem: {data.get('problem')}\n\n"
        "----- Conversation -----\n"
        f"{data.get('notes')}\n"
    )
    with smtplib.SMTP(host, port, timeout=20) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)
    return True


def conversation_text(messages: list) -> str:
    lines = []
    for item in messages:
        role = "Client" if item["role"] == "user" else "ANG"
        lines.append(f"{role}: {item['content']}")
    return "\n".join(lines)


def queue_suggestion(text: str) -> None:
    st.session_state.queued = text


# ---------------------------------------------------------------------------
# STATE + UI
# ---------------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": WELCOME_MESSAGE}
    ]
if "queued" not in st.session_state:
    st.session_state.queued = None

user_only = [m for m in st.session_state.messages if m["role"] == "user"]
show_landing = len(user_only) == 0

st.markdown(
    '<div class="ang-top"><div class="ang-mark">A</div><div class="ang-brand">ANG</div></div>',
    unsafe_allow_html=True,
)

if show_landing:
    hero_html = (
        '<div class="ang-hero">'
        f'<div class="ang-logo">{LOGO_SVG}</div>'
        '<div class="ang-hello">Hi, welcome to ANG</div>'
        '<div class="ang-title">Can I help you with anything?</div>'
        '<div class="ang-sub">Tell us the business problem. We will help you find the right system to fix it.</div>'
        '</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)
    st.markdown("<div style='height:34px'></div>", unsafe_allow_html=True)
    cols = st.columns(3)
    for i, (col, (title, subtitle, prompt)) in enumerate(zip(cols, SUGGESTIONS)):
        with col:
            st.button(
                title,
                use_container_width=True,
                on_click=queue_suggestion,
                args=(prompt,),
                key=f"sugg_{i}",
            )
else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

user_message = st.chat_input("Ask ANG anything...")
if st.session_state.queued:
    user_message = st.session_state.queued
    st.session_state.queued = None

api_key = get_api_key()

if user_message:
    st.session_state.messages.append({"role": "user", "content": user_message})

    lang = detect_language(user_message)
    api_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": language_instruction(lang)},
    ] + st.session_state.messages

    try:
        if not api_key:
            raise RuntimeError("missing key")
        client = get_client(api_key)
        reply = call_model(client, api_messages)
        reply = polish_reply(client, reply, lang, user_message)
        reply = strip_unconfirmed_claims(reply)
        reply = enforce_one_question(reply)
        if not reply or ROLE_LEAK.search(reply):
            reply = GENERIC_QUESTION[lang]
        if PROOF_RE.search(user_message):
            # Never let the model improvise proof: use a fixed honest answer.
            reply = PROOF_REPLY[lang] + " " + GENERIC_QUESTION[lang]
        user_count = len([m for m in st.session_state.messages if m["role"] == "user"])
        wants_contact = bool(INTENT_RE.search(user_message))
        first_time_nudge = user_count >= 3 and not st.session_state.get("nudged")
        if wants_contact or first_time_nudge or PROOF_RE.search(user_message):
            reply = add_nudge(reply, lang)
            st.session_state.nudged = True
    except Exception:
        reply = ERROR_MESSAGE[lang]

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

if not show_landing:
    with st.expander("Contact ANG team", expanded=len(user_only) >= 3):
        st.caption("Optional. Share your details when you are ready.")
        with st.form("lead_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Name")
                email = st.text_input("Email")
            with col2:
                company = st.text_input("Company")
                phone = st.text_input("Phone / WhatsApp")
            problem = st.text_area("Main problem", height=70)
            submitted = st.form_submit_button("Send to ANG")
            if submitted:
                if not (name or email or phone):
                    st.warning("Please enter a name, email, or phone number.")
                else:
                    lead = {
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "name": name.strip(),
                        "company": company.strip(),
                        "email": email.strip(),
                        "phone": phone.strip(),
                        "problem": problem.strip(),
                        "notes": conversation_text(st.session_state.messages),
                    }
                    try:
                        save_lead(lead)
                    except Exception:
                        pass
                    try:
                        sent = notify_team(lead)
                    except Exception:
                        sent = False
                    if sent:
                        st.success("Thanks. Your details have been sent to the ANG team.")
                    else:
                        st.warning(
                            "Your details were noted, but we could not notify the team "
                            "automatically. Please contact ANG directly."
                        )
