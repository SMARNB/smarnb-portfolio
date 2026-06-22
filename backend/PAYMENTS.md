# Payments — how it works now & how to go live

## What's built now ✅
- At **checkout** the client picks a **payment method** (JazzCash, Easypaisa, bank
  transfer, JazzCash *Pay Later / Yeylo*, BaadMay, Stripe card, PayPal, Wise,
  crypto). The list is editable in `assets/js/config.js → payments`.
- The choice is **saved on the order** (`payment_method`) and shown in the client
  dashboard, the developer dashboard, and the order email.
- The developer marks **`payment_status`** = `unpaid → paid → refunded` from the
  admin dashboard.
- A **Payments** section on the homepage lists accepted methods as a trust signal.

> So today the flow is: client orders + picks a method → you get notified → **you
> send them the payment link/details** (JazzCash invoice, Stripe link, bank info)
> → mark the order **Paid**. No money is processed on the site yet, which is why it
> stays fully static-safe.

## Why it's not auto-charging yet (the honest part)
Every real gateway needs **your merchant account + secret API keys**, and the
Pakistani ones need a **registered business**:

| Method | What you need to go live |
|---|---|
| **Stripe** (cards, intl) | Stripe account → API keys. Easiest to automate. Works worldwide; card payments from Pakistan need a Stripe-supported entity (e.g. a US/UK Stripe, Payoneer, or Wise business). |
| **JazzCash** | JazzCash **Business** merchant account → Merchant ID, Password, Integrity Salt. Sandbox available. |
| **JazzCash Pay Later (Yeylo)** | Enabled **inside your JazzCash merchant** as a BNPL option (Yeylo is the BNPL rail) — no separate integration, it appears on the JazzCash checkout. |
| **BaadMay** | Apply as a **BaadMay merchant**; they provide an integration/checkout. BNPL approval is per-merchant. |
| **Easypaisa** | Easypaisa merchant account → store/API credentials. |
| **PayPal / Wise / Crypto** | Usually handled as a **manual link / address** you send — no integration needed. |

## Recommended path: wire Stripe first (I can do this for you)
Stripe is the one I can fully automate. When you're ready:

1. Create a Stripe account → **Developers → API keys** → copy the **Secret key**
   (`sk_test_…` for testing).
2. Add to `backend/.env`:
   ```
   STRIPE_SECRET_KEY=sk_test_xxx
   STRIPE_SUCCESS_URL=https://yourdomain/app.html
   STRIPE_CANCEL_URL=https://yourdomain/#pricing
   ```
3. Tell me, and I'll add (it's ~50 lines, already scoped):
   - `POST /api/payments/stripe/checkout/{order_id}` → creates a Stripe **Checkout
     Session** from the order's line items and returns the URL.
   - A **"Pay now"** button on the client dashboard for `unpaid` orders.
   - A Stripe **webhook** (`/api/payments/stripe/webhook`) that flips
     `payment_status → paid` automatically when Stripe confirms.
   - `pip install stripe` added to `requirements.txt`.

That gives you real, automatic card payments end-to-end. The local methods
(JazzCash/BaadMay) can then be added the same way once your merchant accounts are
approved — each just needs its keys dropped into `.env`.
