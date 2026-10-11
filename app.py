import csv
import os
import re
from datetime import datetime
from pathlib import Path

import httpx
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
# gemma2-9b-it is no longer in Groq's model list, so it was replaced.
FALLBACK_MODELS = [
    PRIMARY_MODEL,
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]
LEADS_FILE = Path("anzo_leads.csv")

SYSTEM_PROMPT = """
You are ANZO's AI business consultant and lead qualification assistant.

ANZO is a digital technology agency focused on AI, automation, and software.
You help a visitor understand their business problem, recommend a suitable ANZO
solution, and guide serious prospects to the ANZO team.

You are NOT:
- a generic FAQ bot
- a service menu
- the client
- a salesperson who invents prices, timelines, clients, results, or guarantees

IDENTITY LOCK:
- Always speak as ANZO's consultant. Never speak as the visitor.
- Never invent the visitor's lead volume, tools, budget, process, company, or results.
- If a fact was not given by the visitor, do not pretend it exists.

ANZO CONFIRMED CAPABILITY AREAS (a project can combine several):
- AI chatbots and AI agents
- AI voice / call agents
- Customer support, sales, and lead qualification agents
- WhatsApp AI agents and WhatsApp automation
- Business process automation
- Lead management systems and automated lead follow-ups
- Email, CRM, Google Sheets, data, reporting, and notification automation
- Custom business workflows
- Website development
- Web applications, dashboards, portals, internal tools, and custom software
- Mobile app development for iOS and Android

CONFIRMED vs PROPOSED vs TO BE CONFIRMED:
- Confirmed: the capability areas listed above. You may say "ANZO builds WhatsApp automation".
- Proposed: your suggested design for this visitor. Word it as a suggestion
  ("mera suggestion hai", "the approach I'd suggest"), never as a promise.
- To be confirmed by the ANZO team: anything more specific than the list above.
  This includes connecting to a specific named platform (a particular CRM, Facebook,
  HubSpot, a payment gateway, a booking tool), specific frameworks or technologies,
  "native" or "cross-platform" apps, exact features, timelines, and pricing.
  For these, say plainly that the ANZO team confirms it after reviewing the requirements.

DIAGNOSE BEFORE YOU RECOMMEND:
Understand the problem before proposing a solution. Do not name a service just
because the visitor mentioned a technology. If the visitor already gave enough
detail (business type, process, goal), do not ask for it again. Use the history
and never repeat a question that was already answered.

Useful things to find out, one at a time and only if still unknown:
- Lead or follow-up problems: business type, where leads come from (WhatsApp,
  website, social media, ads, calls), where they are recorded (CRM, Excel, Google
  Sheets, nowhere), who follows up and how (manually or with a tool), where leads get missed.
- Workflow automation: where the process starts, what is done manually, which tools
  are used, where delays or errors happen.
- Chatbot or agent: who it talks to, which channel, its main purpose, when it should
  hand over to a human.
- Website, software, or mobile app: business goal, intended users, essential
  features, existing systems. Discuss a technical approach only after these are clear.

REPLY MODES (pick the one that fits the visitor's latest message):
1. DIAGNOSE: the visitor described a problem or goal only in general terms, picked a
   broad option (build an AI agent, automate a process, website/software, mobile app,
   not sure yet), or said something like "I need a chatbot". Reply with one sentence
   acknowledging their specific problem, then ONE question about their current situation.
   Do not recommend a solution yet.
2. RECOMMEND: you now understand the business and the workflow. In 3 to 5 short
   sentences: restate the problem, suggest the connected ANZO solution and what it
   would do, state the business benefit (no fake numbers), and note anything the ANZO
   team must confirm. A question at the end is optional. Only ask one if you still
   need a key detail, otherwise end with the statement.
3. ANSWER: the visitor asked a direct question. Answer it directly in 1 to 3 sentences
   first. A follow-up question is optional.
4. SCOPE / PRICING: explain that cost and timeline depend on scope, complexity,
   features, integrations, AI requirements, platforms, and workflows. The ANZO team
   confirms them after reviewing the requirements. Never give a number or a deadline.
5. SUMMARY / HANDOFF: when you have enough information or the visitor wants to proceed,
   summarize in a few lines: the problem, the proposed solution (marked as a proposal),
   key requirements, and what the ANZO team still needs to confirm. Then invite them to
   fill the "ANZO team ko details bhejein" form below the chat so the team can follow up.

If the visitor says they are not sure what they need, reassure them and ask what is
currently taking too much time, where repetitive work happens, or where leads and
customers are being lost.

Do not end every reply with a question. Vary the shape of your replies. Do not use
the same sentence pattern two replies in a row.

QUESTION RULES:
- At most one question mark in a reply.
- Ask for one piece of information. One question may cover two closely related
  things (for example where leads come from and how they are tracked), but never
  ask for a list of details.
- Do not ask for name, email, or phone early. Only after real interest, or at handoff.

STYLE:
- Professional, confident, friendly, human, concise. Plain language for business owners.
- 2 to 5 short sentences. No headings. Bullets only when listing 3 or more parts.
- No emojis, no pressure, no aggressive sales language.
- Never say "How can I help you today?".

LANGUAGE:
- Match the visitor's latest message.
- Roman Urdu / Hinglish in, Roman Urdu / Hinglish out.
- English in, English out.
- Urdu script in, Urdu out.
- Keep product names in English: WhatsApp, CRM, Excel, Google Sheets.

PRICING / TIMELINE:
- Never invent a price or deadline. Never promise an exact cost.

ACCURACY:
- Never invent clients, case studies, testimonials, results, team members,
  integrations, technologies, features, or guarantees.
- If something is unknown, say the ANZO team can confirm it.

EXAMPLES (they show the shape only. Never copy their wording or their facts):

Mode DIAGNOSE
Visitor: Meri team repetitive kaam mein time lagati hai aur leads ka follow-up miss ho jata hai. Mujhe AI agents aur automation chahiye.
You: Repetitive kaam aur missed follow-ups ka matlab hai ke leads haath se nikal rahi hain. Aap kis type ka business chalate hain, aur abhi incoming leads ko kaise handle karte hain?

Mode RECOMMEND
Visitor: Hum real estate agency hain. Leads Facebook ads aur WhatsApp se aati hain aur sales team Excel mein manually track karti hai.
You: Leads do channels se aa rahi hain aur tracking haath se ho rahi hai, isi liye follow-up miss hone ka risk rehta hai. Mera suggestion hai ek connected setup: dono channels ki leads ek jagah aayein, WhatsApp AI agent turant jawab de kar zaroori details le, aur follow-up reminders automatic chalen. Is se team ka manual kaam kam hoga aur koi lead bina jawab ke nahi rahegi. Aapke Facebook aur Excel setup ke saath exact connection ANZO team requirements dekh kar confirm karegi.

Mode ANSWER
Visitor: Do you build iOS apps?
You: Yes, ANZO builds iOS and Android apps, both customer-facing apps and internal business tools. The exact technical approach is decided once the team understands your requirements.

Mode SCOPE / PRICING
Visitor: Kitna cost aayega?
You: Cost project ke scope par depend karti hai, jaise features, integrations, AI requirements aur platforms. Exact price aur timeline ANZO team requirements dekh kar confirm karti hai. Aap kya banwana chahte hain?

Integration question
Visitor: Can you connect it to HubSpot?
You: ANZO does CRM automation, but whether it can connect to HubSpot specifically is something the ANZO team confirms after reviewing your setup. If you share what you want to automate, I can outline the requirements for them.

BAD EXAMPLES (never do these):
- Mujhe har din 20-30 leads milte hain.
- ANZO chatbots provide karta hai. Price 50,000 hai.
- Conversion 40 percent badh jayegi.
- Yes, ANZO builds native iOS apps using Swift. (invented technology)
- Replying with a solution before understanding a vague request.
"""

WELCOME_MESSAGE = (
    "Hey, I'm ANZO's AI assistant. Tell me what you're trying to build, "
    "automate, or improve, and I'll help you figure out the right solution. "
    "(Aap Roman Urdu mein bhi likh sakte hain.)"
)

QUICK_OPTIONS = [
    ("Build an AI Agent", "I want to build an AI agent for my business."),
    ("Automate a Process", "I want to automate a process in my business."),
    ("Build a Website / Software", "I want to build a website or software for my business."),
    ("Build a Mobile App", "I want to build a mobile app."),
    ("I'm Not Sure Yet", "I'm not sure yet what I need."),
]

# Words that are clearly Roman Urdu. Words that are also common English words
# (team, process, lead, leads, main, is, us) are intentionally NOT included,
# otherwise English messages were detected as Roman Urdu.
ROMAN_MARKERS = {
    "hai", "hain", "kya", "kyun", "mujhe", "mera", "meri", "mere", "aap",
    "aapki", "aapka", "apki", "apka", "hum", "hamari", "hamare", "humari",
    "lekin", "magar", "nahi", "nahin", "chahiye", "chahte", "chahta", "chahti",
    "karna", "karte", "karti", "karta", "karein", "karen", "karo", "hota",
    "hoti", "hote", "wala", "wali", "wale", "yeh", "ye", "woh", "wo", "abhi",
    "kitna", "kitni", "kitne", "kaise", "kaisa", "batao", "bataen", "bataiye",
    "se", "ko", "ka", "ki", "ke", "mein", "aur", "ya", "liye", "baad",
    "pehle", "bhi", "sirf", "kuch", "koi", "sakte", "sakta", "sakti", "bohat",
    "bahut", "zaroor", "rahi", "raha", "rahe", "agar", "toh", "kahan", "kaun",
    "kab", "kaam", "kiya", "dein", "lein", "banana", "banwana", "chalate",
    "chalati", "zyada", "saath", "sath", "tak", "nay", "ne",
}

# Catches replies where the model starts speaking as the client.
ROLE_LEAK = re.compile(
    r"^\s*(hamari agency|meri agency|hamari company|meri company|mera business"
    r"|mujhe\s+(har|roz|rozana|din|bohat|bahut)\b)",
    re.IGNORECASE
)

QUESTION_MARKS = "?؟"  # ASCII and Urdu/Arabic question marks


def get_secret(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def get_api_key() -> str:
    return get_secret("GROQ_API_KEY")


def detect_language(text: str) -> str:
    if re.search(r"[؀-ۿ]", text or ""):
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
            "Ask at most one short question, and only if you need information."
        )
    if lang == "urdu":
        return (
            "The visitor wrote in Urdu. Reply in simple Urdu. "
            "You are ANZO's consultant, not the visitor. "
            "Ask at most one short question, and only if you need information."
        )
    return (
        "The visitor wrote in English. Reply in clear English. "
        "You are ANZO's consultant, not the visitor. "
        "Ask at most one short question, and only if you need information."
    )


def looks_like_roman_urdu(text: str) -> bool:
    words = re.findall(r"[A-Za-z]+", (text or "").lower())
    if not words:
        return False
    hits = sum(1 for w in words if w in ROMAN_MARKERS)
    return hits >= 2


def enforce_one_question(text: str) -> str:
    """Keep at most one question. Earlier questions are dropped, but the rest of
    the reply is kept (the old version cut the whole reply at the first '?')."""
    text = (text or "").strip()
    if not text:
        return text
    if sum(text.count(ch) for ch in QUESTION_MARKS) <= 1:
        return text

    parts = re.split(r"(?<=[.!?؟])(\s+)", text)
    sentences = parts[0::2]
    seps = parts[1::2] + [""]
    question_idx = [i for i, s in enumerate(sentences) if s.rstrip().endswith(tuple(QUESTION_MARKS))]
    if len(question_idx) <= 1:
        # Several question marks inside one sentence: keep up to the first one.
        first = min(text.find(ch) for ch in QUESTION_MARKS if ch in text)
        return text[: first + 1].strip()

    keep_question = question_idx[-1]
    rebuilt = []
    for i, sentence in enumerate(sentences):
        if i in question_idx and i != keep_question:
            continue
        rebuilt.append(sentence + seps[i])
    return "".join(rebuilt).strip()


def get_client(api_key: str) -> OpenAI:
    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )


def call_model(client: OpenAI, messages: list, temperature: float = 0.25) -> str:
    last_error = None
    for model in FALLBACK_MODELS:
        kwargs = {}
        if "gpt-oss" in model:
            # Low reasoning effort keeps replies fast and stops reasoning tokens
            # from eating the whole token budget (which returned empty replies).
            kwargs["extra_body"] = {"reasoning_effort": "low"}
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=1024,
                **kwargs,
            )
            content = (response.choices[0].message.content or "").strip()
            if content:
                return content
            last_error = RuntimeError(f"Empty reply from {model}")
        except Exception as error:
            last_error = error
            err = str(error).lower()
            # A bad key will fail on every model, so stop early.
            if "401" in err or "invalid api key" in err:
                raise
            # Anything else (model removed, rate limit, overload): try the next model.
            continue
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
        "Keep at most one question.",
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


def neutral_reply(lang: str) -> str:
    """Safe reply when the model output is empty or unusable. It does not
    assume anything about the visitor's business."""
    if lang == "english":
        return (
            "Could you tell me a little more about what you're trying to build, "
            "automate, or improve in your business?"
        )
    return (
        "Aap apne business mein kya banana, automate, ya improve karna chahte hain, "
        "thoda detail mein bata sakte hain?"
    )


def error_reply(lang: str) -> str:
    if lang == "english":
        return (
            "Sorry, I can't reply right now. Please try again in a moment, "
            "or send your details to the ANZO team using the form below."
        )
    return (
        "Sorry, main abhi jawab nahi de paa raha. Thodi der baad try karein, "
        "ya neeche form se ANZO team ko apni details bhej dein."
    )


def send_lead_webhook(data: dict) -> bool:
    """Optional. If LEADS_WEBHOOK_URL is set (env or Streamlit secrets), the lead
    is also POSTed there (Zapier, Make, n8n, Google Apps Script, etc.). This
    matters because anzo_leads.csv is wiped when Streamlit Cloud restarts."""
    url = get_secret("LEADS_WEBHOOK_URL")
    if not url:
        return False
    try:
        response = httpx.post(url, json=data, timeout=10)
        return response.is_success
    except Exception:
        return False


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


if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": WELCOME_MESSAGE}
    ]
if "lang" not in st.session_state:
    st.session_state.lang = "english"

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

# Quick options are shown only before the visitor sends the first message.
quick_slot = None
quick_clicked = None
if len(st.session_state.messages) == 1:
    quick_slot = st.empty()
    with quick_slot.container():
        option_cols = st.columns(2)
        for index, (label, text) in enumerate(QUICK_OPTIONS):
            if option_cols[index % 2].button(
                label, key=f"quick_{index}", use_container_width=True
            ):
                quick_clicked = text

user_message = st.chat_input("Apna message yahan likhein...") or quick_clicked
api_key = get_api_key()

if user_message:
    if quick_slot is not None:
        quick_slot.empty()

    st.session_state.messages.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.markdown(user_message)

    lang = detect_language(user_message)
    # A very short reply such as "WhatsApp" has no language signal, so keep the
    # language of the conversation instead of switching to English.
    short_message = len(re.findall(r"[A-Za-z؀-ۿ]+", user_message)) <= 3
    if lang == "english" and short_message and st.session_state.lang != "english":
        lang = st.session_state.lang
    st.session_state.lang = lang

    system_content = SYSTEM_PROMPT + "\n\n" + language_instruction(lang)
    api_messages = [{"role": "system", "content": system_content}] + st.session_state.messages

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
                    reply = neutral_reply(lang)
                st.markdown(reply)
                st.session_state.messages.append(
                    {"role": "assistant", "content": reply}
                )
            except Exception:
                fallback = error_reply(lang)
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
            lead = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "name": name.strip(),
                "company": company.strip(),
                "email": email.strip(),
                "phone": phone.strip(),
                "problem": problem.strip(),
                "notes": conversation_text(st.session_state.messages),
            }
            save_lead(lead)
            webhook_configured = bool(get_secret("LEADS_WEBHOOK_URL"))
            delivered = send_lead_webhook(lead)
            if webhook_configured and not delivered:
                st.warning(
                    "Lead save ho gayi, lekin ANZO team ko bhejne mein masla aaya. "
                    "Please dobara try karein."
                )
            else:
                st.success("Lead save ho gayi.")
