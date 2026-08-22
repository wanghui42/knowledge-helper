# -*- coding: utf-8 -*-
"""E2E 集成测试：开始 → 诊断 → 规划 → 教学 → 后测 → 状态更新（文档第 17 节）。

使用 FastAPI TestClient + 确定性 provider，完整跑通学习闭环。
"""
import importlib
import os
import sys
import tempfile
from pathlib import Path

# 先把 backend 加入路径（不导入任何子模块）
BACKEND = str(Path(__file__).resolve().parent.parent / "backend")
sys.path.insert(0, BACKEND)

# 临时数据库路径
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
TMP_DB_URL = f"sqlite:///{_tmp.name}"
os.environ["DATABASE_URL"] = TMP_DB_URL

# 强制按新 URL 加载 config 与 database
import config
config.DATABASE_URL = TMP_DB_URL

import database  # noqa: E402
import sqlalchemy
from sqlalchemy import create_engine
database.engine = create_engine(TMP_DB_URL, connect_args={"check_same_thread": False})
database.SessionLocal = sqlalchemy.orm.sessionmaker(
    bind=database.engine, autoflush=False, autocommit=False
)

# 现在才加载 main
import pytest
from fastapi.testclient import TestClient

# 强制确定性 provider
config.LLM_PROVIDER = "deterministic"
config.OPENAI_API_KEY = ""

# 关键：让 providers 用确定性实现
import agents.providers as _ap
importlib.reload(_ap)

import main  # noqa: E402
# 让 main 内部的 engine/database 引用也指向新库
main.engine = database.engine
main.Base = database.Base
import orchestration.learning_loop as _ll
_ll.engine = database.engine


@pytest.fixture(scope="module")
def client():
    database.Base.metadata.create_all(bind=database.engine)
    with TestClient(main.app) as c:
        yield c
    database.engine.dispose()
    Path(_tmp.name).unlink(missing_ok=True)


def test_full_learning_loop(client):
    r = client.post("/api/learning/start", json={"goal": "学习微积分", "subject": "math"})
    assert r.status_code == 200
    data = r.json()
    assert data["stage"] == "DIAGNOSIS"
    assert data["question"] is not None
    session_id = data["session_id"]

    answered = 0
    question = data["question"]
    while question is not None and answered < 8:
        r = client.post(f"/api/learning/{session_id}/answer", json={"question_id": question["id"], "answer": 0})
        assert r.status_code == 200
        resp = r.json()
        answered += 1
        question = resp["question"]
        if resp["stage"] in ("TEACHING", "COMPLETE"):
            break

    r = client.get(f"/api/learning/{session_id}")
    assert r.status_code == 200
    state = r.json()
    assert state["stage"] in ("TEACHING", "COMPLETE")

    r = client.get(f"/api/learning/{session_id}/map")
    assert r.status_code == 200
    map_data = r.json()
    assert len(map_data["nodes"]) >= 6
    ids = {n["id"] for n in map_data["nodes"]}
    for e in map_data["edges"]:
        assert e["source"] in ids and e["target"] in ids

    if state["stage"] == "TEACHING":
        with client.stream("POST", f"/api/learning/{session_id}/message", json={"message": "请讲解极限"}) as resp:
            assert resp.status_code == 200
            body = "".join(resp.iter_text())
        assert "data:" in body

        r = client.post(f"/api/learning/{session_id}/start-assessment")
        assert r.status_code == 200
        aq = r.json()["question"]
        assert aq is not None

        answered_assess = 0
        while aq is not None and answered_assess < 5:
            r = client.post(f"/api/learning/{session_id}/answer", json={"question_id": aq["id"], "answer": 0})
            assert r.status_code == 200
            resp = r.json()
            answered_assess += 1
            aq = resp["question"]

        r = client.get(f"/api/learning/{session_id}/progress")
        assert r.status_code == 200
        progress = r.json()
        assert len(progress["nodes"]) >= 6

    r = client.get(f"/api/learning/{session_id}/events")
    assert r.status_code == 200
    events = r.json()
    assert len(events) > 0


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_session_404(client):
    r = client.get("/api/learning/not_exist")
    assert r.status_code == 404
