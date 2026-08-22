"use client";

import { useEffect, useState } from "react";
import { marked } from "marked";
import katex from "katex";

/**
 * Markdown + LaTeX 渲染。
 *
 * 关键：必须先提取保护 LaTeX 公式，再做 markdown 渲染，最后还原为 KaTeX HTML。
 * 否则 marked 会把 `$x>2$` 中的 `>` 转义成 `&gt;`，导致 KaTeX 无法渲染，
 * 最终显示为字面文本 `x&gt;2`（bug 根因）。
 */
function renderMarkdown(src: string): string {
  const blocks: string[] = [];

  // 1. 提取并保护 LaTeX 公式（先块级 $$...$$，后行内 $...$）
  let s = src || "";
  s = s.replace(/\$\$([\s\S]+?)\$\$/g, (m) => {
    blocks.push(m);
    return `\u0000LATEX${blocks.length - 1}\u0000`;
  });
  s = s.replace(/\$([^$\n]+?)\$/g, (m) => {
    blocks.push(m);
    return `\u0000LATEX${blocks.length - 1}\u0000`;
  });

  // 2. markdown 渲染（占位符不受影响）
  const md = marked.parse(s) as string;

  // 3. 还原占位符并渲染为 KaTeX
  return md.replace(/\u0000LATEX(\d+)\u0000/g, (_m, i) => {
    const blk = blocks[Number(i)];
    const display = blk.startsWith("$$");
    const tex = blk
      .replace(/^\$\$?/, "")
      .replace(/\$\$$/, "")
      .replace(/\$$/, "");
    try {
      return katex.renderToString(tex.trim(), {
        displayMode: display,
        throwOnError: false,
      });
    } catch {
      return blk; // 渲染失败时回退为原文
    }
  });
}

export default function MarkdownView({ content }: { content: string }) {
  const [html, setHtml] = useState("");

  useEffect(() => {
    setHtml(renderMarkdown(content));
  }, [content]);

  return (
    <div
      className="markdown-body space-y-2 text-[15px] leading-relaxed"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
