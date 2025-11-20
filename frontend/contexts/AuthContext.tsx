"use client";

import { createContext, useContext, useEffect, useState, useRef, ReactNode } from "react";
import { getCurrentUser, fetchAuthSession, signOut, AuthUser } from "aws-amplify/auth";
import { Hub } from "aws-amplify/utils";

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  checkUser: () => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
  isRedirecting: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  
  const [isRedirecting, setIsRedirecting] = useState(false); 
  const isInitialized = useRef(false);

  useEffect(() => {
    if (isInitialized.current) return;
    isInitialized.current = true;

    // ... (Hub Listener setup remains the same)
    const unsubscribe = Hub.listen("auth", ({ payload }) => {
      const { event } = payload as { event: string };
      if (event === "signedIn" || event === "tokenRefresh") {
        checkUser();
      } else if (event === "signedOut" || event === "tokenRefresh_failure") {
        // ... (sign out logic)
        setUser(null);
        setToken(null);
        setLoading(false);
        setIsRedirecting(false); 
      }
    });

    const isOAuthCallback = window.location.search.includes('code=') || 
                            window.location.search.includes('error=');

    if (isOAuthCallback) {
      console.log("🔐 OAuth callback detected. Initiating masked redirect process.");
      setIsRedirecting(true);
      setLoading(false);
    } else {
      checkUser();
    }

    return () => {
      isInitialized.current = false;
      unsubscribe();
    };
  }, []);


  const checkUser = async () => {
    setLoading(true); 
    
    try {
      const session = await fetchAuthSession();
      const currentUser = await getCurrentUser();
      
      setUser(currentUser);
      setToken(session.tokens?.idToken?.toString() ?? null);
    } catch (error) {
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
      setIsRedirecting(false); 
    }
  };


  const logout = async () => {
    try {
      await signOut({ global: true });
    } catch (error) {
      console.error("Error signing out:", error);
    }
  };

  const value = {
    user,
    token,
    loading,
    isRedirecting,
    checkUser,
    logout,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};