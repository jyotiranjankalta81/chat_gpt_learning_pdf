# Complexity Cheat Sheet

## Time Complexity Quick Reference

| Complexity | Name | Example |
|-----------|------|---------|
| O(1) | Constant | HashMap get/put, array index access |
| O(log n) | Logarithmic | Binary search, TreeMap operations |
| O(n) | Linear | Single loop, HashMap build |
| O(n log n) | Linearithmic | Sorting, heap build+extractions |
| O(n²) | Quadratic | Nested loops, bubble sort |
| O(n³) | Cubic | 3 nested loops, naive matrix multiply |
| O(2^n) | Exponential | Subset generation, naive recursion |
| O(n!) | Factorial | Permutation generation |

## Java Collections Complexity

| Collection | Add | Remove | Get/Contains | Iterate |
|-----------|-----|--------|------------|---------|
| ArrayList | O(1)* | O(n) | O(1) | O(n) |
| LinkedList | O(1) | O(1)** | O(n) | O(n) |
| HashMap | O(1)* | O(1)* | O(1)* | O(n) |
| TreeMap | O(log n) | O(log n) | O(log n) | O(n) |
| HashSet | O(1)* | O(1)* | O(1)* | O(n) |
| TreeSet | O(log n) | O(log n) | O(log n) | O(n) |
| PriorityQueue | O(log n) | O(log n)*** | O(1) peek | O(n) |
| ArrayDeque | O(1) | O(1) | O(1) | O(n) |

*Amortized average case  **At head/tail  ***O(n) for arbitrary element

## Algorithm Complexity

| Algorithm | Best | Average | Worst | Space |
|-----------|------|---------|-------|-------|
| Binary Search | O(1) | O(log n) | O(log n) | O(1) |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) |
| Quick Sort | O(n log n) | O(n log n) | O(n²) | O(log n) |
| Heap Sort | O(n log n) | O(n log n) | O(n log n) | O(1) |
| BFS/DFS | O(V+E) | O(V+E) | O(V+E) | O(V) |
| Dijkstra | — | O((V+E)logV) | — | O(V+E) |
| Bellman-Ford | O(VE) | O(VE) | O(VE) | O(V) |

## Space Complexity Patterns

| Pattern | Space |
|---------|-------|
| Iterative with variables | O(1) |
| Recursion depth d | O(d) |
| Recursion depth log n | O(log n) |
| Array of size n | O(n) |
| 2D array n×n | O(n²) |
| HashMap/HashSet of n items | O(n) |
