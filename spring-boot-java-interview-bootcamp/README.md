# Spring Boot + Core Java + Collections Interview Bootcamp

A **5-day crash course** built to make an experienced backend engineer (MERN / AWS / SQL)
**crack a Spring Boot + Java Microservices Developer interview** — fast.

This is not a university course. Every topic is chosen because it is *repeatedly asked* at
TCS, Infosys, Cognizant, Accenture, Capgemini, IBM, Oracle, Deloitte, EY, Wipro, LTIMindtree,
and top product companies (Google, Amazon, Microsoft, Uber, Stripe, Netflix, VMware).

## Teaching format

Every major topic follows the same 12-part structure:

1. Why Interviewers Ask This
2. Core Concept
3. Internal Working
4. Memory Diagram (ASCII)
5. Real Production Example
6. Most Asked Interview Questions (+ follow-ups)
7. Interview Traps
8. Best Answer (senior-level)
9. Coding Example (production-quality Java)
10. Follow-up Coding Questions
11. Summary
12. Cheat Sheet

Every **module** ends with: Top 25 interview questions, top coding questions, common
follow-ups with senior answers, a one-page cheat sheet, and a **mock interview** section.

## Modules

| # | Module | Priority |
|---|--------|----------|
| 01 | Core Java (JVM, memory, OOP, SOLID, strings, records) | Highest |
| 02 | Collections Framework (internals of ArrayList, HashMap, CHM...) | Highest |
| 03 | Java 8+ (lambdas, functional interfaces, streams, Optional) | High |
| 04 | Exception Handling | High |
| 05 | Multithreading & Concurrency | High |
| 06 | Spring Framework (IoC, DI, beans) | Highest |
| 07 | Spring Boot (auto-config, request lifecycle, actuator) | Highest |
| 08 | Spring Data JPA / Hibernate | Highest |
| 09 | Spring Security (JWT, filter chain) | Highest |
| 10 | REST API design | High |
| 11 | Microservices (gateway, Eureka, Feign, Resilience4j, Kafka) | High |

## Building the PDFs

```bash
pip install markdown weasyprint
python3 spring-boot-java-interview-bootcamp/build_pdfs.py
```

This produces:

- One professionally formatted PDF **per module** in `spring-boot-java-interview-bootcamp/pdf/`
- A cumulative **Master** PDF (cover + TOC + all modules)
- Copies of every PDF into the repository-root `docs/` directory

## How to use in 5 days

- **Day 1** — Modules 1 & 2 (Core Java + Collections). These decide most first rounds.
- **Day 2** — Modules 3, 4, 5 (Java 8+, Exceptions, Concurrency).
- **Day 3** — Modules 6 & 7 (Spring + Spring Boot).
- **Day 4** — Modules 8 & 9 (JPA + Security).
- **Day 5** — Modules 10 & 11 (REST + Microservices) + revise all cheat sheets.

Read the **Best Answer** and **Cheat Sheet** sections out loud. Do the **mock interviews**.
