# -*- coding: utf-8 -*-
"""微积分 v0.1 种子数据：知识地图 + 诊断题库 + 后测题库 + 教学模板。

文档第 6 节给出 9 个知识节点的初始范围，这里展开为带属性描述的 DAG。
题目均带 SymPy 可验证字段（verify_type / math_expr / correct_answer_expr / limit_at）。
"""

KNOWLEDGE_MAP = {
    "subject": "math",
    "version": 1,
    "nodes": [
        {"id": "function", "title": "函数", "description": "函数定义、定义域、值域、复合函数", "difficulty": 0.3, "importance": 0.9},
        {"id": "limit", "title": "极限", "description": "极限直觉、极限运算、单侧极限", "difficulty": 0.5, "importance": 0.9},
        {"id": "continuity", "title": "连续性", "description": "连续定义、间断点分类", "difficulty": 0.5, "importance": 0.7},
        {"id": "average_rate", "title": "平均变化率", "description": "平均变化率概念", "difficulty": 0.4, "importance": 0.6},
        {"id": "derivative_definition", "title": "导数定义", "description": "导数定义、极限表达式", "difficulty": 0.6, "importance": 0.9},
        {"id": "derivative_geometry", "title": "切线斜率", "description": "切线斜率与瞬时变化率", "difficulty": 0.6, "importance": 0.8},
        {"id": "derivative_rules", "title": "基本求导法则", "description": "幂法则、和差法则、常数倍", "difficulty": 0.6, "importance": 0.9},
        {"id": "chain_rule", "title": "链式法则", "description": "复合函数求导", "difficulty": 0.75, "importance": 0.9},
        {"id": "integral", "title": "积分基础", "description": "不定积分、基本积分公式", "difficulty": 0.8, "importance": 0.8},
    ],
    "edges": [
        {"source": "function", "target": "limit", "relation": "prerequisite"},
        {"source": "function", "target": "average_rate", "relation": "prerequisite"},
        {"source": "limit", "target": "continuity", "relation": "prerequisite"},
        {"source": "limit", "target": "derivative_definition", "relation": "prerequisite"},
        {"source": "average_rate", "target": "derivative_definition", "relation": "prerequisite"},
        {"source": "derivative_definition", "target": "derivative_geometry", "relation": "prerequisite"},
        {"source": "derivative_definition", "target": "derivative_rules", "relation": "prerequisite"},
        {"source": "derivative_rules", "target": "chain_rule", "relation": "prerequisite"},
        {"source": "chain_rule", "target": "integral", "relation": "prerequisite"},
        {"source": "derivative_geometry", "target": "integral", "relation": "related"},
    ],
}

# ---- 诊断题库（每节点至少 2 题，覆盖不同 skill） ----
QUESTION_BANK: dict[str, list[dict]] = {
    "function": [
        {
            "id": "q_function_01", "node_id": "function", "skill": "Concept", "type": "mcq",
            "question": "函数 $f(x)=\\frac{1}{x-2}$ 的定义域是？",
            "options": ["所有实数", "除 $x=2$ 外的所有实数", "$x>2$", "$x<2$"],
            "correct_index": 1, "difficulty": 0.3,
        },
        {
            "id": "q_function_02", "node_id": "function", "skill": "Procedure", "type": "mcq",
            "question": "设 $f(x)=2x+1$，$g(x)=x^2$，则复合函数 $f(g(2))$ 的值是？",
            "options": ["9", "10", "17", "7"],
            "correct_index": 0, "difficulty": 0.35,
        },
    ],
    "limit": [
        {
            "id": "q_limit_01", "node_id": "limit", "skill": "Concept", "type": "mcq",
            "question": "极限 $\\lim_{x \\to 0} \\frac{\\sin x}{x}$ 的值是？",
            "options": ["0", "1", "$\\infty$", "不存在"],
            "correct_index": 1, "difficulty": 0.5,
            "verify_type": "limit", "math_expr": "sin(x)/x", "correct_answer_expr": "1", "limit_at": "0",
        },
        {
            "id": "q_limit_02", "node_id": "limit", "skill": "Procedure", "type": "mcq",
            "question": "计算极限 $\\lim_{x \\to 2} (x^2 - 1)$",
            "options": ["3", "5", "4", "7"],
            "correct_index": 0, "difficulty": 0.4,
            "verify_type": "limit", "math_expr": "x**2 - 1", "correct_answer_expr": "3", "limit_at": "2",
        },
    ],
    "continuity": [
        {
            "id": "q_cont_01", "node_id": "continuity", "skill": "Concept", "type": "mcq",
            "question": "函数在某点连续需要满足哪三个条件？",
            "options": [
                "存在极限、极限等于函数值、函数有定义",
                "左极限存在、右极限存在、导数存在",
                "函数有界、单调、可导",
                "导数存在、二阶导数存在、连续可导",
            ],
            "correct_index": 0, "difficulty": 0.5,
        },
        {
            "id": "q_cont_02", "node_id": "continuity", "skill": "Transfer", "type": "mcq",
            "question": "函数 $f(x)=\\begin{cases} x+1 & x<1 \\\\ 2 & x=1 \\\\ x^2 & x>1 \\end{cases}$ 在 $x=1$ 处：",
            "options": ["连续", "左连续但不连续", "右连续但不连续", "左右都不连续"],
            "correct_index": 2, "difficulty": 0.65,
        },
    ],
    "average_rate": [
        {
            "id": "q_avg_01", "node_id": "average_rate", "skill": "Concept", "type": "mcq",
            "question": "函数 $f(x)=x^2$ 在区间 $[1,3]$ 上的平均变化率是？",
            "options": ["2", "4", "6", "3"],
            "correct_index": 1, "difficulty": 0.45,
            "verify_type": "derivative", "math_expr": "x**2", "correct_answer_expr": "4",
        },
        {
            "id": "q_avg_02", "node_id": "average_rate", "skill": "Procedure", "type": "mcq",
            "question": "平均变化率 $\\frac{f(b)-f(a)}{b-a}$ 的几何意义是？",
            "options": [
                "割线的斜率",
                "切线的斜率",
                "函数的零点",
                "函数的极值",
            ],
            "correct_index": 0, "difficulty": 0.4,
        },
    ],
    "derivative_definition": [
        {
            "id": "q_def_01", "node_id": "derivative_definition", "skill": "Concept", "type": "mcq",
            "question": "导数定义的极限表达式 $f'(a)=\\lim_{h \\to 0} \\frac{f(a+h)-f(a)}{h}$ 中 $h$ 表示？",
            "options": [
                "自变量的增量",
                "函数值的增量",
                "曲线长度",
                "常数",
            ],
            "correct_index": 0, "difficulty": 0.55,
        },
        {
            "id": "q_def_02", "node_id": "derivative_definition", "skill": "Procedure", "type": "mcq",
            "question": "用定义求 $f(x)=x^2$ 在 $x=2$ 处的导数 $f'(2)$",
            "options": ["2", "4", "8", "0"],
            "correct_index": 1, "difficulty": 0.6,
        },
    ],
    "derivative_geometry": [
        {
            "id": "q_geo_01", "node_id": "derivative_geometry", "skill": "Concept", "type": "mcq",
            "question": "导数 $f'(a)$ 的几何意义是曲线 $y=f(x)$ 在点 $(a, f(a))$ 处？",
            "options": ["切线的斜率", "割线的长度", "曲线的曲率", "函数的极值"],
            "correct_index": 0, "difficulty": 0.5,
        },
        {
            "id": "q_geo_02", "node_id": "derivative_geometry", "skill": "Procedure", "type": "mcq",
            "question": "曲线 $y=x^3$ 在 $x=1$ 处的切线斜率是？",
            "options": ["1", "3", "6", "0"],
            "correct_index": 1, "difficulty": 0.55,
            "verify_type": "derivative", "math_expr": "x**3", "correct_answer_expr": "3*x**2",
        },
    ],
    "derivative_rules": [
        {
            "id": "q_rules_01", "node_id": "derivative_rules", "skill": "Procedure", "type": "mcq",
            "question": "求导：$\\frac{d}{dx}(3x^2 + 2x)$",
            "options": ["$6x + 2$", "$6x$", "$3x + 2$", "$2x^2 + 2$"],
            "correct_index": 0, "difficulty": 0.55,
            "verify_type": "derivative", "math_expr": "3*x**2 + 2*x", "correct_answer_expr": "6*x + 2",
        },
        {
            "id": "q_rules_02", "node_id": "derivative_rules", "skill": "Transfer", "type": "mcq",
            "question": "某物体位移 $s(t)=5t^2$（米），$t$ 秒时瞬时速度 $v(t)$ 为？",
            "options": ["$10t$ m/s", "$5t$ m/s", "$2.5t$ m/s", "$t^2$ m/s"],
            "correct_index": 0, "difficulty": 0.6,
            "verify_type": "derivative", "math_expr": "5*t**2", "correct_answer_expr": "10*t",
        },
    ],
    "chain_rule": [
        {
            "id": "q_chain_01", "node_id": "chain_rule", "skill": "Procedure", "type": "mcq",
            "question": "链式法则求导：$\\frac{d}{dx}(2x+1)^3$",
            "options": ["$6(2x+1)^2$", "$3(2x+1)^2$", "$6(2x+1)$", "$2(2x+1)^3$"],
            "correct_index": 0, "difficulty": 0.7,
            "verify_type": "derivative", "math_expr": "(2*x+1)**3", "correct_answer_expr": "6*(2*x+1)**2",
        },
        {
            "id": "q_chain_02", "node_id": "chain_rule", "skill": "Concept", "type": "mcq",
            "question": "链式法则 $\frac{d}{dx} f(g(x)) =$ ?",
            "options": ["$f'(g(x)) \\cdot g'(x)$", "$f'(x) \\cdot g'(x)$", "$f'(g(x))$", "$f(g'(x))$"],
            "correct_index": 0, "difficulty": 0.6,
        },
    ],
    "integral": [
        {
            "id": "q_int_01", "node_id": "integral", "skill": "Procedure", "type": "mcq",
            "question": "不定积分 $\\int 3x^2 \\, dx$ 是？",
            "options": ["$x^3 + C$", "$6x + C$", "$x^3$", "$\\frac{x^3}{3} + C$"],
            "correct_index": 0, "difficulty": 0.75,
        },
        {
            "id": "q_int_02", "node_id": "integral", "skill": "Concept", "type": "mcq",
            "question": "定积分 $\\int_0^1 2x \\, dx$ 的值是？",
            "options": ["1", "2", "$\\frac{1}{2}$", "0"],
            "correct_index": 0, "difficulty": 0.7,
        },
    ],
}

# ---- 后测题库（每节点 3 题：Concept / Procedure / Transfer） ----
ASSESSMENT_QUESTIONS: dict[str, list[dict]] = {
    "function": [
        {"id": "a_function_01", "node_id": "function", "skill": "Concept", "type": "mcq",
         "question": "下列哪一个是函数 $f(x)=\\sqrt{x-1}$ 的自然定义域？",
         "options": ["$x \\geq 1$", "$x > 0$", "$x \\geq 0$", "所有实数"],
         "correct_index": 0, "difficulty": 0.35},
        {"id": "a_function_02", "node_id": "function", "skill": "Procedure", "type": "mcq",
         "question": "若 $f(x)=x+3$，$g(x)=x^2$，求 $g(f(1))$",
         "options": ["16", "4", "25", "10"],
         "correct_index": 0, "difficulty": 0.4},
        {"id": "a_function_03", "node_id": "function", "skill": "Transfer", "type": "mcq",
         "question": "某快递费用：首重 1kg 内 8 元，每超 1kg 加 2 元，$x$ kg（$x>1$）总费用 $C(x)$ 为？",
         "options": ["$8 + 2(x-1)$", "$8x$", "$2x$", "$8+2x$"],
         "correct_index": 0, "difficulty": 0.45},
    ],
    "limit": [
        {"id": "a_limit_01", "node_id": "limit", "skill": "Concept", "type": "mcq",
         "question": "$\\lim_{x \\to 3} (2x+1)$ 等于？",
         "options": ["7", "5", "9", "6"],
         "correct_index": 0, "difficulty": 0.4,
         "verify_type": "limit", "math_expr": "2*x+1", "correct_answer_expr": "7", "limit_at": "3"},
        {"id": "a_limit_02", "node_id": "limit", "skill": "Procedure", "type": "mcq",
         "question": "$\\lim_{x \\to 0} \\frac{1-\\cos x}{x^2}$（可用洛必达或三角恒等式）",
         "options": ["$\\frac{1}{2}$", "1", "0", "不存在"],
         "correct_index": 0, "difficulty": 0.75,
         "verify_type": "limit", "math_expr": "(1-cos(x))/x**2", "correct_answer_expr": "1/2", "limit_at": "0"},
        {"id": "a_limit_03", "node_id": "limit", "skill": "Transfer", "type": "mcq",
         "question": "数列 $a_n = \\frac{n}{n+1}$，当 $n \\to \\infty$ 时趋近于？",
         "options": ["1", "0", "$\\infty$", "$\\frac{1}{2}$"],
         "correct_index": 0, "difficulty": 0.55},
    ],
    "continuity": [
        {"id": "a_cont_01", "node_id": "continuity", "skill": "Concept", "type": "mcq",
         "question": "若 $\\lim_{x \\to a} f(x) = f(a)$，则 $f$ 在 $a$ 处？",
         "options": ["连续", "可导", "有界", "单调"],
         "correct_index": 0, "difficulty": 0.4},
        {"id": "a_cont_02", "node_id": "continuity", "skill": "Procedure", "type": "mcq",
         "question": "确定 $k$ 使 $f(x)=\\begin{cases} x^2 & x<1 \\\\ k & x\\geq 1 \\end{cases}$ 在 $x=1$ 连续：$k=$?",
         "options": ["1", "2", "0", "-1"],
         "correct_index": 0, "difficulty": 0.6},
        {"id": "a_cont_03", "node_id": "continuity", "skill": "Transfer", "type": "mcq",
         "question": "介值定理的适用前提是？",
         "options": [
             "$f$ 在闭区间连续，$f(a) \\neq f(b)$，$u$ 介于两者之间",
             "$f$ 在开区间可导",
             "$f$ 单调递增",
             "$f$ 有界",
         ],
         "correct_index": 0, "difficulty": 0.65},
    ],
    "average_rate": [
        {"id": "a_avg_01", "node_id": "average_rate", "skill": "Concept", "type": "mcq",
         "question": "函数 $f(x)=x^3$ 在 $[0,2]$ 的平均变化率为？",
         "options": ["4", "8", "2", "6"],
         "correct_index": 0, "difficulty": 0.5},
        {"id": "a_avg_02", "node_id": "average_rate", "skill": "Procedure", "type": "mcq",
         "question": "$f(x)=2x+5$ 在任意区间 $[a,b]$ 的平均变化率恒为？",
         "options": ["2", "5", "$a+b$", "0"],
         "correct_index": 0, "difficulty": 0.45},
        {"id": "a_avg_03", "node_id": "average_rate", "skill": "Transfer", "type": "mcq",
         "question": "汽车 1 小时内行驶 80km，平均速度 $80$ km/h。这属于？",
         "options": ["平均变化率", "瞬时变化率", "加速度", "位移"],
         "correct_index": 0, "difficulty": 0.35},
    ],
    "derivative_definition": [
        {"id": "a_def_01", "node_id": "derivative_definition", "skill": "Concept", "type": "mcq",
         "question": "导数定义中，$\\lim_{h\\to0}\\frac{f(a+h)-f(a)}{h}$ 若存在，则 $f$ 在 $a$ 处？",
         "options": ["可导", "必连续但不一定可导", "必不连续", "无定义"],
         "correct_index": 0, "difficulty": 0.55},
        {"id": "a_def_02", "node_id": "derivative_definition", "skill": "Procedure", "type": "mcq",
         "question": "用定义求 $f(x)=x^3$ 在 $x=1$ 的导数 $f'(1)$",
         "options": ["3", "1", "6", "9"],
         "correct_index": 0, "difficulty": 0.7},
        {"id": "a_def_03", "node_id": "derivative_definition", "skill": "Transfer", "type": "mcq",
         "question": "$f$ 在 $a$ 可导能推出 $f$ 在 $a$ 连续。反之？",
         "options": ["不一定成立", "一定成立", "两者等价", "无法判断"],
         "correct_index": 0, "difficulty": 0.6},
    ],
    "derivative_geometry": [
        {"id": "a_geo_01", "node_id": "derivative_geometry", "skill": "Concept", "type": "mcq",
         "question": "切线方程：$y=f(x)$ 在 $(a,f(a))$ 处切线为？",
         "options": ["$y-f(a)=f'(a)(x-a)$", "$y=f(a)(x-a)$", "$y=f'(a)x$", "$y-f(a)=\\frac{x-a}{f'(a)}$"],
         "correct_index": 0, "difficulty": 0.55},
        {"id": "a_geo_02", "node_id": "derivative_geometry", "skill": "Procedure", "type": "mcq",
         "question": "曲线 $y=x^2$ 在 $x=2$ 处切线斜率为？",
         "options": ["4", "2", "8", "1"],
         "correct_index": 0, "difficulty": 0.5,
         "verify_type": "derivative", "math_expr": "x**2", "correct_answer_expr": "2*x"},
        {"id": "a_geo_03", "node_id": "derivative_geometry", "skill": "Transfer", "type": "mcq",
         "question": "自由落体 $s(t)=\\frac{1}{2}gt^2$，$t=2$s 时瞬时速度 $v(2)$ 为？",
         "options": ["$2g$", "$g$", "$4g$", "$\\frac{1}{2}g$"],
         "correct_index": 0, "difficulty": 0.6,
         "verify_type": "derivative", "math_expr": "0.5*g*t**2", "correct_answer_expr": "g*t"},
    ],
    "derivative_rules": [
        {"id": "a_rules_01", "node_id": "derivative_rules", "skill": "Concept", "type": "mcq",
         "question": "幂法则：$\\frac{d}{dx}x^n$ 等于？",
         "options": ["$nx^{n-1}$", "$x^{n-1}$", "$(n-1)x^n$", "$n x^n$"],
         "correct_index": 0, "difficulty": 0.4},
        {"id": "a_rules_02", "node_id": "derivative_rules", "skill": "Procedure", "type": "mcq",
         "question": "求导：$\\frac{d}{dx}(4x^3 - 5x + 2)$",
         "options": ["$12x^2 - 5$", "$12x^2$", "$4x^2 - 5$", "$3x^2 - 5$"],
         "correct_index": 0, "difficulty": 0.55,
         "verify_type": "derivative", "math_expr": "4*x**3 - 5*x + 2", "correct_answer_expr": "12*x**2 - 5"},
        {"id": "a_rules_03", "node_id": "derivative_rules", "skill": "Transfer", "type": "mcq",
         "question": "边际成本 $C(x)=0.5x^2+3x$（元），产量 $x=10$ 时的边际成本为？",
         "options": ["13 元/件", "8 元/件", "50 元/件", "33 元/件"],
         "correct_index": 0, "difficulty": 0.7,
         "verify_type": "derivative", "math_expr": "0.5*x**2+3*x", "correct_answer_expr": "x+3"},
    ],
    "chain_rule": [
        {"id": "a_chain_01", "node_id": "chain_rule", "skill": "Procedure", "type": "mcq",
         "question": "求导：$\\frac{d}{dx} \\sin(2x)$",
         "options": ["$2\\cos(2x)$", "$\\cos(2x)$", "$-2\\cos(2x)$", "$2\\sin(2x)$"],
         "correct_index": 0, "difficulty": 0.65,
         "verify_type": "derivative", "math_expr": "sin(2*x)", "correct_answer_expr": "2*cos(2*x)"},
        {"id": "a_chain_02", "node_id": "chain_rule", "skill": "Concept", "type": "mcq",
         "question": "$\\frac{d}{dx} e^{x^2}$ 等于？",
         "options": ["$2x e^{x^2}$", "$e^{x^2}$", "$x^2 e^{x^2}$", "$2 e^{x^2}$"],
         "correct_index": 0, "difficulty": 0.7,
         "verify_type": "derivative", "math_expr": "exp(x**2)", "correct_answer_expr": "2*x*exp(x**2)"},
        {"id": "a_chain_03", "node_id": "chain_rule", "skill": "Transfer", "type": "mcq",
         "question": "种群增长 $P(t)=100\\cdot 2^{0.1t}$，$t=10$ 时增长率 $P'(10)$ 近似为？",
         "options": ["$10\\ln 2 \\cdot 2$", "$100\\ln2$", "$200$", "$\\ln 2 \\cdot 100$"],
         "correct_index": 0, "difficulty": 0.8},
    ],
    "integral": [
        {"id": "a_int_01", "node_id": "integral", "skill": "Concept", "type": "mcq",
         "question": "不定积分 $\\int \\cos x \\, dx$ 等于？",
         "options": ["$\\sin x + C$", "$-\\sin x + C$", "$\\cos x + C$", "$-\\cos x + C$"],
         "correct_index": 0, "difficulty": 0.55},
        {"id": "a_int_02", "node_id": "integral", "skill": "Procedure", "type": "mcq",
         "question": "定积分 $\\int_1^2 \\frac{1}{x} \\, dx$ 等于？",
         "options": ["$\\ln 2$", "1", "$\\ln 1$", "$\\frac{1}{2}$"],
         "correct_index": 0, "difficulty": 0.7},
        {"id": "a_int_03", "node_id": "integral", "skill": "Transfer", "type": "mcq",
         "question": "速度 $v(t)=3t^2$ m/s，$t \\in [0,2]$ 秒内位移为？",
         "options": ["8 m", "6 m", "12 m", "4 m"],
         "correct_index": 0, "difficulty": 0.75},
    ],
}

# ---- 教学模板（TutorAgent 降级内容） ----
TUTOR_TEMPLATES: dict[str, str] = {
    "_default": """## 📖 {title}

让我带你逐步掌握这个知识点。

### 概念讲解
**{title}** 是微积分中的核心基础概念。它的关键在于理解其**定义与直觉**：

> 数学上，我们关心的是当自变量的变化趋近于某个点时，函数值的变化规律。

### 举个例子
来看一个具体例子帮助你建立直觉：

```
输入: {message}
当前掌握度: {mastery:.2f}
```

### 检验理解 🤔
请你试着回答：**用你自己的话，描述一下 {title} 的核心思想是什么？** 回答后我会给出针对性反馈。

如果你对某个细节感到困惑，随时告诉我，我会换个角度再讲一遍。
""",
    "function": """## 📖 函数（Function）

函数是微积分的基石——它是描述"输入→输出"映射关系的规则。

### 概念讲解
函数 $f$ 将定义域（$D$）中的每个 $x$ 唯一映射到值域中的一个值 $f(x)$。理解函数要注意三点：

1. **定义域**：$x$ 能取哪些值
2. **对应法则**：$x$ 如何变成 $f(x)$
3. **值域**：$f(x)$ 实际能得到哪些值

例如 $f(x) = \\sqrt{x-1}$：根号内必须 $x-1 \\ge 0$，所以定义域是 $x \\ge 1$。

### 复合函数
$f(g(x))$ 表示先算 $g$ 再算 $f$。例如 $f(x)=x^2$，$g(x)=2x+1$，则：

$$f(g(x)) = (2x+1)^2$$

### 检验理解 🤔
> **问题**：函数 $f(x)=\\frac{1}{x^2-4}$ 的定义域是什么？提示：分母不能为 0。

（当前掌握度：{mastery:.2f}）
""",
    "limit": """## 📖 极限（Limit）

极限是微积分的灵魂——它描述函数在"趋近"某个点时的行为。

### 概念讲解
符号 $\\lim_{x \\to a} f(x) = L$ 的含义是：**当 $x$ 无限接近 $a$（但不必等于 $a$）时，$f(x)$ 无限接近 $L$**。

关键直觉：
- 我们关心的是"趋近过程"，不是"点本身的值"
- 左极限（$x \\to a^-$）与右极限（$x \\to a^+$）都存在且相等时，极限才存在

### 经典极限
$$\\lim_{x \\to 0} \\frac{\\sin x}{x} = 1$$

### 检验理解 🤔
> **问题**：计算 $\\lim_{x \\to 2} \\frac{x^2-4}{x-2}$。提示：先因式分解再约分。

（当前掌握度：{mastery:.2f}）
""",
    "continuity": """## 📖 连续性（Continuity）

连续意味着"一笔画"——函数图像没有断裂。

### 概念讲解
$f$ 在 $x=a$ 处连续当且仅当同时满足：

1. $f(a)$ 有定义
2. $\\lim_{x \\to a} f(x)$ 存在
3. $\\lim_{x \\to a} f(x) = f(a)$

其中任意一条不满足就是**间断点**。间断点又分为可去间断、跳跃间断和无穷间断等类型。

### 直观理解
想象在函数图像上画图，**笔不离纸**就是连续；需要"跳一下"或"断一下"就是不连续。

### 检验理解 🤔
> **问题**：$f(x)=\\frac{x^2-1}{x-1}$ 在 $x=1$ 处是否连续？若不连续，属于哪种间断？

（当前掌握度：{mastery:.2f}）
""",
    "average_rate": """## 📖 平均变化率（Average Rate of Change）

平均变化率描述函数在一段区间内的"平均速度"。

### 概念讲解
函数 $f$ 在区间 $[a,b]$ 上的平均变化率为：

$$\\frac{\\Delta y}{\\Delta x} = \\frac{f(b)-f(a)}{b-a}$$

**几何意义**：连接 $(a,f(a))$ 与 $(b,f(b))$ 两点的**割线斜率**。

### 物理类比
汽车从 $t=1$ 到 $t=3$ 走了 100km，平均速度就是 50km/h——这正是位移关于时间的平均变化率。

### 检验理解 🤔
> **问题**：$f(x)=x^2$ 在 $[1,3]$ 上的平均变化率是多少？（提示：算割线斜率）

（当前掌握度：{mastery:.2f}）
""",
    "derivative_definition": """## 📖 导数定义（Derivative Definition）

导数是平均变化率取极限的结果——它描述"瞬时"变化率。

### 概念讲解
$$f'(a) = \\lim_{h \\to 0} \\frac{f(a+h)-f(a)}{h}$$

当 $h \\to 0$ 时，割线趋近于**切线**，平均变化率趋近于**瞬时变化率**。

### 为什么重要
- 速度是位移的导数
- 加速度是速度的导数
- 边际成本是总成本的导数

导数的存在性（可导）蕴含连续性（连续），反之不成立——例如 $f(x)=|x|$ 在 0 处连续但不可导。

### 检验理解 🤔
> **问题**：用定义求 $f(x)=x^2$ 在 $x=1$ 处的导数。（写出极限表达式并化简）

（当前掌握度：{mastery:.2f}）
""",
    "derivative_geometry": """## 📖 切线斜率与瞬时变化率

导数最有用的几何解释：**切线的斜率**。

### 概念讲解
曲线 $y=f(x)$ 在点 $(a, f(a))$ 处的切线方程为：

$$y - f(a) = f'(a)(x-a)$$

其中 $f'(a)$ 就是切线的斜率，也是函数在该点的瞬时变化率。

### 例子
$y = x^2$ 在 $x=2$ 处：$f'(x)=2x$，所以 $f'(2)=4$。切线为 $y-4=4(x-2)$。

### 检验理解 🤔
> **问题**：曲线 $y=x^3$ 在 $x=1$ 处的切线斜率是多少？切线方程是什么？

（当前掌握度：{mastery:.2f}）
""",
    "derivative_rules": """## 📖 基本求导法则

掌握法则，求导就能"机械化"完成。

### 概念讲解
1. **幂法则**：$\\frac{d}{dx}x^n = nx^{n-1}$
2. **常数倍**：$\\frac{d}{dx}[cf(x)] = cf'(x)$
3. **和差法则**：$\\frac{d}{dx}[f(x) \\pm g(x)] = f'(x) \\pm g'(x)$
4. **常见导数**：$\\frac{d}{dx}\\sin x = \\cos x$，$\\frac{d}{dx} e^x = e^x$

### 例子
$$\\frac{d}{dx}(3x^2 + 2x) = 6x + 2$$

### 检验理解 🤔
> **问题**：求 $\\frac{d}{dx}(4x^3 - 5x + 2)$。

（当前掌握度：{mastery:.2f}）
""",
    "chain_rule": """## 📖 链式法则（Chain Rule）

复合函数求导的"剥洋葱"法则。

### 概念讲解
$$\frac{d}{dx} f(g(x)) = f'(g(x)) \\cdot g'(x)$$

**口诀**：先对外层函数求导，再乘以内层函数的导数。

### 例子
$$\\frac{d}{dx}(2x+1)^3 = 3(2x+1)^2 \\cdot 2 = 6(2x+1)^2$$

### 检验理解 🤔
> **问题**：求 $\\frac{d}{dx} \\sin(2x)$。（提示：外层 $\\sin$，内层 $2x$）

（当前掌握度：{mastery:.2f}）
""",
    "integral": """## 📖 积分基础（Integration）

积分是导数的"逆运算"，也是求面积/累积量的工具。

### 概念讲解
**不定积分**：$\\int f(x)\\,dx = F(x) + C$，其中 $F'(x) = f(x)$。

**基本公式**：
- $\\int x^n \\, dx = \\frac{x^{n+1}}{n+1} + C$（$n \\neq -1$）
- $\\int \\cos x \\, dx = \\sin x + C$
- $\\int \\frac{1}{x}\\, dx = \\ln|x| + C$

**微积分基本定理**：$\\int_a^b f(x)\\,dx = F(b) - F(a)$——把"求面积"转化为"算原函数差值"。

### 检验理解 🤔
> **问题**：计算 $\\int_0^1 2x \\, dx$。（提示：先找原函数，再代上下限）

（当前掌握度：{mastery:.2f}）
""",
}
