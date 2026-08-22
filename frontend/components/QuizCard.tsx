"use client";

import { useState } from "react";
import type { Question } from "@/lib/types";
import MarkdownView from "./MarkdownView";

const SKILL_COLORS: Record<string, string> = {
  Concept: "bg-indigo-100 text-indigo-700",
  Procedure: "bg-emerald-100 text-emerald-700",
  Transfer: "bg-amber-100 text-amber-700",
};

const OPTION_LETTERS = ["A", "B", "C", "D"];

interface Props {
  question: Question;
  onSubmit: (answerIndex: number) => Promise<void>;
  disabled?: boolean;
}

export default function QuizCard({ question, onSubmit, disabled }: Props) {
  const [selected, setSelected] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ correct: boolean } | null>(null);

  async function submit(idx: number) {
    if (selected !== null || submitting) return;
    setSelected(idx);
    setSubmitting(true);
    try {
      const r = await onSubmit(idx);
      setResult(r);
    } catch (e) {
      console.error(e);
      setSelected(null);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600">
          测评 · {question.skill}
        </span>
        <span className="text-xs text-gray-400">
          难度 {question.difficulty.toFixed(2)}
        </span>
      </div>

      <MarkdownView content={question.question} />

      <div className="mt-4 space-y-2">
        {question.options.map((opt, i) => {
          const isSelected = selected === i;
          const isCorrect = result?.correct === true && isSelected;
          const isWrong = result?.correct === false && isSelected;
          return (
            <button
              key={i}
              onClick={() => submit(i)}
              disabled={disabled || selected !== null}
              className={[
                "flex w-full items-start gap-3 rounded-lg border px-4 py-3 text-left text-sm transition",
                isSelected
                  ? isCorrect
                    ? "border-green-400 bg-green-50"
                    : isWrong
                      ? "border-red-400 bg-red-50"
                      : "border-indigo-400 bg-indigo-50"
                  : "border-gray-200 bg-white hover:border-indigo-300 hover:bg-indigo-50/50",
                disabled || selected !== null ? "cursor-default opacity-90" : "cursor-pointer",
              ].join(" ")}
            >
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-gray-100 text-xs font-semibold text-gray-600">
                {OPTION_LETTERS[i]}
              </span>
              <MarkdownView content={opt} />
            </button>
          );
        })}
      </div>

      {result && (
        <div
          className={`mt-4 rounded-lg px-4 py-2 text-sm font-medium ${
            result.correct ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
          }`}
        >
          {result.correct ? "✅ 回答正确！" : "❌ 回答错误，没关系，继续加油！"}
        </div>
      )}
    </div>
  );
}
