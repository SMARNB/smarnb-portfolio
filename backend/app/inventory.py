"""Inventory — a small, reusable stock module (items + an auditable move ledger).

Design goals (per the owner: "create it in a way I could reuse it for other
softwares"): no coupling to the rest of the app except one hook —
``consume_for_order(db, order)`` called when an order's payment lands. Items
whose ``stock`` is None are catalogued but untracked (services are effectively
unlimited); numeric stock is decremented per paid order line whose title matches
the item's name (case-insensitive), with low-stock alerts to the owner.

Everything commits its own work and never raises into the payment path.
"""
from . import config, models


def serialize_item(item: models.InventoryItem) -> dict:
    low = (item.stock is not None and item.stock <= (item.low_stock_threshold or 0))
    return {
        "id": item.id, "sku": item.sku, "name": item.name, "kind": item.kind,
        "stock": item.stock, "low_stock_threshold": item.low_stock_threshold,
        "tracked": item.stock is not None, "low": low, "active": item.active,
        "notes": item.notes or "", "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def serialize_move(m: models.StockMove) -> dict:
    return {"id": m.id, "delta": m.delta, "reason": m.reason, "ref": m.ref,
            "note": m.note, "created_at": m.created_at}


def list_items(db, include_inactive: bool = True):
    q = db.query(models.InventoryItem)
    if not include_inactive:
        q = q.filter(models.InventoryItem.active.is_(True))
    return q.order_by(models.InventoryItem.name).all()


def get_item(db, item_id: int):
    return db.get(models.InventoryItem, item_id)


def get_item_by_sku(db, sku: str):
    return (db.query(models.InventoryItem)
            .filter(models.InventoryItem.sku == (sku or "").strip())
            .first())


def create_item(db, *, sku: str, name: str, kind: str = "product",
                stock=None, low_stock_threshold: int = 1, notes: str = ""):
    item = models.InventoryItem(
        sku=(sku or "").strip(), name=(name or "").strip(), kind=kind or "product",
        stock=stock, low_stock_threshold=low_stock_threshold, notes=notes or "")
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(db, item, **fields):
    for key in ("sku", "name", "kind", "low_stock_threshold", "active", "notes"):
        if key in fields and fields[key] is not None:
            setattr(item, key, fields[key])
    # `stock` may legitimately be set to None (stop tracking) — use a sentinel.
    if "stock" in fields:
        item.stock = fields["stock"]
    db.commit()
    db.refresh(item)
    return item


def adjust_stock(db, item, delta: int, reason: str = "manual",
                 ref: str = "", note: str = ""):
    """Apply a signed stock change and record it in the ledger. Untracked items
    (stock None) record the move but keep stock None."""
    if item.stock is not None:
        item.stock = max(0, (item.stock or 0) + int(delta))
    db.add(models.StockMove(item_id=item.id, delta=int(delta),
                            reason=reason[:30], ref=(ref or "")[:60],
                            note=(note or "")[:300]))
    db.commit()
    db.refresh(item)
    return item


def moves_for(db, item, limit: int = 50):
    return (db.query(models.StockMove)
            .filter(models.StockMove.item_id == item.id)
            .order_by(models.StockMove.created_at.desc(), models.StockMove.id.desc())
            .limit(limit).all())


def _alert_low_stock(db, item):
    """Best-effort owner alerts (WhatsApp ping + email); never raises."""
    text = "📦 LOW STOCK: %s — %s left (threshold %s)." % (
        item.name or item.sku, item.stock, item.low_stock_threshold)
    try:
        from . import notify
        notify.notify_owner(text)
    except Exception:
        pass
    try:
        from . import emailer
        emailer.send(db, config.OWNER_EMAIL, "Low stock: " + (item.name or item.sku),
                     "<p>%s</p><p>Restock it from /admin → Inventory.</p>" % text,
                     kind="other")
    except Exception:
        pass


def consume_for_order(db, order) -> list:
    """Decrement tracked items matching the paid order's line titles. Returns the
    list of affected items. Wrapped so it can never break the payment flow."""
    touched = []
    items = {}
    for line in (order.items or []):
        title = ((line or {}).get("service") or "").strip().lower()
        if title:
            items[title] = line
    if not items:
        return touched
    try:
        for inv in list_items(db, include_inactive=False):
            if inv.stock is None:
                continue
            line = items.get((inv.name or "").strip().lower())
            if not line:
                continue
            qty = int(line.get("qty") or 1)
            adjust_stock(db, inv, -qty, reason="order_paid", ref=order.public_id,
                         note=(line.get("tier") or ""))
            touched.append(inv)
            if inv.stock is not None and inv.stock <= (inv.low_stock_threshold or 0):
                _alert_low_stock(db, inv)
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
    return touched
