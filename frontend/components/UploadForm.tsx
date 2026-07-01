"use client";

import { useState } from "react";
import { ApiError, RedactedTurn, uploadChat } from "@/lib/api";

const PLACEHOLDER = `Paste a conversation, one message per line, like:

Alex: hey! how's your week going?
Jordan: pretty good, just got back from a hike`;

export default function UploadForm({
  token,
  onUploaded,
}: {
  token: string;
  onUploaded: (threadId: string, redactedTurns: RedactedTurn[]) => void;
}) {
  const [rawText, setRawText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const result = await uploadChat(token, rawText);
      onUploaded(result.thread_id, result.turns);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl w-full">
      <h2 className="text-xl font-semibold mb-3">Paste your conversation</h2>
      <p className="text-sm text-gray-500 mb-3">
        Names and other identifying details are redacted before anything is stored or analyzed.
      </p>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <textarea
          required
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
          placeholder={PLACEHOLDER}
          rows={10}
          className="border rounded px-3 py-2 font-mono text-sm"
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="bg-black text-white rounded px-3 py-2 disabled:opacity-50 self-start"
        >
          {submitting ? "Uploading…" : "Upload & continue"}
        </button>
      </form>
    </div>
  );
}
