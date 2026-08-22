# -*- coding: utf-8 -*-
"""全局配置：从环境变量 / .env 读取。"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'app.db'}")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
# "auto"：有 key 用 OpenAI Agents SDK；无 key 用确定性 fallback（演示/测试模式）
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")
SEED_DATA_PATH = BASE_DIR / "seed" / "microcalculus.json"
