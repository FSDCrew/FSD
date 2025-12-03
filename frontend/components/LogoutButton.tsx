"use client"

import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { Button } from "@/components/ui/button";

export default function LogoutButton() {
    const { isAuthenticated, loading, logout } = useAuth();
    const router = useRouter();

    const handleLogout = async () => {
      if (!isAuthenticated) return;
      try {
          await logout();
          toast.success("Logged out successfully");
          router.push("/auth/login");
      } catch (err) {
          toast.error("Error signing out. Please try again.");
          console.error("Error signing out:", err);
      }
    }

    return (
      <Button
        onClick={handleLogout}
        variant="outline"
      >
        <div>Logout</div>
      </Button>
    )
}