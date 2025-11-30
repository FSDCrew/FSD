"use client"

import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';

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
      <button
        onClick={handleLogout}
        disabled={loading}
        className={`flex text-sm px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:opacity-90 transition-opacity ${
          loading
            ? 'cursor-not-allowed'
            : 'hover:cursor-pointer'
        }`}
      >
        <div>Logout</div>
      </button>
    )
}