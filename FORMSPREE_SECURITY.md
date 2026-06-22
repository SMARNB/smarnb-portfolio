# Formspree — Spam & Scam Prevention

This covers (1) what's already wired in the code, and (2) the **manual steps you
must do in the Formspree dashboard** (I can't click through their UI for you).

Your form endpoint: `https://formspree.io/f/xwvdkyve`

---

## 1. Already implemented in code ✅

**Honeypot field.** Both the contact form and the checkout form include a hidden
input named **`_gotcha`**:

```html
<input class="hp" tabindex="-1" autocomplete="off" name="_gotcha" aria-hidden="true">
```

- It's hidden from humans via CSS (`.hp { position:absolute; left:-9999px; … }` — off-screen, not focusable).
- Real users leave it empty; bots that auto-fill every field will fill it.
- We **reject the submission client-side** if it's non-empty, **and** we send the
  value to Formspree, which **also drops it server-side** because `_gotcha` is
  Formspree's standard honeypot name. Defense in depth.

That alone stops the large majority of dumb bots. The steps below stop the rest.

---

## 2. Manual steps in the Formspree dashboard

Log in at <https://formspree.io>, open the form (`xwvdkyve`). Menu names move
around between plan tiers; if you don't see an option, it's usually under
**Form → Settings** or **Form → Rules/Plugins**, and a few items need a paid
plan (Formspree notes this inline).

### A. Turn on the built-in spam filters first
**Form → Settings → Spam filtering**
- Enable **reCAPTCHA** (or hCaptcha) — biggest single win against bots.
- Keep **Akismet** spam filtering **on** (default).
- Confirm **honeypot** detection is **on** (it pairs with the `_gotcha` field above).

### B. Blocklists — block specific scam senders / domains / IPs
**Form → Settings → Allowlist / Blocklist** (a.k.a. "Blocked emails")
1. In **Blocklist**, add the exact scam **email addresses** (one per line), e.g.
   `scammer@example.com`.
2. To block a whole **domain**, add a wildcard: `*@baddomain.com`.
3. To block by **IP**: open a spammy submission in **Form → Submissions**, copy the
   sender **IP** shown in its metadata, then add it under **Blocked IPs**
   (IP/domain blocking is a paid-tier feature on Formspree — upgrade if the option
   is greyed out).
4. Save. Future matching submissions are auto-rejected and never emailed to you.

> Tip: build the blocklist reactively — each time a scam gets through, open it,
> copy the email/domain/IP, and add it here.

### C. Keyword rules — auto-flag spam by content
**Form → Settings → Spam filtering → Custom rules** (paid tier)
1. Add a rule: **If `message` contains any of** → list scam keywords/phrases,
   e.g. `crypto, SEO services, guaranteed ranking, gift card, wire transfer,
   bitcoin, telegram @, loan offer, investment opportunity`.
2. Set the action to **Mark as spam** (quarantine — it won't hit your inbox).
3. Add a second rule for obvious link-spam: **If `message` contains** `http://`
   **or** `https://` **and** `message` length `<` 120 → **Mark as spam**
   (short messages that are mostly a link are almost always spam).

If your plan doesn't expose custom rules, replicate this with an inbox filter in
Gmail (see E).

### D. Dynamic routing — send risky/link-containing messages to a review inbox
**Form → Settings → Email / Routing** (Formspree "Rules" / routing, paid tier)
1. First set a **secondary review address** (e.g. create
   `aliraza.review@gmail.com` or a Gmail **+alias** like
   `shahjee975+review@gmail.com` — aliases need no new account).
2. Add a routing rule: **If `message` contains** `http://` **or** `https://`
   **→ route to** `shahjee975+review@gmail.com` (instead of your primary inbox).
3. Optional: route by `budget` — e.g. send "Under $250" inquiries to the review
   alias and `$1,000+` straight to your primary inbox.
4. Keep clean submissions routing to your **primary** `shahjee975@gmail.com`.

### E. No paid plan? Do C & D in Gmail instead (free) 🆓
Formspree always emails you, so you can filter on arrival:
1. Gmail → **Settings → Filters and Blocked Addresses → Create a new filter**.
2. **Has the words:** `from:(formspree) (crypto OR "gift card" OR "guaranteed ranking" OR bitcoin OR "wire transfer")`
   → **Create filter** → **Skip the Inbox + Apply label "Spam-review"**.
3. Second filter: `from:(formspree) (http OR https)` → apply label **"Review"**
   (and optionally **Forward** to your review alias). This is the free equivalent
   of dynamic routing.
4. Block a sender entirely: open their email → **⋮ → Block "sender"**.

---

## 3. Recommended baseline (do these five)
1. ✅ Honeypot — **done in code**.
2. Enable **reCAPTCHA** + keep **Akismet** on (§A).
3. Build the **blocklist** reactively (§B).
4. **Keyword → mark as spam** rule, or the Gmail filter (§C/E).
5. **Route link-containing messages** to a review alias (§D/E).

With 1–2 alone you'll stop ~95% of spam; 3–5 handle the targeted scam stuff.
