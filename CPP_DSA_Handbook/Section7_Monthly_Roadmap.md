# Section 7: 1-Month FAANG Preparation Roadmap
## Structured Daily Plan for C++ DSA Mastery

> **Philosophy:** Consistency beats intensity. 4-5 focused hours daily for 30 days is better than 12-hour cramming sessions. With your 5 years of backend experience, you have a huge advantage — you understand systems, can estimate complexity intuitively, and write clean code.

---

## Overview

| Week | Theme | Goal |
|------|-------|------|
| Week 1 | C++ + Foundations + Basic Patterns | Comfortable with C++ and core patterns |
| Week 2 | Core DSA Patterns | Master sliding window, two pointers, hashing, sorting |
| Week 3 | Advanced Patterns | Trees, graphs, DP, backtracking |
| Week 4 | Mock Interviews + Company Prep | Interview-ready, pattern fluency |

---

## Daily Structure (4-5 Hours)

```
Morning (1.5-2 hrs): Learn/Review
  - Study theory from this handbook
  - Review pattern template
  - Understand 1-2 new concepts

Afternoon (2-2.5 hrs): Practice
  - Solve 3-5 LeetCode problems (Easy → Medium → Hard)
  - Time yourself (45 min per problem max)
  - Review solutions after

Evening (30 min): Revision
  - Review what you learned today
  - Update your personal cheatsheet
  - Quick mock communication practice
```

---

## Week 1: C++ Mastery + DSA Foundations

### Day 1 — C++ Syntax & Types

**Theory (from Section 1):**
- Variables, data types, operators
- Conditions, loops
- Functions (by value vs by reference)
- Type casting, overflow

**LeetCode Problems:**
1. [Two Sum](https://leetcode.com/problems/two-sum/) — Easy
2. [Palindrome Number](https://leetcode.com/problems/palindrome-number/) — Easy
3. [Reverse Integer](https://leetcode.com/problems/reverse-integer/) — Medium
4. [FizzBuzz](https://leetcode.com/problems/fizz-buzz/) — Easy

**C++ Focus:** Practice declaring variables, writing loops, using cin/cout

---

### Day 2 — Arrays & Strings

**Theory:**
- vector vs array
- String operations (substr, find, compare)
- STL: sort, reverse, find, count

**LeetCode Problems:**
1. [Best Time to Buy and Sell Stock](https://leetcode.com/problems/best-time-to-buy-and-sell-stock/) — Easy
2. [Contains Duplicate](https://leetcode.com/problems/contains-duplicate/) — Easy
3. [Valid Anagram](https://leetcode.com/problems/valid-anagram/) — Easy
4. [Maximum Subarray](https://leetcode.com/problems/maximum-subarray/) — Medium (Kadane's)

---

### Day 3 — HashMap & HashSet

**Theory (Section 2: map/unordered_map/set/unordered_set):**
- When to use each
- O(1) vs O(log n) tradeoffs
- Custom hash, collision handling

**LeetCode Problems:**
1. [Two Sum](https://leetcode.com/problems/two-sum/) — Revisit with hashmap
2. [Group Anagrams](https://leetcode.com/problems/group-anagrams/) — Medium
3. [Top K Frequent Elements](https://leetcode.com/problems/top-k-frequent-elements/) — Medium
4. [Longest Consecutive Sequence](https://leetcode.com/problems/longest-consecutive-sequence/) — Medium

---

### Day 4 — Binary Search Fundamentals

**Theory (Section 3, Section 4 Pattern 3):**
- Classic binary search
- Lower/upper bound
- Binary search on answer pattern

**LeetCode Problems:**
1. [Binary Search](https://leetcode.com/problems/binary-search/) — Easy
2. [Search Insert Position](https://leetcode.com/problems/search-insert-position/) — Easy
3. [First Bad Version](https://leetcode.com/problems/first-bad-version/) — Easy
4. [Koko Eating Bananas](https://leetcode.com/problems/koko-eating-bananas/) — Medium
5. [Search in Rotated Sorted Array](https://leetcode.com/problems/search-in-rotated-sorted-array/) — Medium

---

### Day 5 — Recursion & Backtracking Introduction

**Theory (Section 3: Recursion, Section 4 Pattern 10):**
- Recursion tree visualization
- Base case + recursive case
- Subsets and permutations

**LeetCode Problems:**
1. [Fibonacci Number](https://leetcode.com/problems/fibonacci-number/) — Easy
2. [Climbing Stairs](https://leetcode.com/problems/climbing-stairs/) — Easy
3. [Subsets](https://leetcode.com/problems/subsets/) — Medium
4. [Permutations](https://leetcode.com/problems/permutations/) — Medium

---

### Day 6 — Sorting Algorithms

**Theory (Section 3):**
- Merge sort implementation
- Quick sort implementation
- When to use which sort
- Custom comparators

**LeetCode Problems:**
1. [Sort Colors](https://leetcode.com/problems/sort-colors/) — Medium (Dutch flag)
2. [Merge Intervals](https://leetcode.com/problems/merge-intervals/) — Medium
3. [Largest Number](https://leetcode.com/problems/largest-number/) — Medium
4. [Kth Largest Element](https://leetcode.com/problems/kth-largest-element-in-an-array/) — Medium

---

### Day 7 — Week 1 Review & Mock

**Morning:** Review all week 1 material. Fill gaps.

**Practice: Solve without looking at solutions:**
1. [Two Sum II](https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/) — Medium
2. [3Sum](https://leetcode.com/problems/3sum/) — Medium
3. [Find Minimum in Rotated Sorted Array](https://leetcode.com/problems/find-minimum-in-rotated-sorted-array/) — Medium

**Mock Interview:** Time yourself (45 min/problem). Speak out loud.

---

## Week 2: Core Patterns Mastery

### Day 8 — Sliding Window

**Theory (Section 4 Pattern 1):**
- Fixed-size window
- Variable-size window
- Monotonic deque

**LeetCode Problems:**
1. [Maximum Average Subarray I](https://leetcode.com/problems/maximum-average-subarray-i/) — Easy
2. [Longest Substring Without Repeating Characters](https://leetcode.com/problems/longest-substring-without-repeating-characters/) — Medium
3. [Minimum Window Substring](https://leetcode.com/problems/minimum-window-substring/) — Hard
4. [Sliding Window Maximum](https://leetcode.com/problems/sliding-window-maximum/) — Hard

---

### Day 9 — Two Pointers

**Theory (Section 4 Pattern 2):**
- Opposite direction
- Same direction (fast/slow)
- Floyd's cycle detection

**LeetCode Problems:**
1. [Valid Palindrome](https://leetcode.com/problems/valid-palindrome/) — Easy
2. [Container With Most Water](https://leetcode.com/problems/container-with-most-water/) — Medium
3. [3Sum](https://leetcode.com/problems/3sum/) — Medium (revisit)
4. [Trapping Rain Water](https://leetcode.com/problems/trapping-rain-water/) — Hard
5. [Linked List Cycle](https://leetcode.com/problems/linked-list-cycle/) — Easy

---

### Day 10 — Prefix Sum

**Theory (Section 4 Pattern 4):**
- 1D and 2D prefix sums
- Subarray sum with hashmap trick

**LeetCode Problems:**
1. [Range Sum Query](https://leetcode.com/problems/range-sum-query-immutable/) — Easy
2. [Subarray Sum Equals K](https://leetcode.com/problems/subarray-sum-equals-k/) — Medium
3. [Product of Array Except Self](https://leetcode.com/problems/product-of-array-except-self/) — Medium
4. [Count Number of Nice Subarrays](https://leetcode.com/problems/count-number-of-nice-subarrays/) — Medium

---

### Day 11 — Stack & Monotonic Stack

**Theory (Section 4 Pattern 6):**
- Stack for bracket matching
- Monotonic stack for NGE
- Histogram rectangle

**LeetCode Problems:**
1. [Valid Parentheses](https://leetcode.com/problems/valid-parentheses/) — Easy
2. [Min Stack](https://leetcode.com/problems/min-stack/) — Medium
3. [Daily Temperatures](https://leetcode.com/problems/daily-temperatures/) — Medium
4. [Largest Rectangle in Histogram](https://leetcode.com/problems/largest-rectangle-in-histogram/) — Hard
5. [Decode String](https://leetcode.com/problems/decode-string/) — Medium

---

### Day 12 — Linked Lists

**Theory:**
- ListNode structure
- Reversal, cycle detection, merge
- Fast/slow pointers

**LeetCode Problems:**
1. [Reverse Linked List](https://leetcode.com/problems/reverse-linked-list/) — Easy
2. [Merge Two Sorted Lists](https://leetcode.com/problems/merge-two-sorted-lists/) — Easy
3. [Linked List Cycle II](https://leetcode.com/problems/linked-list-cycle-ii/) — Medium
4. [Remove Nth Node From End](https://leetcode.com/problems/remove-nth-node-from-end-of-list/) — Medium
5. [LRU Cache](https://leetcode.com/problems/lru-cache/) — Medium

---

### Day 13 — Heap/Priority Queue

**Theory (Section 4 Pattern 11):**
- Max-heap, min-heap
- K-th element problems
- Stream processing

**LeetCode Problems:**
1. [Kth Largest Element](https://leetcode.com/problems/kth-largest-element-in-an-array/) — Medium
2. [Top K Frequent Elements](https://leetcode.com/problems/top-k-frequent-elements/) — Medium
3. [K Closest Points to Origin](https://leetcode.com/problems/k-closest-points-to-origin/) — Medium
4. [Find Median from Data Stream](https://leetcode.com/problems/find-median-from-data-stream/) — Hard
5. [Merge K Sorted Lists](https://leetcode.com/problems/merge-k-sorted-lists/) — Hard

---

### Day 14 — Week 2 Review & Mock

**Full Mock Interview (2 problems, 45 min each):**

Randomly pick from:
- Sliding window
- Two pointers
- HashMap
- Stack

**Reflection:**
- Which patterns are weak? → More focus in week 3
- Timing: Are you finishing in 45 min?
- Communication: Are you thinking out loud?

---

## Week 3: Advanced Patterns

### Day 15 — Binary Trees

**Theory (Section 4 Pattern 7):**
- DFS: inorder, preorder, postorder
- BFS: level order
- TreeNode struct, recursion patterns

**LeetCode Problems:**
1. [Maximum Depth of Binary Tree](https://leetcode.com/problems/maximum-depth-of-binary-tree/) — Easy
2. [Invert Binary Tree](https://leetcode.com/problems/invert-binary-tree/) — Easy
3. [Diameter of Binary Tree](https://leetcode.com/problems/diameter-of-binary-tree/) — Easy
4. [Binary Tree Level Order Traversal](https://leetcode.com/problems/binary-tree-level-order-traversal/) — Medium
5. [Lowest Common Ancestor of BST](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/) — Medium

---

### Day 16 — Binary Tree Advanced + BST

**LeetCode Problems:**
1. [Validate Binary Search Tree](https://leetcode.com/problems/validate-binary-search-tree/) — Medium
2. [Binary Tree Right Side View](https://leetcode.com/problems/binary-tree-right-side-view/) — Medium
3. [Construct Binary Tree from Preorder and Inorder](https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/) — Medium
4. [Serialize and Deserialize Binary Tree](https://leetcode.com/problems/serialize-and-deserialize-binary-tree/) — Hard
5. [Binary Tree Maximum Path Sum](https://leetcode.com/problems/binary-tree-maximum-path-sum/) — Hard

---

### Day 17 — Graph Fundamentals

**Theory (Section 4 Pattern 8):**
- Adjacency list/matrix
- DFS and BFS templates
- Connected components

**LeetCode Problems:**
1. [Number of Islands](https://leetcode.com/problems/number-of-islands/) — Medium
2. [Clone Graph](https://leetcode.com/problems/clone-graph/) — Medium
3. [Course Schedule](https://leetcode.com/problems/course-schedule/) — Medium (Topological sort)
4. [Pacific Atlantic Water Flow](https://leetcode.com/problems/pacific-atlantic-water-flow/) — Medium
5. [Word Ladder](https://leetcode.com/problems/word-ladder/) — Hard (BFS)

---

### Day 18 — Graph Advanced (Dijkstra, Union-Find)

**Theory:**
- Dijkstra's shortest path
- Union-Find / Disjoint Set Union
- Minimum spanning tree (Kruskal/Prim)

**LeetCode Problems:**
1. [Network Delay Time](https://leetcode.com/problems/network-delay-time/) — Medium (Dijkstra)
2. [Number of Provinces](https://leetcode.com/problems/number-of-provinces/) — Medium (Union-Find)
3. [Redundant Connection](https://leetcode.com/problems/redundant-connection/) — Medium (Union-Find)
4. [Min Cost to Connect All Points](https://leetcode.com/problems/min-cost-to-connect-all-points/) — Medium (Prim/Kruskal)
5. [Cheapest Flights Within K Stops](https://leetcode.com/problems/cheapest-flights-within-k-stops/) — Medium

---

### Day 19 — Dynamic Programming I (1D)

**Theory (Section 4 Pattern 9):**
- DP framework: subproblem, recurrence, base cases
- Linear DP: climbing stairs, house robber
- LIS with binary search

**LeetCode Problems:**
1. [Climbing Stairs](https://leetcode.com/problems/climbing-stairs/) — Easy
2. [House Robber](https://leetcode.com/problems/house-robber/) — Medium
3. [House Robber II](https://leetcode.com/problems/house-robber-ii/) — Medium
4. [Longest Increasing Subsequence](https://leetcode.com/problems/longest-increasing-subsequence/) — Medium
5. [Word Break](https://leetcode.com/problems/word-break/) — Medium

---

### Day 20 — Dynamic Programming II (2D)

**Theory:**
- Grid DP
- String DP (LCS, Edit Distance)
- 0/1 Knapsack

**LeetCode Problems:**
1. [Unique Paths](https://leetcode.com/problems/unique-paths/) — Medium
2. [Longest Common Subsequence](https://leetcode.com/problems/longest-common-subsequence/) — Medium
3. [Edit Distance](https://leetcode.com/problems/edit-distance/) — Hard
4. [Coin Change](https://leetcode.com/problems/coin-change/) — Medium
5. [Partition Equal Subset Sum](https://leetcode.com/problems/partition-equal-subset-sum/) — Medium

---

### Day 21 — Backtracking + Intervals + Greedy

**Theory (Section 4 Patterns 10, 12, 13):**

**LeetCode Problems:**
1. [Combination Sum](https://leetcode.com/problems/combination-sum/) — Medium
2. [N-Queens](https://leetcode.com/problems/n-queens/) — Hard
3. [Merge Intervals](https://leetcode.com/problems/merge-intervals/) — Medium (revisit)
4. [Non-overlapping Intervals](https://leetcode.com/problems/non-overlapping-intervals/) — Medium
5. [Jump Game II](https://leetcode.com/problems/jump-game-ii/) — Medium

---

## Week 4: Interview Simulation & Company Prep

### Day 22 — Trie + Bit Manipulation

**Theory (Section 4 Patterns 14, 15):**

**LeetCode Problems:**
1. [Implement Trie](https://leetcode.com/problems/implement-trie-prefix-tree/) — Medium
2. [Word Search II](https://leetcode.com/problems/word-search-ii/) — Hard
3. [Single Number](https://leetcode.com/problems/single-number/) — Easy
4. [Number of 1 Bits](https://leetcode.com/problems/number-of-1-bits/) — Easy
5. [Missing Number](https://leetcode.com/problems/missing-number/) — Easy

---

### Day 23 — Company-Specific: Google/Meta

**Google-style (algorithmic, complex):**
1. [Median of Two Sorted Arrays](https://leetcode.com/problems/median-of-two-sorted-arrays/) — Hard
2. [Regular Expression Matching](https://leetcode.com/problems/regular-expression-matching/) — Hard
3. [Trapping Rain Water](https://leetcode.com/problems/trapping-rain-water/) — Hard
4. [Alien Dictionary](https://leetcode.com/problems/alien-dictionary/) — Hard

**Meta-style (practical, clean code):**
1. [Flatten Binary Tree to Linked List](https://leetcode.com/problems/flatten-binary-tree-to-linked-list/) — Medium
2. [Remove Invalid Parentheses](https://leetcode.com/problems/remove-invalid-parentheses/) — Hard

---

### Day 24 — Company-Specific: Amazon/Microsoft

**Amazon (LP + algorithm):**
1. [LRU Cache](https://leetcode.com/problems/lru-cache/) — Medium
2. [Find All Anagrams in a String](https://leetcode.com/problems/find-all-anagrams-in-a-string/) — Medium
3. [Copy List with Random Pointer](https://leetcode.com/problems/copy-list-with-random-pointer/) — Medium
4. [Design Add and Search Words](https://leetcode.com/problems/design-add-and-search-words-data-structure/) — Medium

---

### Day 25 — Company-Specific: Uber/Airbnb/Banks

**Focus: Graphs + System thinking:**
1. [Course Schedule II](https://leetcode.com/problems/course-schedule-ii/) — Medium
2. [Reconstruct Itinerary](https://leetcode.com/problems/reconstruct-itinerary/) — Hard
3. [Task Scheduler](https://leetcode.com/problems/task-scheduler/) — Medium
4. [Max Points on a Line](https://leetcode.com/problems/max-points-on-a-line/) — Hard

---

### Day 26-27 — Full Mock Interviews

**Day 26 Mock 1:**
- Set timer for 45 minutes
- Pick 1 random medium problem
- Speak aloud, follow the 7-step framework
- Review and grade yourself

**Day 27 Mock 2:**
- Use [interviewing.io](https://interviewing.io/) or [Pramp](https://pramp.com/)
- Real interview with another engineer
- Focus on communication quality

---

### Day 28 — Hard Problems Sprint

**Challenge mode — solve all in 1 hour each:**
1. [Word Search II](https://leetcode.com/problems/word-search-ii/) — Hard
2. [Minimum Window Substring](https://leetcode.com/problems/minimum-window-substring/) — Hard
3. [Maximum Profit in Job Scheduling](https://leetcode.com/problems/maximum-profit-in-job-scheduling/) — Hard

---

### Day 29 — Weak Areas + System Design Review

**Morning:** Identify 3 patterns you're weakest at. Solve 2 problems each.

**Afternoon:** Review system design concepts relevant to DSA:
- Consistent hashing → Hashmap internals
- B-Trees → BST/self-balancing trees
- Skip lists → Balanced BST alternative
- Bloom filters → Probabilistic data structures

---

### Day 30 — Final Review & Mental Preparation

**Morning:**
- Review your personal cheatsheet
- Go through pattern summary table (Section 4)
- Review STL cheatsheet (Section 2)

**Afternoon:**
- Solve 3-5 easy problems to build confidence
- Review behavioral stories
- Prepare questions to ask interviewers

**Evening:**
- Rest
- Visualize yourself succeeding in the interview
- Sleep 8 hours

---

## LeetCode Top 75 Roadmap (Categorized)

### Arrays & Hashing
| # | Problem | Difficulty | Pattern |
|---|---------|-----------|---------|
| 1 | Two Sum | Easy | HashMap |
| 2 | Contains Duplicate | Easy | HashSet |
| 3 | Valid Anagram | Easy | HashMap |
| 4 | Group Anagrams | Medium | HashMap |
| 5 | Top K Frequent | Medium | HashMap + Heap |
| 6 | Encode/Decode Strings | Medium | String |
| 7 | Product of Array Except Self | Medium | Prefix/Suffix |
| 8 | Valid Sudoku | Medium | HashSet |
| 9 | Longest Consecutive Sequence | Medium | HashSet |

### Two Pointers
| # | Problem | Difficulty | Pattern |
|---|---------|-----------|---------|
| 10 | Valid Palindrome | Easy | Two Pointers |
| 11 | Two Sum II | Medium | Two Pointers |
| 12 | 3Sum | Medium | Sort + Two Pointers |
| 13 | Container With Most Water | Medium | Two Pointers |
| 14 | Trapping Rain Water | Hard | Two Pointers |

### Sliding Window
| # | Problem | Difficulty | Pattern |
|---|---------|-----------|---------|
| 15 | Best Time to Buy/Sell Stock | Easy | Sliding Window |
| 16 | Longest Substring Without Repeating | Medium | SW Variable |
| 17 | Longest Repeating Char Replacement | Medium | SW + Counter |
| 18 | Permutation In String | Medium | SW Fixed |
| 19 | Minimum Window Substring | Hard | SW Variable |
| 20 | Sliding Window Maximum | Hard | SW + Deque |

### Binary Search
| # | Problem | Difficulty | Pattern |
|---|---------|-----------|---------|
| 21 | Binary Search | Easy | Classic BS |
| 22 | Search a 2D Matrix | Medium | BS |
| 23 | Koko Eating Bananas | Medium | BS on Answer |
| 24 | Find Min in Rotated Sorted Array | Medium | BS |
| 25 | Search in Rotated Sorted Array | Medium | BS |
| 26 | Time Based Key-Value Store | Medium | BS |
| 27 | Median of Two Sorted Arrays | Hard | BS |

### Stack
| # | Problem | Difficulty | Pattern |
|---|---------|-----------|---------|
| 28 | Valid Parentheses | Easy | Stack |
| 29 | Min Stack | Medium | Stack |
| 30 | Evaluate Reverse Polish Notation | Medium | Stack |
| 31 | Generate Parentheses | Medium | Backtrack |
| 32 | Daily Temperatures | Medium | Monotonic Stack |
| 33 | Car Fleet | Medium | Monotonic Stack |
| 34 | Largest Rectangle in Histogram | Hard | Monotonic Stack |

### Linked List
| # | Problem | Difficulty | Pattern |
|---|---------|-----------|---------|
| 35 | Reverse Linked List | Easy | Two Pointer |
| 36 | Merge Two Sorted Lists | Easy | Merge |
| 37 | Reorder List | Medium | Fast/Slow |
| 38 | Remove Nth From End | Medium | Fast/Slow |
| 39 | Linked List Cycle | Easy | Fast/Slow |
| 40 | Find Duplicate Number | Medium | Floyd's Cycle |
| 41 | LRU Cache | Medium | HashMap + DLL |
| 42 | Merge K Sorted Lists | Hard | Heap |
| 43 | Reverse Nodes in K-Group | Hard | Recursion |

### Trees
| # | Problem | Difficulty | Pattern |
|---|---------|-----------|---------|
| 44 | Invert Binary Tree | Easy | DFS |
| 45 | Maximum Depth | Easy | DFS |
| 46 | Diameter of Tree | Easy | DFS |
| 47 | Balanced Binary Tree | Easy | DFS |
| 48 | Same Tree | Easy | DFS |
| 49 | Subtree of Another Tree | Easy | DFS |
| 50 | LCA of BST | Medium | DFS |
| 51 | BST Insert/Delete | Medium | BST |
| 52 | Validate BST | Medium | DFS |
| 53 | Kth Smallest in BST | Medium | Inorder |
| 54 | Construct BST from Preorder | Medium | DFS |
| 55 | Level Order Traversal | Medium | BFS |
| 56 | Right Side View | Medium | BFS |
| 57 | Count Good Nodes | Medium | DFS |
| 58 | Word Search II | Hard | Trie + DFS |
| 59 | Max Path Sum | Hard | DFS |
| 60 | Serialize/Deserialize Tree | Hard | BFS/DFS |

### Graphs
| # | Problem | Difficulty | Pattern |
|---|---------|-----------|---------|
| 61 | Number of Islands | Medium | DFS/BFS |
| 62 | Clone Graph | Medium | DFS/BFS |
| 63 | Max Area of Island | Medium | DFS |
| 64 | Pacific Atlantic Water Flow | Medium | DFS |
| 65 | Surrounded Regions | Medium | DFS |
| 66 | Rotting Oranges | Medium | BFS |
| 67 | Walls and Gates | Medium | BFS |
| 68 | Course Schedule | Medium | Topo Sort |
| 69 | Course Schedule II | Medium | Topo Sort |
| 70 | Redundant Connection | Medium | Union-Find |
| 71 | Word Ladder | Hard | BFS |

### DP
| # | Problem | Difficulty | Pattern |
|---|---------|-----------|---------|
| 72 | Climbing Stairs | Easy | 1D DP |
| 73 | House Robber | Medium | 1D DP |
| 74 | Coin Change | Medium | Unbounded Knapsack |
| 75 | Longest Increasing Subsequence | Medium | DP + BS |

---

## Revision Schedule

### Daily Quick Revision (15 min/day)

```
Monday:    Sliding Window + Two Pointers
Tuesday:   Binary Search + Prefix Sum
Wednesday: Stack + HashMap
Thursday:  Trees (DFS/BFS templates)
Friday:    Graphs + DP templates
Saturday:  Mock interview + Backtracking
Sunday:    Rest or catch-up
```

### Pattern Template Flashcard System

Create flashcards (physical or Anki) for:
1. Sliding window variable template
2. Binary search on answer template
3. DFS tree template
4. BFS graph template
5. DP coin change template
6. Union-Find template
7. Monotonic stack NGE template
8. Backtracking subsets template
9. Dijkstra's template
10. Prefix sum + hashmap template

Review all 10 flashcards daily (5-10 min).

---

## Mock Interview Schedule

| Day | Type | Platform |
|-----|------|----------|
| 7 | Solo mock | Timer + speak aloud |
| 14 | Solo mock | Timer + speak aloud |
| 21 | Peer mock | With a friend |
| 24 | Professional mock | interviewing.io |
| 26 | Solo mock | Full simulation |
| 27 | Peer/Professional mock | Pramp |
| 29 | Final solo | Confidence builder |

---

## Progress Tracker

### Weekly Pattern Mastery Self-Assessment

Rate yourself 1-5 for each pattern after each week:

| Pattern | Week 1 | Week 2 | Week 3 | Week 4 |
|---------|--------|--------|--------|--------|
| Sliding Window | | | | |
| Two Pointers | | | | |
| Binary Search | | | | |
| Prefix Sum | | | | |
| HashMap | | | | |
| Stack | | | | |
| Tree DFS | | | | |
| Tree BFS | | | | |
| Graph DFS/BFS | | | | |
| Dynamic Programming | | | | |
| Backtracking | | | | |
| Heap | | | | |
| Intervals | | | | |
| Greedy | | | | |
| Trie | | | | |
| Bit Manipulation | | | | |

**Score 1:** Can't recognize the pattern
**Score 2:** Can recognize but not code
**Score 3:** Can code with hints/reference
**Score 4:** Can code independently in 30 min
**Score 5:** Can solve optimally + explain + handle follow-ups in < 20 min

**Target:** All patterns at 4+ before interviews.

---

## Resources

### Primary (This Handbook)
- Section 1-7 as your core reference

### LeetCode
- [NeetCode 150](https://neetcode.io/) — Best curated list
- [Blind 75](https://leetcode.com/discuss/general-discussion/460599/blind-75-leetcode-questions) — Classic list
- Use LeetCode Premium for company-specific questions

### For Deeper Learning
- **Book:** "Introduction to Algorithms" (CLRS) — Reference for theory
- **Book:** "Competitive Programming 3" — Advanced techniques
- **YouTube:** 
  - NeetCode (pattern explanations)
  - Back To Back SWE (deep algorithmic thinking)
  - Abdul Bari (algorithms foundation)

### Practice Platforms
- [LeetCode](https://leetcode.com) — Primary
- [HackerRank](https://hackerrank.com) — Good for C++ syntax
- [Codeforces](https://codeforces.com) — Competitive programming
- [AlgoExpert](https://algoexpert.io) — Video solutions

---

*You have everything you need. The next step is consistent daily execution. Start with Day 1. Good luck!*
