import React, { createContext, useContext, useEffect, useState } from "react";
import type { TenantStatus, User } from "@/types";
import { getCurrentUser, getTenantStatus } from "@/services/auth";
import { getTenantSchema, setAuthToken } from "@/services/api";

interface AuthContextValue {
  user: User | null;
  tenantSchema: string | null;
  setupCompleted: boolean | null;
  tenantStatus: TenantStatus | null;
  loading: boolean;
  setUser: (user: User | null) => void;
  setSetupCompleted: (value: boolean) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
  refreshTenantStatus: () => Promise<TenantStatus | null>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [setupCompleted, setSetupCompleted] = useState<boolean | null>(null);
  const [tenantStatus, setTenantStatus] = useState<TenantStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const tenantSchema = getTenantSchema();

  const refreshTenantStatus = async () => {
    const schema = getTenantSchema();
    if (!schema || schema === "sistema") {
      setSetupCompleted(true);
      setTenantStatus({
        schema_name: schema || "sistema",
        setup_completed: true,
        is_sistema: true,
      });
      return null;
    }
    try {
      const status = await getTenantStatus();
      setTenantStatus(status);
      setSetupCompleted(status.setup_completed);
      return status;
    } catch {
      setSetupCompleted(null);
      setTenantStatus(null);
      return null;
    }
  };

  const refreshUser = async () => {
    try {
      const u = await getCurrentUser();
      setUser(u);
      await refreshTenantStatus();
    } catch {
      setUser(null);
      setSetupCompleted(null);
      setTenantStatus(null);
      setAuthToken(null);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem("assapp_access");
    if (token) {
      refreshUser().finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const logout = () => {
    setAuthToken(null);
    localStorage.removeItem("assapp_tenant_schema");
    setUser(null);
    setSetupCompleted(null);
    setTenantStatus(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        tenantSchema,
        setupCompleted,
        tenantStatus,
        loading,
        setUser,
        setSetupCompleted,
        logout,
        refreshUser,
        refreshTenantStatus,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de AuthProvider");
  return ctx;
}
