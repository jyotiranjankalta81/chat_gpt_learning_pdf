# SQL & NoSQL Interview Mastery — Senior Software Engineer Edition

> Written from the perspective of a Principal Database Engineer & Senior Interviewer
> (Google, Meta, Amazon, Microsoft, Uber, Stripe, Netflix, LinkedIn).
>
> **Audience:** Backend engineers with 5+ years of experience.
> **Primary database:** PostgreSQL. Comparisons include MySQL, MongoDB, Redis, Cassandra, DynamoDB.
> **Scope:** Only what is actually asked in senior SWE interviews. No beginner filler, no rarely used features.

---

## How to Use This Guide

Every chapter follows the same 12-part format:

1. **Why Interviewers Ask This** — what signal the interviewer is trying to extract
2. **Core Concept** — the deep mental model
3. **Internal Working** — what the engine actually does
4. **Visualization (ASCII)** — diagram of the mechanism
5. **Real Production Example** — how this shows up at FAANG scale
6. **Common Interview Questions** — the exact questions you will hear
7. **Common Mistakes** — the traps that fail candidates
8. **Best Practices** — what a senior answer sounds like
9. **Coding Questions** — hands-on exercises
10. **SQL Examples** — runnable PostgreSQL
11. **Optimization Techniques** — how to make it fast
12. **Follow-up Questions** — the interviewer's next move after your answer

Each module ends with **5 easy, 5 medium, and 5 hard practice problems**.

Work through modules in order. Module 4 (Indexes) and Module 6 (Transactions & Concurrency)
are the highest-signal modules in senior interviews — do not skim them.

---

## Modules

| # | Module | File | Interview Weight |
|---|--------|------|------------------|
| 1 | Database Fundamentals | [modules/module-01-fundamentals.md](modules/module-01-fundamentals.md) | ★★★★★ |
| 2 | SQL Core | [modules/module-02-sql-core.md](modules/module-02-sql-core.md) | ★★★★☆ |
| 3 | Joins | [modules/module-03-joins.md](modules/module-03-joins.md) | ★★★★☆ |
| 4 | Indexes (Highest Priority) | [modules/module-04-indexes.md](modules/module-04-indexes.md) | ★★★★★ |
| 5 | Query Optimization | [modules/module-05-query-optimization.md](modules/module-05-query-optimization.md) | ★★★★★ |
| 6 | Transactions & Concurrency | [modules/module-06-transactions-concurrency.md](modules/module-06-transactions-concurrency.md) | ★★★★★ |
| 7 | Database Scaling | [modules/module-07-scaling.md](modules/module-07-scaling.md) | ★★★★★ |
| 8 | NoSQL | [modules/module-08-nosql.md](modules/module-08-nosql.md) | ★★★★☆ |
| 9 | Database Design | [modules/module-09-database-design.md](modules/module-09-database-design.md) | ★★★★☆ |
| 10 | Interview SQL (Top Problems) | [modules/module-10-interview-sql.md](modules/module-10-interview-sql.md) | ★★★★★ |
| 11 | Production Debugging | [modules/module-11-production-debugging.md](modules/module-11-production-debugging.md) | ★★★★☆ |

---

## The Senior-Level Answer Framework

When answering *any* database interview question, structure your answer as:

```
1. Definition        (one crisp sentence — shows precision)
2. Mechanism         (how the engine implements it — shows depth)
3. Trade-off         (what you give up — shows judgment)
4. Production story  (where you used/broke it — shows experience)
5. Scale limit       (when it stops working — shows senior thinking)
```

Interviewers at Google/Meta/Amazon are not testing whether you know the word "index."
They are testing whether you can **predict system behavior under load** and
**defend design decisions with trade-offs**. Every chapter in this guide is written
to arm you with exactly that.

---

## Quick Self-Assessment (Can you answer these cold?)

- Why does `SELECT COUNT(*)` on a 500M-row Postgres table take minutes even with indexes?
- Why can a composite index on `(a, b)` serve `WHERE a = 1` but not `WHERE b = 1`?
- Why does `READ COMMITTED` still allow lost updates, and how do you fix it without `SERIALIZABLE`?
- Why does `OFFSET 1000000 LIMIT 10` get slower as offset grows, and what replaces it?
- Why does Cassandra write faster than Postgres, and what does it sacrifice?
- How do you shard a payments table, and what breaks when you do?

If any of these makes you pause, the corresponding module will fix it.
