# Section 5.2 — Problem-Solving Strategy

---

## Pattern Recognition Framework

When you see a new problem, scan for these signals in order:

```
STEP 1: Read the problem statement carefully
STEP 2: Check the constraints (n = ?)
STEP 3: Look for pattern keywords
STEP 4: Identify which pattern(s) apply
STEP 5: Choose the right template
```

---

## Pattern Signal Keywords

| Keywords | Pattern |
|----------|---------|
| "subarray/substring with constraint", "window of size k" | **Sliding Window** |
| "sorted array", "palindrome", "two numbers that sum to" | **Two Pointers** |
| "sorted/rotated", "find minimum", "search in X", "binary answer" | **Binary Search** |
| "range sum", "sum of subarray = k", "number of subarrays" | **Prefix Sum** |
| "two numbers sum to target", "duplicates", "frequency", "group by" | **HashMap/HashSet** |
| "next greater", "histogram", "brackets", "expression evaluation" | **Stack** |
| "binary tree", "path sum", "level order", "LCA" | **Tree DFS/BFS** |
| "graph", "connected components", "shortest path", "detect cycle" | **Graph** |
| "max/min with choices", "ways to do X", "optimal subsequence" | **Dynamic Programming** |
| "all subsets", "all permutations", "generate all X" | **Backtracking** |
| "top K", "kth largest/smallest", "merge K sorted" | **Heap** |
| "overlapping intervals", "meeting rooms", "merge ranges" | **Intervals** |
| "minimum jumps", "make locally best choice" | **Greedy** |
| "prefix search", "autocomplete", "word dictionary" | **Trie** |
| "XOR of duplicates", "missing number", "power of 2" | **Bit Manipulation** |

---

## Decision Tree for Optimization

```
Input is sorted array?
├── YES: Binary Search or Two Pointers
└── NO:
    Looking for subarray?
    ├── YES: Sliding Window or Prefix Sum
    └── NO:
        Need to count occurrences?
        ├── YES: HashMap
        └── NO:
            Tree or Graph structure?
            ├── YES: DFS/BFS
            └── NO:
                Optimization with choices?
                ├── YES: DP or Greedy
                └── Multiple solutions needed?
                    ├── YES: Backtracking
                    └── Priority/ordering?
                        └── YES: Heap
```

---

## Complexity-Driven Pattern Selection

When you know the required complexity (from constraints):

| Required Time | Try These Patterns |
|--------------|-------------------|
| O(log n) | Binary Search, Balanced BST |
| O(n) | Sliding Window, Two Pointers, Prefix Sum, HashMap |
| O(n log n) | Sorting + scan, Heap, Tree |
| O(n²) | DP (2D), Nested loops (if acceptable) |
| O(2^n) | Backtracking, Bitmask DP (small n) |

---

## Common Optimizations to Mention

```
From O(n²) to O(n):
- Nested loops → Sliding window or two pointers
- Linear search per element → Precompute with HashMap
- Brute force pairs → Complement lookup

From O(n) to O(log n):
- Linear scan → Binary search (needs sorted/monotonic)
- n operations → Divide and conquer

Space optimizations:
- 2D DP → Rolling array (1D DP)
- Recursion → Iterative with explicit stack
- HashMap → Array (when key range is bounded)
```

---

## Time Management in Interviews

```
45-minute interview structure:
- 0-2 min:   Clarify the problem
- 2-5 min:   Discuss approach, verify with interviewer
- 5-25 min:  Code the solution
- 25-30 min: Test and debug
- 30-35 min: Discuss complexity
- 35-40 min: Optimize if time allows
- 40-45 min: Questions for interviewer

If problem is hard:
- Spend more time on planning (save coding time)
- Get brute force working first
- Optimize incrementally

Warning signs:
- Still planning after 10 min → May not finish
- Not communicating for 5+ min → Interviewer gets worried
- No code after 15 min → Very concerning
```

---

## Testing Strategy

```java
// Always test in this order:
// 1. The provided example
// 2. Edge case: empty input
// 3. Edge case: single element
// 4. Edge case: all same elements
// 5. Edge case: negative numbers (if applicable)
// 6. Edge case: maximum size (does it overflow?)

// Example test walk-through:
// Problem: Two Sum, nums=[2,7,11,15], target=9
// Expected: [0,1] (nums[0]+nums[1]=9)

// Walk through:
// i=0: complement=9-2=7, seen={}, not found, add {2:0}
// i=1: complement=9-7=2, seen={2:0}, FOUND at index 0
// Return [0, 1] ✓

// Edge cases:
// nums=[], target=0 → Should return [] (empty)
// nums=[3], target=6 → Should return [] (can't use same element twice)
// nums=[3,3], target=6 → Should return [0,1]
```

---

## Company-Specific Behavioral Anchors

### Google / Alphabet
- They value: **Clarity of thought**, can you arrive at optimal solution cleanly?
- Key soft skill: Googleyness — collaborative, intellectually humble
- Often ask: System design + algorithm in same round

### Amazon
- They value: **Leadership Principles** — Bias for Action, Dive Deep, Customer Obsession
- DSA focus: Medium/Hard graphs, DP, OOP design
- Key: Connect your solution to real-world implications

### Microsoft
- They value: **Collaboration and growth mindset**
- DSA focus: Trees, strings, OOP, and some system design
- Key: Clean, well-structured code. Follow-up questions on tradeoffs.

### Meta (Facebook)
- They value: **Speed and correctness**
- DSA focus: Graph problems, dynamic programming, trees
- Key: Finish coding quickly, handle edge cases, optimize

### Goldman Sachs / JP Morgan / Morgan Stanley
- They value: **Problem-solving under constraints** + financial reasoning
- Technical interviews similar to Big Tech but may include:
  - Order book simulation (Priority Queue)
  - Rate limiting algorithms
  - Cache invalidation
  - Stream processing (similar to Kafka patterns)
- Key: Show you understand system constraints and tradeoffs

### Atlassian / Uber / Airbnb
- They value: **Working code + good engineering judgment**
- DSA focus: Similar to Big Tech but sometimes more practical
- Key: Code reviews, explaining decisions, test coverage thinking
