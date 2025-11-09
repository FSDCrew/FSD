"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

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
        <Button
          onClick={() => router.push("/studio")}
          variant="ghost"
          size="sm"
        >
          Dashboard
        </Button>
        <Button
          onClick={handleLogout}
          variant="secondary"
          size="sm"
        >
          Logout
        </Button>
      </nav>
    </header>
  );
}
