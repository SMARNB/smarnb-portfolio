/* Reactive cart state on top of lib/cart.ts. Header badge, cart drawer and the
   store all read from here; mutations re-render every consumer. */
import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import * as Cart from "../lib/cart";
import type { CartItem } from "../lib/cart";

interface CartCtx {
  items: CartItem[];
  count: number;
  total: number;
  add: (item: Omit<CartItem, "key" | "qty">) => void;
  remove: (key: string) => void;
  setQty: (key: string, qty: number) => void;
  clear: () => void;
  refresh: () => void;
}
const Ctx = createContext<CartCtx | null>(null);

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>(() => Cart.getCart());

  const add = useCallback((item: Omit<CartItem, "key" | "qty">) => setItems(Cart.addItem(item)), []);
  const remove = useCallback((key: string) => setItems(Cart.removeItem(key)), []);
  const setQty = useCallback((key: string, qty: number) => setItems(Cart.setQty(key, qty)), []);
  const clear = useCallback(() => setItems(Cart.clearCart()), []);
  const refresh = useCallback(() => setItems(Cart.getCart()), []);

  const value = useMemo<CartCtx>(
    () => ({
      items,
      count: Cart.cartCount(items),
      total: Cart.cartTotal(items),
      add,
      remove,
      setQty,
      clear,
      refresh,
    }),
    [items, add, remove, setQty, clear, refresh],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useCart(): CartCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useCart must be used within CartProvider");
  return ctx;
}
