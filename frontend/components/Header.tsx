"use client";

import { useRouter } from "next/navigation";
import LogoutButton from "./LogoutButton";

export default function Header() {
  const router = useRouter();

  // const handleLogout = () => {
  //   localStorage.removeItem("fsd_token");
  //   router.push("/");
  // };

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
        <LogoutButton />
      </nav>
    </header>
  );
}
