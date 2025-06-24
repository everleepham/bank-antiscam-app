"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "@/components/ui/sonner";
import { useSession } from "@/components/session-context";

export default function TransactionsPage() {
  const { user } = useSession();
  const router = useRouter();
  const [recipient, setRecipient] = useState("");
  const [amount, setAmount] = useState("");
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (!user) {
      router.replace("/login");
      return;
    }
    fetchTransactions(user.email);
    // eslint-disable-next-line
  }, [user]);

  const fetchTransactions = async (email: string) => {
    setLoading(true);
    try {
      // Fetch user_id from backend (simulate for now)
      const userIdRes = await fetch("http://localhost:5000/score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const userData = await userIdRes.json();
      if (!userIdRes.ok || !userData.user_id) {
        toast("Could not fetch user ID");
        setLoading(false);
        return;
      }
      const user_id = userData.user_id;
      const res = await fetch(`http://localhost:5000/transactions/${user_id}`);
      const data = await res.json();
      if (res.ok) {
        setTransactions(data.transactions || []);
      } else {
        toast(data.error || "Failed to fetch transactions");
      }
    } catch {
      toast("Network error");
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return toast("Please log in");
    setSending(true);
    try {
      const res = await fetch("http://localhost:5000/transactions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sender: { user_email: user.email },
          recipient: { user_email: recipient },
          amount: parseFloat(amount),
          status: "pending",
          timestamp: new Date().toISOString(),
        }),
      });
      const data = await res.json();
      if (res.ok) {
        toast("Transaction sent");
        setRecipient("");
        setAmount("");
        fetchTransactions(user.email);
      } else {
        toast(data.error || "Transaction failed");
      }
    } catch {
      toast("Network error");
    } finally {
      setSending(false);
    }
  };

  if (!user) return null;

  return (
    <div className="flex flex-col items-center min-h-screen py-8 gap-8">
      <Card className="w-full max-w-md">
        <CardHeader>Send Money</CardHeader>
        <CardContent>
          <form onSubmit={handleSend} className="space-y-4">
            <div>
              <Label htmlFor="recipient">Recipient Email</Label>
              <Input id="recipient" value={recipient} onChange={e => setRecipient(e.target.value)} required disabled={sending} />
            </div>
            <div>
              <Label htmlFor="amount">Amount</Label>
              <Input id="amount" type="number" value={amount} onChange={e => setAmount(e.target.value)} required min="1" step="0.01" disabled={sending} />
            </div>
            <Button type="submit" className="w-full" disabled={sending}>{sending ? "Sending..." : "Send"}</Button>
          </form>
        </CardContent>
      </Card>
      <Card className="w-full max-w-2xl">
        <CardHeader>Transaction History</CardHeader>
        <CardContent>
          {loading ? (
            <div>Loading...</div>
          ) : transactions.length === 0 ? (
            <div>No transactions found.</div>
          ) : (
            <div className="space-y-2">
              {transactions.map((txn, i) => (
                <div key={i} className="border-b pb-2">
                  <div><b>To:</b> {txn.recipient_email || txn.recipient?.user_email}</div>
                  <div><b>Amount:</b> €{txn.amount}</div>
                  <div><b>Status:</b> {txn.status}</div>
                  <div><b>Reason:</b> {txn.flag_reason || "-"}</div>
                  <div className="text-xs text-gray-500">{txn.timestamp}</div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
} 