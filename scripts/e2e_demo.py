# -*- coding: utf-8 -*-
"""E2E 联调脚本：创建会话 → 完成诊断 → 教学 → 后测 → 状态更新。"""
import json
import time
import urllib.request

BASE = "http://localhost:8000/api/learning"


def post(path, body):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def get(path):
    with urllib.request.urlopen(BASE + path) as r:
        return json.loads(r.read().decode())


# 1. 创建会话
data = post("/start", {"goal": "学习微积分", "subject": "math"})
sid = data["session_id"]
print(f"[1] session={sid} stage={data['stage']}")

# 2. 诊断答题（最多 8 题）
q = data["question"]
n = 0
while q and n < 8:
    # 前两题故意答错，之后全对，观察 mastery 变化
    answer = 0 if n >= 2 else 1
    res = post(f"/{sid}/answer", {"question_id": q["id"], "answer": answer})
    n += 1
    print(f"    Q{n} [{q['skill']}] -> {'正确' if res['correct'] else '错误'} stage={res['stage']}")
    q = res["question"]
    if res["stage"] == "TEACHING":
        break

print(f"[2] 诊断完成，共 {n} 题，stage={res['stage']}")

# 3. 知识地图
mm = get(f"/{sid}/map")
print(f"[3] 知识地图: {len(mm['nodes'])} 节点, {len(mm['edges'])} 边")

# 4. 教学对话（SSE 流式）
req = urllib.request.Request(
    BASE + f"/{sid}/message", data=json.dumps({"message": "请讲解一下极限"}).encode(),
    headers={"Content-Type": "application/json"}, method="POST",
)
with urllib.request.urlopen(req) as r:
    sse_body = r.read().decode()
print(f"[4] SSE 流式回复: {len(sse_body)} 字节, 含 {sse_body.count('data:')} 个事件")

# 5. 启动后测
a = post(f"/{sid}/start-assessment", {})
print(f"[5] 后测启动 stage={a['stage']} question={a['question']['id'] if a['question'] else None}")

# 6. 完成后测（全对）
q = a["question"]
m = 0
while q and m < 5:
    res = post(f"/{sid}/answer", {"question_id": q["id"], "answer": 0})
    m += 1
    print(f"    A{m} [{q['skill']}] -> {'正确' if res['correct'] else '错误'} stage={res['stage']}")
    q = res["question"]

# 7. 最终状态
st = get(f"/{sid}")
print(f"[6] 最终 stage={st['stage']}")

# 8. 进度
pg = get(f"/{sid}/progress")
print(f"[7] 进度: {len(pg['nodes'])} 节点")
for n in pg["nodes"][:4]:
    print(f"    {n['node_id']}: overall={n['overall']:.2f} status={n['status']}")

# 9. 事件
ev = get(f"/{sid}/events")
print(f"[8] 事件数: {len(ev)}")
types = [e["event_type"] for e in ev]
print(f"    事件类型: {sorted(set(types))}")
print("\n✅ E2E 联调完成")
