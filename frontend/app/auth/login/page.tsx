"use client";

import { useEffect } from 'react';
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import LoginButton from "@/components/LoginButton";


export default function LoginPage() {

  // const handleLogin = (e: React.FormEvent) => {
  //   e.preventDefault();
  //   // Simple mock login - replace with your actual auth logic
  //   if (email && password) {
  //     localStorage.setItem("fsd_token", "mock-token-" + Date.now());
  //     router.push("/studio");
  //   }
  // };
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated && !loading) {
      router.push("/studio");
    }
  }, [isAuthenticated, loading, router]);


  if (loading) {
    return <div>Loading...</div>;
  }


  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-md p-8 bg-card border border-border rounded-lg shadow-lg">
        <h1 className="text-3xl font-bold mb-6 text-center">Login to FSD Studio</h1>
          <LoginButton />
          <p className="mt-4 text-center text-sm text-muted-foreground">
            Demo: Enter any email and password to login
          </p>
      </div>
    </div>
  );
}
