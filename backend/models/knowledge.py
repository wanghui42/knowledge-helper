# -*- coding: utf-8 -*-
"""knowledge_nodes / knowledge_edges 表：知识地图 DAG。"""
from sqlalchemy import String, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    subject: Mapped[str] = mapped_column(String(64), default="math", index=True)
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, default="")
    difficulty: Mapped[float] = mapped_column(Float, default=0.5)  # 0-1
    importance: Mapped[float] = mapped_column(Float, default=0.5)  # 0-1
    confidence: Mapped[float] = mapped_column(Float, default=1.0)  # LLM 生成置信度
    version: Mapped[int] = mapped_column(default=1)

    outgoing: Mapped[list["KnowledgeEdge"]] = relationship(
        foreign_keys="KnowledgeEdge.source_id", back_populates="source"
    )
    incoming: Mapped[list["KnowledgeEdge"]] = relationship(
        foreign_keys="KnowledgeEdge.target_id", back_populates="target"
    )


class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(64), ForeignKey("knowledge_nodes.id"), index=True)
    target_id: Mapped[str] = mapped_column(String(64), ForeignKey("knowledge_nodes.id"), index=True)
    relation: Mapped[str] = mapped_column(String(32), default="prerequisite")  # prerequisite | related
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    source: Mapped["KnowledgeNode"] = relationship(foreign_keys=[source_id], back_populates="outgoing")
    target: Mapped["KnowledgeNode"] = relationship(foreign_keys=[target_id], back_populates="incoming")
