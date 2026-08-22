// 前后端共享类型（对应文档第 11 节）

export type SessionStage =
  | "INIT"
  | "DIAGNOSIS"
  | "PLANNING"
  | "TEACHING"
  | "ASSESSMENT"
  | "REPLAN"
  | "COMPLETE";

export interface Question {
  id: string;
  node_id: string;
  skill: string;
  type: string;
  question: string;
  options: string[];
  difficulty: number;
}

export interface KnowledgeNodeView {
  id: string;
  title: string;
  description: string;
  difficulty: number;
  importance: number;
  mastery: number | null;
  status: "weak" | "developing" | "mastered" | "stable" | "none" | "untested";
}

export interface KnowledgeEdgeView {
  source: string;
  target: string;
  relation: "prerequisite" | "related";
}

export interface KnowledgeMapData {
  nodes: KnowledgeNodeView[];
  edges: KnowledgeEdgeView[];
}

export interface StartResponse {
  session_id: string;
  stage: SessionStage;
  goal: string;
  subject: string;
  question: Question | null;
}

export interface AnswerResponse {
  correct: boolean;
  stage: SessionStage;
  question: Question | null;
}

export interface ProgressNode {
  node_id: string;
  title: string;
  conceptual: number;
  procedural: number;
  transfer: number;
  overall: number;
  evidence_count: number;
  status: string;
}

export interface ProgressResponse {
  session_id: string;
  stage: SessionStage;
  goal: string;
  current_node_id: string | null;
  nodes: ProgressNode[];
}

export interface EventItem {
  id: number;
  event_type: string;
  payload: Record<string, unknown>;
  created_at: string | null;
}

export interface SessionState {
  session_id: string;
  stage: SessionStage;
  goal: string;
  subject: string;
  current_node_id: string | null;
  current_question_id?: string | null;
  question?: Question | null;
}
