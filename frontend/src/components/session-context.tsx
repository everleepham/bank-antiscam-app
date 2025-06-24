"use client";
import { createContext, useContext, useEffect, useState } from "react";

type User = { email: string; fname?: string; lname?: string } | null;

type SessionContextType = {
  user: User;
  login: (user: User) => void;
  logout: () => void;
};

const SessionContext = createContext<SessionContextType>({
  user: null,
  login: () => {},
  logout: () => {},
});

export function SessionProvider({ children }: { children: React.ReactNode }) {
  // Set a default user for development/testing
  const defaultUser = { email: "admin@admin.com", fname: "admin", lname: "admin" };
  const [user, setUser] = useState<User>(defaultUser);

  useEffect(() => {
    const stored = typeof window !== "undefined" ? localStorage.getItem("user") : null;
    if (stored) setUser(JSON.parse(stored));
    else setUser(defaultUser);
  }, []);

  const login = (user: User) => {
    setUser(user);
    if (typeof window !== "undefined") localStorage.setItem("user", JSON.stringify(user));
  };
  const logout = () => {
    setUser(null);
    if (typeof window !== "undefined") localStorage.removeItem("user");
  };

  return (
    <SessionContext.Provider value={{ user, login, logout }}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  return useContext(SessionContext);
} 