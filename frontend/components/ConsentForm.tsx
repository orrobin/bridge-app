"use client";

import { useEffect, useState } from "react";
import { ApiError, ConsentNotice, getConsentNotice, recordConsent } from "@/lib/api";

export default function ConsentForm({
  token,
  onConsented,
}: {
  token: string;
  onConsented: () => void;
}) {
  const [notice, setNotice] = useState<ConsentNotice | null>(null);
  const [jurisdiction, setJurisdiction] = useState("");
  const [isAdultConfirmed, setIsAdultConfirmed] = useState(false);
  const [otherPartyAck, setOtherPartyAck] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    getConsentNotice().then(setNotice).catch(() => setNotice(null));
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await recordConsent(token, jurisdiction, isAdultConfirmed, otherPartyAck);
      onConsented();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-md w-full">
      <h2 className="text-xl font-semibold mb-3">Before we start</h2>

      <div className="bg-amber-50 border border-amber-200 rounded p-3 text-sm text-amber-900 mb-4">
        {notice?.notice_text ??
          "We'll redact names and identifying details before analysis. The other person in this conversation didn't consent to being analyzed -- we minimize what we keep about them and never build a long-term profile of them."}
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <label className="text-sm font-medium">
          Your jurisdiction (e.g. US-CA, EU-DE)
          <input
            required
            value={jurisdiction}
            onChange={(e) => setJurisdiction(e.target.value)}
            className="border rounded px-3 py-2 w-full mt-1"
          />
        </label>

        <label className="flex items-start gap-2 text-sm">
          <input
            type="checkbox"
            checked={isAdultConfirmed}
            onChange={(e) => setIsAdultConfirmed(e.target.checked)}
            className="mt-1"
          />
          I confirm I am 18 years of age or older.
        </label>

        <label className="flex items-start gap-2 text-sm">
          <input
            type="checkbox"
            checked={otherPartyAck}
            onChange={(e) => setOtherPartyAck(e.target.checked)}
            className="mt-1"
          />
          I understand and accept the notice above about the other person&apos;s data.
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={submitting || !isAdultConfirmed || !otherPartyAck}
          className="bg-black text-white rounded px-3 py-2 disabled:opacity-50"
        >
          {submitting ? "Please wait…" : "Continue"}
        </button>
      </form>
    </div>
  );
}
