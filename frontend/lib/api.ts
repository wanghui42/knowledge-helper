// API 客户端（REST + SSE）
import type {
  AnswerResponse,
  EventItem,
  KnowledgeMapData,
  ProgressResponse,
  Question,
  SessionState,
  StartResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${res.status} ${body.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  start: (goal: string, subject = "math") =>
    request<StartResponse>("/api/learning/start", {
      method: "POST",
      body: JSON.stringify({ goal, subject }),
    }),

  session: (sessionId: string) =>
    request<SessionState>(`/api/learning/${sessionId}`),

  map: (sessionId: string) =>
    request<KnowledgeMapData>(`/api/learning/${sessionId}/map`),

  answer: (sessionId: string, questionId: string, answer: number) =>
    request<AnswerResponse>(`/api/learning/${sessionId}/answer`, {
      method: "POST",
      body: JSON.stringify({ question_id: questionId, answer }),
    }),

  progress: (sessionId: string) =>
    request<ProgressResponse>(`/api/learning/${sessionId}/progress`),

  events: (sessionId: string) =>
    request<EventItem[]>(`/api/learning/${sessionId}/events`),

  startAssessment: (sessionId: string) =>
    request<{ stage: string; question: Question | null }>(
      `/api/learning/${sessionId}/start-assessment`,
      { method: "POST" }
    ),

  /** SSE 流式教学对话 */
  async streamMessage(
    sessionId: string,
    message: string,
    onToken: (chunk: string) => void,
    onDone: (meta: { intent?: string; node_id?: string }) => void,
    signal?: AbortSignal
  ): Promise<void> {
    const res = await fetch(`${API_BASE}/api/learning/${sessionId}/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
      signal,
    });
    if (!res.ok || !res.body) {
      throw new Error(`message failed: ${res.status}`);
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let meta: { intent?: string; node_id?: string } = {};
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      // 按 SSE 事件分隔
      const events = buffer.split("\n\n");
      buffer = events.pop() || "";
      for (const ev of events) {
        const line = ev
          .split("\n")
          .find((l) => l.startsWith("data: "));
        if (!line) continue;
        try {
          const data = JSON.parse(line.slice(6));
          if (data.type === "token") onToken(data.content as string);
          else if (data.type === "done") meta = data;
        } catch {
          /* 忽略脏数据 */
        }
      }
    }
    onDone(meta);
  },
};
