# -*- coding: utf-8 -*-
"""验证答题后地图状态切换。"""
import json
import urllib.request

BASE = "http://localhost:8000/api/learning"
SID = "sess_5bcea5a3c365"


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


# 答对第一题（q_function_01 正确答案 index 1）
r1 = post(f"/{SID}/answer", {"question_id": "q_function_01", "answer": 1})
print("Q1 correct:", r1["correct"], "stage:", r1["stage"])

# 再答一题（答错，q_function_02 正确答案 index 0）
r2 = post(f"/{SID}/answer", {"question_id": "q_function_02", "answer": 2})
print("Q2 correct:", r2["correct"], "stage:", r2["stage"])

print("--- map after answering ---")
d = get(f"/{SID}/map")
for n in d["nodes"]:
    print(f"  {n['id']:20s} mastery={n['mastery']} status={n['status']}")
