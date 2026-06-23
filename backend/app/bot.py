"""Rule-based chat assistant.

No external API, no keys, no data leaves the server. It reads the live services
catalog from the database and can: greet, explain services & packages, gather a
client's requirements, and start an order — or hand off to the developer.

`respond()` is a pure function: given the conversation state, the latest visitor
message and the services catalog, it returns the bot's reply(s), suggested quick
replies, the next state, and an optional action (e.g. create an order). The router
applies the action and persists the state.
"""
import re

from . import config

GREETINGS = ("hi", "hello", "hey", "yo", "salam", "assalam", "asalam", "hola", "start")
THANKS = ("thanks", "thank you", "thankyou", "thx", "appreciate")
HUMAN = ("human", "real person", "agent", "talk to ali", "talk to you", "speak to",
         "speak with", "contact you", "call you", "live chat", "representative")
ORDER_WORDS = ("order", "buy", "purchase", "hire", "book", "get started", "place an order",
               "i want", "i need", "start a project", "checkout")
SERVICE_WORDS = ("service", "services", "offer", "what do you do", "what can you", "help with",
                 "menu", "options", "catalog")
PRICE_WORDS = ("price", "pricing", "cost", "how much", "rate", "rates", "budget", "quote", "package")
RESTART = ("cancel", "restart", "start over", "nevermind", "never mind", "stop")


def _dev():
    return config.ADMIN_NAME or "the developer"


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _has(text, words):
    return any(w in text for w in words)


def _money(n):
    try:
        return (config.CURRENCY or "$") + "{:,.0f}".format(float(n))
    except Exception:
        return (config.CURRENCY or "$") + str(n)


def _short_title(title):
    """Mirror the site's shortened service labels so quick-reply buttons match."""
    t = title or ""
    t = re.sub(r" in Python$", "", t)
    t = re.sub(r"^Full-Stack ", "", t)
    t = re.sub(r" for SaaS & Admin Dashboards", "", t)
    t = re.sub(r" for OCR & Data Scraping", "", t)
    t = re.sub(r"^Premium Commercial ", "", t)
    return t.strip()


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
        # token overlap (ignore tiny words)
        toks = {w for w in re.split(r"[^a-z0-9]+", t) if len(w) > 2}
        cand = set(re.split(r"[^a-z0-9]+", title + " " + short + " " + " ".join(s.get("tags") or [])))
        score += len(toks & {_norm(c) for c in cand if c})
        if score > best_score:
            best, best_score = s, score
    return best if best_score >= 2 else None


def _match_tier(text, service):
    t = _norm(text)
    for p in service.get("packages") or []:
        if _norm(p.get("tier", "")) and _norm(p.get("tier", "")) in t:
            return p
    # also accept generic words
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


def _greeting():
    return ("Hi! 👋 I'm {}'s assistant. I can explain the services, share pricing, "
            "and even start your order. What are you looking to build?").format(_dev())


def respond(state, text, services, *, logged_in_name="", logged_in_email=""):
    """Return dict: {messages:[str], quick_replies:[str], state:dict, action:dict|None}."""
    state = dict(state or {})
    t = _norm(text)
    out = {"messages": [], "quick_replies": [], "state": state, "action": None}

    def finish(msgs, quick=None, action=None):
        out["messages"] = msgs if isinstance(msgs, list) else [msgs]
        out["quick_replies"] = quick or []
        out["action"] = action
        out["state"] = state
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
                # reset flow; router appends the confirmation w/ the new order id
                state.clear()
                return finish([], [], action)
            if t.startswith("n") or "change" in t or "edit" in t:
                state["step"] = "choose_service"
                return finish("No problem — let's redo it. Which service is it for?",
                              _service_titles(services))
            return _confirm_prompt(state)

    # ---- NOT IN A FLOW: intent routing -------------------------------------
    # A direct service mention always wins (e.g. clicked a service button).
    svc = _match_service(text, services)

    if _has(t, ORDER_WORDS) or t in ("get a quote", "get started"):
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

    if _has(t, GREETINGS) and len(t) <= 24:
        return finish(_greeting(), ["See services", "Get a quote", "Talk to a human"])

    if _has(t, THANKS):
        return finish("You're welcome! 🙌 Anything else I can help with?",
                      ["See services", "Get a quote"])

    if svc and (_has(t, PRICE_WORDS) or True) and not _has(t, SERVICE_WORDS):
        state["service"] = svc["slug"]
        state["service_title"] = svc["title"]
        return finish(_explain_service(svc),
                      ["Order " + _short_title(svc["title"]), "See other services", "Talk to a human"])

    if _has(t, SERVICE_WORDS) or _has(t, PRICE_WORDS) or "other services" in t:
        return finish(_list_services_text(services),
                      _service_titles(services) + ["Get a quote"])

    # Fallback
    return finish(
        "I can explain any service, share pricing, or start your order. "
        "Want me to list what {} offers?".format(_dev()),
        ["See services", "Get a quote", "Talk to a human"])


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
            "state": state, "action": None}
