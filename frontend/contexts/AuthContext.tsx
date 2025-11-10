"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { getCurrentUser, fetchAuthSession, signOut, AuthUser } from "aws-amplify/auth";
import { Hub } from "aws-amplify/utils";

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  checkUser: () => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    // 1. Set up the Hub listener to catch auth events
    const unsubscribe = Hub.listen("auth", ({ payload }) => {
      const { event } = payload;
      console.log("Auth event:", event);

      // 2. When 'signedIn' fires, the code exchange is complete.
      //    Run checkUser() to get the user data and tokens.
      if (event === "signedIn") {
        console.log("Hub: 'signedIn' event detected. Running checkUser.");
        checkUser();
      
      // 3. When 'signedOut' fires, clear the user state.
      } else if (event === "signedOut") {
        console.log("Hub: 'signedOut' event detected. Clearing user state.");
        setUser(null);
        setToken(null);
      }
    });

    // Only check user on mount if we're NOT in the middle of OAuth callback
    const isOAuthCallback = window.location.search.includes('code=') || 
                            window.location.search.includes('error=');
    
    if (!isOAuthCallback) {
      checkUser();
    } else {
      setLoading(false);
    }
    // } else {
    //   // We're in OAuth flow - just stop loading spinner
    //   // The Hub listener will handle the rest
    //   setLoading(false);
    // }

    // 5. Cleanup the listener when the component unmounts
    return () => {
      console.log("AuthProvider Unmounted: Cleaning up Hub listener.");
      unsubscribe();
    };
  }, []); 

  const checkUser = async () => {
    console.log("checkUser: Starting...");
    try {
      const session = await fetchAuthSession();
      console.log("checkUser: Session fetched successfully.");

      const currentUser = await getCurrentUser();
      console.log("checkUser: Current user fetched.", currentUser);

      setUser(currentUser);
      setToken(session.tokens?.idToken?.toString() ?? null);
    } catch (error) {
      console.log("Not signed in", error);
      setUser(null);
      setToken(null);
    } finally {
      console.log("%ccheckUser: Finally block reached. Setting loading to false.", "color: green; font-weight: bold;");
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await signOut();
    } catch (error) {
      console.error("Error signing out:", error);
    }
  };

  const value = {
    user,
    token,
    loading,
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