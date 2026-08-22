"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import mermaid from "mermaid";

const DEFAULT_MERMAID = `flowchart TD
  A[函数基础] --> B[极限概念]
  B --> C[导数定义]
  C --> D[微分应用]
  D --> E[积分基础]

  classDef focus fill:#eff6ff,stroke:#4f46e5,color:#312e81,stroke-width:2px;
  classDef normal fill:#ffffff,stroke:#cbd5e1,color:#334155;
  class A,B,C,D,E normal;
  class B focus;`;

function escapeLabel(value: string) {
  return value.replace(/"/g, "&quot;").replace(/\n/g, " ");
}

function buildLocalMap(input: string) {
  const text = input.trim();
  if (!text) return DEFAULT_MERMAID;

  const candidates = [
    { key: "函数", label: "函数基础" },
    { key: "极限", label: "极限" },
    { key: "导数", label: "导数" },
    { key: "微分", label: "微分" },
    { key: "积分", label: "积分" },
    { key: "概率", label: "概率" },
    { key: "统计", label: "统计" },
    { key: "矩阵", label: "矩阵" },
    { key: "向量", label: "向量" },
    { key: "线性代数", label: "线性代数" },
  ];

  const found = candidates.filter((item) => text.includes(item.key));
  const nodes = found.length >= 2 ? found : candidates.slice(0, 4);

  const lines = ["flowchart TD"];
  for (let i = 0; i < nodes.length; i += 1) {
    lines.push(`  N${i}["${escapeLabel(nodes[i].label)}"]`);
    if (i > 0) lines.push(`  N${i - 1} --> N${i}`);
  }
  lines.push("  classDef normal fill:#ffffff,stroke:#cbd5e1,color:#334155;");
  lines.push("  class N0 normal;");
  return lines.join("\n");
}

export default function KnowledgeWorkspace() {
  const [mode, setMode] = useState<"natural" | "mermaid">("natural");
  const [input, setInput] = useState("我想系统学习微积分，已经会函数，希望真正理解极限、导数和积分之间的关系。");
  const [code, setCode] = useState(DEFAULT_MERMAID);
  const [rendered, setRendered] = useState(true);
  const [renderError, setRenderError] = useState("");
  const [selectedNode, setSelectedNode] = useState<string | null>("极限概念");
  const previewRef = useRef<HTMLDivElement>(null);

  const previewCode = useMemo(
    () => (mode === "natural" ? buildLocalMap(input) : code),
    [code, input, mode],
  );

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: "base",
      securityLevel: "strict",
      flowchart: { htmlLabels: true, curve: "basis" },
      themeVariables: {
        primaryColor: "#ffffff",
        primaryTextColor: "#0f172a",
        primaryBorderColor: "#cbd5e1",
        lineColor: "#94a3b8",
        secondaryColor: "#eff6ff",
        tertiaryColor: "#f8fafc",
        fontFamily: "PingFang SC, Microsoft YaHei, sans-serif",
      },
    });
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function render() {
      if (!previewRef.current) return;
      setRendered(false);
      setRenderError("");
      try {
        const id = `knowledge-map-${Date.now()}`;
        const { svg } = await mermaid.render(id, previewCode);
        if (cancelled || !previewRef.current) return;
        previewRef.current.innerHTML = svg;
        const svgElement = previewRef.current.querySelector("svg");
        if (svgElement) {
          svgElement.style.maxWidth = "100%";
          svgElement.style.height = "auto";
          svgElement.setAttribute("preserveAspectRatio", "xMidYMid meet");
        }
        setRendered(true);
      } catch (error) {
        if (cancelled) return;
        setRenderError(error instanceof Error ? error.message : String(error));
      }
    }
    render();
    return () => {
      cancelled = true;
    };
  }, [previewCode]);

  function handleReset() {
    setInput("");
    setCode(DEFAULT_MERMAID);
    setSelectedNode(null);
  }

  return (
    <section className="mx-auto w-full max-w-7xl">
      <div className="mb-8 text-center">
        <div className="mb-3 inline-flex items-center rounded-full border border-indigo-100 bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700">
          Knowledge Workspace · MVP
        </div>
        <h1 className="text-4xl font-semibold tracking-tight text-slate-900 md:text-5xl">你想学什么？</h1>
        <p className="mx-auto mt-3 max-w-2xl text-sm leading-6 text-slate-500 md:text-base">
          先把你想学习的内容告诉系统。右侧会把知识结构可视化；后续再由 LLM 负责生成和分析。
        </p>
      </div>

      <div className="overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-[0_20px_60px_-25px_rgba(15,23,42,0.20)]">
        <div className="flex flex-col border-b border-slate-200 lg:flex-row">
          <div className="flex-1 border-b border-slate-200 p-6 lg:border-b-0 lg:border-r lg:p-8">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold text-slate-900">知识输入</div>
                <div className="mt-1 text-xs text-slate-400">现在先用本地逻辑模拟，后续接 LLM。</div>
              </div>
              <button
                type="button"
                onClick={handleReset}
                className="rounded-lg px-2.5 py-1.5 text-xs text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
              >
                清空
              </button>
            </div>

            <div className="mb-4 inline-flex rounded-xl bg-slate-100 p-1 text-xs font-medium">
              <button
                type="button"
                onClick={() => setMode("natural")}
                className={`rounded-lg px-3 py-2 transition ${mode === "natural" ? "bg-white text-slate-900 shadow-sm" : "text-slate-500"}`}
              >
                自然语言
              </button>
              <button
                type="button"
                onClick={() => setMode("mermaid")}
                className={`rounded-lg px-3 py-2 transition ${mode === "mermaid" ? "bg-white text-slate-900 shadow-sm" : "text-slate-500"}`}
              >
                Mermaid
              </button>
            </div>

            {mode === "natural" ? (
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="例如：我想学习微积分，目前会函数和初等代数，但对极限没有直觉，希望最终能理解导数和积分。"
                className="min-h-[290px] w-full resize-none rounded-2xl border border-slate-200 bg-slate-50/70 p-5 text-[15px] leading-7 text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-indigo-300 focus:bg-white focus:ring-4 focus:ring-indigo-50"
              />
            ) : (
              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                spellCheck={false}
                className="min-h-[290px] w-full resize-none rounded-2xl border border-slate-200 bg-slate-950 p-5 font-mono text-xs leading-6 text-slate-200 outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
              />
            )}

            <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
              <div className="text-xs text-slate-400">
                {mode === "natural" ? "本地预览：关键词 → 简单知识链" : "高级模式：直接编辑 Mermaid 源码"}
              </div>
              <button
                type="button"
                onClick={() => setRendered(true)}
                className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700"
              >
                更新知识地图 →
              </button>
            </div>
          </div>

          <div className="flex-1 bg-slate-50/70 p-6 lg:p-8">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold text-slate-900">知识地图</div>
                <div className="mt-1 text-xs text-slate-400">当前只是结构预览，尚未进入诊断。</div>
              </div>
              <div className="rounded-lg bg-white px-2.5 py-1.5 text-xs font-medium text-slate-500 shadow-sm">
                {rendered ? "已渲染" : "渲染中…"}
              </div>
            </div>

            <div className="relative min-h-[360px] overflow-hidden rounded-2xl border border-slate-200 bg-white">
              <div className="pointer-events-none absolute inset-x-0 top-0 h-12 bg-gradient-to-b from-white to-transparent" />
              {renderError ? (
                <div className="m-5 rounded-xl border border-red-100 bg-red-50 p-4 text-xs leading-5 text-red-700">
                  <div className="font-semibold">Mermaid 渲染失败</div>
                  <div className="mt-1 break-words">{renderError}</div>
                </div>
              ) : (
                <div className="h-[360px] overflow-auto p-5">
                  <div ref={previewRef} className="flex min-h-full items-center justify-center [&>svg]:max-w-full" />
                </div>
              )}
            </div>

            <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-500">
              <button
                type="button"
                onClick={() => setSelectedNode("函数基础")}
                className={`rounded-full border px-3 py-1.5 transition ${selectedNode === "函数基础" ? "border-indigo-200 bg-indigo-50 text-indigo-700" : "border-slate-200 bg-white"}`}
              >
                函数基础
              </button>
              <button
                type="button"
                onClick={() => setSelectedNode("极限概念")}
                className={`rounded-full border px-3 py-1.5 transition ${selectedNode === "极限概念" ? "border-indigo-200 bg-indigo-50 text-indigo-700" : "border-slate-200 bg-white"}`}
              >
                极限概念
              </button>
              <span className="rounded-full border border-slate-200 bg-white px-3 py-1.5">当前节点：{selectedNode ?? "未选择"}</span>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-4 border-t border-slate-200 bg-white p-5 md:flex-row md:items-center md:justify-between md:px-8">
          <div>
            <div className="text-sm font-semibold text-slate-900">下一步</div>
            <div className="mt-1 text-xs text-slate-400">确认知识结构后，再开始诊断和建立你的 Learner State。</div>
          </div>
          <button
            type="button"
            className="rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-400"
            disabled
            title="后续接入学习会话"
          >
            确认地图，开始诊断 →
          </button>
        </div>
      </div>
    </section>
  );
}
