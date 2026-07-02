# Operating Systems — Senior SWE Interview Mastery

Interview-focused OS notes for Software Engineer / Senior Software Engineer / Backend
Engineer interviews at Google, Meta, Amazon, Microsoft, Apple, Uber, Netflix, Stripe,
LinkedIn, and Cloudflare. Assumes 5+ years of experience — no beginner theory, no history.

Every topic follows the same 14-part structure: why interviewers ask it, core concept,
internal working, ASCII diagram, real production example, advantages, trade-offs, common
mistakes, performance implications, common interview questions, follow-up questions,
coding/debugging scenarios, best practices, and practice questions. Every module ends with
a one-page cheat sheet, top interview questions, common mistakes, and a mock interview.

## Contents

| Module | Topic | Markdown | PDF |
|---|---|---|---|
| 1 | Process & Thread | [src](src/module-01-process-thread.md) | [pdf](pdf/OS_Interview_Module_01_Process_Thread.pdf) |
| 2 | CPU Scheduling | [src](src/module-02-cpu-scheduling.md) | [pdf](pdf/OS_Interview_Module_02_CPU_Scheduling.pdf) |
| 3 | Synchronization (highest priority) | [src](src/module-03-synchronization.md) | [pdf](pdf/OS_Interview_Module_03_Synchronization_Highest_Priority.pdf) |
| 4 | Deadlocks | [src](src/module-04-deadlocks.md) | [pdf](pdf/OS_Interview_Module_04_Deadlocks.pdf) |
| 5 | Memory Management | [src](src/module-05-memory-management.md) | [pdf](pdf/OS_Interview_Module_05_Memory_Management.pdf) |
| 6 | Memory (Page) Replacement | [src](src/module-06-page-replacement.md) | [pdf](pdf/OS_Interview_Module_06_Memory_Page_Replacement.pdf) |
| 7 | File Systems | [src](src/module-07-file-systems.md) | [pdf](pdf/OS_Interview_Module_07_File_Systems.pdf) |
| 8 | I/O (epoll, kqueue, DMA, io_uring) | [src](src/module-08-io.md) | [pdf](pdf/OS_Interview_Module_08_I_O.pdf) |
| 9 | Linux Concepts (fork, signals, IPC) | [src](src/module-09-linux-concepts.md) | [pdf](pdf/OS_Interview_Module_09_Linux_Concepts.pdf) |
| 10 | Production Interview Scenarios | [src](src/module-10-interview-scenarios.md) | [pdf](pdf/OS_Interview_Module_10_Production_Interview_Scenarios.pdf) |

**Cumulative Master PDF (all 10 modules, ~120 pages):** [pdf/OS_Interview_Master.pdf](pdf/OS_Interview_Master.pdf)

## Suggested study order

1. Module 3 (Synchronization) and Module 1 (Process & Thread) — the most frequently asked.
2. Module 5 (Memory) and Module 9 (Linux) — the deepest follow-up chains.
3. Module 8 (I/O) — mandatory for backend/system design crossover (epoll, zero-copy).
4. Modules 4, 6, 2, 7 — targeted review.
5. Module 10 — rehearse out loud; these are the on-call scenario questions.

Study one topic at a time; after each, answer its Practice Questions before moving on, and
finish each module with its Mock Interview under time pressure.

## Rebuilding the PDFs

```bash
pip install weasyprint markdown
python3 docs/build_pdfs.py
```

PDFs are written to `docs/pdf/`.
