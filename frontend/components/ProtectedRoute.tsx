"use client";
 
import { useEffect } from 'react';
import { useRouter } from "next/navigation";
import { useAuth } from '../contexts/AuthContext';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/auth/login");
    }
  }, [loading, isAuthenticated, router]);

  if (loading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center h-screen bg-white-500">
        <div className="text-xl text-black">Loading...</div>
      </div>
    );
  }

  return children;
};


export default ProtectedRoute;