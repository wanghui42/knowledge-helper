"use client";

import KnowledgeWorkspace from "@/components/KnowledgeWorkspace";

export default function StartPage() {
  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8 md:px-8 md:py-10">
      <header className="mx-auto mb-10 flex w-full max-w-7xl items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-lg text-white shadow-sm">
            ✦
          </div>
          <div>
            <div className="text-sm font-bold tracking-tight text-slate-900">Knowledge Helper</div>
            <div className="text-xs text-slate-400">Adaptive Learning Workspace</div>
          </div>
        </div>
        <div className="hidden text-xs text-slate-400 sm:block">MVP · Knowledge-first prototype</div>
      </header>

      <KnowledgeWorkspace />

      <p className="mx-auto mt-6 max-w-7xl text-center text-xs leading-5 text-slate-400">
        当前版本先验证知识输入与结构可视化；LLM 生成、诊断和学习状态将在后续阶段接入。
      </p>
    </main>
  );
}
