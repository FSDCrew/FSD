"use client"

import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/navigation';

export default function LogoutButton() {
    const { isAuthenticated, loading, logout } = useAuth();
    const router = useRouter();

    const handleLogout = async () => {
      if (!isAuthenticated) return;
      try {
          await logout();
          router.push("/auth/login");
      } catch (err) {
          console.log("Error signing out:", err);
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