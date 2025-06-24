"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/sonner";
import { useSession } from "@/components/session-context";

export default function SuspiciousPage() {
  const { user } = useSession();
  const router = useRouter();
  const [reasons, setReasons] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!user) {
      router.replace("/login");
      return;
    }
    fetchReasons(user.email);
    // eslint-disable-next-line
  }, [user]);

  const fetchReasons = async (email: string) => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:5000/score/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (res.ok && data.reasons) {
        setReasons(data.reasons);
      } else {
        setReasons([]);
        toast(data.error || "No suspicious activity found");
      }
    } catch {
      toast("Network error");
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader>Suspicious Activity</CardHeader>
        <CardContent>
          {loading ? (
            <div>Loading...</div>
          ) : reasons.length === 0 ? (
            <div>No suspicious activity detected.</div>
          ) : (
            <ul className="list-disc pl-5 space-y-1">
              {reasons.map((reason, i) => (
                <li key={i}>{reason}</li>
              ))}
            </ul>
          )}
          <Button onClick={() => user && fetchReasons(user.email)} disabled={loading} className="w-full mt-4">{loading ? "Refreshing..." : "Refresh"}</Button>
        </CardContent>
      </Card>
    </div>
  );
} 