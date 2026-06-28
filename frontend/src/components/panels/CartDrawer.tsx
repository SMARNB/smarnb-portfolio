/* Cart drawer — line items with qty steppers, subtotal and checkout. Port of
   renderCart() in app.js. Always mounted; the `.open` class drives the CSS slide. */
import { Icon } from "../../lib/icons";
import { money } from "../../lib/format";
import { useCart } from "../../context/CartContext";
import { useUI } from "../../context/UIContext";

export function CartDrawer() {
  const { items, total, count, remove, setQty } = useCart();
  const { isOpen, close, openCheckout } = useUI();
  const open = isOpen("cart");

  return (
    <aside
      className={`drawer${open ? " open" : ""}`}
      id="cartDrawer"
      role="dialog"
      aria-modal="true"
      aria-labelledby="cartTitle"
      aria-hidden={!open}
    >
      <div className="drawer-head">
        <h3 id="cartTitle">Your cart {count > 0 ? `(${count})` : ""}</h3>
        <button className="close-btn" aria-label="Close cart" onClick={() => close("cart")}>
          <Icon name="close" size={20} />
        </button>
      </div>

      <div className="drawer-body" id="cartBody">
        {items.length === 0 ? (
          <div className="empty-state">
            <Icon name="cartBig" />
            <p>Your cart is empty.</p>
            <p style={{ fontSize: ".85rem" }}>Browse the packages and add a service to get started.</p>
          </div>
        ) : (
          items.map((i) => (
            <div className="cart-line" key={i.key}>
              <div>
                <h4>{i.service}</h4>
                <div className="meta">
                  {i.tier} · {i.delivery}
                </div>
                <div className="qty" style={{ marginTop: ".6rem" }}>
                  <button aria-label="Decrease quantity" onClick={() => setQty(i.key, i.qty - 1)}>
                    <Icon name="minus" size={16} />
                  </button>
                  <span>{i.qty}</span>
                  <button aria-label="Increase quantity" onClick={() => setQty(i.key, i.qty + 1)}>
                    <Icon name="plus" size={16} />
                  </button>
                </div>
              </div>
              <div style={{ textAlign: "right", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                <span className="price">{money(i.price * i.qty)}</span>
                <button className="remove" onClick={() => remove(i.key)}>
                  Remove
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {items.length > 0 && (
        <div className="drawer-foot" id="cartFoot">
          <div className="cart-foot-row">
            <span>Subtotal</span>
            <span className="total">{money(total)}</span>
          </div>
          <p className="form-note">Final price confirmed before any payment. No charge until you approve.</p>
          <button className="btn btn-primary btn-block" onClick={openCheckout}>
            <Icon name="arrow" size={18} /> Checkout
          </button>
          <button className="btn btn-ghost btn-block" onClick={() => close("cart")}>
            Keep browsing
          </button>
        </div>
      )}
    </aside>
  );
}
