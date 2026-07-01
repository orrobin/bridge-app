import { AnalyzeResponse } from "@/lib/api";

const CONFIDENCE_STYLES: Record<string, string> = {
  low: "bg-gray-100 text-gray-700",
  medium: "bg-blue-100 text-blue-800",
  high: "bg-purple-100 text-purple-800",
};

function ConfidenceBadge({ confidence }: { confidence: string }) {
  return (
    <span
      className={`text-xs font-medium px-2 py-0.5 rounded-full ${
        CONFIDENCE_STYLES[confidence] ?? CONFIDENCE_STYLES.low
      }`}
    >
      {confidence} confidence
    </span>
  );
}

function Citations({ citations }: { citations: string[] }) {
  if (citations.length === 0) return null;
  return (
    <p className="text-xs text-gray-400 mt-1">
      Sources: {citations.join(", ")}
    </p>
  );
}

export default function ResultsView({
  result,
  onStartOver,
}: {
  result: AnalyzeResponse;
  onStartOver: () => void;
}) {
  if (result.safety_stopped) {
    return (
      <div className="mx-auto max-w-xl w-full">
        <h2 className="text-xl font-semibold mb-3">We&apos;ve paused this analysis</h2>
        <div className="bg-red-50 border border-red-200 rounded p-4 text-sm text-red-900">
          {result.safety_message}
        </div>
        <button onClick={onStartOver} className="mt-4 text-sm underline">
          Start over
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl w-full flex flex-col gap-8">
      <div>
        <h2 className="text-xl font-semibold mb-1">Patterns in this conversation</h2>
        <p className="text-sm text-gray-500 mb-3">
          Hypotheses, not verdicts -- text-only inference is low-validity.
        </p>
        <div className="flex flex-col gap-3">
          {result.hypotheses.map((h, i) => (
            <div key={i} className="border rounded p-3">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm">{h.claim}</p>
                <ConfidenceBadge confidence={h.confidence} />
              </div>
              <p className="text-xs text-gray-500 mt-2">
                <span className="font-medium">Could also mean: </span>
                {h.counter_evidence}
              </p>
              <Citations citations={h.citations} />
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-1">Possible emotional reads</h2>
        <div className="flex flex-col gap-3">
          {result.emotional_reads.map((r, i) => (
            <div key={i} className="border rounded p-3">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm">{r.read}</p>
                <ConfidenceBadge confidence={r.confidence} />
              </div>
              <p className="text-xs text-gray-500 mt-2">
                <span className="font-medium">Could also mean: </span>
                {r.counter_read}
              </p>
            </div>
          ))}
        </div>
      </div>

      {result.strategy && (
        <div>
          <h2 className="text-xl font-semibold mb-1">Authentic reply options</h2>
          {result.strategy.disinterest_detected && (
            <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded p-2 mb-3">
              This conversation shows signs of disinterest -- options below are about a graceful,
              respectful close, not pursuing further.
            </p>
          )}
          <div className="flex flex-col gap-3">
            {result.strategy.options.map((o, i) => (
              <div key={i} className="border rounded p-3">
                <p className="text-sm font-medium">&ldquo;{o.message}&rdquo;</p>
                <p className="text-xs text-gray-500 mt-1">{o.reasoning}</p>
                {o.is_meeting_suggestion && (
                  <span className="inline-block mt-2 text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full">
                    meeting suggestion
                  </span>
                )}
                <Citations citations={o.citations} />
              </div>
            ))}
          </div>
        </div>
      )}

      <button onClick={onStartOver} className="text-sm underline self-start">
        Analyze another conversation
      </button>
    </div>
  );
}
