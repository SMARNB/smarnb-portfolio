"""Rule-based chat assistant — first-party, no external API, no keys, no data leaves
the server.

It reads the live services catalog from the database and can: greet, make small
talk, answer common-language questions (hours, payments, contact, delivery time,
NDA, how to order, …), explain services & packages, gather a client's requirements,
and start an order — or hand off to the developer.

It also "learns": the developer can teach it answers in the dashboard (BotKnowledge),
which are matched here with the highest priority. Anything it still can't answer
confidently is flagged back to the router (``unanswered``) so it gets logged for the
developer to teach later.

Matching is fuzzy (token overlap + typo-tolerant ratios) so slightly misspelled or
loosely-worded questions still land on the right answer.

``respond()`` is a pure function: given the conversation state, the latest visitor
message, the services catalog and the curated knowledge, it returns the bot's
reply(s), suggested quick replies, the next state, an optional action (e.g. create an
order), and flags (``matched_knowledge_id``, ``unanswered``). The router applies the
action, bumps knowledge hits, logs unanswered questions and persists the state.
"""
import difflib
import re

from . import config

GREETINGS = ("hi", "hello", "hey", "hey there", "yo", "salam", "assalam", "asalam",
             "aoa", "hola", "start", "good morning", "good afternoon", "good evening",
             "morning", "evening", "greetings", "howdy")
THANKS = ("thanks", "thank you", "thankyou", "thx", "appreciate", "much appreciated")
HUMAN = ("human", "real person", "agent", "talk to ali", "talk to you", "speak to",
         "speak with", "live chat", "representative",
         "real human", "talk to a person", "talk to someone", "talk to a human")
ORDER_WORDS = ("order", "buy", "purchase", "hire", "book", "get started", "place an order",
               "i want", "i need", "start a project", "checkout", "lets do it", "lets go")
SERVICE_WORDS = ("service", "services", "offer", "what do you do", "what can you", "help with",
                 "menu", "options", "catalog", "what do you offer", "what can you do")
PRICE_WORDS = ("price", "pricing", "cost", "how much", "rate", "rates", "budget", "quote", "package")
RESTART = ("cancel", "restart", "start over", "nevermind", "never mind", "stop", "reset")

# Words that carry little meaning when comparing two phrases.
STOP = {"the", "a", "an", "to", "of", "for", "is", "are", "am", "do", "does", "did",
        "you", "your", "yours", "i", "me", "my", "mine", "we", "our", "us", "can",
        "could", "would", "will", "please", "with", "and", "or", "on", "in", "it",
        "that", "this", "these", "those", "what", "whats", "how", "when", "where",
        "who", "which", "be", "have", "has", "any", "some", "im", "ive", "u", "ur",
        "from", "about", "into", "onto", "over", "under", "just", "like", "also",
        "too", "out", "off", "away", "back", "as", "at", "but", "if", "so", "than",
        "then", "there", "here", "all", "not", "no", "yes", "was", "were", "by"}


def _dev():
    return config.ADMIN_NAME or "the developer"


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _clean(s):
    """Lowercase, drop punctuation, collapse spaces — for whole-word matching."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", _norm(s))).strip()


def _has(text, words):
    """True if any keyword/phrase appears as a WHOLE word/phrase (not a substring).
    Avoids false hits like 'yo' inside 'you' or 'hi' inside 'which'."""
    t = " " + _clean(text) + " "
    for w in words:
        w = _clean(w)
        if w and (" " + w + " ") in t:
            return True
    return False


def _money(n):
    try:
        return (config.CURRENCY or "$") + "{:,.0f}".format(float(n))
    except Exception:
        return (config.CURRENCY or "$") + str(n)


# --- Fuzzy matching helpers ---------------------------------------------------
def _tok(s):
    return [w for w in re.split(r"[^a-z0-9]+", _norm(s)) if w]


def _content(s):
    return [w for w in _tok(s) if w not in STOP and len(w) > 1]


def _phrase_match(text, phrase):
    """Score 0..1 for how well a trigger `phrase` matches the user's `text`.
    Tolerates word order and typos so "how mch is it" still finds "how much" — but
    a short all-filler trigger ("how do you do") must NOT hijack a longer,
    content-rich question ("what services do you offer and how much for a
    dashboard") just because how/do/you happen to appear scattered in it."""
    t = _norm(text)
    p = _norm(phrase)
    if not p or not t:
        return 0.0
    if p in t:                       # whole phrase appears verbatim → certain
        return 1.0
    ptoks = _tok(p)
    ttoks = set(_tok(t))
    pc = set(_content(p))            # trigger's meaningful (non-stop) words
    tc = set(_content(t))            # message's meaningful words
    # Every CONTENT word of the trigger is present (any order) → strong match.
    # Keyed on content words so an all-stop-word trigger can't match this way.
    if pc and pc <= tc:
        return 0.95
    # Trigger is made ONLY of stop-words (e.g. "how are you", "how do you do").
    # Those are real small-talk phrases, but only when the message is itself
    # small-talk — not a longer question that merely contains the filler words.
    if ptoks and not pc and all(w in ttoks for w in ptoks):
        return 0.9 if len(tc) == 0 else 0.3
    ratio = difflib.SequenceMatcher(None, t, p).ratio()
    overlap = (len(pc & tc) / len(pc)) if pc else 0.0
    # typo tolerance: best fuzzy match between content words
    fuzz = 0.0
    for w in pc:
        for u in tc:
            r = difflib.SequenceMatcher(None, w, u).ratio()
            if r > fuzz:
                fuzz = r
    return max(ratio, 0.55 * overlap + 0.45 * fuzz)


def _best_entry(text, entries, triggers_of):
    """Return (entry, score) for the best-matching entry. `triggers_of(entry)` →
    list of trigger phrases."""
    best, best_score = None, 0.0
    for e in entries:
        trigs = [tr for tr in triggers_of(e) if tr and tr.strip()]
        if not trigs:
            continue
        sc = max(_phrase_match(text, tr) for tr in trigs)
        if sc > best_score:
            best, best_score = e, sc
    return best, best_score


# --- Service catalog helpers --------------------------------------------------
def _short_title(title):
    """Mirror the site's shortened service labels so quick-reply buttons match."""
    t = title or ""
    t = re.sub(r" in Python$", "", t)
    t = re.sub(r"^Full-Stack ", "", t)
    t = re.sub(r" for SaaS & Admin Dashboards", "", t)
    t = re.sub(r" for OCR & Data Scraping", "", t)
    t = re.sub(r"^Premium Commercial ", "", t)
    return t.strip()


def _sing(w):
    """Crude singularizer so 'dashboards' and 'dashboard' compare equal."""
    return w[:-1] if len(w) > 3 and w.endswith("s") else w


def _match_service(text, services):
    """Find the service a message refers to (handles quick-reply labels & free text)."""
    t = _norm(text)
    if not t:
        return None
    best, best_score = None, 0
    for s in services:
        title = _norm(s["title"])
        short = _norm(_short_title(s["title"]))
        score = 0
        if t == title or t == short:
            return s
        if t in title or t in short or short in t or title in t:
            score = 5
        toks = {_sing(w) for w in re.split(r"[^a-z0-9]+", t) if len(w) > 2}
        cand = set(re.split(r"[^a-z0-9]+", title + " " + short + " " + " ".join(s.get("tags") or [])))
        score += len(toks & {_sing(_norm(c)) for c in cand if c})
        if score > best_score:
            best, best_score = s, score
    return best if best_score >= 2 else None


def _strong_service(text, services):
    """Only match a service when the user clearly named it (clicked a chip or typed
    the title), so loose chatter doesn't get hijacked into a service explanation."""
    t = _norm(text)
    if not t:
        return None
    for s in services:
        title = _norm(s["title"])
        short = _norm(_short_title(s["title"]))
        if t == title or t == short:
            return s
        if (len(short) >= 5 and short in t) or (len(title) >= 5 and title in t):
            return s
    return None


def _match_tier(text, service):
    t = _norm(text)
    for p in service.get("packages") or []:
        if _norm(p.get("tier", "")) and _norm(p.get("tier", "")) in t:
            return p
    aliases = {"basic": 0, "starter": 0, "cheap": 0, "standard": 1, "popular": 1,
               "premium": 2, "pro": 2, "best": 2, "full": 2}
    for word, idx in aliases.items():
        if word in t:
            pks = service.get("packages") or []
            if idx < len(pks):
                return pks[idx]
    return None


def _service_titles(services):
    return [_short_title(s["title"]) for s in services]


def _list_services_text(services):
    lines = ["Here's what I can help you with — pick one to learn more 👇"]
    for s in services[:12]:
        pks = s.get("packages") or []
        if pks:
            low = min(p.get("price", 0) for p in pks)
            lines.append("• **{}** — from {}".format(_short_title(s["title"]), _money(low)))
        else:
            lines.append("• **{}**".format(_short_title(s["title"])))
    return "\n".join(lines)


def _explain_service(s):
    parts = ["**{}**".format(s["title"])]
    if s.get("short"):
        parts.append(s["short"])
    pks = s.get("packages") or []
    if pks:
        parts.append("\n**Packages:**")
        for p in pks:
            bits = [_money(p.get("price", 0))]
            if p.get("delivery"):
                bits.append(p["delivery"])
            extra = " · ".join(bits)
            tier = p.get("tier", "")
            summ = (" — " + p["summary"]) if p.get("summary") else ""
            parts.append("• **{}** ({}){}".format(tier, extra, summ))
    dels = s.get("deliverables") or []
    if dels:
        parts.append("\n**You get:** " + ", ".join(dels[:6]) + ".")
    return "\n".join(parts)


def _first_name(name):
    """A friendly first name to address a signed-in client by (safe if blank)."""
    return (str(name or "").strip().split() or [""])[0][:40]


def _greeting(name=""):
    fn = _first_name(name)
    hi = "Hi {}! 👋".format(fn) if fn else "Hi! 👋"
    return ("{} I'm {}'s assistant. I can explain the services, share pricing, "
            "and even start your order. What are you looking to build?").format(hi, _dev())


# --- Built-in knowledge (common-language Q&A) ---------------------------------
def _ctx():
    return {
        "dev": _dev(),
        "email": (config.CONTACT_EMAIL or "").strip(),
        "whatsapp": (config.CONTACT_WHATSAPP or "").strip(),
        "location": (config.LOCATION or "").strip(),
        "currency": config.CURRENCY or "$",
    }


def _contact_answer(ctx):
    parts = ["Here's how to reach {} 👇".format(ctx["dev"])]
    if ctx["email"]:
        parts.append("• ✉️ Email: **{}**".format(ctx["email"]))
    if ctx["whatsapp"]:
        parts.append("• 💬 WhatsApp: **{}**".format(ctx["whatsapp"]))
    parts.append("• Or use the contact form / WhatsApp button in the site's contact section.")
    parts.append("\nI can also start your order or get you a quote right here — just say the word!")
    return "\n".join(parts)


DEFAULT_QUICK = ["See services", "Get a quote", "Talk to a human"]

# Purely-social built-in answers (keyed by their first trigger). These should
# politely YIELD when the visitor is, in the same message, clearly asking about
# the business — so "hi, how are you — what's your pricing?" routes to pricing, not
# small talk. Topical entries (payments, delivery, contact, NDA, …) are NOT here:
# they stay authoritative even alongside service/price words.
_SOCIAL_LEADS = {"how are you", "who are you", "where are you", "what languages",
                 "good job", "bye"}

# Each entry: (triggers, answer, quick).  answer is a template string (formatted
# with ctx) or a callable(ctx) -> str.  quick=None falls back to DEFAULT_QUICK.
BUILTIN_KB = [
    (["how are you", "how are you doing", "hows it going", "how is it going",
      "how do you do", "whats up", "sup", "you good"],
     "I'm doing great, thanks for asking! 😊 More importantly — how can I help with your project today?",
     ["See services", "Get a quote"]),

    (["who are you", "what are you", "are you a bot", "are you human", "is this a bot",
      "are you real", "your name", "whats your name", "who is this", "who am i talking to"],
     "I'm {dev}'s friendly assistant bot 🤖. I can explain services, share pricing and start an order — "
     "and I can bring in {dev} anytime if you say “talk to a human.”",
     None),

    (["where are you", "where are you based", "what country", "your location",
      "where do you live", "are you local", "timezone", "time zone", "where are you from"],
     "I'm based in {location}. Time zones are no problem — work and updates happen around your schedule. 🌍",
     ["See services", "Get a quote"]),

    (["what languages", "which language", "do you speak", "languages do you speak",
      "can you speak", "language"],
     "Feel free to write in your own words — I understand plain English and I'll do my best to help. "
     "For anything tricky, {dev} can jump right in.",
     None),

    (["are you available", "availability", "are you free", "can you take new work",
      "working hours", "when are you online", "how soon can you start", "do you have time",
      "are you accepting", "open for work"],
     "Yes — currently available for new projects! ⏱️ I usually reply within a day. "
     "Want to see the services or get a quote?",
     ["See services", "Get a quote"]),

    (["how long", "delivery time", "turnaround", "how many days", "when will it be ready",
      "how fast", "eta", "time to deliver", "how long does it take", "lead time", "deadline"],
     "Delivery depends on the package — each tier lists its own timeframe (from a couple of days to a "
     "few weeks). Want me to show the packages so you can compare?",
     ["See services", "Get a quote"]),

    (["how do i contact", "contact you", "contact details", "email address", "whats your email",
      "your email", "phone number", "whatsapp", "how to reach you", "reach you", "get in touch",
      "your number", "contact info"],
     _contact_answer,
     ["Get a quote", "Talk to a human"]),

    (["how do i pay", "payment methods", "payment options", "how to pay", "do you take paypal",
      "accept payment", "ways to pay", "method of payment", "do you accept", "pay you", "stripe",
      "jazzcash", "sadapay", "easypaisa", "bank transfer"],
     "Payments are flexible 💳 — local options (Raast, SadaPay, JazzCash), international transfer, or "
     "buy-now-pay-later. You pick a method at checkout and I'll send secure details to confirm.",
     ["See services", "Get a quote"]),

    (["refund", "money back", "guarantee", "do you offer revisions", "how many revisions",
      "not satisfied", "what if i dont like", "warranty", "revision policy"],
     "Every package includes revisions, and I work with you until you're happy with the result. "
     "Each tier lists exactly how many revisions are included.",
     ["See services", "Get a quote"]),

    (["nda", "non disclosure", "confidential", "keep it private", "sign an nda", "is my idea safe",
      "privacy"],
     "Absolutely — happy to sign an NDA. Your idea stays private, and you own all the final source "
     "files and rights to what you pay for. 🔒",
     None),

    (["how does it work", "whats the process", "your process", "how do i get started",
      "how do i start a project", "steps", "what happens next", "how do we begin"],
     "Easy 👇 1) Pick a service & package in the store and add it to your cart. 2) Check out — you'll get "
     "an order ID to track. 3) {dev} confirms the details and gets to work. Want me to set it up for you "
     "here? Just say “order.”",
     ["Get a quote", "See services"]),

    (["track my order", "where is my order", "order status", "check my order", "track order",
      "status of my order", "my order", "track an order"],
     "You can track any order anytime — click **Track an order** on the site and enter your order ID "
     "(it looks like ALR-XXXXXX). Want me to take you through anything else?",
     ["See services", "Get a quote"]),

    (["discount", "cheaper", "lower price", "negotiate", "best price", "any deal", "too expensive",
      "reduce price", "can you do it for less", "expensive", "lower the price"],
     "Tell me your budget and what you need — I'll suggest the best-fit package or tailor a custom quote "
     "to match. 👍",
     ["Get a quote", "See services"]),

    (["portfolio", "examples", "previous work", "past work", "samples", "show me your work",
      "case studies", "any examples", "your work"],
     "Sure! Check the **Work** and **Projects** sections on the site — including my flagship "
     "computer-vision system, CodeWatch. Want to see the services too?",
     ["See services", "Get a quote"]),

    (["bye", "goodbye", "see you", "thats all", "that is all", "good night", "cya", "later",
      "talk later"],
     "Thanks for stopping by! 👋 Whenever you're ready, I'm right here to help with your project.",
     ["See services", "Get a quote"]),

    (["good job", "nice", "awesome", "great", "cool", "love it", "amazing", "perfect", "wonderful",
      "well done"],
     "Thank you! 🙌 Anything else I can help you with?",
     ["See services", "Get a quote"]),
]


def _render(answer, ctx):
    if callable(answer):
        return answer(ctx)
    try:
        return answer.format(**ctx)
    except Exception:
        return answer


def respond(state, text, services, *, knowledge=None, logged_in_name="", logged_in_email=""):
    """Return dict: {messages, quick_replies, state, action, matched_knowledge_id, unanswered}."""
    state = dict(state or {})
    knowledge = knowledge or []
    t = _norm(text)
    out = {"messages": [], "quick_replies": [], "state": state, "action": None,
           "matched_knowledge_id": None, "unanswered": False}

    def finish(msgs, quick=None, action=None, knowledge_id=None, unanswered=False):
        out["messages"] = msgs if isinstance(msgs, list) else [msgs]
        out["quick_replies"] = quick or []
        out["action"] = action
        out["state"] = state
        out["matched_knowledge_id"] = knowledge_id
        out["unanswered"] = unanswered
        return out

    # Universal escapes -------------------------------------------------------
    if _has(t, RESTART):
        state.clear()
        return finish("No problem — cleared that. What would you like to do?",
                      ["See services", "Get a quote", "Talk to a human"])

    if _has(t, HUMAN):
        state["needs_human"] = True
        return finish(
            ["Sure — I've flagged this chat for {} and they'll jump in here as soon as they're "
             "around. ⏱️".format(_dev()),
             "In the meantime I can keep helping, or you can reach out on WhatsApp from the contact section."],
            ["See services", "Get a quote"])

    # Catalog not loaded yet (services not imported) — stay useful, hand off.
    if not services and not _has(t, GREETINGS) and not _has(t, THANKS):
        state.clear()
        state["needs_human"] = True
        return finish(
            "I'd love to help! Tell me what you'd like built — your goals and any deadline — "
            "and I'll pass the details straight to {}.".format(_dev()),
            ["Talk to a human"])

    # ---- ORDER FLOW (multi-step) -------------------------------------------
    if state.get("flow") == "order":
        step = state.get("step")

        if step == "choose_service":
            s = _match_service(text, services)
            if not s:
                return finish("Which service is it for? Tap one below 👇",
                              _service_titles(services))
            state["service"] = s["slug"]
            state["service_title"] = s["title"]
            state["step"] = "choose_tier"
            tiers = [p.get("tier", "") for p in (s.get("packages") or [])]
            return finish([_explain_service(s), "\nWhich package would you like?"],
                          tiers + ["Not sure — help me choose"])

        if step == "choose_tier":
            s = _find(services, state.get("service"))
            if not s:
                state["step"] = "choose_service"
                return finish("Let's pick the service first.", _service_titles(services))
            if "not sure" in t or "help me choose" in t:
                return finish("No worries! The **Standard** tier is the most popular — it's the "
                              "best balance of scope and price. Want to go with that, or tell me "
                              "your budget and I'll suggest one?",
                              [p.get("tier", "") for p in (s.get("packages") or [])])
            p = _match_tier(text, s)
            if not p:
                return finish("Tap the package you'd like 👇",
                              [pp.get("tier", "") for pp in (s.get("packages") or [])])
            state["tier"] = p.get("tier", "")
            state["price"] = p.get("price", 0)
            state["step"] = "requirements"
            return finish("Great choice — **{}** ({}). Tell me a bit about your project: goals, "
                          "any links/references, and your deadline.".format(state["tier"], _money(state["price"])),
                          [])

        if step == "requirements":
            state.setdefault("order", {})["requirements"] = text.strip()
            if logged_in_name and logged_in_email:
                state["order"]["name"] = logged_in_name
                state["order"]["email"] = logged_in_email
                state["step"] = "confirm"
                return _confirm_prompt(state)
            state["step"] = "name"
            return finish("Got it 📝 What's your name?", [])

        if step == "name":
            state.setdefault("order", {})["name"] = text.strip()[:120]
            state["step"] = "email"
            return finish("Thanks, {}! What's the best email to reach you and send the order "
                          "details to?".format(state["order"]["name"].split(" ")[0]), [])

        if step == "email":
            email = text.strip()
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                return finish("Hmm, that doesn't look like an email — mind sharing a valid one? "
                              "(e.g. you@example.com)", [])
            state.setdefault("order", {})["email"] = email[:200]
            state["step"] = "confirm"
            return _confirm_prompt(state)

        if step == "confirm":
            if t.startswith("y") or "confirm" in t or "place" in t or "yes" in t:
                order = state.get("order", {})
                action = {
                    "type": "create_order",
                    "service": state.get("service_title", ""),
                    "tier": state.get("tier", ""),
                    "price": state.get("price", 0),
                    "name": order.get("name", ""),
                    "email": order.get("email", ""),
                    "requirements": order.get("requirements", ""),
                }
                state.clear()
                return finish([], [], action)
            if t.startswith("n") or "change" in t or "edit" in t:
                state["step"] = "choose_service"
                return finish("No problem — let's redo it. Which service is it for?",
                              _service_titles(services))
            return _confirm_prompt(state)

    # ---- NOT IN A FLOW: intent routing -------------------------------------
    if _has(t, ORDER_WORDS) or t in ("get a quote", "get started"):
        svc = _match_service(text, services)
        state["flow"] = "order"
        if svc:
            state["service"] = svc["slug"]
            state["service_title"] = svc["title"]
            state["step"] = "choose_tier"
            tiers = [p.get("tier", "") for p in (svc.get("packages") or [])]
            return finish(["Awesome — let's set up your order for **{}**.".format(_short_title(svc["title"])),
                           _explain_service(svc), "\nWhich package would you like?"],
                          tiers + ["Not sure — help me choose"])
        state["step"] = "choose_service"
        return finish("Let's get you a quote! Which service is it for? 👇", _service_titles(services))

    if _has(t, GREETINGS) and len(t) <= 28:
        return finish(_greeting(logged_in_name), ["See services", "Get a quote", "Talk to a human"])

    if _has(t, THANKS):
        return finish("You're welcome! 🙌 Anything else I can help with?",
                      ["See services", "Get a quote"])

    # 1) Curated knowledge the developer taught the bot (highest priority).
    if knowledge:
        e, score = _best_entry(text, knowledge,
                               lambda x: [x.get("question", "")] +
                                         [k for k in re.split(r"[,\n;]+", x.get("keywords", "")) if k.strip()])
        if e and score >= 0.78:
            return finish(e.get("answer", "").strip() or _greeting(logged_in_name),
                          ["See services", "Get a quote", "Talk to a human"],
                          knowledge_id=e.get("id"))

    # 2) Built-in common-language Q&A (small talk, hours, payments, contact, …).
    #    A purely-social reply yields to a clear business intent in the same
    #    message (services / pricing / ordering), so chit-chat never buries a real
    #    question.
    e, score = _best_entry(text, BUILTIN_KB, lambda x: x[0])
    if e and score >= 0.8:
        social = e[0][0] in _SOCIAL_LEADS
        business = _has(t, SERVICE_WORDS) or _has(t, PRICE_WORDS) or _has(t, ORDER_WORDS)
        if not (social and business):
            ctx = _ctx()
            return finish(_render(e[1], ctx), e[2] or DEFAULT_QUICK)

    # 3) A clearly-named service → explain it.
    strong = _strong_service(text, services)
    if strong and not _has(t, SERVICE_WORDS):
        state["service"] = strong["slug"]
        state["service_title"] = strong["title"]
        return finish(_explain_service(strong),
                      ["Order " + _short_title(strong["title"]), "See other services", "Talk to a human"])

    # 4) General "show me services / pricing" intents.
    if _has(t, SERVICE_WORDS) or _has(t, PRICE_WORDS) or "other services" in t:
        return finish(_list_services_text(services),
                      _service_titles(services) + ["Get a quote"])

    # 5) A looser service match, when the user is clearly asking about cost.
    svc = _match_service(text, services)
    if svc and _has(t, PRICE_WORDS):
        state["service"] = svc["slug"]
        state["service_title"] = svc["title"]
        return finish(_explain_service(svc),
                      ["Order " + _short_title(svc["title"]), "See other services", "Talk to a human"])

    # Fallback — flag as unanswered so the developer can teach a reply later.
    return finish(
        "Good question! I'm not 100% sure on that one, but I don't want to guess. I can explain any "
        "service, share pricing, start your order — or loop in {} to answer you directly.".format(_dev()),
        ["See services", "Get a quote", "Talk to a human"],
        unanswered=True)


def _find(services, slug):
    for s in services:
        if s.get("slug") == slug:
            return s
    return None


def _confirm_prompt(state):
    o = state.get("order", {})
    summary = ("Here's your request:\n"
               "• **Service:** {}\n• **Package:** {} ({})\n• **Name:** {}\n• **Email:** {}\n"
               "• **Details:** {}\n\nShall I place it? (yes / no)").format(
        state.get("service_title", ""), state.get("tier", ""), _money(state.get("price", 0)),
        o.get("name", ""), o.get("email", ""),
        (o.get("requirements", "") or "")[:200] + ("…" if len(o.get("requirements", "") or "") > 200 else ""))
    return {"messages": [summary], "quick_replies": ["Yes, place it", "No, change something"],
            "state": state, "action": None, "matched_knowledge_id": None, "unanswered": False}
