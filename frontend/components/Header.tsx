"use client";

import { useRouter } from "next/navigation";
import LogoutButton from "./LogoutButton";
import { Button } from "./ui/button";
import Image from "next/image";

export default function Header() {
  const router = useRouter();

  return (
    <header className="w-full flex items-center justify-between py-4 px-6 border-b border-border bg-card">
      <div className="flex items-center gap-2 cursor-pointer" onClick={() => router.push("/studio")}>
        <Image
          src="/logo-black.png"
          alt="Company Logo"
          width={150}
          height={40}
          className="h-13 w-auto"
        />
      </div>
      <nav className="flex items-center gap-4">
        <Button
          onClick={() => router.push("/studio")}
          variant="ghost"
          size="sm"
        >
          Dashboard
        </Button>
        <LogoutButton />
      </nav>
    </header>
  );
}
