"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function StartPage() {
  const router = useRouter();
  const [goal, setGoal] = useState("学习微积分");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleStart() {
    if (!goal.trim() || loading) return;
    setLoading(true);
    setError("");
    try {
      const res = await api.start(goal.trim());
      // 进入学习页，带上 sessionId
      router.push(`/learn?session=${res.session_id}`);
    } catch (e) {
      setError((e as Error).message);
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-lg rounded-2xl bg-white p-8 shadow-xl">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-600 text-3xl text-white">
            🎓
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            LLM 一对一自适应教学系统
          </h1>
          <p className="mt-2 text-sm text-gray-500">
            输入学习目标，AI 私教将为你诊断、规划并一对一教学
          </p>
        </div>

        <label className="mb-2 block text-sm font-medium text-gray-700">
          学习目标
        </label>
        <input
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleStart()}
          placeholder="例如：学习微积分"
          className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
        />

        {error && (
          <div className="mt-4 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-600">
            ⚠️ 启动失败：{error}
          </div>
        )}

        <button
          onClick={handleStart}
          disabled={loading}
          className="mt-6 w-full rounded-lg bg-indigo-600 py-3 font-medium text-white transition hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "正在创建学习会话…" : "开始学习 🚀"}
        </button>

        <p className="mt-4 text-center text-xs text-gray-400">
          后端未启动？请先运行：<code className="rounded bg-gray-100 px-1">uvicorn main:app</code>
        </p>
      </div>
    </main>
  );
}
