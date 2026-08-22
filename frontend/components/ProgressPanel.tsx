"use client";

import type { ProgressResponse, SessionStage } from "@/lib/types";

const STAGE_LABEL: Record<SessionStage, string> = {
  INIT: "初始化",
  DIAGNOSIS: "诊断测评",
  PLANNING: "规划路径",
  TEACHING: "教学",
  ASSESSMENT: "后测",
  REPLAN: "重新规划",
  COMPLETE: "已完成",
};

const STATUS_COLOR: Record<string, string> = {
  weak: "text-red-600 bg-red-50",
  developing: "text-amber-600 bg-amber-50",
  mastered: "text-green-600 bg-green-50",
  stable: "text-blue-600 bg-blue-50",
  untested: "text-gray-500 bg-gray-100",
};

export default function ProgressPanel({ data }: { data: ProgressResponse }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4">
      <h3 className="mb-3 text-sm font-semibold text-gray-700">
        📊 学习进度（Progress）
      </h3>

      <div className="mb-4 rounded-lg bg-indigo-50 p-3">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">当前阶段</span>
          <span className="rounded-full bg-indigo-600 px-2.5 py-0.5 text-xs font-semibold text-white">
            {STAGE_LABEL[data.stage] ?? data.stage}
          </span>
        </div>
        <div className="mt-2 text-sm font-medium text-gray-800">
          🎯 {data.goal}
        </div>
        {data.current_node_id && (
          <div className="mt-1 text-xs text-gray-500">
            当前教学节点：<b>{data.current_node_id}</b>
          </div>
        )}
      </div>

      <div className="space-y-2">
        {data.nodes.map((n) => (
          <div key={n.node_id} className="rounded-lg border border-gray-100 p-2.5">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-800">{n.title}</span>
              <span
                className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${STATUS_COLOR[n.status] ?? STATUS_COLOR.untested}`}
              >
                {n.status}
              </span>
            </div>
            {n.evidence_count > 0 ? (
              <>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-gray-100">
                  <div
                    className="h-full rounded-full bg-indigo-500 transition-all"
                    style={{ width: `${Math.min(n.overall * 100, 100)}%` }}
                  />
                </div>
                <div className="mt-1 flex justify-between text-[11px] text-gray-400">
                  <span>概念 {n.conceptual.toFixed(2)}</span>
                  <span>流程 {n.procedural.toFixed(2)}</span>
                  <span>迁移 {n.transfer.toFixed(2)}</span>
                  <span>综合 {n.overall.toFixed(2)}</span>
                </div>
              </>
            ) : (
              <div className="mt-1 text-[11px] text-gray-400">尚未测评</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
