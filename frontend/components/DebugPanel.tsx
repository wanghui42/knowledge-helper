"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { EventItem } from "@/lib/types";

interface Props {
  sessionId: string;
}

export default function DebugPanel({ sessionId }: Props) {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [open, setOpen] = useState(true);

  async function refresh() {
    try {
      setEvents(await api.events(sessionId));
    } catch {
      /* 忽略 */
    }
  }

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 3000);
    return () => clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  return (
    <div className="rounded-xl border border-dashed border-gray-300 bg-white/60 p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-600">
          🐞 调试面板（Debug）
        </h3>
        <div className="flex gap-1">
          <button
            onClick={() => setOpen(!open)}
            className="rounded px-2 py-0.5 text-xs text-gray-500 hover:bg-gray-100"
          >
            {open ? "收起" : "展开"}
          </button>
          <button
            onClick={refresh}
            className="rounded px-2 py-0.5 text-xs text-gray-500 hover:bg-gray-100"
          >
            刷新
          </button>
        </div>
      </div>

      {open && (
        <div className="max-h-56 space-y-1 overflow-y-auto font-mono text-[11px] text-gray-500">
          {events.length === 0 && <div className="text-gray-400">暂无事件</div>}
          {events.map((e) => (
            <div key={e.id} className="flex gap-2 border-b border-gray-100 pb-1">
              <span className="shrink-0 text-indigo-500">{e.event_type}</span>
              <span className="truncate text-gray-400">
                {JSON.stringify(e.payload)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
