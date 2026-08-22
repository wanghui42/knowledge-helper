# -*- coding: utf-8 -*-
"""mermaid.py：知识地图 → Mermaid flowchart（文档第 16 节数据接口）。"""
from __future__ import annotations


def nodes_to_mermaid(nodes: list[dict], edges: list[dict]) -> str:
    """把 {id,title,mastery,status} 节点与 {source,target,relation} 边转为 Mermaid 代码。"""
    lines = ["flowchart TD"]
    status_class = {
        "weak": "classDef weak fill:#fee2e2,stroke:#ef4444,color:#7f1d1d;",
        "developing": "classDef developing fill:#fef3c7,stroke:#f59e0b,color:#78350f;",
        "mastered": "classDef mastered fill:#dcfce7,stroke:#22c55e,color:#14532d;",
        "stable": "classDef stable fill:#dbeafe,stroke:#3b82f6,color:#1e3a8a;",
        "none": "classDef none fill:#f3f4f6,stroke:#9ca3af,color:#374151;",
    }
    for c in status_class.values():
        lines.append(c)

    for n in nodes:
        node_id = n["id"]
        title = n.get("title", node_id)
        mastery = n.get("mastery")
        status = n.get("status", "none")
        label = title
        if mastery is not None:
            label = f"{title} ({mastery:.2f})"
        # 转义括号外的特殊字符
        safe = label.replace("(", "&#40;").replace(")", "&#41;").replace('"', "&quot;")
        lines.append(f'    {node_id}["{safe}"]:::{status}')

    for e in edges:
        arrow = "-->|prerequisite|" if e.get("relation", "prerequisite") == "prerequisite" else "---"
        lines.append(f"    {e['source']}{arrow}{e['target']}")

    return "\n".join(lines)
