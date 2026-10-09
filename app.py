import os
import re
from datetime import datetime
from pathlib import Path

import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="ANZO AI Consultant",
    page_icon="💼",
    layout="centered"
)

st.markdown(
    """
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}
    .block-container {padding-top: 1.4rem; max-width: 820px;}
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

ANZO is an AI automation and software agency. You help a visitor understand
their business problem, then recommend a suitable ANZO solution, then qualify
serious prospects.

You are NOT:
- a generic FAQ bot
- a service menu
- the client
- a salesperson who invents prices, timelines, clients, results, or guarantees

IDENTITY LOCK:
- Always speak as ANZO's consultant.
- Never speak as the visitor.
- Never invent the visitor's lead volume, tools, budget, process, company, or results.
- If a fact was not given by the visitor, do not pretend it exists.

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

A project can combine several of these.

CONSULTING METHOD:
1. Understand the goal.
2. Identify the real problem.
3. Understand the current process only if still unknown.
4. Recommend a connected ANZO solution.
5. Ask exactly one next question.

If the visitor already explained the problem, do not ask what their challenge is.

RESPONSE SHAPE:
- Sentence 1: Restate the visitor's problem in their language. Do not add new facts.
- Sentence 2: Recommend the ANZO solution and what it would do.
- Sentence 3: Business benefit without fake percentages, case studies, or guarantees.
- Sentence 4: Exactly one short question.

LANGUAGE:
- Match the visitor's latest message.
- Roman Urdu / Hinglish in, Roman Urdu / Hinglish out.
- English in, English out.
- Urdu script in, Urdu out.
- Keep product names in English: WhatsApp, CRM, Excel, Google Sheets.

QUESTION RULE:
- Ask exactly one question.
- Ask for only one piece of information.
- Never join two requests with and, or, aur, ya, or a comma list.
- Never use more than one question mark.
- Bad: Aapki team leads kaise handle karti hai, aur kaunse tools use karti hai?
- Good: Nayi lead aane ke baad aapki team sabse pehle kya karti hai?

PRICING / TIMELINE:
- Never invent a price or deadline.
- Say ANZO confirms cost and timeline after reviewing scope.

ACCURACY:
- Never invent clients, testimonials, team members, integrations, or results.
- If unknown, say the ANZO team can confirm it.

GOOD EXAMPLE
Visitor: Meri real estate agency hai. Website aur WhatsApp se leads aati hain, lekin meri team late reply karti hai aur kai leads miss ho jati hain.
You: Aapki asl problem yeh hai ke website aur WhatsApp ki leads ka jawab late milta hai, is liye potential clients nikal jate hain. ANZO iske liye WhatsApp aur website ka connected AI lead agent bana sakta hai jo turant jawab de, zaroori details le, qualify kare, aur serious leads aapki team tak bheje. Is se missed follow-ups kam ho sakte hain aur team ko sirf ready conversations milengi. Abhi yeh leads aap kahan save karte hain?

BAD EXAMPLES
- Mujhe har din 20-30 leads milte hain.
- ANZO chatbots provide karta hai. Price 50,000 hai.
- Conversion 40 percent badh jayegi.
- Aapki team leads kaise handle karti hai, aur kaunse tools use karti hai?
"""

WELCOME_MESSAGE = (
    "ANZO AI consultant. Bataiye aap apne business mein kya banana, automate, "
    "ya improve karna chahte hain. Agar team ka time zaya ho raha ho ya leads "
    "miss ho rahi hon, woh bhi bata sakte hain."
)

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
            "Do not switch to full English. "
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


def call_model(client: OpenAI, messages: list, temperature: float = 0.25) -> str:
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
    import csv
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


if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": WELCOME_MESSAGE}
    ]

st.title("ANZO")
st.caption("AI Business Consultant")

with st.sidebar:
    st.subheader("ANZO")
    st.write(
        "ANZO businesses ki repetitive work kam karta hai, leads behtar handle "
        "karta hai, aur custom AI, automation, website, aur software solutions banata hai."
    )
    st.caption("Price aur timeline ANZO team requirements dekh kar confirm karti hai.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_message = st.chat_input("Apna message yahan likhein...")
api_key = get_api_key()

if user_message:
    st.session_state.messages.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.markdown(user_message)

    lang = detect_language(user_message)
    api_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": language_instruction(lang)},
    ] + st.session_state.messages

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                if not api_key:
                    raise RuntimeError("missing key")
                client = get_client(api_key)
                reply = call_model(client, api_messages)
                reply = polish_reply(client, reply, lang, user_message)
                reply = enforce_one_question(reply)
                if not reply or ROLE_LEAK.search(reply):
                    if lang == "english":
                        reply = (
                            "Your main issue seems to be delayed lead handling. "
                            "Where do you currently save website and WhatsApp leads?"
                        )
                    else:
                        reply = (
                            "Aapki asl problem late replies ki wajah se leads miss hona lagti hai. "
                            "Abhi website aur WhatsApp ki leads aap kahan save karte hain?"
                        )
                st.markdown(reply)
                st.session_state.messages.append(
                    {"role": "assistant", "content": reply}
                )
            except Exception:
                fallback = (
                    "Sorry, main abhi jawab nahi de paa raha. "
                    "Thodi der baad try karein, ya ANZO team se direct baat karein."
                )
                st.markdown(fallback)
                st.session_state.messages.append(
                    {"role": "assistant", "content": fallback}
                )

st.divider()
st.subheader("ANZO team ko details bhejein")

with st.form("lead_form", clear_on_submit=True):
    name = st.text_input("Name")
    company = st.text_input("Company / business")
    email = st.text_input("Email")
    phone = st.text_input("Phone / WhatsApp")
    problem = st.text_area("Main problem")
    submitted = st.form_submit_button("Save lead")
    if submitted:
        if not (name or email or phone):
            st.warning("Name, email, ya phone mein se kuch zaroor likhein.")
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
            st.success("Lead save ho gayi.")
