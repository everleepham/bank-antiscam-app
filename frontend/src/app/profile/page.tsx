"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/sonner";
import { useSession } from "@/components/session-context";

export default function ProfilePage() {
  const { user } = useSession();
  const router = useRouter();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchProfile = async () => {
    setLoading(true);
    if (!user) {
      toast("No user found. Please log in.");
      setLoading(false);
      return;
    }
    try {
      const res = await fetch("http://localhost:5000/score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: user.email }),
      });
      const data = await res.json();
      if (res.ok) {
        setProfile({ ...data, email: user.email });
      } else {
        toast(data.error || "Failed to fetch profile");
      }
    } catch {
      toast("Network error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!user) {
      router.replace("/login");
      return;
    }
    fetchProfile();
    // eslint-disable-next-line
  }, [user]);

  if (!user) return null;
  if (!profile) {
    return <div className="flex justify-center items-center min-h-screen">Loading profile...</div>;
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader>Profile</CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div>Email: <b>{profile.email}</b></div>
            <div>Score: <b>{profile.score ?? "-"}</b></div>
            <div>Flag: <b>{profile.flag}</b></div>
            <div className="text-yellow-700">{profile.message}</div>
            <Button onClick={fetchProfile} disabled={loading} className="w-full mt-4">{loading ? "Refreshing..." : "Refresh Profile"}</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 