#!/usr/bin/env python3
"""Generate the Elite 39-Day Interview Blueprint PDF (80–120 pages)."""

import os
import xml.sax.saxutils as saxutils

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    HRFlowable,
)

from pdf_styles import (
    build_styles,
    section_banner,
    std_table,
    checklist_table,
    NumberedCanvas,
    revision_dates,
    DARK_BLUE,
    MED_BLUE,
    LIGHT_BLUE,
    ACCENT_TEAL,
    ACCENT_GOLD,
    LIGHT_GOLD,
    WHITE,
    GREEN_BG,
    ORANGE_BG,
)
from data.leetcode_roadmap import (
    PROBLEM_DB,
    DAILY_ASSIGNMENTS,
    TOPIC_ORDER,
    get_problem_row,
)
from data.daily_curriculum import (
    DAILY_PLAN,
    READINESS_SCORES,
    STRENGTHS,
    WEAKNESSES,
    RISKS,
    PRIORITIES,
    SYSTEM_DESIGNS,
    RESUME_BULLETS,
    MOCK_SCHEDULE,
    COMPANY_TARGETS,
)

OUTPUT_FILENAME = "Elite_39_Day_Interview_Blueprint.pdf"
FOOTER_TEXT = "Elite 39-Day Interview Blueprint  •  July 1 – August 8, 2026"
FULL_WIDTH = 17.5 * cm

DAILY_TIME_BLOCKS = [
    ("05:30 – 06:00", "Wake, hydrate, stretch, review today's LeetCode targets", "Prep"),
    ("06:00 – 08:30", "LeetCode Block 1 — new M/H problems, strict 20-min timers", "2.5h"),
    ("08:30 – 09:00", "Breakfast and mental reset", "Break"),
    ("09:00 – 11:00", "Backend deep-dive — Node.js or Java/Spring (alternating focus)", "2.0h"),
    ("11:00 – 11:15", "Short break — walk, no screens", "Break"),
    ("11:15 – 12:45", "LeetCode Block 2 — continue new problems + pattern notes", "1.5h"),
    ("12:45 – 13:30", "Lunch and light walk", "Break"),
    ("13:30 – 15:00", "SQL drills + hands-on exercises", "1.5h"),
    ("15:00 – 15:15", "Short break", "Break"),
    ("15:15 – 16:45", "System Design / OS / Networking study block", "1.5h"),
    ("16:45 – 17:00", "Short break", "Break"),
    ("17:00 – 18:30", "LeetCode Block 3 — revision + Hard problems from weak patterns", "1.5h"),
    ("18:30 – 19:15", "Dinner and decompress", "Break"),
    ("19:15 – 20:15", "Behavioral STAR practice + resume tailoring", "1.0h"),
    ("20:15 – 21:30", "Job applications, mock interviews, or project work", "1.25h"),
    ("21:30 – 22:00", "Spaced repetition review + update progress tracker", "0.5h"),
    ("22:00 – 22:30", "Wind down — no study screens", "Break"),
    ("22:30", "Sleep — target 7 hours for cognitive recovery", "Sleep"),
]

NODE_CORE_TOPICS = [
    "Event loop, libuv, and non-blocking I/O architecture",
    "CommonJS vs ESM modules and module resolution",
    "Streams API — readable, writable, duplex, transform, backpressure",
    "Express.js middleware chain, routing, and error handling",
    "Async patterns — callbacks, Promises, async/await",
    "Error handling — operational vs programmer errors, graceful shutdown",
    "Authentication — JWT, sessions, OAuth 2.0, refresh tokens",
    "Caching strategies — Redis, in-memory, cache-aside, TTL policies",
    "Database integration — Mongoose ODM, connection pooling, transactions",
    "Testing — Jest, supertest, mocking, integration test patterns",
    "Security — OWASP Top 10, input validation, rate limiting, CORS",
    "Performance — profiling, clustering, worker threads, load balancing",
    "Microservices — service discovery, API gateway, circuit breakers",
    "Message queues — Bull/BullMQ, RabbitMQ, Kafka basics",
    "Production ops — logging (pino), monitoring, health checks, PM2",
]

JAVA_CORE_TOPICS = [
    "JVM, JRE, JDK, bytecode, and compilation pipeline",
    "Data types, operators, control flow, and OOP fundamentals",
    "Interfaces, abstract classes, composition vs inheritance",
    "Collections — ArrayList, LinkedList, HashMap, HashSet internals",
    "Exception handling — checked vs unchecked, try-with-resources",
    "Generics, lambdas, and Stream API",
    "Multithreading — ExecutorService, CompletableFuture, synchronization",
    "Spring Boot fundamentals — auto-configuration, starters, Actuator",
    "Dependency injection and IoC container",
    "Spring MVC — REST controllers, validation, exception handlers",
    "Spring Data JPA — entities, repositories, relationships, N+1 fixes",
    "Spring Security — filter chain, JWT, method-level authorization",
    "Testing — JUnit 5, Mockito, @WebMvcTest, Testcontainers",
    "Transactions — @Transactional, isolation levels, propagation",
    "Docker + deployment — multi-stage builds, health probes, K8s basics",
]

SQL_CORE_TOPICS = [
    "SELECT, WHERE, ORDER BY, LIMIT, and basic filtering",
    "INNER, LEFT, RIGHT, and FULL OUTER JOIN patterns",
    "GROUP BY, HAVING, and aggregate functions",
    "Subqueries — scalar, correlated, EXISTS, IN, derived tables",
    "Window functions — ROW_NUMBER, RANK, DENSE_RANK, LEAD, LAG",
    "Indexing — B-tree, composite, covering indexes, EXPLAIN plans",
    "Normalization — 1NF through 3NF, denormalization tradeoffs",
    "Transactions — ACID, isolation levels, deadlocks",
    "Query optimization — join order, index selection, query plans",
    "Stored procedures, triggers, and views",
    "Schema design — keys, constraints, foreign keys, cascades",
    "Advanced patterns — CTEs, recursive queries, pivot/unpivot",
    "Performance tuning — slow query analysis, partitioning",
    "Replication, sharding, and read replicas",
    "Interview SQL patterns — top-N, gaps, running totals, dedup",
]

ATS_CHECKLIST = [
    "One-page format (two pages max for 5+ years experience)",
    "Standard fonts — Arial, Calibri, or Helvetica at 10–11pt",
    "No tables, text boxes, headers/footers, or graphics that break parsing",
    "Section headers: Experience, Skills, Education (standard labels)",
    "Keywords from job description woven into bullets naturally",
    "Quantified impact — users, latency, uptime, revenue where possible",
    "Separate tailored versions for Node-heavy vs Java-heavy roles",
    "PDF export from Word or Google Docs (not scanned image)",
    "Contact info in body text, not header/footer",
    "Skills section lists exact technologies from target job posts",
    "File name format: FirstName_LastName_Backend_Engineer.pdf",
    "LinkedIn URL and GitHub with active Spring Boot portfolio link",
]

NEGOTIATION_TIPS = [
    "Never disclose current compensation first — ask for their range",
    "Anchor high with researched market data (Levels.fyi, Glassdoor, Blind)",
    "Negotiate total comp — base, bonus, equity, signing, relocation separately",
    "Get competing offers to strengthen leverage — share timelines honestly",
    "Ask for 48–72 hours to review written offers before accepting",
    "Request sign-on bonus to offset unvested equity from current role",
    "Clarify equity — vesting schedule, cliff, refresh grants, valuation method",
    "Negotiate start date for prep time if needed before Day 1",
    "Get role level confirmed in writing — Senior vs Staff affects future growth",
    "Ask about remote policy, on-call expectations, and promotion timeline",
]


def _esc(text):
    """Escape text for ReportLab Paragraph markup."""
    return saxutils.escape(str(text)) if text is not None else ""


def _p(text, styles, style="BodyText2"):
    return Paragraph(text, styles[style])


def _spacer(h=0.3):
    return Spacer(1, h * cm)


def draw_cover_page(canvas, _doc):
    """Dark blue cover page drawn on canvas."""
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(DARK_BLUE)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)

    canvas.setFillColor(ACCENT_GOLD)
    canvas.rect(1.5 * cm, h - 3 * cm, w - 3 * cm, 0.15 * cm, fill=1, stroke=0)

    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 30)
    canvas.drawCentredString(w / 2, h * 0.62, "Elite 39-Day Interview Blueprint")

    canvas.setFont("Helvetica", 15)
    canvas.setFillColor(LIGHT_BLUE)
    canvas.drawCentredString(w / 2, h * 0.55, "Complete Parallel Prep System")

    canvas.setFont("Helvetica", 12)
    canvas.drawCentredString(w / 2, h * 0.48, "DSA  •  Node.js  •  Java/Spring Boot  •  SQL  •  System Design")

    canvas.setFillColor(ACCENT_TEAL)
    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawCentredString(w / 2, h * 0.40, "July 1 – August 8, 2026")

    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 10)
    lines = [
        "MERN Stack Engineer → Full-Stack Backend Interview Ready",
        "39 Days  •  14 Daily Study Hours  •  15 System Designs  •  1,076 LeetCode Assignments",
        "5 Mock Interview Days  •  Behavioral STAR  •  Resume & Job Search Playbook",
    ]
    y = h * 0.30
    for line in lines:
        canvas.drawCentredString(w / 2, y, line)
        y -= 16

    canvas.setFillColor(ACCENT_GOLD)
    canvas.setFont("Helvetica-Oblique", 9)
    canvas.drawCentredString(w / 2, 2.5 * cm, "Discipline beats talent when talent doesn't work hard.")
    canvas.restoreState()


def build_toc(styles):
    story = []
    story.append(section_banner("Table of Contents", styles, bg=MED_BLUE))
    story.append(_spacer(0.4))
    entries = [
        "Section 1: Readiness Assessment",
        "Section 2: Daily Schedule — 14 Study Hours",
        "Section 3: LeetCode Roadmap — 39 Days",
        "Section 4: Node.js Backend Curriculum",
        "Section 5: Java Spring Boot Curriculum",
        "Section 6: SQL Mastery Curriculum",
        "Section 7: MongoDB",
        "Section 8: Operating Systems",
        "Section 9: Computer Networks",
        "Section 10: System Design — 15 Designs",
        "Section 11: Behavioral — 39-Day STAR Prompts",
        "Section 12: Resume & ATS Optimization",
        "Section 13: Job Search Strategy",
        "Section 14: Mock Interview Schedule",
        "Section 15: Spaced Repetition Calendar",
        "Section 16: Progress Dashboard",
        "Section 17: Final Week Strategy & Negotiation",
        "Appendix A: Full 39-Day Daily Playbook",
        "Appendix B: Company Application Tracker",
        "Appendix C: Interview Scorecards",
    ]
    for entry in entries:
        story.append(_p(entry, styles, "TOCEntry"))
    story.append(PageBreak())
    return story


def build_section_1_readiness(styles):
    story = []
    story.append(section_banner("Section 1: Readiness Assessment", styles))
    story.append(_spacer(0.3))
    story.append(_p(
        "Baseline self-assessment across 22 skill areas (1–10 scale). "
        "Re-score weekly on Days 7, 14, 21, 28, 35, and 39 to track improvement.",
        styles,
    ))
    story.append(_spacer(0.2))

    score_rows = [[_esc(skill), f"{score}/10", _readiness_bar(score)] for skill, score in READINESS_SCORES.items()]
    story.append(std_table(
        ["Skill Area", "Score", "Visual"],
        score_rows,
        [7 * cm, 2 * cm, 8.5 * cm],
        styles,
    ))
    story.append(_spacer(0.4))

    story.append(_p("Strengths", styles, "SubTitle"))
    story.append(checklist_table(STRENGTHS, styles))
    story.append(_spacer(0.3))

    story.append(_p("Weaknesses to Address", styles, "SubTitle"))
    story.append(checklist_table(WEAKNESSES, styles))
    story.append(_spacer(0.3))

    story.append(_p("Risk Factors", styles, "SubTitle"))
    story.append(checklist_table(RISKS, styles))
    story.append(_spacer(0.3))

    story.append(_p("Top Priorities (39-Day Focus)", styles, "SubTitle"))
    story.append(checklist_table(PRIORITIES, styles))
    story.append(PageBreak())
    return story


def _readiness_bar(score):
    filled = "█" * score
    empty = "░" * (10 - score)
    return filled + empty


def build_section_2_schedule(styles):
    story = []
    story.append(section_banner("Section 2: Daily Schedule — 14 Study Hours", styles))
    story.append(_spacer(0.3))
    story.append(_p(
        "Fixed daily rhythm from <b>05:30 wake</b> to <b>22:30 sleep</b>. "
        "Study blocks total <b>14 hours</b> including 5.5h LeetCode across 3 blocks. "
        "Volume ramps from 15 to 35+ problems/day by July 31. Mandatory breaks prevent burnout. "
        "Adjust weekend blocks slightly for mock interview days (see Section 14).",
        styles,
    ))
    story.append(_spacer(0.2))

    rows = [[t, activity, hours] for t, activity, hours in DAILY_TIME_BLOCKS]
    story.append(std_table(
        ["Time", "Activity", "Study Hours"],
        rows,
        [3 * cm, 11 * cm, 3.5 * cm],
        styles,
    ))
    story.append(_spacer(0.3))

    story.append(_p("Weekly Rhythm", styles, "SubTitle"))
    weekly = [
        ["Mon–Fri", "Full 14h schedule; 15→35+ LeetCode; 2–3 job applications daily"],
        ["Saturday", "Mock interview or deep system design day; lighter LeetCode"],
        ["Sunday", "Review week gaps; prep next week; 1 hour rest from new material"],
    ]
    story.append(std_table(["Day Type", "Adjustment"], weekly, [4 * cm, 13.5 * cm], styles))
    story.append(_spacer(0.3))

    story.append(_p("Phase Overview", styles, "SubTitle"))
    phases = [
        ["Days 1–10", "Foundation", "Core patterns, Node/Java basics, first system designs"],
        ["Days 11–20", "Build", "Advanced DSA, Spring depth, SQL speed drills"],
        ["Days 21–30", "Intensify", "Hard problems, full system designs, weekly mocks"],
        ["Days 31–39", "Final Sprint", "Revision, mocks, applications, interview readiness"],
    ]
    story.append(std_table(["Days", "Phase", "Focus"], phases, [3 * cm, 3 * cm, 11.5 * cm], styles))
    story.append(PageBreak())
    return story


def build_section_3_leetcode(styles):
    story = []
    story.append(section_banner("Section 3: LeetCode Roadmap — 39 Days", styles))
    story.append(_spacer(0.3))
    story.append(_p(
        f"<b>{len(PROBLEM_DB)}-problem database</b> calibrated for DSA 4.5/5. "
        f"Volume ramps <b>15 → 35+ problems/day</b> by July 31 (~13% Easy, ~50% Medium, ~37% Hard). "
        f"Pattern progression: {', '.join(TOPIC_ORDER[:8])}… and more. "
        "Use spaced repetition dates in the Revision column.",
        styles,
    ))
    story.append(_spacer(0.2))

    header = ["#", "Title", "Diff", "Pattern", "Concept", "Min", "Follow-up", "Revision", "Freq"]
    col_widths = [0.7 * cm, 3.8 * cm, 0.65 * cm, 1.6 * cm, 2.4 * cm, 0.65 * cm, 0.85 * cm, 2.2 * cm, 0.65 * cm]

    for day in range(1, 40):
        plan = DAILY_PLAN[day]
        problems = DAILY_ASSIGNMENTS.get(day, [])
        story.append(_p(
            f"<b>Day {day}</b> — {_esc(plan['date'])}  |  Phase: {_esc(plan['phase'])}  |  "
            f"{len(problems)} problems  |  Focus: {_esc(plan['daily_focus'])}",
            styles,
            "SubSubTitle",
        ))
        rows = [
            [_esc(c) if isinstance(c, str) else c for c in get_problem_row(num, day)]
            for num in problems
        ]
        story.append(std_table(header, rows, col_widths, styles, font_style="CellSmall"))
        story.append(_spacer(0.25))

        if day % 3 == 0 and day < 39:
            story.append(PageBreak())

    story.append(PageBreak())
    return story


def build_section_4_node(styles):
    story = []
    story.append(section_banner("Section 4: Node.js Backend Curriculum", styles))
    story.append(_spacer(0.3))
    story.append(_p(
        "Node.js is your primary strength — this curriculum ensures interview-crisp depth "
        "on event loop, production patterns, and backend architecture beyond CRUD APIs.",
        styles,
    ))
    story.append(_spacer(0.2))

    story.append(_p("Core Topic Map", styles, "SubTitle"))
    story.append(checklist_table(NODE_CORE_TOPICS, styles))
    story.append(_spacer(0.3))

    story.append(_p("39-Day Node.js Daily Curriculum", styles, "SubTitle"))
    rows = []
    for day in range(1, 40):
        plan = DAILY_PLAN[day]
        rows.append([day, _esc(plan["date"]), _esc(plan["node_topic"][:80]), _esc(plan["node_exercise"][:60])])
    story.append(std_table(
        ["Day", "Date", "Topic", "Exercise"],
        rows,
        [1 * cm, 2.5 * cm, 7 * cm, 7 * cm],
        styles,
        font_style="CellSmall",
    ))
    story.append(_spacer(0.3))

    story.append(_p("Sample Interview Questions by Week", styles, "SubTitle"))
    for week_start in range(1, 40, 7):
        week_end = min(week_start + 6, 39)
        story.append(_p(f"Week {(week_start - 1) // 7 + 1} (Days {week_start}–{week_end})", styles, "SubSubTitle"))
        for day in range(week_start, week_end + 1):
            questions = DAILY_PLAN[day].get("node_questions", [])
            if questions:
                story.append(_p(f"<b>Day {day}:</b> {_esc(questions[0])}", styles, "Cell"))
        story.append(_spacer(0.15))
    story.append(PageBreak())
    return story


def build_section_5_java(styles):
    story = []
    story.append(section_banner("Section 5: Java Spring Boot Curriculum", styles))
    story.append(_spacer(0.3))
    story.append(_p(
        "Java/Spring Boot is the growth area — frame as MERN veteran expanding backend breadth. "
        "Daily exercises build toward one portfolio-ready Spring Boot REST project by Day 25.",
        styles,
    ))
    story.append(_spacer(0.2))

    story.append(_p("Core Topic Map", styles, "SubTitle"))
    story.append(checklist_table(JAVA_CORE_TOPICS, styles))
    story.append(_spacer(0.3))

    story.append(_p("39-Day Java/Spring Daily Curriculum", styles, "SubTitle"))
    rows = []
    for day in range(1, 40):
        plan = DAILY_PLAN[day]
        rows.append([day, _esc(plan["date"]), _esc(plan["java_topic"][:75]), _esc(plan["java_exercise"][:65])])
    story.append(std_table(
        ["Day", "Date", "Topic", "Exercise"],
        rows,
        [1 * cm, 2.5 * cm, 7 * cm, 7 * cm],
        styles,
        font_style="CellSmall",
    ))
    story.append(_spacer(0.3))

    story.append(_p("Spring Boot Project Milestones", styles, "SubTitle"))
    milestones = [
        ["Day 5", "Project scaffold — Spring Initializr, layered architecture, first REST endpoint"],
        ["Day 10", "JPA entities, repositories, PostgreSQL integration, basic CRUD"],
        ["Day 15", "Spring Security + JWT filter chain, role-based access"],
        ["Day 20", "Test suite — JUnit 5, @WebMvcTest, Testcontainers integration tests"],
        ["Day 25", "Dockerfile, README, API docs, demo-ready for interviews"],
        ["Day 30", "Performance tuning, Actuator metrics, production checklist review"],
    ]
    story.append(std_table(["Day", "Milestone"], milestones, [2 * cm, 15.5 * cm], styles))
    story.append(PageBreak())
    return story


def build_section_6_sql(styles):
    story = []
    story.append(section_banner("Section 6: SQL Mastery Curriculum", styles))
    story.append(_spacer(0.3))
    story.append(_p(
        "SQL is a known gap vs NoSQL comfort — daily timed drills target window functions, "
        "complex joins, and EXPLAIN-driven optimization until speed matches MongoDB fluency.",
        styles,
    ))
    story.append(_spacer(0.2))

    story.append(_p("Core Topic Progression", styles, "SubTitle"))
    story.append(checklist_table(SQL_CORE_TOPICS, styles))
    story.append(_spacer(0.3))

    story.append(_p("39-Day SQL Daily Topics & Problems", styles, "SubTitle"))
    for day in range(1, 40):
        plan = DAILY_PLAN[day]
        story.append(_p(f"<b>Day {day} — {_esc(plan['date'])}:</b> {_esc(plan['sql_topic'])}", styles, "SubSubTitle"))
        for i, prob in enumerate(plan.get("sql_problems", []), 1):
            story.append(_p(f"  {i}. {_esc(prob)}", styles, "Cell"))
        story.append(_spacer(0.1))
        if day % 5 == 0:
            story.append(_spacer(0.1))
    story.append(PageBreak())
    return story


def build_section_7_mongo(styles):
    story = []
    story.append(section_banner("Section 7: MongoDB", styles))
    story.append(_spacer(0.3))
    story.append(_p(
        "Leverage existing MERN MongoDB strength while filling gaps in aggregation pipelines, "
        "indexing strategy, replication, sharding, and transaction semantics.",
        styles,
    ))
    story.append(_spacer(0.2))

    mongo_topics = [
        "Document model, BSON types, _id generation, CRUD operations",
        "Schema design — embedding vs referencing, denormalization patterns",
        "Indexing — single, compound, multikey, text, TTL indexes",
        "Aggregation pipeline — $match, $group, $lookup, $unwind, $facet",
        "Transactions — multi-document ACID, session handling",
        "Replication — replica sets, read preferences, write concerns",
        "Sharding — shard keys, chunk migration, balancer",
        "Performance — explain plans, covered queries, index intersection",
        "Mongoose ODM — schemas, middleware, virtuals, population",
        "Change streams and capped collections for real-time patterns",
        "Atlas cloud — backups, monitoring, search indexes",
        "Interview patterns — design schema for e-commerce, social feed, analytics",
    ]
    story.append(_p("MongoDB Core Curriculum", styles, "SubTitle"))
    story.append(checklist_table(mongo_topics, styles))
    story.append(_spacer(0.3))

    story.append(_p("Daily MongoDB Topics (39-Day Plan)", styles, "SubTitle"))
    rows = []
    for day in range(1, 40):
        topic = DAILY_PLAN[day].get("mongo_topic")
        if topic:
            rows.append([day, _esc(DAILY_PLAN[day]["date"]), _esc(topic)])
    story.append(std_table(
        ["Day", "Date", "MongoDB Topic"],
        rows,
        [1.5 * cm, 3 * cm, 13 * cm],
        styles,
    ))
    story.append(PageBreak())
    return story


def build_section_8_os(styles):
    story = []
    story.append(section_banner("Section 8: Operating Systems", styles))
    story.append(_spacer(0.3))
    story.append(_p(
        "Structured OS review for backend interviews — processes, memory, scheduling, "
        "synchronization, file systems, containers, and production operations.",
        styles,
    ))
    story.append(_spacer(0.2))

    os_fundamentals = [
        "Processes vs threads — address space, PCB, context switching",
        "CPU scheduling — FCFS, SJF, round-robin, priority, multilevel queue",
        "Memory management — paging, segmentation, virtual memory, TLB, page faults",
        "Deadlocks — four conditions, prevention, avoidance, detection, recovery",
        "Synchronization — mutex, semaphore, monitor, condition variables, spinlocks",
        "File systems — inodes, directories, journaling, permissions",
        "Virtualization vs containers — hypervisors, cgroups, namespaces",
        "Linux process management — signals, niceness, ps/top/htop",
        "Docker — images, layers, Dockerfile, multi-stage builds, volumes",
        "Kubernetes — pods, services, deployments, HPA, ConfigMaps, Secrets",
        "Monitoring — SLIs, SLOs, SLAs, error budgets, alerting",
        "CI/CD — build pipelines, blue-green, canary deployments",
        "Debugging — memory leaks, heap dumps, core dumps, strace",
    ]
    story.append(_p("OS Fundamentals Checklist", styles, "SubTitle"))
    story.append(checklist_table(os_fundamentals, styles))
    story.append(_spacer(0.3))

    story.append(_p("Daily OS Topics (39-Day Plan)", styles, "SubTitle"))
    rows = []
    for day in range(1, 40):
        topic = DAILY_PLAN[day].get("os_topic")
        if topic:
            rows.append([day, _esc(DAILY_PLAN[day]["date"]), _esc(topic)])
    story.append(std_table(
        ["Day", "Date", "OS Topic"],
        rows,
        [1.5 * cm, 3 * cm, 13 * cm],
        styles,
    ))
    story.append(PageBreak())
    return story


def build_section_9_networks(styles):
    story = []
    story.append(section_banner("Section 9: Computer Networks", styles))
    story.append(_spacer(0.3))
    story.append(_p(
        "Networking fundamentals for backend engineers — from OSI model through production "
        "patterns including load balancing, caching, TLS, and microservice communication.",
        styles,
    ))
    story.append(_spacer(0.2))

    net_fundamentals = [
        "OSI and TCP/IP models — layers, encapsulation, protocols per layer",
        "IP addressing — subnets, CIDR notation, NAT, public vs private",
        "TCP vs UDP — three-way handshake, reliability, use cases, ports",
        "HTTP/1.1 vs HTTP/2 vs HTTP/3 — multiplexing, head-of-line blocking, QUIC",
        "DNS — resolution flow, record types (A, AAAA, CNAME, MX), caching",
        "TLS/SSL — handshake, certificates, cipher suites, HTTPS termination",
        "Load balancing — L4 vs L7, algorithms, health checks, sticky sessions",
        "WebSockets vs SSE vs long polling — real-time communication tradeoffs",
        "CDN — edge caching, cache keys, purge strategies, origin shield",
        "API Gateway — routing, auth termination, rate limiting, aggregation",
        "gRPC vs REST — protobuf, HTTP/2, streaming, service contracts",
        "Reverse proxy vs forward proxy — Nginx configuration concepts",
        "Service mesh — sidecar proxy, mTLS, traffic management (Istio)",
        "Consistent hashing — virtual nodes, ring topology, minimal reshuffling",
        "Kafka networking — partitions, consumer groups, offset management",
        "HTTP caching — Cache-Control, ETag, conditional requests",
        "Latency budget — DNS + TCP + TLS + server + DB for typical API call",
        "DDoS mitigation — rate limiting, WAF, anycast scrubbing",
        "Zero-trust networking — mTLS between microservices",
        "Troubleshooting — ping, traceroute, tcpdump, DNS debug methodology",
    ]
    story.append(_p("Networking Fundamentals Checklist", styles, "SubTitle"))
    story.append(checklist_table(net_fundamentals, styles))
    story.append(_spacer(0.3))

    story.append(_p("Daily Networking Topics (39-Day Plan)", styles, "SubTitle"))
    rows = []
    for day in range(1, 40):
        topic = DAILY_PLAN[day].get("network_topic")
        if topic:
            rows.append([day, _esc(DAILY_PLAN[day]["date"]), _esc(topic)])
    story.append(std_table(
        ["Day", "Date", "Networking Topic"],
        rows,
        [1.5 * cm, 3 * cm, 13 * cm],
        styles,
    ))
    story.append(PageBreak())
    return story


def build_section_10_system_design(styles):
    story = []
    story.append(section_banner("Section 10: System Design — 15 Complete Designs", styles))
    story.append(_spacer(0.3))
    story.append(_p(
        "Each design includes requirements, API, database schema, scaling, caching, "
        "queues, partitioning, replication, and explicit tradeoffs. Practice one design "
        "every 2–3 days; whiteboard with 45-minute timer.",
        styles,
    ))

    fields = [
        ("requirements", "Requirements"),
        ("api", "API Design"),
        ("db", "Database Schema"),
        ("scaling", "Scaling Strategy"),
        ("caching", "Caching Layer"),
        ("queues", "Message Queues"),
        ("partitioning", "Partitioning"),
        ("replication", "Replication"),
        ("tradeoffs", "Key Tradeoffs"),
    ]

    for name, design in SYSTEM_DESIGNS.items():
        story.append(_spacer(0.3))
        story.append(_p(f"Design: {name}", styles, "SubTitle"))
        for key, label in fields:
            value = design[key]
            if key == "tradeoffs":
                story.append(_p(f"<b>{label}:</b>", styles, "SubSubTitle"))
                story.append(checklist_table(value, styles))
            else:
                story.append(_p(f"<b>{label}:</b> {_esc(value)}", styles, "BodyText2"))
        story.append(_spacer(0.2))
        story.append(HRFlowable(width=FULL_WIDTH, thickness=0.5, color=MED_BLUE))
        if list(SYSTEM_DESIGNS.keys()).index(name) % 3 == 2:
            story.append(PageBreak())

    story.append(PageBreak())
    return story


def build_section_11_behavioral(styles):
    story = []
    story.append(section_banner("Section 11: Behavioral — 39-Day STAR Prompts", styles))
    story.append(_spacer(0.3))
    story.append(_p(
        "Daily behavioral prompt for STAR method practice (Situation, Task, Action, Result). "
        "Record 2-minute spoken answers; include metrics. Build a story bank of 8–10 core stories.",
        styles,
    ))
    story.append(_spacer(0.2))

    star_framework = [
        "Situation — Set context in 2 sentences (team, product, scale)",
        "Task — Your specific responsibility and constraint",
        "Action — What YOU did (use 'I', not 'we'); technical and leadership details",
        "Result — Quantified outcome (latency, revenue, uptime, team velocity)",
        "Reflection — What you learned; what you'd do differently",
    ]
    story.append(_p("STAR Framework Reminder", styles, "SubTitle"))
    story.append(checklist_table(star_framework, styles))
    story.append(_spacer(0.3))

    story.append(_p("Daily STAR Prompts", styles, "SubTitle"))
    rows = []
    for day in range(1, 40):
        plan = DAILY_PLAN[day]
        rows.append([day, _esc(plan["date"]), _esc(plan["behavioral"])])
    story.append(std_table(
        ["Day", "Date", "Behavioral Prompt"],
        rows,
        [1.5 * cm, 3 * cm, 13 * cm],
        styles,
        font_style="CellSmall",
    ))

    story.append(_spacer(0.3))
    story.append(_p("Core Story Bank Categories", styles, "SubTitle"))
    categories = [
        "Production incident / outage recovery",
        "Technical conflict / architecture disagreement",
        "Mentoring / upskilling a junior developer",
        "Missed deadline / failure and recovery",
        "Measurable business impact feature",
        "Technical debt reduction / code quality improvement",
        "Cross-functional stakeholder management",
        "Learning new technology under time pressure",
        "Performance optimization with metrics",
        "Leadership without authority",
    ]
    story.append(checklist_table(categories, styles))
    story.append(PageBreak())
    return story


def build_section_12_resume(styles):
    story = []
    story.append(section_banner("Section 12: Resume & ATS Optimization", styles))
    story.append(_spacer(0.3))

    for version, bullets in RESUME_BULLETS.items():
        story.append(_p(f"Resume Bullets — {version} Version", styles, "SubTitle"))
        story.append(checklist_table(bullets, styles))
        story.append(_spacer(0.3))

    story.append(_p("ATS Optimization Checklist", styles, "SubTitle"))
    story.append(checklist_table(ATS_CHECKLIST, styles))
    story.append(_spacer(0.3))

    story.append(_p("Tailoring Guide", styles, "SubTitle"))
    tailoring = [
        ["Node.js roles", "Lead with Node bullets; Java as secondary; emphasize MongoDB, Redis, Express"],
        ["Java/Spring roles", "Lead with Java bullets; frame MERN as full-stack breadth; link Spring portfolio"],
        ["Full-stack roles", "Mix General + Node bullets; show React + backend depth"],
        ["FAANG / big tech", "Emphasize scale metrics, system design exposure, DSA readiness"],
        ["Startups", "Emphasize ownership, speed, end-to-end delivery, production incident stories"],
    ]
    story.append(std_table(["Target", "Strategy"], tailoring, [4 * cm, 13.5 * cm], styles))
    story.append(PageBreak())
    return story


def build_section_13_job_search(styles):
    story = []
    story.append(section_banner("Section 13: Job Search Strategy", styles))
    story.append(_spacer(0.3))
    story.append(_p(
        f"Target list of {len(COMPANY_TARGETS)} companies with tiered application strategy. "
        "Apply strategically — don't spray and pray. Warm up with Tier 3 before Tier 1.",
        styles,
    ))
    story.append(_spacer(0.2))

    story.append(_p("Target Companies", styles, "SubTitle"))
    company_rows = []
    for i, company in enumerate(COMPANY_TARGETS, 1):
        tier = "Tier 1" if i <= 10 else ("Tier 2" if i <= 25 else "Tier 3")
        company_rows.append([i, _esc(company), tier])
    story.append(std_table(
        ["#", "Company", "Tier"],
        company_rows,
        [1 * cm, 10 * cm, 6.5 * cm],
        styles,
        font_style="CellSmall",
    ))
    story.append(_spacer(0.3))

    story.append(_p("Application Strategy", styles, "SubTitle"))
    strategy = [
        "Days 1–10: Apply to 2–3 Tier 3 companies daily; practice application flow",
        "Days 11–20: Increase to 3–4 daily; add Tier 2; begin recruiter outreach (1–2/day)",
        "Days 21–30: Target 4–5 daily; prioritize referrals; tailor resume per stack",
        "Days 31–39: Focus on active pipelines; Tier 1 with strong referrals only",
        "Track every application in Appendix B tracker — follow up at 5 and 10 business days",
        "LinkedIn: 3 connection requests daily to engineers at target companies",
        "GitHub: Pin Spring Boot portfolio repo; keep commit activity visible",
        "Referrals: Ask after establishing rapport — provide resume blurb and role links",
    ]
    story.append(checklist_table(strategy, styles))
    story.append(_spacer(0.3))

    story.append(_p("Daily Application Targets (from curriculum)", styles, "SubTitle"))
    app_rows = [[d, _esc(DAILY_PLAN[d]["date"]), DAILY_PLAN[d]["applications_target"],
                 DAILY_PLAN[d]["recruiter_outreach"]] for d in range(1, 40)]
    story.append(std_table(
        ["Day", "Date", "Applications", "Recruiter Outreach"],
        app_rows,
        [1.5 * cm, 3.5 * cm, 3 * cm, 3 * cm],
        styles,
    ))
    story.append(PageBreak())
    return story


def build_section_14_mocks(styles):
    story = []
    story.append(section_banner("Section 14: Mock Interview Schedule", styles))
    story.append(_spacer(0.3))
    story.append(_p(
        "Five full mock interview days simulate real interview loops. Record every session, "
        "score with Appendix C scorecards, and write a 30-minute post-mortem after each mock.",
        styles,
    ))

    for mock_num, mock in MOCK_SCHEDULE.items():
        story.append(_spacer(0.3))
        story.append(_p(
            f"Mock #{mock_num} — Day {mock['day']} ({mock['date']})  |  Focus: {mock['focus']}",
            styles,
            "SubTitle",
        ))
        rounds = [[_esc(r["time"]), _esc(r["type"]), _esc(r["topics"])] for r in mock["rounds"]]
        story.append(std_table(
            ["Time", "Round Type", "Topics"],
            rounds,
            [3 * cm, 4 * cm, 10.5 * cm],
            styles,
        ))

    story.append(_spacer(0.3))
    story.append(_p("Mock Interview Best Practices", styles, "SubTitle"))
    practices = [
        "Use timer — strict 45 min for coding, 45 min for system design",
        "No hints during coding rounds; verbalize thought process continuously",
        "Record audio/video for review — note filler words and pacing",
        "Score each round immediately using Appendix C scorecards",
        "Identify top 3 gaps; schedule remedial study for next 2 days",
        "Alternate peer mocks with paid platforms (Pramp, Interviewing.io) if available",
    ]
    story.append(checklist_table(practices, styles))
    story.append(PageBreak())
    return story


def build_section_15_spaced_repetition(styles):
    story = []
    story.append(section_banner("Section 15: Spaced Repetition Revision Calendar", styles))
    story.append(_spacer(0.3))
    story.append(_p(
        "Spaced repetition schedule: revisit material at Day+0, +2, +6, +13, +20, +29. "
        "This aligns with LeetCode problem revision dates and daily topic reviews.",
        styles,
    ))
    story.append(_spacer(0.2))

    story.append(_p("Revision Interval Reference", styles, "SubTitle"))
    intervals = [
        ["Day +0", "Initial learning — solve problem or study topic"],
        ["Day +2", "First revision — re-solve without notes, 50% time limit"],
        ["Day +6", "Second revision — explain pattern aloud, solve from scratch"],
        ["Day +13", "Third revision — timed re-solve, note any hesitation"],
        ["Day +20", "Fourth revision — mock interview conditions"],
        ["Day +29", "Final revision — must solve in target time with clean code"],
    ]
    story.append(std_table(["Interval", "Action"], intervals, [3 * cm, 14.5 * cm], styles))
    story.append(_spacer(0.3))

    story.append(_p("Topic Revision Calendar by Start Day", styles, "SubTitle"))
    rev_rows = []
    for day in range(1, 40):
        rev_rows.append([f"Day {day}", revision_dates(day), _esc(DAILY_PLAN[day]["daily_focus"][:50])])
    story.append(std_table(
        ["Start Day", "Revision Days", "Topic Focus"],
        rev_rows,
        [2 * cm, 5 * cm, 10.5 * cm],
        styles,
        font_style="CellSmall",
    ))
    story.append(_spacer(0.3))

    story.append(_p("Weekly Consolidation Days", styles, "SubTitle"))
    consolidation = [
        ["Day 7", "Review all Week 1 problems marked 'Again'; re-read Node event loop notes"],
        ["Day 14", "Review Week 2 gaps from Mock #1 post-mortem; SQL timed set"],
        ["Day 21", "Review Week 3; Mock #3 prep; system design flash cards"],
        ["Day 28", "Full week review before Final Sprint; Mock #4 debrief"],
        ["Day 35", "Mock #5 debrief; prioritize Final Sprint weak areas only"],
    ]
    story.append(std_table(["Day", "Consolidation Focus"], consolidation, [2 * cm, 15.5 * cm], styles))
    story.append(PageBreak())
    return story


def build_section_16_progress(styles):
    story = []
    story.append(section_banner("Section 16: Progress Dashboard", styles))
    story.append(_spacer(0.3))
    story.append(_p(
        "Track daily completion across all workstreams. Mark ☐ → ☑ in your copy. "
        "Weekly summary rows aggregate totals for accountability.",
        styles,
    ))
    story.append(_spacer(0.2))

    tracker_header = ["Day", "Date", "Phase", "LC", "Node", "Java", "SQL", "SD", "Apps", "Beh"]
    tracker_rows = []
    for day in range(1, 40):
        plan = DAILY_PLAN[day]
        sd = "☐" if plan.get("system_design") else "—"
        tracker_rows.append([
            day, _esc(plan["date"][:6]), _esc(plan["phase"][:4]),
            "☐", "☐", "☐", "☐", sd,
            f"☐/{plan['applications_target']}", "☐",
        ])
    story.append(std_table(
        tracker_header,
        tracker_rows,
        [1 * cm, 1.8 * cm, 1.8 * cm, 0.9 * cm, 0.9 * cm, 0.9 * cm, 0.9 * cm, 0.9 * cm, 1.2 * cm, 0.9 * cm],
        styles,
        font_style="CellSmall",
    ))
    story.append(_spacer(0.3))

    story.append(_p("Weekly Summary Template", styles, "SubTitle"))
    weeks = [
        ["Week 1", "Days 1–7", "Problems: __/119", "Mocks: 0", "Apps: __", "Readiness Δ: __"],
        ["Week 2", "Days 8–14", "Problems: __/152", "Mocks: 1", "Apps: __", "Readiness Δ: __"],
        ["Week 3", "Days 15–21", "Problems: __/184", "Mocks: 1", "Apps: __", "Readiness Δ: __"],
        ["Week 4", "Days 22–28", "Problems: __/217", "Mocks: 1", "Apps: __", "Readiness Δ: __"],
        ["Week 5", "Days 29–35", "Problems: __/252", "Mocks: 1", "Apps: __", "Readiness Δ: __"],
        ["Final", "Days 36–39", "Problems: __/152", "Mocks: 0", "Apps: __", "Readiness Δ: __"],
        ["Week 6", "Days 36–39", "Review only", "Mocks: 1", "Apps: __", "Final score: __"],
    ]
    story.append(std_table(
        ["Week", "Days", "LeetCode", "Mocks", "Applications", "Score Change"],
        weeks,
        [2 * cm, 2.5 * cm, 3.5 * cm, 2 * cm, 2.5 * cm, 5 * cm],
        styles,
    ))

    story.append(_spacer(0.3))
    story.append(_p("Key Metrics to Track", styles, "SubTitle"))
    metrics = [
        "LeetCode problems solved / re-solved within time target",
        "SQL problems completed under 25-minute timer",
        "System designs whiteboarded (target: 15 total)",
        "Behavioral stories rehearsed with recording (target: 10 stories)",
        "Mock interview average score (target: 7+/10 by Day 35)",
        "Applications submitted vs responses vs interviews scheduled",
    ]
    story.append(checklist_table(metrics, styles))
    story.append(PageBreak())
    return story


def build_section_17_final_week(styles):
    story = []
    story.append(section_banner("Section 17: Final Week Strategy (Aug 1–8)", styles))
    story.append(_spacer(0.3))
    story.append(_p(
        "Days 36–39 are about consolidation, rest, and interview readiness — not new material. "
        "Protect sleep and cognitive freshness over cramming.",
        styles,
    ))
    story.append(_spacer(0.2))

    final_days = []
    for day in range(36, 40):
        plan = DAILY_PLAN[day]
        final_days.append([day, _esc(plan["date"]), _esc(plan["phase"]), _esc(plan["daily_focus"])])
    story.append(std_table(
        ["Day", "Date", "Phase", "Strategy"],
        final_days,
        [1.5 * cm, 3 * cm, 2.5 * cm, 10.5 * cm],
        styles,
    ))
    story.append(_spacer(0.3))

    story.append(_p("Final Week Daily Priorities", styles, "SubTitle"))
    for day in range(36, 40):
        plan = DAILY_PLAN[day]
        story.append(_p(f"<b>Day {day} ({_esc(plan['date'])}):</b> {_esc(plan['daily_focus'])}", styles, "SubSubTitle"))
        checklist = [
            f"Node: {_esc(plan['node_topic'][:70])}",
            f"Java: {_esc(plan['java_topic'][:70])}",
            f"SQL: {_esc(plan['sql_topic'][:70])}",
            f"Behavioral: {_esc(plan['behavioral'][:70])}",
            f"Applications target: {plan['applications_target']}",
        ]
        if plan.get("system_design"):
            checklist.append(f"System Design: {_esc(plan['system_design'])}")
        story.append(checklist_table(checklist, styles))
        story.append(_spacer(0.15))

    story.append(_p("Offer Negotiation Tips", styles, "SubTitle"))
    story.append(checklist_table(NEGOTIATION_TIPS, styles))
    story.append(_spacer(0.3))

    story.append(_p("Day-Before-Interview Checklist", styles, "SubTitle"))
    day_before = [
        "Confirm interview time, timezone, and platform (Zoom/Teams/HackerRank)",
        "Prepare quiet space, backup internet, charged laptop, water",
        "Review one-page cheat sheets only — no new problems",
        "Lay out clothes; plan to sleep by 22:30",
        "Prepare 3 thoughtful questions for the interviewer",
        "Rehearse 90-second 'Tell me about yourself' once",
        "Set two alarms; calendar reminder 30 min before",
    ]
    story.append(checklist_table(day_before, styles))
    story.append(PageBreak())
    return story


def build_appendix_a(styles):
    story = []
    story.append(section_banner("Appendix A: Full 39-Day Daily Playbook", styles, bg=ACCENT_TEAL))
    story.append(_spacer(0.3))
    story.append(_p(
        "Complete daily checklist for all 39 days. Mark each item when done. "
        "Follow the schedule in Section 2 for time blocks.",
        styles,
    ))

    for day in range(1, 40):
        plan = DAILY_PLAN[day]
        story.append(_spacer(0.25))
        story.append(_p(
            f"Day {day} — {_esc(plan['date'])}  |  {_esc(plan['phase'])}  |  {_esc(plan['daily_focus'])}",
            styles,
            "SubTitle",
        ))

        problems = DAILY_ASSIGNMENTS.get(day, [])
        lc_items = [f"LeetCode #{n}: {_esc(PROBLEM_DB[n][0])}" for n in problems[:5]]
        if len(problems) > 5:
            lc_items.append(f"... +{len(problems) - 5} more problems (see Section 3)")
        lc_items.insert(0, f"Complete {len(problems)} LeetCode problems")

        daily_checklist = [
            f"☐ Morning LeetCode Block 1 ({len(problems)} problems)",
        ] + [f"☐ {item}" for item in lc_items[1:]]
        daily_checklist.extend([
            f"☐ Node.js: {_esc(plan['node_topic'][:65])}",
            f"☐ Node exercise: {_esc(plan['node_exercise'][:65])}",
            f"☐ Java: {_esc(plan['java_topic'][:65])}",
            f"☐ Java exercise: {_esc(plan['java_exercise'][:65])}",
            f"☐ SQL: {_esc(plan['sql_topic'][:65])}",
        ])
        for i, prob in enumerate(plan.get("sql_problems", []), 1):
            daily_checklist.append(f"☐ SQL problem {i}: {_esc(prob[:55])}")
        if plan.get("mongo_topic"):
            daily_checklist.append(f"☐ MongoDB: {_esc(plan['mongo_topic'][:65])}")
        if plan.get("os_topic"):
            daily_checklist.append(f"☐ OS: {_esc(plan['os_topic'][:65])}")
        if plan.get("network_topic"):
            daily_checklist.append(f"☐ Networks: {_esc(plan['network_topic'][:65])}")
        if plan.get("system_design"):
            daily_checklist.append(f"☐ System Design: {_esc(plan['system_design'])}")
        daily_checklist.extend([
            f"☐ Behavioral STAR: {_esc(plan['behavioral'][:65])}",
            f"☐ Submit {plan['applications_target']} job application(s)",
            f"☐ Recruiter outreach: {plan['recruiter_outreach']} message(s)",
            "☐ Evening spaced repetition review (30 min)",
            "☐ Update progress tracker (Section 16)",
            "☐ Journal: top learning + top gap today",
        ])
        if plan.get("mock"):
            daily_checklist.append(f"☐ Mock interview: {_esc(plan['mock'])}")

        rows = [[item.replace("☐ ", "")] for item in daily_checklist]
        t = std_table(["Daily Checklist"], [[r[0]] for r in rows], [17.5 * cm], styles, font_style="CellSmall")
        story.append(t)

        if day % 2 == 0:
            story.append(PageBreak())

    story.append(PageBreak())
    return story


def build_appendix_b(styles):
    story = []
    story.append(section_banner("Appendix B: Company Application Tracker", styles, bg=ACCENT_TEAL))
    story.append(_spacer(0.3))
    story.append(_p(
        "Track every application, referral, and follow-up. Update status within 24 hours of any change.",
        styles,
    ))
    story.append(_spacer(0.2))

    rows = [[_esc(company), "☐", "☐", "Not Applied", "Research + tailor resume"] for company in COMPANY_TARGETS]
    story.append(std_table(
        ["Company", "Applied", "Referral", "Status", "Next Action"],
        rows,
        [4.5 * cm, 1.8 * cm, 1.8 * cm, 3.5 * cm, 5.9 * cm],
        styles,
        font_style="CellSmall",
    ))
    story.append(_spacer(0.3))

    story.append(_p("Status Legend", styles, "SubTitle"))
    legend = [
        ["Not Applied", "On target list, not yet submitted"],
        ["Applied", "Application submitted, awaiting response"],
        ["Phone Screen", "Recruiter or HM initial call scheduled/completed"],
        ["Technical", "Coding or technical round in progress"],
        ["Onsite", "Virtual onsite or panel scheduled"],
        ["Offer", "Offer received — enter negotiation (Section 17)"],
        ["Rejected", "Log reason; revisit in 6 months if company still target"],
        ["Withdrawn", "Removed from pipeline intentionally"],
    ]
    story.append(std_table(["Status", "Meaning"], legend, [3.5 * cm, 14 * cm], styles, font_style="CellSmall"))
    story.append(PageBreak())
    return story


def build_appendix_c(styles):
    story = []
    story.append(section_banner("Appendix C: Interview Scorecards", styles, bg=ACCENT_TEAL))
    story.append(_spacer(0.3))
    story.append(_p(
        "Use these scorecards after every mock and real interview. Rate 1–10 per criterion. "
        "Target average 7+ before real Tier 1 interviews.",
        styles,
    ))

    scorecards = {
        "DSA / Coding": [
            "Problem understanding and clarifying questions",
            "Approach explanation before coding",
            "Correctness of algorithm and edge cases",
            "Time and space complexity analysis",
            "Code quality — naming, structure, readability",
            "Testing with examples and dry run",
            "Communication throughout — thought process audible",
            "Speed — finished within time limit",
        ],
        "Node.js Backend": [
            "Event loop and async model accuracy",
            "Express/middleware architecture knowledge",
            "Error handling and production patterns",
            "Authentication and security awareness",
            "Database integration (MongoDB/SQL)",
            "Caching, queues, and scaling strategies",
            "Testing and debugging approach",
            "Real project examples with metrics",
        ],
        "Java / Spring Boot": [
            "JVM and core Java fundamentals",
            "Spring IoC and dependency injection",
            "REST API design and validation",
            "JPA/Hibernate and database mapping",
            "Spring Security and JWT implementation",
            "Transaction management understanding",
            "Testing strategy (unit, integration)",
            "Project demo readiness and code walkthrough",
        ],
        "System Design": [
            "Requirements clarification and scope definition",
            "High-level architecture diagram",
            "API design and data model",
            "Scaling strategy with justification",
            "Caching, queues, and async patterns",
            "Tradeoff analysis — explicit pros/cons",
            "Back-of-envelope calculations",
            "Failure modes, monitoring, and operational concerns",
        ],
        "Behavioral": [
            "STAR structure adherence",
            "Specific metrics and quantified results",
            "Clear individual contribution (uses 'I')",
            "Relevance to question asked",
            "Concise delivery (2–3 minutes)",
            "Authenticity and self-awareness",
            "Leadership and collaboration examples",
            "Strong closing reflection or learning",
        ],
    }

    for area, criteria in scorecards.items():
        story.append(_spacer(0.3))
        story.append(_p(area, styles, "SubTitle"))
        header = ["Criterion", "Score (1–10)", "Notes"]
        rows = [[_esc(c), "___", ""] for c in criteria]
        rows.append(["<b>TOTAL / Average</b>", "___ / 10", ""])
        story.append(std_table(header, rows, [8 * cm, 2.5 * cm, 7 * cm], styles, font_style="CellSmall"))

    story.append(PageBreak())
    return story


def build_pdf(output_path=None):
    """Assemble all sections and write the PDF."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if output_path is None:
        output_path = os.path.join(script_dir, OUTPUT_FILENAME)

    styles = build_styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
        title="Elite 39-Day Interview Blueprint",
        author="Interview Prep System",
        canvasmaker=lambda *args, **kwargs: NumberedCanvas(
            *args, footer_text=FOOTER_TEXT, **kwargs
        ),
    )

    story = []
    story.append(Spacer(1, 0.1 * cm))
    story.append(PageBreak())

    story.extend(build_toc(styles))
    story.extend(build_section_1_readiness(styles))
    story.extend(build_section_2_schedule(styles))
    story.extend(build_section_3_leetcode(styles))
    story.extend(build_section_4_node(styles))
    story.extend(build_section_5_java(styles))
    story.extend(build_section_6_sql(styles))
    story.extend(build_section_7_mongo(styles))
    story.extend(build_section_8_os(styles))
    story.extend(build_section_9_networks(styles))
    story.extend(build_section_10_system_design(styles))
    story.extend(build_section_11_behavioral(styles))
    story.extend(build_section_12_resume(styles))
    story.extend(build_section_13_job_search(styles))
    story.extend(build_section_14_mocks(styles))
    story.extend(build_section_15_spaced_repetition(styles))
    story.extend(build_section_16_progress(styles))
    story.extend(build_section_17_final_week(styles))
    story.extend(build_appendix_a(styles))
    story.extend(build_appendix_b(styles))
    story.extend(build_appendix_c(styles))

    doc.build(story, onFirstPage=draw_cover_page, onLaterPages=lambda c, d: None)
    return output_path


def count_pdf_pages(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            return None
    return len(PdfReader(path).pages)


if __name__ == "__main__":
    out = build_pdf()
    pages = count_pdf_pages(out)
    if pages is not None:
        print(f"Generated: {out}")
        print(f"Page count: {pages}")
    else:
        print(f"Generated: {out}")
        print("Page count: install pypdf for automatic count (pip install pypdf)")
