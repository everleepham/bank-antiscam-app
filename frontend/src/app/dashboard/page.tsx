"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/sonner";
import { useSession } from "@/components/session-context";

export default function DashboardPage() {
  const { user } = useSession();
  const router = useRouter();
  const [score, setScore] = useState<number | null>(null);
  const [flag, setFlag] = useState<string>("");
  const [warning, setWarning] = useState<string>("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!user) {
      router.replace("/login");
      return;
    }
    fetchScore(user.email);
    // eslint-disable-next-line
  }, [user]);

  const fetchScore = async (email: string) => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:5000/score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (res.ok) {
        setScore(data.score);
        setFlag(data.flag);
        setWarning(data.message);
      } else {
        toast(data.error || "Failed to fetch score");
      }
    } catch {
      toast("Network error");
    } finally {
      setLoading(false);
    }
  };

  const recalculateScore = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const res = await fetch("http://localhost:5000/score/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: user.email }),
      });
      const data = await res.json();
      if (res.ok) {
        toast("Score recalculated");
        setScore(data.score_calculated);
        // Optionally update flag/warning if returned
      } else {
        toast(data.error || "Failed to recalculate score");
      }
    } catch {
      toast("Network error");
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return null;
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader>Dashboard</CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>Email: <b>{user.email}</b></div>
            <div>Trust Score: <b>{score ?? "-"}</b></div>
            <div>Flag: <b>{flag}</b></div>
            <div className="text-yellow-700">{warning}</div>
            <Button onClick={recalculateScore} disabled={loading} className="w-full">{loading ? "Recalculating..." : "Recalculate Score"}</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 