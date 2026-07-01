"use client";

import { useState } from "react";
import AuthForm from "@/components/AuthForm";
import ConsentForm from "@/components/ConsentForm";
import UploadForm from "@/components/UploadForm";
import ResultsView from "@/components/ResultsView";
import { ApiError, AnalyzeResponse, RedactedTurn, analyze } from "@/lib/api";

type Step = "auth" | "consent" | "upload" | "analyzing" | "results";

export default function Home() {
  const [step, setStep] = useState<Step>("auth");
  const [token, setToken] = useState<string | null>(null);
  const [redactedTurns, setRedactedTurns] = useState<RedactedTurn[]>([]);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleUploaded(newThreadId: string, turns: RedactedTurn[]) {
    setRedactedTurns(turns);
    setStep("analyzing");
    setError(null);
    try {
      const response = await analyze(token!, newThreadId);
      setResult(response);
      setStep("results");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
      setStep("upload");
    }
  }

  function startOver() {
    setRedactedTurns([]);
    setResult(null);
    setError(null);
    setStep("upload");
  }

  return (
    <main className="flex-1 flex flex-col items-center justify-center px-4 py-10">
      {step === "auth" && (
        <AuthForm
          onAuthenticated={(newToken) => {
            setToken(newToken);
            setStep("consent");
          }}
        />
      )}

      {step === "consent" && token && (
        <ConsentForm token={token} onConsented={() => setStep("upload")} />
      )}

      {(step === "upload" || step === "analyzing") && token && (
        <div className="w-full flex flex-col items-center gap-3">
          <UploadForm token={token} onUploaded={handleUploaded} />
          {step === "analyzing" && (
            <p className="text-sm text-gray-500">Analyzing your conversation…</p>
          )}
          {error && <p className="text-sm text-red-600">{error}</p>}
          {redactedTurns.length > 0 && step === "upload" && (
            <details className="text-xs text-gray-400 max-w-xl w-full">
              <summary>Last redacted upload (debug)</summary>
              <pre className="whitespace-pre-wrap">
                {redactedTurns.map((t) => `${t.speaker}: ${t.text}`).join("\n")}
              </pre>
            </details>
          )}
        </div>
      )}

      {step === "results" && result && (
        <ResultsView result={result} onStartOver={startOver} />
      )}
    </main>
  );
}
