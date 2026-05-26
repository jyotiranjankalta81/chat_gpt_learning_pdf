# C++ DSA Interview Handbook
## Complete FAANG/MAANG Preparation Guide

> **Language:** C++ | **Level:** Beginner to Advanced | **Target:** FAANG, MAANG, Big Tech, Global Banks, Product Companies

---

## Who This Is For

This handbook is designed for engineers with strong backend experience (MERN, AWS, DevOps) who need to master **Data Structures & Algorithms in C++** for top-tier technical interviews at:

- **FAANG/MAANG:** Google, Meta, Amazon, Apple, Netflix, Microsoft
- **Big Tech:** Uber, Airbnb, Atlassian, Siemens
- **Global Banks:** Morgan Stanley, Wells Fargo, Citi, HSBC

---

## Handbook Structure

| Section | Topic | Focus |
|---------|-------|-------|
| [Section 1](./Section1_CPP_Fundamentals.md) | C++ Fundamentals | Syntax, OOP, Templates, Memory |
| [Section 2](./Section2_STL_Deep_Dive.md) | STL Deep Dive | All containers, algorithms, complexity |
| [Section 3](./Section3_DSA_Foundations.md) | DSA Foundations | Complexity, Recursion, Sorting, Searching |
| [Section 4](./Section4_DSA_Patterns.md) | Complete DSA Pattern System | 15 major patterns with templates |
| [Section 5](./Section5_Competitive_Programming.md) | Competitive Programming | Fast I/O, Optimizations, Tricks |
| [Section 6](./Section6_Interview_Preparation.md) | Interview Preparation | Mindset, Communication, Strategy |
| [Section 7](./Section7_Monthly_Roadmap.md) | 1-Month Roadmap | Daily plan, LeetCode roadmap |

---

## Quick Reference Cheat Sheets

### STL Time Complexity Summary

| Container | Access | Search | Insert | Delete |
|-----------|--------|--------|--------|--------|
| `vector` | O(1) | O(n) | O(1) amortized | O(n) |
| `array` | O(1) | O(n) | N/A | N/A |
| `deque` | O(1) | O(n) | O(1) both ends | O(1) both ends |
| `list` | O(n) | O(n) | O(1) | O(1) |
| `map` | O(log n) | O(log n) | O(log n) | O(log n) |
| `unordered_map` | O(1) avg | O(1) avg | O(1) avg | O(1) avg |
| `set` | O(log n) | O(log n) | O(log n) | O(log n) |
| `unordered_set` | O(1) avg | O(1) avg | O(1) avg | O(1) avg |
| `priority_queue` | O(1) top | O(n) | O(log n) | O(log n) |
| `stack` | O(1) top | O(n) | O(1) | O(1) |
| `queue` | O(1) front | O(n) | O(1) | O(1) |

### Pattern Recognition Quick Guide

| Problem Signal | Pattern |
|---------------|---------|
| Subarray/substring of size k | Sliding Window |
| Sorted array, find pair/triplet | Two Pointers |
| Search in sorted/rotated array | Binary Search |
| Subarray sum, range queries | Prefix Sum |
| Frequency count, duplicates | HashMap/HashSet |
| Matching brackets, next greater | Stack |
| Tree traversal, path problems | Tree DFS/BFS |
| Shortest path, connected components | Graph BFS/DFS |
| Optimal substructure, overlapping subproblems | DP |
| Generate all combinations/permutations | Backtracking |
| K largest/smallest, median | Heap |
| Overlapping intervals | Intervals |
| Local optimal = Global optimal | Greedy |
| Prefix search, autocomplete | Trie |
| XOR, powers of 2 | Bit Manipulation |

---

## Essential C++ Headers for Interviews

```cpp
#include <bits/stdc++.h>  // Includes everything — use in interviews
using namespace std;

// Or individually:
#include <iostream>
#include <vector>
#include <string>
#include <map>
#include <unordered_map>
#include <set>
#include <unordered_set>
#include <queue>
#include <stack>
#include <algorithm>
#include <numeric>
#include <climits>
#include <cmath>
```

---

## Complexity Analysis Quick Reference

| Notation | Name | Example |
|----------|------|---------|
| O(1) | Constant | Array access, HashMap lookup |
| O(log n) | Logarithmic | Binary search, BST operations |
| O(n) | Linear | Linear scan, Single loop |
| O(n log n) | Linearithmic | Merge sort, Heap sort |
| O(n²) | Quadratic | Nested loops, Bubble sort |
| O(2ⁿ) | Exponential | Recursive Fibonacci, Subsets |
| O(n!) | Factorial | Permutations |

---

## Interview Communication Template

```
1. UNDERSTAND: Restate problem, clarify constraints
2. EXAMPLES: Walk through 2-3 examples including edge cases  
3. BRUTE FORCE: State the naive approach + complexity
4. OPTIMIZE: Identify bottleneck, apply pattern
5. CODE: Write clean, commented code
6. TEST: Dry run with examples, test edge cases
7. COMPLEXITY: State time and space complexity
```

---

*Generated for 1-month intensive FAANG preparation | C++ | May 2026*
