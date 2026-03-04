# LLM-Powered Code Generation: A Literature Review

*Last updated: December 2025*

## 1. Introduction

Large language models have transformed automated code generation from a
research curiosity into a practical tool used by millions of developers daily.
This review covers key papers, benchmarks, and emerging patterns in the field.

## 2. Benchmark Comparison

Performance of major models on standard code generation benchmarks:

| Model                    | Parameters | HumanEval pass@1 | SWE-bench Resolved | License        |
| ------------------------ | ---------- | ---------------- | ------------------ | -------------- |
| Codex (2021)             | 12B        | 28.8%            | N/A                | Proprietary    |
| StarCoder (2023)         | 15.5B      | 33.6%            | N/A                | Open (BigCode) |
| CodeLlama (2023)         | 34B        | 53.7%            | N/A                | Open (Meta)    |
| GPT-4 (2023)             | Unknown    | 67.0%            | 1.7%               | Proprietary    |
| Claude 3.5 Sonnet (2024) | Unknown    | 92.0%            | 49.0%              | Proprietary    |
| DeepSeek-V3 (2025)       | 671B MoE   | 82.6%            | 42.0%              | Open           |
| Claude Opus 4 (2025)     | Unknown    | 95.2%            | 72.5%              | Proprietary    |

## 3. Key Papers

### 3.1 Evaluating Large Language Models Trained on Code

**Authors:** Chen et al. (OpenAI, 2021)
The Codex paper introduced the [HumanEval benchmark](https://github.com/openai/human-eval)
(164 hand-written Python problems). Key finding: sampling multiple solutions
and selecting the best dramatically improves results (pass@100 reached 70.2%
vs 28.8% for pass@1).

### 3.2 Competition-Level Code Generation with AlphaCode

**Authors:** Li et al. (DeepMind, 2022)
Generated millions of candidates for competitive programming problems,
then filtered using test cases. Reached top 54% of Codeforces competitors.
Key insight: brute-force generation + filtering outperforms careful single-shot
generation for algorithmic problems.

### 3.3 SWE-bench: Real-World GitHub Issues

**Authors:** Jimenez et al. (Princeton, 2024)
Benchmark of 2,294 real GitHub issues from 12 Python repos. Models must
produce patches that pass the repo's test suite. See
[swebench.com](https://www.swebench.com/) for the leaderboard.

## 4. Evaluation Benchmarks

| Benchmark      | What It Measures              | Realism | Language |
| -------------- | ----------------------------- | ------- | -------- |
| HumanEval      | Isolated function generation  | Low     | Python   |
| MBPP           | Simple programming problems   | Low     | Python   |
| SWE-bench      | Real GitHub issue resolution  | High    | Python   |
| LiveCodeBench  | Fresh competitive programming | Medium  | Multi    |
| BigCodeBench   | Complex function composition  | Medium  | Python   |
| Aider polyglot | Multi-language editing        | High    | Multi    |

## 5. Emerging Patterns

### 5.1 Agentic Code Generation

The shift from "model generates code" to "model uses tools to iteratively
develop code" has produced the largest practical gains:

1. **File navigation** — Read existing code to understand context
2. **Test execution** — Run tests to verify generated code works
3. **Error correction** — Parse error messages and fix issues
4. **Multi-step planning** — Break complex tasks into subtasks

Tools like [Claude Code](https://claude.ai/code),
[Cursor](https://cursor.com), and
[Aider](https://aider.chat) implement variations of this loop.

### 5.2 Retrieval-Augmented Generation for Code

* Embed code chunks with specialized models (CodeBERT, UniXcoder)
* Retrieve relevant files/functions before generation
* Include test files as context to guide implementation

## 6. Open Questions

1. How do we measure code quality beyond "does it pass tests"?
2. What's the ceiling for LLM code generation?
3. How should codebases be structured to be LLM-friendly?

## 7. References

* [HumanEval benchmark](https://github.com/openai/human-eval)
* [SWE-bench](https://www.swebench.com/)
* [The Stack dataset](https://huggingface.co/datasets/bigcode/the-stack)
* [BigCodeBench](https://bigcode-bench.github.io/)