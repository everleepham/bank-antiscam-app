"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useSession } from "@/components/session-context";

export default function NavBar() {
  const { user } = useSession();
  if (!user) return null;
  return (
    <nav className="flex gap-4 p-4 border-b mb-8 items-center justify-center bg-white/80 backdrop-blur sticky top-0 z-10">
      <Link href="/dashboard"><Button variant="ghost">Dashboard</Button></Link>
      <Link href="/profile"><Button variant="ghost">Profile</Button></Link>
      <Link href="/transactions"><Button variant="ghost">Transactions</Button></Link>
      <Link href="/suspicious"><Button variant="ghost">Suspicious</Button></Link>
      <Link href="/admin"><Button variant="ghost">Admin</Button></Link>
    </nav>
  );
} 