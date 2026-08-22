"use client";

import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";
import type { KnowledgeMapData } from "@/lib/types";

mermaid.initialize({
  startOnLoad: false,
  theme: "default",
  securityLevel: "loose",
  fontFamily: "PingFang SC, Microsoft YaHei, sans-serif",
});

function toMermaid(data: KnowledgeMapData): string {
  const lines = ["flowchart TD"];
  lines.push('classDef weak fill:#fee2e2,stroke:#ef4444,color:#7f1d1d;');
  lines.push('classDef developing fill:#fef3c7,stroke:#f59e0b,color:#78350f;');
  lines.push('classDef mastered fill:#dcfce7,stroke:#22c55e,color:#14532d;');
  lines.push('classDef stable fill:#dbeafe,stroke:#3b82f6,color:#1e3a8a;');
  lines.push('classDef none fill:#f3f4f6,stroke:#9ca3af,color:#374151;');
  lines.push('classDef untested fill:#f3f4f6,stroke:#9ca3af,color:#374151;');

  for (const n of data.nodes) {
    const label = n.mastery != null
      ? `${n.title} (${n.mastery.toFixed(2)})`
      : n.title;
    const status = n.status || "none";
    lines.push(`    ${n.id}["${label.replace(/"/g, "&quot;")}"]:::${status}`);
  }
  for (const e of data.edges) {
    const arrow = e.relation === "prerequisite" ? "-->|前置|" : "---|相关|";
    lines.push(`    ${e.source}${arrow}${e.target}`);
  }
  return lines.join("\n");
}

export default function KnowledgeMap({ data }: { data: KnowledgeMapData }) {
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!data || !ref.current) return;
    const code = toMermaid(data);
    const el = ref.current;
    el.innerHTML = "";
    mermaid
      .render(`mmd-${Date.now()}`, code)
      .then(({ svg }) => {
        el.innerHTML = svg;
      })
      .catch((e) => setError(String(e)));
  }, [data]);

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4">
      <h3 className="mb-3 text-sm font-semibold text-gray-700">
        🗺️ 知识地图（Knowledge Map）
      </h3>
      {error && (
        <div className="mb-2 rounded bg-red-50 px-3 py-2 text-xs text-red-600">
          Mermaid 渲染失败：{error}
        </div>
      )}
      <div className="mermaid-container overflow-x-auto" ref={ref} />
      <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-gray-500">
        <span className="flex items-center gap-1">
          <i className="h-2.5 w-2.5 rounded-sm bg-red-200" /> weak
        </span>
        <span className="flex items-center gap-1">
          <i className="h-2.5 w-2.5 rounded-sm bg-amber-200" /> developing
        </span>
        <span className="flex items-center gap-1">
          <i className="h-2.5 w-2.5 rounded-sm bg-green-200" /> mastered
        </span>
        <span className="flex items-center gap-1">
          <i className="h-2.5 w-2.5 rounded-sm bg-blue-200" /> stable
        </span>
        <span className="flex items-center gap-1">
          <i className="h-2.5 w-2.5 rounded-sm bg-gray-200" /> 未测
        </span>
      </div>
    </div>
  );
}
