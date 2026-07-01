"use client";

import { useState } from "react";
import { ApiError, login, signup } from "@/lib/api";

export default function AuthForm({ onAuthenticated }: { onAuthenticated: (token: string) => void }) {
  const [mode, setMode] = useState<"login" | "signup">("signup");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "signup") {
        await signup(email, password);
      }
      const { access_token } = await login(email, password);
      onAuthenticated(access_token);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm w-full">
      <h1 className="text-2xl font-semibold mb-1">Bridge</h1>
      <p className="text-sm text-gray-500 mb-6">
        A private, evidence-grounded communication coach.
      </p>

      <div className="flex gap-2 mb-4 text-sm">
        <button
          className={`px-3 py-1 rounded ${mode === "signup" ? "bg-black text-white" : "bg-gray-100 text-gray-900"}`}
          onClick={() => setMode("signup")}
          type="button"
        >
          Sign up
        </button>
        <button
          className={`px-3 py-1 rounded ${mode === "login" ? "bg-black text-white" : "bg-gray-100 text-gray-900"}`}
          onClick={() => setMode("login")}
          type="button"
        >
          Log in
        </button>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <input
          type="email"
          required
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="border rounded px-3 py-2"
        />
        <input
          type="password"
          required
          minLength={8}
          placeholder="Password (min 8 characters)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="border rounded px-3 py-2"
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="bg-black text-white rounded px-3 py-2 disabled:opacity-50"
        >
          {submitting ? "Please wait…" : mode === "signup" ? "Create account" : "Log in"}
        </button>
      </form>
    </div>
  );
}
