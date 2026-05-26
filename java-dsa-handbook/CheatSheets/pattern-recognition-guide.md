# Pattern Recognition Quick Guide

## Signal Words → Pattern Mapping

| Signal | Pattern | Template Key |
|--------|---------|-------------|
| "Subarray/substring with constraint" | Sliding Window | expand right, shrink left |
| "Max/min window of size k" | Fixed Sliding Window | add right element, remove k-ago element |
| "Sorted array + two elements" | Two Pointers | left/right converge |
| "Fast/slow to detect cycle" | Floyd's Cycle | fast=2x, slow=1x |
| "Sorted + find target" | Binary Search | left+right, mid = left+(right-left)/2 |
| "Minimize max / maximize min" | Binary Search on Answer | condition() + binary search |
| "Sum of subarray from l to r" | Prefix Sum | prefix[r+1]-prefix[l] |
| "Count subarrays with sum k" | Prefix Sum + HashMap | prefixCount.get(sum-k) |
| "Two elements sum to target" | HashMap Complement | seen.contains(target-n) |
| "Frequency/group by" | HashMap | freq.getOrDefault(k,0)+1 |
| "Next greater element" | Monotonic Stack | decreasing stack, pop when violated |
| "Histogram area" | Monotonic Stack | index stack, compute width on pop |
| "Tree traversal / path" | DFS recursive | null check, recurse left/right, combine |
| "Level by level" | BFS with queue | level-size loop pattern |
| "LCA" | Tree DFS | return non-null child |
| "Connected components" | BFS/DFS/UnionFind | visited[] + explore |
| "Cycle in directed graph" | 3-color DFS | white/gray/black |
| "Topological order" | Kahn's Algorithm | indegree[] + queue |
| "Shortest path, weighted" | Dijkstra | min-heap + dist[] |
| "Max/min with choices" | DP | dp[i] = max(options) |
| "Count ways to X" | DP | dp[i] += dp[i-choice] |
| "All subsets/combinations" | Backtracking | add, recurse, remove |
| "All permutations" | Backtracking | used[], pick any unused |
| "Top K elements" | Min-Heap size K | poll when size > k |
| "Merge K sorted" | Min-Heap | heap of (val, list, idx) |
| "Stream median" | Two Heaps | maxHeap lower, minHeap upper |
| "Overlapping intervals" | Sort by start + merge | curr.end = max(curr.end, next.end) |
| "Minimum rooms/resources" | Heap end times | poll if freed, offer new end |
| "Greedy jump/reach" | Greedy | track maxReach, jump when forced |
| "Prefix search / autocomplete" | Trie | insert + DFS collect |
| "XOR duplicates/single" | Bit XOR | a^a=0, a^0=a |
| "Power of 2" | Bit Trick | n>0 && (n&(n-1))==0 |

## The 3-Question Framework

For every problem:
1. **What's the input type?** (sorted array / graph / string / tree)
2. **What's the output?** (index / count / boolean / list / minimum)
3. **What constraint makes it hard?** (k distinct / sum = target / no overlap)

## Time Budget per Pattern

| Pattern | Expected Solve Time (Medium) |
|---------|------------------------------|
| Sliding Window | 15-20 min |
| Two Pointers | 15-20 min |
| Binary Search | 20-25 min |
| Prefix Sum | 15-20 min |
| HashMap | 10-15 min |
| Stack | 20-25 min |
| Tree DFS/BFS | 20-30 min |
| Graph | 25-35 min |
| Dynamic Programming | 30-40 min |
| Backtracking | 25-35 min |
| Heap | 20-25 min |
| Intervals | 20-25 min |
