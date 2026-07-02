/* Checkout modal — order summary + customer form → places the order via the API
   (falls back to local + Formspree), then shows a success screen with the order
   ID, a WhatsApp confirm link and a "track this order" jump. Port of the checkout
   flow in app.js. */
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Icon } from "../../lib/icons";
import { CONFIG } from "../../lib/config";
import { money, validEmail, whatsappLink } from "../../lib/format";
import { placeOrder, placeOrderViaApi, orderSummaryText } from "../../lib/cart";
import type { Customer, LocalOrder } from "../../lib/cart";
import { API } from "../../lib/api";
import type { ApiError, PaymentConfig } from "../../lib/types";
import { useCart } from "../../context/CartContext";
import { useUI } from "../../context/UIContext";
import { useToast } from "../../context/ToastContext";
import { ManualPayDetails, ProofUpload, manualMethodKey } from "./ManualPayment";

// The dropdown option that means "pay online by card now" (Safepay hosted checkout).
const CARD_LABEL = CONFIG.payments.find((p) => p.id === "card")?.label ?? "Credit / Debit card";

function PaymentOptions({ safepayOn }: { safepayOn: boolean }) {
  // With online card payment enabled, regroup so buyers can't confuse the instant
  // option with the manual ones: card first under "Pay online now", everything
  // else clearly labelled as a manual transfer (details sent after the order).
  // Option VALUES stay the original labels — the backend + pay-now logic match on them.
  const groups: Record<string, { value: string; text: string }[]> = {};
  CONFIG.payments.forEach((p) => {
    const isCard = p.id === "card";
    const group = safepayOn
      ? (isCard ? "Pay online now — instant" : "Manual transfer — I'll send details after the order")
      : p.group;
    (groups[group] = groups[group] || []).push({
      value: p.label,
      text: safepayOn && isCard ? p.label + " (pay now, secure)" : p.label,
    });
  });
  const names = Object.keys(groups);
  if (safepayOn) names.sort((a) => (a.startsWith("Pay online") ? -1 : 1));
  return (
    <>
      <option value="">Select how you'd like to pay…</option>
      {names.map((g) => (
        <optgroup key={g} label={g}>
          {groups[g].map((p) => (
            <option key={p.value} value={p.value}>
              {p.text}
            </option>
          ))}
        </optgroup>
      ))}
    </>
  );
}

export function CheckoutModal() {
  const { items, total, refresh } = useCart();
  const { isOpen, close, openTrack } = useUI();
  const { toast } = useToast();
  const open = isOpen("checkout");

  const [order, setOrder] = useState<LocalOrder | null>(null);
  const [status, setStatus] = useState<{ type: string; msg: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [method, setMethod] = useState("");
  const [gated, setGated] = useState(false);
  const [payCfg, setPayCfg] = useState<PaymentConfig>({ stripe_enabled: false });
  // Embedded (in-site) card checkout: Safepay's payment app in an iframe — the
  // buyer never leaves the site. Completion is detected by polling /verify.
  const [embed, setEmbed] = useState<{ url: string; pid: string; hosted: string } | null>(null);
  const [paid, setPaid] = useState(false);

  // Reset to the form whenever the modal re-opens, and learn whether online card
  // checkout (Safepay) is available so "Credit / Debit card" can charge instantly.
  useEffect(() => {
    if (open) {
      setOrder(null);
      setStatus(null);
      setBusy(false);
      setMethod("");
      setGated(false);
      setEmbed(null);
      setPaid(false);
      API.get<PaymentConfig>("/api/payments/config")
        .then(setPayCfg)
        .catch(() => setPayCfg({ stripe_enabled: false }));
    }
  }, [open]);

  // While the embedded checkout is showing, poll the server until the payment is
  // verified (the server re-checks with Safepay — the browser can't fake this).
  useEffect(() => {
    if (!embed || paid) return;
    const t = window.setInterval(() => {
      API.get<{ paid?: boolean }>("/api/payments/safepay/verify/" + encodeURIComponent(embed.pid))
        .then((r) => {
          if (r && r.paid) {
            setPaid(true);
            setEmbed(null);
            toast("Payment received for " + embed.pid + " ✅", "check");
          }
        })
        .catch(() => {});
    }, 3500);
    return () => window.clearInterval(t);
  }, [embed, paid, toast]);

  const payNow = !!payCfg.safepay_enabled && method === CARD_LABEL;

  const summary = useMemo(() => items, [items]);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = e.currentTarget;
    if ((f.elements.namedItem("_gotcha") as HTMLInputElement)?.value) return; // honeypot
    const name = (f.elements.namedItem("name") as HTMLInputElement).value.trim();
    const email = (f.elements.namedItem("email") as HTMLInputElement).value.trim();
    if (!name || !validEmail(email)) {
      setStatus({ type: "err", msg: "Please add your name and a valid email." });
      return;
    }
    const customer: Customer = {
      name,
      email,
      whatsapp: (f.elements.namedItem("whatsapp") as HTMLInputElement).value.trim(),
      notes: (f.elements.namedItem("notes") as HTMLTextAreaElement).value.trim(),
      payment_method: (f.elements.namedItem("payment") as HTMLSelectElement).value,
    };
    setBusy(true);
    setStatus({ type: "ok", msg: "Placing your order…" });
    try {
      const o = await placeOrderViaApi(customer);
      // Pay-now: if they chose card and Safepay is on, hand off to the secure hosted
      // checkout immediately (buyer pays on getsafepay.com, then returns to /store).
      if (payCfg.safepay_enabled && customer.payment_method === CARD_LABEL) {
        setStatus({ type: "ok", msg: "Opening secure card checkout…" });
        try {
          const r = await API.post<{ url?: string; embed_url?: string }>(
            "/api/payments/safepay/checkout/" + encodeURIComponent(o.id) + "?return_to=%2Fstore",
          );
          // Preferred: embedded — pay right here without leaving the site.
          if (r && r.embed_url) {
            setOrder(o);
            setEmbed({ url: r.embed_url, pid: o.id, hosted: r.url || "" });
            setBusy(false);
            setStatus(null);
            return;
          }
          if (r && r.url) {
            window.location.href = r.url;
            return;
          }
        } catch (err) {
          // Surface the gateway's reason (helps during setup) — the order is still
          // saved, so fall through to the order-received screen afterwards.
          const msg = (err as { message?: string })?.message || "Card checkout couldn't start.";
          toast(msg, "doc");
        }
      }
      setOrder(o);
    } catch (err) {
      const status = (err as ApiError)?.status;
      // Verification gate (must be a signed-in, verified account) or a rejected
      // email — don't fake a local order; guide the buyer to the client area.
      if (status === 401 || status === 403 || status === 400) {
        setGated(status !== 400);
        setStatus({ type: "err", msg: (err as ApiError).message || "Please sign in and verify your email to order." });
        setBusy(false);
        return;
      }
      // Genuine network/other failure → keep the resilient local + WhatsApp fallback.
      setOrder(placeOrder(customer));
    } finally {
      setBusy(false);
      refresh();
    }
  }

  const title = embed ? "Secure card payment" : paid ? "Payment received" : order ? "Order received" : "Checkout";

  return (
    <div
      className={`modal${open ? " open" : ""}`}
      id="checkoutModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="checkoutTitle"
      aria-hidden={!open}
    >
      <div className="modal-head">
        <h3 id="checkoutTitle">{title}</h3>
        <button className="close-btn" aria-label="Close checkout" onClick={() => close("checkout")}>
          <Icon name="close" size={20} />
        </button>
      </div>
      <div className="modal-body" id="checkoutBody">
        {embed ? (
          <div className="embed-pay">
            <iframe
              className="embed-pay-frame"
              src={embed.url}
              title="Safepay secure card payment"
              allow="payment"
            />
            <p className="form-note" style={{ textAlign: "center" }}>
              🔒 Card details are entered in Safepay's secure form — they never touch this site.
              Order <b>{embed.pid}</b> is saved either way.
            </p>
            <div className="pay-row" style={{ justifyContent: "center" }}>
              {embed.hosted && (
                <a className="btn btn-outline btn-sm" href={embed.hosted}>
                  Having trouble? Open the full payment page
                </a>
              )}
              <button className="btn btn-ghost btn-sm" onClick={() => setEmbed(null)}>
                Cancel payment
              </button>
            </div>
          </div>
        ) : order ? (
          <Success order={order} paid={paid} onTrack={() => { close("checkout"); openTrack(order.id); }} onDone={() => close("checkout")} />
        ) : (
          <>
            <div className="order-summary">
              {summary.map((i) => (
                <div className="row" key={i.key}>
                  <span>{i.service} · {i.tier} ×{i.qty}</span>
                  <span>{money(i.price * i.qty)}</span>
                </div>
              ))}
              <div className="row total">
                <span>Total</span>
                <span>{money(total)}</span>
              </div>
            </div>
            <form className="form" onSubmit={onSubmit} noValidate>
              <div className="two">
                <div className="field">
                  <label htmlFor="co-name">Name <span className="req">*</span></label>
                  <input className="input" id="co-name" name="name" required autoComplete="name" />
                </div>
                <div className="field">
                  <label htmlFor="co-email">Email <span className="req">*</span></label>
                  <input className="input" id="co-email" name="email" type="email" required autoComplete="email" />
                </div>
              </div>
              <div className="two">
                <div className="field">
                  <label htmlFor="co-wa">WhatsApp <span style={{ color: "var(--muted)", fontWeight: 400 }}>(optional)</span></label>
                  <input className="input" id="co-wa" name="whatsapp" autoComplete="tel" />
                </div>
                <div className="field">
                  <label htmlFor="co-pay">
                    {payCfg.safepay_enabled ? "Payment method" : "Preferred payment method"}
                  </label>
                  <select
                    className="select"
                    id="co-pay"
                    name="payment"
                    value={method}
                    onChange={(e) => setMethod(e.target.value)}
                  >
                    <PaymentOptions safepayOn={!!payCfg.safepay_enabled} />
                  </select>
                </div>
              </div>
              {manualMethodKey(method) && (
                <div className="manual-pay-inline">
                  <ManualPayDetails methodLabel={method} />
                  <p className="form-note">
                    After placing the order you'll upload your payment screenshot here — I confirm it and start.
                  </p>
                </div>
              )}
              <div className="field">
                <label htmlFor="co-notes">Project details</label>
                <textarea className="textarea" id="co-notes" name="notes" placeholder="Anything I should know — links, references, deadlines…" />
              </div>
              <input className="hp" tabIndex={-1} autoComplete="off" name="_gotcha" aria-hidden="true" />
              {status && <div className={`form-status show ${status.type}`}>{status.msg}</div>}
              {gated && (
                <p className="form-note" style={{ marginTop: ".4rem" }}>
                  <Link to="/app" style={{ color: "var(--accent-2)", fontWeight: 600 }}>
                    Sign in or create a verified account →
                  </Link>{" "}
                  then come back and place your order.
                </p>
              )}
              <button className="btn btn-primary btn-block" type="submit" disabled={busy}>
                <Icon name={payNow ? "arrow" : "check"} size={18} />{" "}
                {payNow ? `Pay ${money(total)} securely` : "Place order"}
              </button>
              <p className="form-note">
                {payNow
                  ? `You'll be redirected to Safepay's secure checkout to pay by card${
                      payCfg.fx_rate
                        ? ` — charged as ${payCfg.safepay_currency || "PKR"} ${Math.round(total * payCfg.fx_rate).toLocaleString()} (today's rate)`
                        : ""
                    }. Your order is saved either way.`
                  : "By placing this order you're sending me a request — I'll confirm the details and payment with you before starting."}
              </p>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

function Success({ order, paid = false, onTrack, onDone }: { order: LocalOrder; paid?: boolean; onTrack: () => void; onDone: () => void }) {
  const waLink = whatsappLink(orderSummaryText(order));
  const manual = !paid && manualMethodKey(order.payment_method || "");
  const emailNote = CONFIG.formspreeId
    ? "A copy has been emailed to me — I'll reply soon."
    : "Tap below to send me the order on WhatsApp so I can confirm.";
  return (
    <>
      <div style={{ textAlign: "center" }}>
        <div className="success-icon">
          <Icon name="check" />
        </div>
        <h3>{paid ? "Payment received — thank you!" : "Thank you!"}</h3>
        <p className="lead" style={{ margin: ".5rem auto 0" }}>
          {paid ? "Your payment is confirmed and your project is queued. Track it anytime with your order ID." : `Your order request is in. ${emailNote}`}
        </p>
        <div className="order-id-box">
          <small>Your order ID — save it to track</small>
          <div className="id">{order.id}</div>
        </div>
        {order.payment_method && !manual && !paid && (
          <p className="form-note" style={{ margin: ".2rem auto 0" }}>
            Payment via <b>{order.payment_method}</b> — I'll send you the details to complete it.
          </p>
        )}
      </div>
      {manual && (
        <div className="manual-pay-inline" style={{ marginTop: ".9rem" }}>
          <h4 style={{ margin: "0 0 .5rem" }}>Complete your payment</h4>
          <ManualPayDetails methodLabel={order.payment_method} />
          <ProofUpload orderId={order.id} />
        </div>
      )}
      <a className="btn btn-primary btn-block" href={waLink} target="_blank" rel="noopener" style={manual ? { marginTop: ".8rem" } : undefined}>
        <Icon name="whatsapp" size={18} /> Confirm on WhatsApp
      </a>
      <button className="btn btn-ghost btn-block mt-2" onClick={onTrack}>
        <Icon name="doc" size={18} /> Track this order
      </button>
      <button className="btn btn-outline btn-block mt-2" onClick={onDone}>
        Done
      </button>
    </>
  );
}
