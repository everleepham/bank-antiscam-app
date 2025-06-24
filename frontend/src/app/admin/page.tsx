"use client";
import { useSession } from "@/components/session-context";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function AdminPage() {
  const { user } = useSession();
  const router = useRouter();
  useEffect(() => {
    if (!user) router.replace("/login");
  }, [user, router]);
  if (!user) return null;
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-2xl">
        <CardHeader>Admin Database Dashboards</CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-4">
            <Button variant="outline">MongoDB</Button>
            <Button variant="outline">Redis</Button>
            <Button variant="outline">Neo4j</Button>
          </div>
          <div className="border rounded p-4 bg-gray-50 text-gray-500">
            <p>Database view coming soon...</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 