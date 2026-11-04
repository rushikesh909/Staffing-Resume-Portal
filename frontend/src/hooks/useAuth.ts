"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { User, UserRole } from "@/lib/types";
import { clearToken, getToken, getUser, setToken, setUser } from "@/lib/auth";
import { getMeApi, loginApi } from "@/lib/api";

export function useAuth() {
  const router = useRouter();
  const [user, setCurrentUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const initAuth = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setCurrentUser(null);
      setIsLoading(false);
      return;
    }

    const cachedUser = getUser();
    if (cachedUser) {
      setCurrentUser(cachedUser);
    }

    try {
      const fetchedUser = await getMeApi();
      if (fetchedUser) {
        setUser(fetchedUser);
        setCurrentUser(fetchedUser);
      }
    } catch {
      // If getMe fails but cachedUser exists, keep cachedUser unless 401
      if (!cachedUser) {
        clearToken();
        setCurrentUser(null);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  const login = async (credentials: { email: string; password: string }) => {
    setIsLoading(true);
    try {
      const res = await loginApi(credentials);
      setToken(res.access_token);

      // Determine user object from login response
      let loggedUser: User;
      if (res.user) {
        loggedUser = res.user;
      } else {
        loggedUser = {
          id: 0,
          email: credentials.email,
          role: (res.role as UserRole) || "recruiter",
          client_id: res.client_id ?? null,
        };
      }

      // Try fetching real user profile if available
      try {
        const fullUser = await getMeApi();
        if (fullUser) {
          loggedUser = fullUser;
        }
      } catch {
        // Fallback to loggedUser constructed from login response
      }

      setUser(loggedUser);
      setCurrentUser(loggedUser);

      // Navigate based on role
      if (loggedUser.role === "client_hiring_manager") {
        router.push("/client/portal");
      } else {
        router.push("/dashboard");
      }

      return { success: true, user: loggedUser };
    } catch (err: any) {
      setIsLoading(false);
      const message =
        err.response?.data?.detail || err.message || "Invalid credentials";
      throw new Error(message);
    }
  };

  const logout = () => {
    clearToken();
    setCurrentUser(null);
    router.push("/login");
  };

  return {
    user,
    role: user?.role,
    isAuthenticated: Boolean(user && getToken()),
    isLoading,
    login,
    logout,
    refreshUser: initAuth,
  };
}
