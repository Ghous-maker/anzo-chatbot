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
    page_title="ANZO AI Consultant",
    page_icon="💼",
    layout="centered"
)

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    </style>
    """,
    unsafe_allow_html=True
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
PRIMARY_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
FALLBACK_MODELS = [
    PRIMARY_MODEL,
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "gemma2-9b-it",
]
LEADS_FILE = Path("anzo_leads.csv")

SYSTEM_PROMPT = """
You are the AI business consultant and lead qualification assistant for ANZO,
an AI automation and software agency.

Your job is NOT to act like a basic FAQ chatbot or a service menu.

Your objective:
UNDERSTAND THE CLIENT'S PROBLEM -> DISCOVER THEIR GOAL -> IDENTIFY THE RIGHT
SOLUTION -> EXPLAIN IT CLEARLY -> QUALIFY THE PROJECT -> GUIDE SERIOUS
PROSPECTS TO ANZO.

ANZO helps businesses reduce repetitive manual work, improve operations,
manage leads, save time, and build custom digital solutions.

ANZO capabilities include:
- AI chatbots and AI agents
- AI voice / call agents
- Customer support, sales, and lead qualification agents
- WhatsApp AI and automation
- Business process and workflow automation
- Lead management and automated follow-ups
- Email, CRM, Google Sheets, data, reporting, and notification automation
- Website development
- Web applications and custom software
- Dashboards, portals, and internal tools
- Mobile apps for Android and iOS
- Other custom AI-powered business solutions

These are capabilities, not a fixed product menu. Combine them when the
business problem needs a connected system.

CORE BEHAVIOUR:
- Always understand the business problem before recommending a solution.
- If the client mentions a technology, discover why they need it.
- Use information already provided. Do not ask for it again.
- If the client is unsure, help them discover the bottleneck.
- Think: business goal -> current problem -> current process -> bottleneck ->
  desired outcome -> ANZO solution.

When recommending a solution, keep it short:
1. One sentence identifying the problem.
2. One sentence explaining the recommended ANZO solution.
3. One sentence explaining the business benefit.
4. Exactly one next question.

SERVICE ROUTING:
- AI agents: intelligent conversations, support, sales, qualification.
- Voice agents: phone calls, call answering, appointments, voice interaction.
- Automation: repetitive work, CRM updates, data movement, notifications,
  follow-ups, operational workflows.
- Website development: online business presence.
- Web apps / custom software: dashboards, portals, SaaS, internal systems.
- Mobile apps: Android / iOS experiences.
- Recommend a combination when needed, for example:
  website + WhatsApp AI agent + lead qualification + CRM + follow-up + dashboard.

LEAD QUALIFICATION:
Collect naturally over the conversation, never all at once:
- Name
- Company / business
- Business type
- Main problem
- Current process
- Desired outcome
- Important features
- Existing tools / systems
- Timeline
- Approximate budget / investment range
- Email
- Phone / WhatsApp

PRICING AND TIMELINES:
- Never invent ANZO pricing.
- Never invent delivery timelines.
- Explain that cost and timeline depend on scope, complexity, features,
  integrations, platforms, workflows, AI requirements, and implementation.
- If asked for an exact number, say the ANZO team must review requirements.

ACCURACY:
Never invent clients, case studies, testimonials, results, guarantees,
technologies, integrations, team members, previous projects, prices, or
timelines. If information is unavailable, say the ANZO team can confirm it.

TONE:
Professional, confident, concise, friendly, modern, human, and
solution-focused. No aggressive sales language. No excessive emojis.
No heavy jargon. Do not repeatedly ask "How can I help you today?"

STRICT RESPONSE RULES:
- Match the user's latest message language.
- If the user writes in Roman Urdu / Hinglish, reply in simple Roman Urdu / Hinglish.
- If the user writes in Urdu script, reply in Urdu.
- If the user writes in English, reply in English.
- Keep tool names in English: WhatsApp, CRM, Excel, Google Sheets.
- Ask exactly one short question per response.
- That question must request only one piece of information.
- Never join two requests with and, or, aur, ya, or a comma list.
- Never use more than one question mark.
- Bad: Aapki team leads kaise handle karti hai, aur kaunse tools use karti hai?
- Good: Nayi lead aane ke baad aapki team sabse pehle kya karti hai?

Always behave like a problem-solving business consultant, not a service menu.
"""

WELCOME_MESSAGE = (
    "Welcome to ANZO. Tell me what you want to build, automate, or improve "
    "in your business. You can also tell me where your team is spending too "
    "much time or losing potential customers."
)

ROMAN_MARKERS = {
    "hai", "hain", "kya", "kyun", "mujhe", "mera", "meri", "mere", "aap",
    "aapki", "apki", "hum", "hamari", "lekin", "magar", "nahi", "nahin",
    "chahiye", "karna", "karte", "karti", "hota", "hoti", "wala", "wali",
    "yeh", "ye", "woh", "wo", "abhi", "kitna", "kitni", "kaise", "kaisa",
    "batao", "bataen", "please", "team", "se", "ko", "ka", "ki", "ke",
    "mein", "main", "aur", "ya", "liye", "baad", "pehle", "process"
}


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
            "The user wrote in Roman Urdu / Hinglish. "
            "Reply in simple Roman Urdu / Hinglish. "
            "Do not switch to full English. "
            "Ask exactly one short question."
        )
    if lang == "urdu":
        return (
            "The user wrote in Urdu. Reply in simple Urdu. "
            "Ask exactly one short question."
        )
    return (
        "The user wrote in English. Reply in clear English. "
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
    if len(marks) <= 1:
        # Still block joined requests like "X, aur Y?"
        return text
    return text[: marks[0] + 1].strip()


def get_client() -> OpenAI:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY missing")
    return OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )


def call_model(client: OpenAI, messages: list, temperature: float = 0.4) -> str:
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
                max_tokens=700,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as error:
            last_error = error
            err = str(error).lower()
            if "model" in err or "404" in err or "not found" in err:
                continue
            raise
    raise RuntimeError(str(last_error) if last_error else "No model available")


def rewrite_language(client: OpenAI, text: str, lang: str) -> str:
    if lang != "roman_urdu":
        return text
    if looks_like_roman_urdu(text):
        return text
    messages = [
        {
            "role": "system",
            "content": (
                "Rewrite the assistant message in simple Roman Urdu / Hinglish. "
                "Keep the same meaning. Do not add new facts, prices, or claims. "
                "Keep exactly one question. Keep tool names in English."
            ),
        },
        {"role": "user", "content": text},
    ]
    rewritten = call_model(client, messages, temperature=0.2)
    return rewritten or text


def extract_contact(text: str) -> dict:
    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text or "")
    phone_match = re.search(r"(\+?\d[\d\s-]{8,}\d)", text or "")
    return {
        "email": email_match.group(0) if email_match else "",
        "phone": phone_match.group(0).strip() if phone_match else "",
    }


def save_lead(data: dict) -> None:
    is_new = not LEADS_FILE.exists()
    fieldnames = [
        "timestamp", "name", "company", "email", "phone",
        "problem", "notes"
    ]
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
if "lead_saved" not in st.session_state:
    st.session_state.lead_saved = False

st.title("ANZO")
st.caption("AI Business Consultant")

with st.sidebar:
    st.subheader("ANZO")
    st.write(
        "ANZO helps businesses reduce manual work, handle leads faster, "
        "and build custom AI, automation, website, and software solutions."
    )
    st.write("This chatbot understands your problem first, then recommends a solution.")
    st.divider()
    st.caption("Pricing and timelines are confirmed by the ANZO team after reviewing requirements.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_message = st.chat_input("Write your message here...")

if user_message:
    st.session_state.messages.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.markdown(user_message)

    if not GROQ_API_KEY:
        with st.chat_message("assistant"):
            st.error("Chatbot is not connected yet. GROQ_API_KEY is missing.")
        st.stop()

    lang = detect_language(user_message)
    api_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": language_instruction(lang)},
    ] + st.session_state.messages

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                client = get_client()
                reply = call_model(client, api_messages)
                reply = rewrite_language(client, reply, lang)
                reply = enforce_one_question(reply)
                if not reply:
                    reply = "Samajh gaya. Aapki current process kya hai?"
                st.markdown(reply)
                st.session_state.messages.append(
                    {"role": "assistant", "content": reply}
                )
            except Exception:
                fallback = (
                    "Sorry, main abhi jawab nahi de paa raha. "
                    "Please thodi der baad try karein, ya ANZO team se direct baat karein."
                )
                st.markdown(fallback)
                st.session_state.messages.append(
                    {"role": "assistant", "content": fallback}
                )

st.divider()
st.subheader("ANZO team ko details bhejein")
st.caption("Jab aap ready hon, apna contact chhod sakte hain. Yeh details is computer par save hongi.")

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
            contact = extract_contact(" ".join([email, phone]))
            save_lead(
                {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "name": name.strip(),
                    "company": company.strip(),
                    "email": email.strip() or contact["email"],
                    "phone": phone.strip() or contact["phone"],
                    "problem": problem.strip(),
                    "notes": conversation_text(st.session_state.messages),
                }
            )
            st.session_state.lead_saved = True
            st.success("Lead save ho gayi. ANZO team isey is computer ki anzo_leads.csv file mein dekh sakti hai.")