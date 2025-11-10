"use client"

import { useAuth } from '../contexts/AuthContext';

export default function LogoutButton() {
    const { isAuthenticated, loading, logout } = useAuth();

    const handleLogout = async () => {
      if (!isAuthenticated) return;
      try {
          await logout();
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