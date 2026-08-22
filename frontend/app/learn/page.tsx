"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type {
  AnswerResponse,
  KnowledgeMapData,
  ProgressResponse,
  Question,
  SessionStage,
} from "@/lib/types";
import KnowledgeMap from "@/components/KnowledgeMap";
import QuizCard from "@/components/QuizCard";
import ProgressPanel from "@/components/ProgressPanel";
import Chat from "@/components/Chat";
import DebugPanel from "@/components/DebugPanel";

const STAGE_BADGE: Record<SessionStage, string> = {
  INIT: "bg-gray-200 text-gray-600",
  DIAGNOSIS: "bg-indigo-100 text-indigo-700",
  PLANNING: "bg-purple-100 text-purple-700",
  TEACHING: "bg-emerald-100 text-emerald-700",
  ASSESSMENT: "bg-amber-100 text-amber-700",
  REPLAN: "bg-sky-100 text-sky-700",
  COMPLETE: "bg-green-100 text-green-700",
};

export default function LearnPage() {
  const router = useRouter();
  const params = useSearchParams();
  const sessionId = params.get("session") || "";

  const [stage, setStage] = useState<SessionStage>("INIT");
  const [goal, setGoal] = useState("");
  const [currentNodeId, setCurrentNodeId] = useState<string | null>(null);
  const [question, setQuestion] = useState<Question | null>(null);
  const [map, setMap] = useState<KnowledgeMapData | null>(null);
  const [progress, setProgress] = useState<ProgressResponse | null>(null);
  const [answerFeedback, setAnswerFeedback] = useState<AnswerResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [chatKey, setChatKey] = useState(0); // 用于教学阶段切换后重建

  const busyRef = useRef(false);

  const refreshAll = useCallback(async () => {
    if (!sessionId) return;
    try {
      const [sess, m, p] = await Promise.all([
        api.session(sessionId),
        api.map(sessionId),
        api.progress(sessionId),
      ]);
      setStage(sess.stage);
      setGoal(sess.goal);
      setCurrentNodeId(sess.current_node_id);
      // 优先使用 session 同步的当前题；回答结果中也可能带回新题
      if (sess.question) setQuestion(sess.question);
      setMap(m);
      setProgress(p);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId) {
      router.replace("/");
      return;
    }
    refreshAll();
  }, [sessionId, refreshAll, router]);

  async function handleAnswer(idx: number) {
    if (!question || busyRef.current) return;
    busyRef.current = true;
    try {
      const res = await api.answer(sessionId, question.id, idx);
      setAnswerFeedback(res);
      setQuestion(res.question);
      setStage(res.stage);
      await refreshAll();
      if (res.stage === "TEACHING") {
        setChatKey((k) => k + 1);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      busyRef.current = false;
    }
  }

  async function handleStartAssessment() {
    setError("");
    try {
      const res = await api.startAssessment(sessionId);
      setQuestion(res.question);
      setStage("ASSESSMENT");
      await refreshAll();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-center text-gray-500">
          <div className="mb-3 text-3xl">⏳</div>
          正在加载学习会话…
        </div>
      </main>
    );
  }

  const canChat = stage === "TEACHING";
  const showQuiz = !!question;

  return (
    <main className="min-h-screen p-4">
      {/* 顶栏 */}
      <header className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-white px-5 py-3 shadow-sm">
        <div className="flex items-center gap-3">
          <span className="text-xl">🎓</span>
          <div>
            <div className="text-sm font-bold text-gray-900">{goal}</div>
            <div className="text-xs text-gray-400">Session: {sessionId}</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold ${STAGE_BADGE[stage] ?? "bg-gray-100"}`}
          >
            {stage}
          </span>
          <button
            onClick={() => {
              router.push("/");
              // 清除 URL
            }}
            className="rounded-lg border border-gray-200 px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
          >
            ← 新会话
          </button>
        </div>
      </header>

      {error && (
        <div className="mb-4 rounded-xl bg-red-50 px-4 py-2 text-sm text-red-600">
          ⚠️ {error}
        </div>
      )}

      {/* 主内容 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* 左：知识地图 */}
        <div className="lg:col-span-1">
          <KnowledgeMap data={map || { nodes: [], edges: [] }} />
          <div className="mt-4">
            <DebugPanel sessionId={sessionId} />
          </div>
        </div>

        {/* 中：测评 / 教学 */}
        <div className="lg:col-span-1">
          {stage === "COMPLETE" ? (
            <div className="rounded-2xl border border-green-200 bg-white p-8 text-center shadow-sm">
              <div className="mb-3 text-5xl">🎉</div>
              <h2 className="text-xl font-bold text-gray-900">学习目标达成！</h2>
              <p className="mt-2 text-sm text-gray-500">
                所有知识节点均达到掌握水平（≥ 0.80），恭喜完成「{goal}」！
              </p>
              <button
                onClick={() => router.push("/")}
                className="mt-6 rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-indigo-700"
              >
                开始新的学习 🚀
              </button>
            </div>
          ) : stage === "TEACHING" ? (
            <div className="flex h-[560px] flex-col">
              <Chat key={chatKey} sessionId={sessionId} />
              <button
                onClick={handleStartAssessment}
                className="mt-3 rounded-xl bg-indigo-600 py-3 text-sm font-semibold text-white shadow transition hover:bg-indigo-700"
              >
                📝 我感觉学会了，开始后测 →
              </button>
            </div>
          ) : showQuiz && question ? (
            <>
              <div className="mb-3 flex items-center justify-between">
                <span className="text-xs text-gray-400">
                  {stage === "DIAGNOSIS"
                    ? "诊断测评中：系统正在摸清你的掌握情况"
                    : "后测中：检验本次教学效果"}
                </span>
                {answerFeedback && (
                  <span className="text-xs text-gray-500">
                    上次回答：{answerFeedback.correct ? "正确 ✅" : "错误 ❌"}
                  </span>
                )}
              </div>
              <QuizCard
                key={question.id}
                question={question}
                onSubmit={handleAnswer}
              />
            </>
          ) : (
            <div className="rounded-2xl border border-gray-200 bg-white p-8 text-center text-sm text-gray-500">
              {stage === "PLANNING" && "正在为你规划学习路径…"}
              {stage === "REPLAN" && "正在重新规划…"}
              {stage === "INIT" && "会话初始化中…"}
            </div>
          )}
        </div>

        {/* 右：进度 */}
        <div className="lg:col-span-1">
          <ProgressPanel
            data={
              progress || {
                session_id: sessionId,
                stage,
                goal,
                current_node_id: currentNodeId,
                nodes: [],
              }
            }
          />
        </div>
      </div>
    </main>
  );
}
