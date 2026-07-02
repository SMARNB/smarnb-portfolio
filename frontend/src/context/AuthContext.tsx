/* Auth/session context — wraps the bearer-JWT API client. Token + user live in
   localStorage (alira_token / alira_user) exactly as before. */
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { API } from "../lib/api";
import type { Token, User } from "../lib/types";

interface AuthCtx {
  user: User | null;
  ready: boolean; // becomes true once the initial /me check resolves
  login: (d: { email: string; password: string; totp_code?: string }) => Promise<Token>;
  register: (d: { email: string; password: string; name?: string; whatsapp?: string }) => Promise<Token>;
  logout: () => void;
  setUser: (u: User | null) => void;
}
const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<User | null>(() => API.getUser());
  const [ready, setReady] = useState(false);

  // Revalidate the stored token on mount so a stale session is cleared cleanly.
  useEffect(() => {
    if (!API.isAuthed()) {
      setReady(true);
      return;
    }
    let cancelled = false;
    API.me()
      .then((me) => {
        if (cancelled) return;
        API.setUser(me);
        setUserState(me);
      })
      .catch(() => {
        if (cancelled) return;
        API.logout();
        setUserState(null);
      })
      .finally(() => {
        if (!cancelled) setReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (d: { email: string; password: string; totp_code?: string }) => {
    const res = await API.login(d);
    if (res.user) setUserState(res.user); // absent when the server asks for a 2FA code
    return res;
  }, []);

  const register = useCallback(
    async (d: { email: string; password: string; name?: string; whatsapp?: string }) => {
      const res = await API.register(d);
      setUserState(res.user);
      return res;
    },
    [],
  );

  const logout = useCallback(() => {
    API.logout();
    setUserState(null);
  }, []);

  const setUser = useCallback((u: User | null) => {
    API.setUser(u);
    setUserState(u);
  }, []);

  return (
    <Ctx.Provider value={{ user, ready, login, register, logout, setUser }}>{children}</Ctx.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
