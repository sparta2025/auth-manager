import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { authApi } from "../api/auth";
import type { Role, User } from "../types";

interface AuthState { user: User|null; roles: Role[]; permissions: string[]; isLoading: boolean; isAuthenticated: boolean; }
interface AuthCtx extends AuthState { login:(e:string,p:string)=>Promise<void>; logout:()=>Promise<void>; refresh:()=>Promise<void>; isAdmin:boolean; hasPermission:(code:string)=>boolean; }

const Ctx = createContext<AuthCtx|null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({ user:null, roles:[], permissions:[], isLoading:true, isAuthenticated:false });

  const refresh = useCallback(async () => {
    if (!localStorage.getItem("access_token")) {
      setState(s=>({...s,isLoading:false,isAuthenticated:false})); return;
    }
    try {
      const [user, roles, permissions] = await Promise.all([authApi.me(), authApi.myRoles(), authApi.myPermissions()]);
      setState({ user, roles, permissions, isLoading:false, isAuthenticated:true });
    } catch {
      localStorage.removeItem("access_token");
      setState({ user:null, roles:[], permissions:[], isLoading:false, isAuthenticated:false });
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const login = useCallback(async (email: string, password: string) => {
    const tokenData = await authApi.login(email, password);
    localStorage.setItem("access_token", tokenData.access_token);
    localStorage.setItem("token_expires_at", String(new Date(tokenData.expires_at).getTime()));
    await refresh();
  }, [refresh]);

  const logout = useCallback(async () => {
    try { await authApi.logout(); } finally {
      localStorage.removeItem("access_token");
      setState({ user:null, roles:[], permissions:[], isLoading:false, isAuthenticated:false });
    }
  }, []);

  const isAdmin = state.roles.some(r => r.name === "administrator");
  const hasPermission = (code: string) => state.permissions.includes(code);

  return <Ctx.Provider value={{...state, login, logout, refresh, isAdmin, hasPermission}}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
}
