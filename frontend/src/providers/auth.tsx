import {
  createContext,
  createMemo,
  createResource,
  useContext,
  type Accessor,
  type ParentProps,
} from "solid-js";

import type { CurrentUser } from "@/types/api";
import { authAPI } from "@/utils/api";

interface AuthContextValue {
  user: Accessor<CurrentUser | null | undefined>;
  isAuthenticated: Accessor<boolean>;
  isLoading: Accessor<boolean>;
  error: Accessor<Error | undefined>;
  refetch: () => void;
}

const AuthContext = createContext<AuthContextValue>();

async function fetchCurrentUser(): Promise<CurrentUser | null> {
  return authAPI.me();
}

export function AuthProvider(props: ParentProps) {
  const [userResource, { refetch }] = createResource(fetchCurrentUser);

  const user = createMemo(() => userResource());
  const isLoading = createMemo(() => userResource.loading);
  const error = createMemo<Error | undefined>(() => userResource.error as Error | undefined);
  const isAuthenticated = createMemo(() => Boolean(user()));

  const value: AuthContextValue = {
    user,
    isAuthenticated,
    isLoading,
    error,
    refetch,
  };

  return (
    <AuthContext.Provider value={value}>{props.children}</AuthContext.Provider>
  );
}

export function useOptionalAuth(): AuthContextValue | undefined {
  return useContext(AuthContext);
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

