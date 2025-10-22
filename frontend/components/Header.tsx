"use client";

import { useRouter } from "next/navigation";

export default function Header() {
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem("fsd_token");
    router.push("/");
  };

  return (
    <header className="w-full flex items-center justify-between py-4 px-6 border-b border-border bg-card">
      <div className="flex items-center gap-2">
        <h1 className="text-xl font-bold">FSD Studio</h1>
      </div>
      <nav className="flex items-center gap-4">
        <button
          onClick={() => router.push("/studio")}
          className="text-sm hover:text-primary transition-colors"
        >
          Dashboard
        </button>
        <button
          onClick={handleLogout}
          className="text-sm px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:opacity-90 transition-opacity"
        >
          Logout
        </button>
      </nav>
    </header>
  );
}
