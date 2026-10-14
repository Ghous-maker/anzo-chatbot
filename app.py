import os
import re
import csv
from datetime import datetime
from pathlib import Path

import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="ANZO | AI Business Consultant",
    page_icon="💼",
    layout="centered"
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"], .stApp, .stAppViewContainer, [data-testid="stAppViewContainer"] {
        font-family: Inter, Arial, sans-serif !important;
        color-scheme: light !important;
        color: #100c0a !important;
    }
    .stApp, [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #f2eef2 0%, #efe9ec 28%, #e0dddc 68%, #d5d1cf 100%) !important;
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
        padding: 18px 16px 110px 16px !important;
        max-width: 920px;
    }

    .anzo-top {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 4px 0 8px 2px;
    }
    .anzo-mark {
        width: 34px;
        height: 34px;
        border-radius: 11px;
        background: #100c0a;
        color: #f2eef2;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 15px;
    }
    .anzo-brand {
        color: #100c0a !important;
        font-weight: 700;
        font-size: 15px;
    }
    .anzo-hero { text-align: center; padding: 28px 12px 8px 12px; }
    .anzo-logo {
        width: 56px;
        height: 56px;
        margin: 0 auto 18px auto;
        border-radius: 16px;
        background: #100c0a;
        color: #f2eef2;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        font-weight: 700;
        box-shadow: 0 12px 28px rgba(16, 12, 10, 0.16);
    }
    .anzo-hello {
        margin: 0;
        color: #423630 !important;
        -webkit-text-fill-color: #423630 !important;
        font-size: 28px;
        font-weight: 500;
    }
    .anzo-title {
        margin: 6px 0 0 0;
        color: #100c0a !important;
        -webkit-text-fill-color: #100c0a !important;
        font-size: 34px;
        line-height: 1.2;
        font-weight: 700;
        background: none !important;
    }
    .anzo-sub {
        max-width: 540px;
        margin: 12px auto 22px auto;
        color: #967e71 !important;
        -webkit-text-fill-color: #967e71 !important;
        font-size: 15px;
        line-height: 1.6;
    }
    h1, h2, h3, p, label, span {
        color: #100c0a;
    }

    [data-testid="stChatMessage"] {
        background: rgba(255,255,255,0.92) !important;
        border: 1px solid #e0dddc !important;
        border-radius: 18px !important;
        padding: 10px 12px !important;
        box-shadow: 0 8px 20px rgba(16, 12, 10, 0.05);
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stMarkdownContainer"] p {
        color: #100c0a !important;
        -webkit-text-fill-color: #100c0a !important;
    }

    div[data-testid="stHorizontalBlock"] > div button {
        background: #ffffff !important;
        color: #100c0a !important;
        -webkit-text-fill-color: #100c0a !important;
        border: 1px solid #e0dddc !important;
        border-radius: 20px !important;
        min-height: 158px !important;
        height: 158px !important;
        white-space: pre-wrap !important;
        overflow: hidden !important;
        text-overflow: clip !important;
        text-align: left !important;
        align-items: flex-start !important;
        justify-content: flex-start !important;
        padding: 18px 16px 16px 16px !important;
        box-shadow: 0 10px 28px rgba(16, 12, 10, 0.06) !important;
        font-size: 15px !important;
        line-height: 1.35 !important;
        font-weight: 700 !important;
    }
    div[data-testid="stHorizontalBlock"] > div button::before {
        content: "";
        display: block;
        width: 38px;
        height: 38px;
        border-radius: 12px;
        background-color: #100c0a;
        background-repeat: no-repeat;
        background-position: center;
        background-size: 18px 18px;
        margin-bottom: 14px;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button::before {
        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' fill='none' stroke='%23f2eef2' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M4 14l9-9'/><path d='M8 5h5v5'/></svg>");
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button::before {
        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' fill='none' stroke='%23f2eef2' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M4 9a5 5 0 0 1 8-4'/><path d='M14 9a5 5 0 0 1-8 4'/><path d='M12 3h3v3'/><path d='M6 15H3v-3'/></svg>");
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button::before {
        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' fill='none' stroke='%23f2eef2' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M12 3l3 3-8 8H4v-3l8-8z'/></svg>");
    }
    div[data-testid="stHorizontalBlock"] > div button:hover {
        border-color: #967e71 !important;
        transform: translateY(-2px);
    }

    [data-testid="stExpander"] {
        background: rgba(255,255,255,0.88) !important;
        border: 1px solid #e0dddc !important;
        border-radius: 16px !important;
    }
    .stTextInput label, .stTextArea label, [data-testid="stExpander"] p, [data-testid="stExpander"] span {
        color: #423630 !important;
        -webkit-text-fill-color: #423630 !important;
    }
    .stTextInput input, .stTextArea textarea {
        background: #f2eef2 !important;
        color: #100c0a !important;
        border: 1px solid #b0b7c1 !important;
        border-radius: 12px !important;
    }

    .stFormSubmitButton button {
        background: linear-gradient(135deg, #423630 0%, #967e71 100%) !important;
        color: #f2eef2 !important;
        border: 0 !important;
        border-radius: 999px !important;
        font-weight: 700 !important;
    }

    [data-testid="stBottom"],
    [data-testid="stBottomBlockContainer"],
    .stChatFloatingInputContainer {
        background: transparent !important;
        background-color: transparent !important;
        border: 0 !important;
        box-shadow: none !important;
    }
    [data-testid="stChatInput"] {
        background: transparent !important;
        padding-bottom: 18px !important;
    }
    [data-testid="stChatInput"] textarea {
        background: #ffffff !important;
        color: #100c0a !important;
        -webkit-text-fill-color: #100c0a !important;
        border: 1px solid #e0dddc !important;
        border-radius: 999px !important;
        caret-color: #100c0a !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #967e71 !important;
        -webkit-text-fill-color: #967e71 !important;
        opacity: 1 !important;
    }
    [data-testid="stChatInput"] button {
        background: linear-gradient(135deg, #967e71 0%, #423630 100%) !important;
        color: #f2eef2 !important;
        border: 0 !important;
        border-radius: 999px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

PRIMARY_MODEL = "openai/gpt-oss-20b"
FALLBACK_MODELS = [
    PRIMARY_MODEL,
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
]
LEADS_FILE = Path("anzo_leads.csv")

SYSTEM_PROMPT = """
You are ANZO's AI business consultant.

ANZO is an AI automation and software agency. Understand the visitor's
business problem first, then recommend a suitable ANZO solution, then
qualify serious prospects.

You are NOT a FAQ bot, service menu, or the visitor.

IDENTITY LOCK:
- Always speak as ANZO's consultant.
- Never speak as the visitor.
- Never invent the visitor's lead volume, tools, budget, process, or results.
- If the visitor did not say a fact, do not pretend it exists.

ANZO capabilities, not a fixed menu:
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
4. Recommend a connected ANZO solution.
5. Ask exactly one next question.

RESPONSE SHAPE:
- Sentence 1: Restate the visitor's problem. Do not add new facts.
- Sentence 2: Recommend the ANZO solution and what it would do.
- Sentence 3: Business benefit without fake percentages, case studies, or guarantees.
- Sentence 4: Exactly one short question.

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

PRICING / TIMELINE:
- Never invent a price or deadline.
- Say ANZO confirms cost and timeline after reviewing scope.

GOOD EXAMPLE
Visitor: Meri real estate agency hai. Website aur WhatsApp se leads aati hain, lekin meri team late reply karti hai aur kai leads miss ho jati hain.
You: Aapki asl problem yeh hai ke website aur WhatsApp ki leads ka jawab late milta hai, is liye potential clients nikal jate hain. ANZO iske liye WhatsApp aur website ka connected AI lead agent bana sakta hai jo turant jawab de, zaroori details le, qualify kare, aur serious leads aapki team tak bheje. Is se missed follow-ups kam ho sakte hain aur team ko sirf ready conversations milengi. Abhi yeh leads aap kahan save karte hain?
"""

SUGGESTIONS = [
    (
        "Missed leads",
        "Late WhatsApp replies",
        "Website and WhatsApp leads come in, but my team replies late and we miss customers.",
    ),
    (
        "Repetitive work",
        "Too much manual follow-up",
        "My team spends too much time on repetitive manual work and follow-ups.",
    ),
    (
        "Custom system",
        "Website, app or dashboard",
        "I need a custom website, dashboard, or software for my business, but I am not sure what to build first.",
    ),
]

ROMAN_MARKERS = {
    "hai", "hain", "kya", "kyun", "mujhe", "mera", "meri", "mere", "aap",
    "aapki", "apki", "hum", "hamari", "lekin", "magar", "nahi", "nahin",
    "chahiye", "karna", "karte", "karti", "hota", "hoti", "wala", "wali",
    "yeh", "ye", "woh", "wo", "abhi", "kitna", "kitni", "kaise", "kaisa",
    "batao", "bataen", "team", "se", "ko", "ka", "ki", "ke", "mein", "main",
    "aur", "ya", "liye", "baad", "pehle", "process", "leads", "lead"
}

ROLE_LEAK = re.compile(
    r"^\s*(mujhe|hamari agency|meri agency|mujh ko)\b",
    re.IGNORECASE
)


def get_api_key() -> str:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if key:
        return key
    try:
        return str(st.secrets.get("GROQ_API_KEY", "")).strip()
    except Exception:
        return ""


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
            "You are ANZO's consultant, not the visitor. "
            "Ask exactly one short question."
        )
    if lang == "urdu":
        return (
            "The visitor wrote in Urdu. Reply in simple Urdu. "
            "You are ANZO's consultant, not the visitor. "
            "Ask exactly one short question."
        )
    return (
        "The visitor wrote in English. Reply in clear English. "
        "You are ANZO's consultant, not the visitor. "
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
    marks = [i for i, ch in enumerate(text) if ch in "??"]
    if not marks:
        return text
    return text[: marks[0] + 1].strip()


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
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=650,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as error:
            last_error = error
            err = str(error).lower()
            if "model" in err or "404" in err or "not found" in err:
                continue
            raise
    raise RuntimeError(str(last_error) if last_error else "No model available")


def polish_reply(client: OpenAI, text: str, lang: str, user_message: str) -> str:
    needs_language_fix = lang == "roman_urdu" and not looks_like_roman_urdu(text)
    needs_role_fix = bool(ROLE_LEAK.search(text or ""))
    if not needs_language_fix and not needs_role_fix:
        return text
    instructions = [
        "Rewrite this ANZO consultant reply.",
        "Keep the same meaning. Do not add prices, timelines, results, or new facts.",
        "Speak as ANZO's consultant, never as the client.",
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


def conversation_text(messages: list) -> str:
    lines = []
    for item in messages:
        role = "Client" if item["role"] == "user" else "ANZO"
        lines.append(f"{role}: {item['content']}")
    return "\n".join(lines)


def queue_suggestion(text: str) -> None:
    st.session_state.queued = text


if "messages" not in st.session_state:
    st.session_state.messages = []
if "queued" not in st.session_state:
    st.session_state.queued = None

show_landing = not any(m["role"] == "user" for m in st.session_state.messages)

st.markdown(
    """
    <div class="anzo-top">
      <div class="anzo-mark">A</div>
      <div class="anzo-brand">ANZO</div>
    </div>
    """,
    unsafe_allow_html=True
)

if show_landing:
    st.markdown(
        """
        <div class="anzo-hero">
          <div class="anzo-logo">A</div>
          <p class="anzo-hello">Hi, welcome to ANZO</p>
          <p class="anzo-title">Can I help you with anything?</p>
          <p class="anzo-sub">Ready to help you fix missed leads, repetitive work, or build the right system. Let's get started.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    cols = st.columns(3, gap="medium")
    for col, (title, subtitle, prompt) in zip(cols, SUGGESTIONS):
        with col:
            st.button(
                f"{title}\n{subtitle}",
                use_container_width=True,
                on_click=queue_suggestion,
                args=(prompt,),
            )
else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

user_message = st.chat_input("Ask ANZO anything...")
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
        reply = enforce_one_question(reply)
        if not reply or ROLE_LEAK.search(reply):
            reply = (
                "Aapki asl problem late replies ki wajah se leads miss hona lagti hai. "
                "Abhi website aur WhatsApp ki leads aap kahan save karte hain?"
            )
    except Exception:
        reply = (
            "Sorry, I cannot reply right now. Please try again in a moment "
            "or contact the ANZO team directly."
        )
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

if not show_landing:
    with st.expander("Contact ANZO team", expanded=False):
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
            submitted = st.form_submit_button("Send to ANZO")
            if submitted:
                if not (name or email or phone):
                    st.warning("Please enter a name, email, or phone number.")
                else:
                    save_lead(
                        {
                            "timestamp": datetime.now().isoformat(timespec="seconds"),
                            "name": name.strip(),
                            "company": company.strip(),
                            "email": email.strip(),
                            "phone": phone.strip(),
                            "problem": problem.strip(),
                            "notes": conversation_text(st.session_state.messages),
                        }
                    )
                    st.success("Thanks. Your details have been saved.")
