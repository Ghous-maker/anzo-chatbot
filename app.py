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

    html, body, .stApp, [data-testid="stAppViewContainer"] {
        font-family: Inter, Arial, sans-serif !important;
        color: #100c0a !important;
        color-scheme: light !important;
    }
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background: linear-gradient(180deg, #f2eef2 0%, #eee9ea 35%, #e0dddc 70%, #d8d3d0 100%) !important;
    }
    #MainMenu, footer, header, .stDeployButton, .stAppDeployButton { display: none !important; }
    [data-testid="stToolbar"],
    [data-testid="stHeader"],
    [data-testid="stDecoration"],
    [data-testid="stToolbarActions"],
    [data-testid="stAppToolbar"],
    [data-testid="manage-app-button"] { display: none !important; }
    .block-container { padding: 18px 16px 28px 16px !important; max-width: 900px; }

    .anzo-top { display:flex; align-items:center; gap:10px; margin: 2px 0 8px 2px; }
    .anzo-mark {
        width:34px; height:34px; border-radius:11px; background:#100c0a; color:#f2eef2;
        display:flex; align-items:center; justify-content:center; font-weight:700;
    }
    .anzo-brand { font-weight:700; color:#100c0a !important; }
    .anzo-hero { text-align:center; padding: 34px 10px 10px 10px; }
    .anzo-logo {
        width:56px; height:56px; margin:0 auto 18px auto; border-radius:16px;
        background:#100c0a; color:#f2eef2; display:flex; align-items:center; justify-content:center;
        font-size:22px; font-weight:700; box-shadow:0 12px 28px rgba(16,12,10,.16);
    }
    .anzo-hello { margin:0; color:#423630 !important; font-size:26px; font-weight:500; }
    .anzo-title {
        margin:8px 0 0 0; color:#100c0a !important; -webkit-text-fill-color:#100c0a !important;
        font-size:40px; line-height:1.15; font-weight:700;
    }
    .anzo-sub {
        max-width:520px; margin:12px auto 8px auto; color:#967e71 !important;
        font-size:15px; line-height:1.6;
    }

    [data-testid="stChatMessage"] {
        background:#fff !important; border:1px solid #e0dddc !important;
        border-radius:18px !important; box-shadow:0 8px 20px rgba(16,12,10,.05);
    }
    [data-testid="stChatMessage"] p { color:#100c0a !important; }

    div[data-testid="stHorizontalBlock"] > div button {
        display:flex !important;
        flex-direction:column !important;
        align-items:flex-start !important;
        justify-content:flex-start !important;
        background:#fff !important;
        color:#100c0a !important;
        border:1px solid #e0dddc !important;
        border-radius:20px !important;
        min-height:168px !important;
        height:168px !important;
        padding:18px 16px !important;
        box-shadow:0 10px 28px rgba(16,12,10,.06) !important;
        text-align:left !important;
        white-space:pre-line !important;
        overflow:visible !important;
        font-weight:700 !important;
        font-size:16px !important;
        line-height:1.35 !important;
    }
    div[data-testid="stHorizontalBlock"] > div button * {
        white-space:pre-line !important;
        overflow:visible !important;
        text-overflow:clip !important;
        color:#100c0a !important;
        -webkit-text-fill-color:#100c0a !important;
    }
    div[data-testid="stHorizontalBlock"] > div button::before {
        content:"";
        width:38px; height:38px; border-radius:12px; background:#100c0a;
        background-repeat:no-repeat; background-position:center; background-size:18px 18px;
        margin:0 0 14px 0; display:block; flex:0 0 38px;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button::before {
        background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' fill='none' stroke='%23f2eef2' stroke-width='1.8' stroke-linecap='round'><path d='M4 14l9-9'/><path d='M8 5h5v5'/></svg>");
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button::before {
        background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' fill='none' stroke='%23f2eef2' stroke-width='1.8' stroke-linecap='round'><path d='M4 9a5 5 0 0 1 8-4'/><path d='M14 9a5 5 0 0 1-8 4'/></svg>");
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button::before {
        background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' fill='none' stroke='%23f2eef2' stroke-width='1.8' stroke-linecap='round'><path d='M12 3l3 3-8 8H4v-3l8-8z'/></svg>");
    }
    div[data-testid="stHorizontalBlock"] > div button:hover { border-color:#967e71 !important; }

    [data-testid="stExpander"] {
        background:rgba(255,255,255,.9) !important; border:1px solid #e0dddc !important;
        border-radius:16px !important;
    }
    .stTextInput label, .stTextArea label { color:#423630 !important; }
    .stTextInput input, .stTextArea textarea {
        background:#fff !important; color:#100c0a !important;
        border:1px solid #e0dddc !important; border-radius:999px !important;
        min-height:48px !important;
    }
    .composer [data-testid="stForm"] {
        background:transparent !important; border:0 !important;
    }
    .stFormSubmitButton button {
        background:linear-gradient(135deg,#967e71 0%, #423630 100%) !important;
        color:#f2eef2 !important; border:0 !important; border-radius:999px !important;
        font-weight:700 !important; min-height:48px !important; width:100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

PRIMARY_MODEL = "openai/gpt-oss-20b"
FALLBACK_MODELS = [PRIMARY_MODEL, "llama-3.1-8b-instant", "gemma2-9b-it"]
LEADS_FILE = Path("anzo_leads.csv")

SYSTEM_PROMPT = """
You are ANZO's AI business consultant.
Understand the visitor's business problem first, then recommend a suitable
ANZO solution, then qualify serious prospects.
Never speak as the visitor. Never invent prices, timelines, results, or facts.
Ask exactly one short question. Match the visitor's language.
Roman Urdu in, Roman Urdu out. English in, English out.
RESPONSE SHAPE:
1) Restate the problem. 2) Recommend the ANZO solution.
3) Business benefit without fake numbers. 4) One question.
GOOD EXAMPLE
Visitor: Meri real estate agency hai. Website aur WhatsApp se leads aati hain, lekin meri team late reply karti hai.
You: Aapki asl problem yeh hai ke website aur WhatsApp ki leads ka jawab late milta hai. ANZO connected AI lead agent bana sakta hai jo turant jawab de, details le, aur serious leads team tak bheje. Is se missed follow-ups kam ho sakte hain. Abhi yeh leads aap kahan save karte hain?
"""

SUGGESTIONS = [
    ("Missed leads\nLate WhatsApp replies",
     "Website and WhatsApp leads come in, but my team replies late and we miss customers."),
    ("Repetitive work\nToo much manual follow-up",
     "My team spends too much time on repetitive manual work and follow-ups."),
    ("Custom system\nWebsite, app or dashboard",
     "I need a custom website, dashboard, or software for my business, but I am not sure what to build first."),
]

ROMAN_MARKERS = {
    "hai","hain","kya","mujhe","mera","meri","aap","lekin","nahi","chahiye",
    "karna","yeh","abhi","kaise","batao","team","mein","aur","leads","lead"
}
ROLE_LEAK = re.compile(r"^\s*(mujhe|hamari agency|meri agency|mujh ko)\b", re.I)


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
    return "roman_urdu" if hits >= 2 else "english"


def language_instruction(lang: str) -> str:
    if lang == "roman_urdu":
        return "Reply in simple Roman Urdu / Hinglish. One short question. You are ANZO's consultant."
    if lang == "urdu":
        return "Reply in simple Urdu. One short question. You are ANZO's consultant."
    return "Reply in clear English. One short question. You are ANZO's consultant."


def enforce_one_question(text: str) -> str:
    text = (text or "").strip()
    marks = [i for i, ch in enumerate(text) if ch in "??"]
    return text[: marks[0] + 1].strip() if marks else text


def get_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")


def call_model(client: OpenAI, messages: list, temperature: float = 0.2) -> str:
    last_error = None
    tried = []
    for model in FALLBACK_MODELS:
        if not model or model in tried:
            continue
        tried.append(model)
        try:
            response = client.chat.completions.create(
                model=model, messages=messages, temperature=temperature, max_tokens=650
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as error:
            last_error = error
            if "model" in str(error).lower() or "404" in str(error):
                continue
            raise
    raise RuntimeError(str(last_error) if last_error else "No model available")


def save_lead(data: dict) -> None:
    is_new = not LEADS_FILE.exists()
    fields = ["timestamp","name","company","email","phone","problem","notes"]
    with LEADS_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        if is_new:
            writer.writeheader()
        writer.writerow(data)


def conversation_text(messages: list) -> str:
    return "\n".join(
        ("Client: " if m["role"] == "user" else "ANZO: ") + m["content"]
        for m in messages
    )


def ask_anzo(user_message: str) -> str:
    lang = detect_language(user_message)
    api_key = get_api_key()
    api_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": language_instruction(lang)},
    ] + st.session_state.messages
    try:
        if not api_key:
            raise RuntimeError("missing key")
        client = get_client(api_key)
        reply = call_model(client, api_messages)
        reply = enforce_one_question(reply)
        if not reply or ROLE_LEAK.search(reply):
            reply = (
                "Aapki asl problem late replies ki wajah se leads miss hona lagti hai. "
                "Abhi website aur WhatsApp ki leads aap kahan save karte hain?"
            )
        return reply
    except Exception:
        return "Sorry, I cannot reply right now. Please try again or contact the ANZO team."


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
    for col, (label, prompt) in zip(cols, SUGGESTIONS):
        with col:
            st.button(label, use_container_width=True, on_click=queue_suggestion, args=(prompt,))
else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

st.write("")
st.markdown('<div class="composer">', unsafe_allow_html=True)
with st.form("composer", clear_on_submit=True):
    c1, c2 = st.columns([8, 2])
    with c1:
        typed = st.text_input(
            "message",
            placeholder="Ask ANZO anything...",
            label_visibility="collapsed"
        )
    with c2:
        sent = st.form_submit_button("Send →")
st.markdown("</div>", unsafe_allow_html=True)

user_message = None
if st.session_state.queued:
    user_message = st.session_state.queued
    st.session_state.queued = None
elif sent and typed and typed.strip():
    user_message = typed.strip()

if user_message:
    st.session_state.messages.append({"role": "user", "content": user_message})
    reply = ask_anzo(user_message)
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
                    save_lead({
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "name": name.strip(),
                        "company": company.strip(),
                        "email": email.strip(),
                        "phone": phone.strip(),
                        "problem": problem.strip(),
                        "notes": conversation_text(st.session_state.messages),
                    })
                    st.success("Thanks. Your details have been saved.")
