"use client";

import { useEffect } from 'react';
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import LoginButton from "@/components/LoginButton";
import Image from "next/image";


export default function LoginPage() {
  const { isAuthenticated, loading, isRedirecting } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated && !loading) {
      router.push("/studio");
    }
  }, [isAuthenticated, loading, router]);

  if (loading || isRedirecting) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-lg">
        Loading...
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-md p-8 bg-card border border-border rounded-lg shadow-lg flex flex-col items-center">
        <div className="flex items-center gap-2 mb-6">
          {/* <h1 className="text-3xl font-bold">Login to</h1> */}
          <div className="cursor-pointer" onClick={() => router.push("/studio")}>
            <Image
              src="/logo-black.png"
              alt="Company Logo"
              width={150}
              height={40}
              className="h-40 w-auto"
            />
          </div>
        </div>
        <LoginButton />
        <p className="mt-4 text-center text-sm text-muted-foreground">
          Demo: Enter any email and password to login
        </p>
      </div>
    </div>
  );
}
