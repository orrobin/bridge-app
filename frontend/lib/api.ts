const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit & { token?: string } = {}
): Promise<T> {
  const { token, headers, ...rest } = options;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, body.detail ?? "Request failed");
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export function signup(email: string, password: string) {
  return request<{ id: string; email: string; is_active: boolean }>("/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function login(email: string, password: string) {
  return request<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export interface ConsentNotice {
  notice_version: string;
  notice_text: string;
}

export function getConsentNotice() {
  return request<ConsentNotice>("/consent/notice");
}

export function recordConsent(
  token: string,
  jurisdiction: string,
  isAdultConfirmed: boolean,
  otherPartyNoticeAck: boolean
) {
  return request("/consent", {
    method: "POST",
    token,
    body: JSON.stringify({
      jurisdiction,
      is_adult_confirmed: isAdultConfirmed,
      other_party_notice_ack: otherPartyNoticeAck,
    }),
  });
}

export interface RedactedTurn {
  speaker: string;
  text: string;
}

export interface UploadResponse {
  id: string;
  thread_id: string;
  turns: RedactedTurn[];
  expires_at: string;
}

export function uploadChat(token: string, rawText: string) {
  return request<UploadResponse>("/upload", {
    method: "POST",
    token,
    body: JSON.stringify({ raw_text: rawText }),
  });
}

export interface Hypothesis {
  claim: string;
  confidence: "low" | "medium" | "high";
  counter_evidence: string;
  citations: string[];
}

export interface EmotionalRead {
  read: string;
  confidence: "low" | "medium" | "high";
  counter_read: string;
}

export interface StrategyOption {
  message: string;
  reasoning: string;
  citations: string[];
  is_meeting_suggestion: boolean;
}

export interface StrategyOutput {
  options: StrategyOption[];
  disinterest_detected: boolean;
  mutual_signals_detected: boolean;
}

export interface AnalyzeResponse {
  safety_stopped: boolean;
  safety_message: string | null;
  hypotheses: Hypothesis[];
  emotional_reads: EmotionalRead[];
  strategy: StrategyOutput | null;
}

export function analyze(token: string, threadId: string) {
  return request<AnalyzeResponse>("/analyze", {
    method: "POST",
    token,
    body: JSON.stringify({ thread_id: threadId }),
  });
}
