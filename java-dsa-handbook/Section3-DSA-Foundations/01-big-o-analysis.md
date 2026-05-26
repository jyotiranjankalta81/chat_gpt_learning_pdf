# Section 3.1 — Big O Analysis

---

## 1. What is Big O?

Big O notation describes the **upper bound** of an algorithm's resource usage (time or space) as input size grows. It's about the **order of magnitude**, not exact values.

```
O(1) < O(log n) < O(n) < O(n log n) < O(n²) < O(2ⁿ) < O(n!)
```

For n = 1,000:
- O(1) → 1 operation
- O(log n) → ~10 operations
- O(n) → 1,000 operations
- O(n log n) → ~10,000 operations
- O(n²) → 1,000,000 operations
- O(2ⁿ) → 10^301 operations (impossible)

---

## 2. Common Complexities Explained

### O(1) — Constant Time

```java
// Time does not depend on input size
int[] arr = {1, 2, 3, 4, 5};
int first = arr[0];              // O(1)
int last = arr[arr.length - 1];  // O(1)
map.get(key);                    // O(1) average
set.contains(val);               // O(1) average
stack.push(val);                 // O(1)
```

### O(log n) — Logarithmic

```java
// Input is halved each step
// Classic: binary search
int binarySearch(int[] arr, int target) {
    int left = 0, right = arr.length - 1;
    while (left <= right) {      // ← repeats log₂(n) times
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) return mid;
        else if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}
// n=1000: ~10 iterations. n=1000000: ~20 iterations
```

### O(n) — Linear

```java
// Visits each element once
int sum = 0;
for (int n : arr) sum += n;       // O(n) — one pass

// Single pass with HashMap — still O(n)
Map<Integer, Integer> freq = new HashMap<>();
for (int n : arr) freq.merge(n, 1, Integer::sum);  // O(n)
```

### O(n log n) — Linearithmic

```java
// Comparison-based sorting algorithms
Arrays.sort(arr);           // O(n log n) — merge sort / tim sort
Collections.sort(list);     // O(n log n)
// Building a heap: O(n), then n extractions: O(n log n)
// n insertions into TreeMap/TreeSet: O(n log n)
```

### O(n²) — Quadratic

```java
// Nested loops — brute force
for (int i = 0; i < n; i++) {
    for (int j = i + 1; j < n; j++) {
        // O(n²) total iterations
    }
}
// Bubble sort, insertion sort, selection sort
// Two-sum naive, checking all pairs
```

### O(2ⁿ) — Exponential

```java
// Recursion that branches into 2 each call
// Classic: naive Fibonacci, all subsets
int fib(int n) {
    if (n <= 1) return n;
    return fib(n-1) + fib(n-2);  // 2 calls each time → O(2ⁿ)
}
// All subsets of n elements: 2ⁿ subsets
// Can usually be optimized with memoization/DP
```

### O(n!) — Factorial

```java
// All permutations of n elements
// Backtracking problems: generate all permutations
// Traveling salesman (brute force)
// n=10: 3,628,800 — barely feasible
// n=15: 1.3 trillion — impossible
```

---

## 3. Analyzing Your Code

### Rules

```
Rule 1: Drop constants
O(2n) → O(n)
O(100) → O(1)
O(n/2) → O(n)

Rule 2: Drop lower-order terms
O(n² + n) → O(n²)
O(n³ + n² + n) → O(n³)
O(n + 500) → O(n)

Rule 3: Different variables for different inputs
void func(int[] a, int[] b) {
    for (int x : a) {}     // O(a)
    for (int y : b) {}     // O(b)
    // Total: O(a + b), NOT O(n)
}

Rule 4: Nested loops multiply
for i in [0,n):      // O(n)
    for j in [0,n):  // O(n)
        ...          // Total: O(n²)

for i in [0,n):      // O(n)
    for j in [0,m):  // O(m)
        ...          // Total: O(n*m)

Rule 5: Recursive — use Master Theorem or recurrence
T(n) = 2T(n/2) + O(n) → O(n log n) [merge sort]
T(n) = T(n/2) + O(1)  → O(log n) [binary search]
T(n) = T(n-1) + O(1)  → O(n) [linear recursion]
T(n) = 2T(n-1) + O(1) → O(2ⁿ) [exponential]
```

### Practice: Identify Complexity

```java
// Example 1
void example1(int n) {
    for (int i = 0; i < n; i++) {          // O(n)
        for (int j = 0; j < n; j++) {      // O(n)
            System.out.print(i + j);        // O(1)
        }
    }
}  // Total: O(n²)

// Example 2
void example2(int n) {
    for (int i = n; i > 0; i /= 2) {      // halves each time → O(log n)
        System.out.println(i);
    }
}  // Total: O(log n)

// Example 3
void example3(int[] arr) {
    for (int i = 0; i < arr.length; i++) {  // O(n)
        for (int j = i; j < arr.length; j++) { // O(n) inner
            // sum: (n) + (n-1) + ... + 1 = n(n+1)/2
        }
    }
}  // Total: O(n²) — even though inner loop shrinks

// Example 4 — with function call
void example4(int[] arr) {
    for (int val : arr) {        // O(n)
        Arrays.sort(arr);        // O(n log n) INSIDE the loop!
    }
}  // Total: O(n² log n) — careful with function calls in loops!

// Example 5 — recursive with memo
int[] memo = new int[n + 1];
int fib(int n) {
    if (n <= 1) return n;
    if (memo[n] != 0) return memo[n];
    return memo[n] = fib(n-1) + fib(n-2);
}  // With memoization: O(n) time, O(n) space
```

---

## 4. Space Complexity

```
O(1)      — Fixed amount of variables (no arrays, no recursion)
O(n)      — Array, list, map of size n; recursion depth n
O(n²)     — 2D array n×n
O(log n)  — Recursion depth of binary search
O(n log n)— Merge sort's stack frames (log n deep, n work each)
```

```java
// O(1) space
int sum = 0;
for (int n : arr) sum += n;  // only one variable

// O(n) space
int[] prefix = new int[n];   // array of size n
Map<Integer, Integer> map = new HashMap<>();  // up to n entries

// O(log n) space — recursion stack
int binarySearch(int[] arr, int l, int r, int target) {
    if (l > r) return -1;
    int mid = (l + r) / 2;
    // recursive call depth: O(log n)
    return arr[mid] == target ? mid :
           arr[mid] < target ? binarySearch(arr, mid+1, r, target) :
                               binarySearch(arr, l, mid-1, target);
}

// O(n) space — recursion
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);  // n stack frames
}
```

---

## 5. Complexity of Java Built-in Operations

| Operation | Time | Space |
|-----------|------|-------|
| `Arrays.sort(int[])` | O(n log n) | O(log n) |
| `Arrays.sort(Integer[])` with comparator | O(n log n) | O(log n) |
| `String.substring(l, r)` | O(r-l) | O(r-l) |
| `String.contains(s)` | O(n*m) | O(1) |
| `StringBuilder.append()` | O(1) amortized | — |
| `HashMap.get/put` | O(1) avg | — |
| `TreeMap.get/put` | O(log n) | — |
| `PriorityQueue.offer/poll` | O(log n) | — |
| `Collections.sort(List)` | O(n log n) | O(log n) |
| `String.split(regex)` | O(n) | O(n) |
| `HashSet.contains` | O(1) avg | — |

---

## 6. Interview Communication Template

When explaining complexity in an interview:

> "Let me analyze the time and space complexity.
> 
> **Time:** The outer loop runs n times, and for each iteration, the inner operation takes O(log n) due to the binary search. So overall, time complexity is **O(n log n)**.
> 
> **Space:** I'm using a HashMap that stores at most n entries, plus constant extra variables. So space complexity is **O(n)**.
> 
> Can I do better? I think there might be an O(n) solution using [two pointers / prefix sum / sliding window]..."

---

## 7. Target Complexity Guide by Problem Size

| n (input size) | Max Acceptable Complexity |
|----------------|--------------------------|
| n ≤ 10 | O(n!) — backtracking OK |
| n ≤ 20 | O(2ⁿ) — bitmask DP |
| n ≤ 100 | O(n³) — 3 nested loops |
| n ≤ 1,000 | O(n²) — 2 nested loops |
| n ≤ 100,000 | O(n log n) — sort, heap, BST |
| n ≤ 1,000,000 | O(n) — single/dual pass |
| n ≤ 10^9 | O(log n) or O(1) |

> **Interview Tip:** If the constraint says n ≤ 10^5, and your solution is O(n²), that's 10^10 operations — will TLE. Always check constraints to determine target complexity.
