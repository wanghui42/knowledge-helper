"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import MarkdownView from "./MarkdownView";

interface ChatMessage {
  role: "user" | "tutor";
  content: string;
  streaming?: boolean;
}

interface Props {
  sessionId: string;
  disabled?: boolean;
}

export default function Chat({ sessionId, disabled }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function send() {
    const text = input.trim();
    if (!text || sending || disabled) return;
    setInput("");
    setSending(true);
    setError("");

    setMessages((m) => [...m, { role: "user", content: text }]);
    const assistantIdx = messages.length + 1; // 新 assistant 消息位置
    setMessages((m) => [...m, { role: "tutor", content: "", streaming: true }]);

    const abort = new AbortController();
    abortRef.current = abort;
    try {
      await api.streamMessage(
        sessionId,
        text,
        (chunk) => {
          setMessages((m) => {
            const next = [...m];
            const target = next[assistantIdx];
            if (target) target.content += chunk;
            return next;
          });
        },
        () => {
          setMessages((m) => {
            const next = [...m];
            const target = next[assistantIdx];
            if (target) target.streaming = false;
            return next;
          });
          setSending(false);
        },
        abort.signal
      );
    } catch (e) {
      setError((e as Error).message || "消息发送失败");
      setMessages((m) => {
        const next = [...m];
        const target = next[assistantIdx];
        if (target) target.streaming = false;
        return next;
      });
      setSending(false);
    }
  }

  return (
    <div className="flex h-full flex-col rounded-xl border border-gray-200 bg-white">
      <div className="border-b border-gray-100 px-4 py-3">
        <h3 className="text-sm font-semibold text-gray-700">💬 一对一教学</h3>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center text-sm text-gray-400">
            <div className="text-center">
              <div className="mb-2 text-2xl">🤖</div>
              我是你的微积分私教，开始提问吧！
              <br />
              例如："请讲解一下导数" 或 "我不太理解极限"
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                msg.role === "user"
                  ? "rounded-br-sm bg-indigo-600 text-white"
                  : "rounded-bl-sm border border-gray-100 bg-gray-50 text-gray-800"
              }`}
            >
              {msg.role === "user" ? (
                <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
              ) : (
                <MarkdownView content={msg.content} />
              )}
              {msg.streaming && (
                <span className="mt-1 inline-block h-2 w-2 animate-pulse rounded-full bg-indigo-400" />
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {error && (
        <div className="px-4 py-1 text-xs text-red-600">{error}</div>
      )}

      <div className="border-t border-gray-100 p-3">
        <div className="flex items-center gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            disabled={disabled || sending}
            placeholder={disabled ? "当前阶段不可对话" : "输入消息…（Enter 发送）"}
            className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none transition focus:border-indigo-400"
          />
          <button
            onClick={send}
            disabled={disabled || sending || !input.trim()}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:opacity-50"
          >
            {sending ? "…" : "发送"}
          </button>
        </div>
      </div>
    </div>
  );
}
