#!/usr/bin/env python3
"""Rebuild leetcode_roadmap.py with DSA 4.5 schedule: 15 qns day 1 → 35+ by July 31."""

import os
import ast
import textwrap
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, "..", "data", "leetcode_roadmap.py")
REPO_ROOT = os.path.join(SCRIPT_DIR, "../..")

result = subprocess.run(
    ["git", "show", "HEAD:interview-prep-blueprint/data/leetcode_roadmap.py"],
    capture_output=True, text=True, cwd=REPO_ROOT,
)
if result.returncode != 0:
    raise RuntimeError("Cannot load base PROBLEM_DB from git")
base_dict = ast.literal_eval(
    result.stdout.split("PROBLEM_DB = ", 1)[1].split("\n\nDAILY_ASSIGNMENTS", 1)[0]
)

from rebuild_assignments import EXTRA_PROBLEMS, build_assignments, get_daily_count


def format_problem_db(db):
    lines = ["PROBLEM_DB = {"]
    for num in sorted(db.keys()):
        t = db[num]
        title = t[0].replace('"', '\\"')
        lines.append(
            f'    {num}: ("{title}", "{t[1]}", "{t[2]}", "{t[3]}", {t[4]}, "{t[5]}", "{t[6]}"),'
        )
    lines.append("}")
    return "\n".join(lines)


def format_assignments(assignments):
    lines = ["DAILY_ASSIGNMENTS = {"]
    for day in range(1, 40):
        lines.append(f"    {day}: {assignments[day]},")
    lines.append("}")
    return "\n".join(lines)


def main():
    full_db = {**base_dict, **EXTRA_PROBLEMS}
    assignments = build_assignments(full_db)

    header = textwrap.dedent('''\
        """LeetCode study roadmap: problem database and 39-day schedule.

        Calibrated for DSA 4.5/5: Day 1 = 15 problems, Day 31 = 35 problems,
        Days 32-39 = 36-38 (revision-heavy). Difficulty mix ~13% Easy, ~50% Medium, ~37% Hard.
        """

    ''')

    tail = textwrap.dedent('''\
        TOPIC_ORDER = [
            "Arrays",
            "Strings",
            "HashMap",
            "Sorting",
            "Two Pointers",
            "Sliding Window",
            "Binary Search",
            "Stack",
            "Queue",
            "Linked List",
            "Trees",
            "BST",
            "Heap",
            "Trie",
            "Graph",
            "Topological Sort",
            "Union Find",
            "Backtracking",
            "Greedy",
            "Intervals",
            "Dynamic Programming",
            "Advanced Graph",
            "Hard Interview Problems",
        ]


        def get_problem_row(num, day_num):
            """Return table row for a problem assigned on day_num."""
            title, diff, pattern, concept, time_min, followup, freq = PROBLEM_DB[num]
            offsets = [0, 2, 6, 13, 20, 29]
            revision_dates = ", ".join(
                f"D{day_num + o}" for o in offsets if day_num + o <= 39
            )
            return [num, title, diff, pattern, concept, time_min, followup, revision_dates, freq]


        def get_daily_count(day):
            """Day 1 = 15, Day 31 = 35, Days 32-39 = 36-38."""
            if day <= 31:
                return round(15 + (35 - 15) * (day - 1) / 30)
            return min(38, 35 + (day - 31))
    ''')

    content = header + format_problem_db(full_db) + "\n\n\n" + format_assignments(assignments) + "\n\n\n" + tail

    with open(DATA_PATH, "w") as f:
        f.write(content)

    total = sum(len(v) for v in assignments.values())
    print(f"Written {DATA_PATH}")
    print(f"Pool: {len(full_db)} | Total slots: {total}")
    for d in [1, 7, 15, 31, 39]:
        probs = assignments[d]
        diffs = [full_db[p][1] for p in probs]
        e, m, h = diffs.count("E"), diffs.count("M"), diffs.count("H")
        pct = round(e / len(probs) * 100)
        print(f"  Day {d}: {len(probs)} qns (E={e}/{pct}%, M={m}, H={h}) target={get_daily_count(d)}")


if __name__ == "__main__":
    main()
