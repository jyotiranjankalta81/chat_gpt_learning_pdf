# Section 3: DSA Foundations
## Complexity Analysis, Recursion, Sorting & Searching

> **Goal:** Build an unshakeable foundation in algorithm analysis, recursion thinking, and the core algorithms that appear in every interview.

---

## Table of Contents
1. [Complexity Analysis](#1-complexity-analysis)
2. [Recursion](#2-recursion)
3. [Sorting Algorithms](#3-sorting-algorithms)
4. [Searching Algorithms](#4-searching-algorithms)
5. [Divide and Conquer](#5-divide-and-conquer)
6. [Recursion Trees](#6-recursion-trees)

---

## 1. Complexity Analysis

### Big-O Notation

Big-O describes the **upper bound** of an algorithm's growth rate as input size n → ∞. It ignores constants and lower-order terms.

```
O(1)        < O(log n)    < O(√n)     < O(n)      < O(n log n)
< O(n²)     < O(n³)       < O(2ⁿ)     < O(n!)
```

### Common Complexities with Real Examples

| Complexity | Name | Example Algorithm | n=10 | n=100 | n=1000 |
|-----------|------|------------------|------|-------|--------|
| O(1) | Constant | Array access, HashMap lookup | 1 | 1 | 1 |
| O(log n) | Logarithmic | Binary search | 3 | 7 | 10 |
| O(√n) | Square root | Sieve of Eratosthenes | 3 | 10 | 32 |
| O(n) | Linear | Linear scan, Single loop | 10 | 100 | 1000 |
| O(n log n) | Linearithmic | Merge sort, Heap sort | 33 | 664 | 9966 |
| O(n²) | Quadratic | Bubble/Selection sort, Nested loops | 100 | 10000 | 1M |
| O(n³) | Cubic | Floyd-Warshall | 1000 | 1M | 1B |
| O(2ⁿ) | Exponential | Subset generation, naive recursion | 1024 | 2^100 | ∞ |
| O(n!) | Factorial | Permutation generation | 3628800 | ∞ | ∞ |

### FAANG Acceptable Complexity by Input Size

```
n ≤ 10:          O(n!) or O(2ⁿ)    — Backtracking, brute force OK
n ≤ 20:          O(2ⁿ)             — Bitmask DP
n ≤ 100:         O(n³)             — Triple nested loops
n ≤ 1,000:       O(n²)             — Double nested loops
n ≤ 10,000:      O(n² log n)       — Careful nested loops
n ≤ 100,000:     O(n log n)        — Sort + BST operations
n ≤ 1,000,000:   O(n) or O(n log n) — Linear algorithms
n ≤ 10,000,000:  O(n) or O(n log n) — Optimized linear
n > 10,000,000:  O(log n) or O(1)  — Binary search, math
```

### How to Calculate Complexity

```cpp
// Rule 1: Drop constants
O(3n) = O(n)
O(n/2) = O(n)

// Rule 2: Drop lower-order terms
O(n² + n) = O(n²)
O(n log n + n) = O(n log n)

// Rule 3: Sequential blocks — ADD
for (int i = 0; i < n; i++) { }    // O(n)
for (int i = 0; i < n; i++) { }    // O(n)
// Total: O(n) + O(n) = O(2n) = O(n)

// Rule 4: Nested blocks — MULTIPLY
for (int i = 0; i < n; i++) {
    for (int j = 0; j < n; j++) {  // O(n) * O(n) = O(n²)
    }
}

// Rule 5: Halving the input — LOG
int i = n;
while (i > 1) {
    i /= 2;                         // O(log n)
}

// Rule 6: Different inputs — different variables
for (int i = 0; i < n; i++) { }   // O(n)
for (int i = 0; i < m; i++) { }   // O(m)
// Total: O(n + m), NOT O(n²)!

// Rule 7: Recursive — use recurrence relation
// T(n) = 2T(n/2) + O(n)  →  O(n log n)  (Merge sort)
// T(n) = T(n-1) + O(1)   →  O(n)        (Linear recursion)
// T(n) = 2T(n-1) + O(1)  →  O(2ⁿ)       (Exponential)
```

### Space Complexity

```cpp
// O(1) — constant extra space
int maxSum = 0;
for (int x : nums) maxSum = max(maxSum, x);

// O(n) — linear extra space
vector<int> result(n);  // Storing n elements
unordered_map<int,int> freq;  // Up to n entries

// O(n) — recursion stack space
// Recursive calls use stack space = depth of recursion
void dfs(int n) {  // O(n) stack space for n recursive calls
    if (n == 0) return;
    dfs(n-1);
}

// O(log n) — balanced tree recursion
void mergeSort(vector<int>& v, int l, int r) {  // O(log n) stack depth
    if (l >= r) return;
    int mid = l + (r - l) / 2;
    mergeSort(v, l, mid);
    mergeSort(v, mid+1, r);
    merge(v, l, mid, r);
}
```

### Master Theorem (Quick Reference)

For T(n) = aT(n/b) + O(n^d):
- If d > log_b(a): T(n) = O(n^d)
- If d = log_b(a): T(n) = O(n^d * log n)
- If d < log_b(a): T(n) = O(n^(log_b(a)))

```
Merge sort:  T(n) = 2T(n/2) + O(n)    → a=2, b=2, d=1 → d=log₂2=1 → O(n log n)
Binary search: T(n) = T(n/2) + O(1)   → a=1, b=2, d=0 → d=log₂1=0 → O(log n)
```

---

## 2. Recursion

### The Recursion Mental Model

Every recursive function has:
1. **Base case** — when to stop
2. **Recursive case** — break into smaller subproblem
3. **Trust the recursion** — assume recursive call works correctly

```cpp
// Example: Factorial
int factorial(int n) {
    if (n <= 1) return 1;          // Base case
    return n * factorial(n - 1);  // Recursive case
}

// Call stack visualization for factorial(4):
// factorial(4) → 4 * factorial(3)
//                    → 3 * factorial(2)
//                           → 2 * factorial(1)
//                                  → 1        (base case)
//                           ← 2 * 1 = 2
//                    ← 3 * 2 = 6
//               ← 4 * 6 = 24
```

### Fibonacci & Memoization

```cpp
// Naive: O(2ⁿ)
int fib(int n) {
    if (n <= 1) return n;
    return fib(n-1) + fib(n-2);
}

// Memoized: O(n) time, O(n) space
unordered_map<int,int> memo;
int fib(int n) {
    if (n <= 1) return n;
    if (memo.count(n)) return memo[n];
    return memo[n] = fib(n-1) + fib(n-2);
}

// Bottom-up DP: O(n) time, O(1) space
int fib(int n) {
    if (n <= 1) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; i++) {
        int c = a + b;
        a = b; b = c;
    }
    return b;
}
```

### Recursive Patterns in Interviews

```cpp
// 1. Subsets / Power Set
void subsets(vector<int>& nums, int idx, vector<int>& current, vector<vector<int>>& result) {
    result.push_back(current);
    for (int i = idx; i < nums.size(); i++) {
        current.push_back(nums[i]);
        subsets(nums, i+1, current, result);
        current.pop_back();  // Backtrack
    }
}

// 2. Permutations
void permutations(vector<int>& nums, vector<bool>& used, vector<int>& current, vector<vector<int>>& result) {
    if (current.size() == nums.size()) {
        result.push_back(current);
        return;
    }
    for (int i = 0; i < nums.size(); i++) {
        if (!used[i]) {
            used[i] = true;
            current.push_back(nums[i]);
            permutations(nums, used, current, result);
            current.pop_back();
            used[i] = false;
        }
    }
}

// 3. Tree traversal
void inorder(TreeNode* node, vector<int>& result) {
    if (!node) return;
    inorder(node->left, result);
    result.push_back(node->val);
    inorder(node->right, result);
}
```

---

## 3. Sorting Algorithms

### Sorting Overview

| Algorithm | Best | Average | Worst | Space | Stable |
|-----------|------|---------|-------|-------|--------|
| Bubble Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |
| Selection Sort | O(n²) | O(n²) | O(n²) | O(1) | No |
| Insertion Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) | Yes |
| Quick Sort | O(n log n) | O(n log n) | O(n²) | O(log n) | No |
| Heap Sort | O(n log n) | O(n log n) | O(n log n) | O(1) | No |
| Counting Sort | O(n+k) | O(n+k) | O(n+k) | O(k) | Yes |
| Radix Sort | O(nk) | O(nk) | O(nk) | O(n+k) | Yes |
| STL `sort` | O(n log n) | O(n log n) | O(n log n) | O(log n) | No |

**Key Insight:** `std::sort` uses **introsort** (hybrid of quicksort + heapsort + insertion sort) — never degrades to O(n²).

### Merge Sort — Implementation

```cpp
// O(n log n) time, O(n) space — STABLE
void merge(vector<int>& arr, int l, int mid, int r) {
    vector<int> left(arr.begin()+l, arr.begin()+mid+1);
    vector<int> right(arr.begin()+mid+1, arr.begin()+r+1);
    
    int i = 0, j = 0, k = l;
    while (i < left.size() && j < right.size()) {
        if (left[i] <= right[j]) arr[k++] = left[i++];
        else arr[k++] = right[j++];
    }
    while (i < left.size()) arr[k++] = left[i++];
    while (j < right.size()) arr[k++] = right[j++];
}

void mergeSort(vector<int>& arr, int l, int r) {
    if (l >= r) return;
    int mid = l + (r - l) / 2;  // Avoids overflow: NOT (l+r)/2
    mergeSort(arr, l, mid);
    mergeSort(arr, mid+1, r);
    merge(arr, l, mid, r);
}

// Interview use case: Count inversions
long long merge_count(vector<int>& arr, int l, int r) {
    if (l >= r) return 0;
    int mid = l + (r - l) / 2;
    long long count = 0;
    count += merge_count(arr, l, mid);
    count += merge_count(arr, mid+1, r);
    // During merge, count pairs
    vector<int> left(arr.begin()+l, arr.begin()+mid+1);
    vector<int> right(arr.begin()+mid+1, arr.begin()+r+1);
    int i = 0, j = 0, k = l;
    while (i < left.size() && j < right.size()) {
        if (left[i] <= right[j]) arr[k++] = left[i++];
        else {
            count += left.size() - i;  // All remaining in left > right[j]
            arr[k++] = right[j++];
        }
    }
    while (i < left.size()) arr[k++] = left[i++];
    while (j < right.size()) arr[k++] = right[j++];
    return count;
}
```

### Quick Sort — Implementation

```cpp
// O(n log n) average, O(n²) worst case — NOT stable
int partition(vector<int>& arr, int l, int r) {
    int pivot = arr[r];  // Pivot = last element
    int i = l - 1;
    for (int j = l; j < r; j++) {
        if (arr[j] <= pivot) {
            swap(arr[++i], arr[j]);
        }
    }
    swap(arr[i+1], arr[r]);
    return i + 1;
}

void quickSort(vector<int>& arr, int l, int r) {
    if (l >= r) return;
    int pi = partition(arr, l, r);
    quickSort(arr, l, pi-1);
    quickSort(arr, pi+1, r);
}

// Randomized quicksort (avoids worst case on sorted input)
int randomPartition(vector<int>& arr, int l, int r) {
    int randIdx = l + rand() % (r - l + 1);
    swap(arr[randIdx], arr[r]);
    return partition(arr, l, r);
}
```

### Counting Sort — Linear Sorting

```cpp
// O(n + k) time, O(k) space — requires bounded integer range
void countSort(vector<int>& arr) {
    int maxVal = *max_element(arr.begin(), arr.end());
    vector<int> count(maxVal + 1, 0);
    
    for (int x : arr) count[x]++;
    
    int idx = 0;
    for (int i = 0; i <= maxVal; i++) {
        while (count[i]-- > 0) arr[idx++] = i;
    }
}
```

---

## 4. Searching Algorithms

### Linear Search

```cpp
// O(n) — works on unsorted arrays
int linearSearch(vector<int>& arr, int target) {
    for (int i = 0; i < arr.size(); i++) {
        if (arr[i] == target) return i;
    }
    return -1;
}
```

### Binary Search — The Most Important Search

```cpp
// O(log n) — REQUIRES sorted array
// Template 1: Classic
int binarySearch(vector<int>& arr, int target) {
    int left = 0, right = arr.size() - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;  // Prevents overflow
        if (arr[mid] == target) return mid;
        else if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}

// Template 2: Find leftmost occurrence (lower_bound)
int lowerBound(vector<int>& arr, int target) {
    int left = 0, right = arr.size();
    while (left < right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] < target) left = mid + 1;
        else right = mid;
    }
    return left;  // First index where arr[i] >= target
}

// Template 3: Find rightmost occurrence (upper_bound)
int upperBound(vector<int>& arr, int target) {
    int left = 0, right = arr.size();
    while (left < right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] <= target) left = mid + 1;
        else right = mid;
    }
    return left;  // First index where arr[i] > target
}

// Template 4: Search on answer (binary search on result)
// "Find minimum k such that condition(k) is true"
int binarySearchOnAnswer(int lo, int hi) {
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (condition(mid)) hi = mid;    // Shrink right
        else lo = mid + 1;               // Shrink left
    }
    return lo;  // Minimum satisfying k
}

// Search in rotated sorted array
int searchRotated(vector<int>& arr, int target) {
    int left = 0, right = arr.size() - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) return mid;
        
        if (arr[left] <= arr[mid]) {  // Left half is sorted
            if (arr[left] <= target && target < arr[mid]) right = mid - 1;
            else left = mid + 1;
        } else {  // Right half is sorted
            if (arr[mid] < target && target <= arr[right]) left = mid + 1;
            else right = mid - 1;
        }
    }
    return -1;
}
```

### Binary Search Application Patterns

```cpp
// 1. Find peak element
int findPeak(vector<int>& arr) {
    int l = 0, r = arr.size() - 1;
    while (l < r) {
        int mid = l + (r - l) / 2;
        if (arr[mid] < arr[mid+1]) l = mid + 1;
        else r = mid;
    }
    return l;
}

// 2. Square root (integer)
int mySqrt(int x) {
    long long l = 0, r = x;
    while (l < r) {
        long long mid = l + (r - l + 1) / 2;  // Upper mid
        if (mid * mid <= x) l = mid;
        else r = mid - 1;
    }
    return l;
}

// 3. Koko eating bananas (binary search on answer)
bool canFinish(vector<int>& piles, int k, int h) {
    long long hours = 0;
    for (int p : piles) hours += (p + k - 1) / k;
    return hours <= h;
}
int minEatingSpeed(vector<int>& piles, int h) {
    int lo = 1, hi = *max_element(piles.begin(), piles.end());
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (canFinish(piles, mid, h)) hi = mid;
        else lo = mid + 1;
    }
    return lo;
}
```

---

## 5. Divide and Conquer

### Template

```
DivideAndConquer(problem):
    if problem is small enough:
        solve directly (base case)
    else:
        divide into subproblems
        recursively solve each subproblem
        combine results
```

### Classic Problems

```cpp
// Maximum Subarray Sum (Kadane's uses DP, but D&C version:)
int maxCrossing(vector<int>& arr, int l, int mid, int r) {
    int leftSum = INT_MIN, rightSum = INT_MIN;
    int sum = 0;
    for (int i = mid; i >= l; i--) {
        sum += arr[i];
        leftSum = max(leftSum, sum);
    }
    sum = 0;
    for (int i = mid+1; i <= r; i++) {
        sum += arr[i];
        rightSum = max(rightSum, sum);
    }
    return leftSum + rightSum;
}

int maxSubarrayDC(vector<int>& arr, int l, int r) {
    if (l == r) return arr[l];
    int mid = l + (r - l) / 2;
    return max({maxSubarrayDC(arr, l, mid),
                maxSubarrayDC(arr, mid+1, r),
                maxCrossing(arr, l, mid, r)});
}

// Closest Pair of Points — O(n log n)
// Binary Exponentiation — O(log n)
long long power(long long base, long long exp, long long mod) {
    long long result = 1;
    base %= mod;
    while (exp > 0) {
        if (exp & 1) result = result * base % mod;
        base = base * base % mod;
        exp >>= 1;
    }
    return result;
}
```

---

## 6. Recursion Trees

### How to Draw a Recursion Tree

For `T(n) = 2T(n/2) + O(n)` (Merge Sort):

```
Level 0:              n                     ← Work: n
Level 1:       n/2        n/2               ← Work: n/2 + n/2 = n
Level 2:    n/4  n/4   n/4  n/4            ← Work: n
...
Level log n: 1  1  1  1  1  1  1  1       ← Work: n

Total levels: log n
Work per level: n
Total: O(n log n)
```

For `T(n) = 2T(n-1) + O(1)` (Naive Fibonacci):

```
Level 0:           fib(n)                  ← 1 call
Level 1:      fib(n-1)  fib(n-2)          ← 2 calls
Level 2:   fib(n-2) fib(n-3) ...          ← 4 calls
...
Level n:   1 1 1 1 1 1 ... (2^n calls)   ← 2^n calls

Total: O(2ⁿ)
```

### Common Recurrences

| Recurrence | Example | Complexity |
|-----------|---------|-----------|
| T(n) = T(n/2) + O(1) | Binary search | O(log n) |
| T(n) = T(n-1) + O(1) | Linear recursion | O(n) |
| T(n) = 2T(n/2) + O(n) | Merge sort | O(n log n) |
| T(n) = 2T(n/2) + O(1) | Tree traversal | O(n) |
| T(n) = T(n-1) + O(n) | Selection sort (recursive) | O(n²) |
| T(n) = 2T(n-1) + O(1) | Naive Fibonacci | O(2ⁿ) |
| T(n) = T(√n) + O(1) | Integer factorization | O(log log n) |

---

## Interview: Complexity Analysis Questions

### Q: What is the complexity of this code?

```cpp
// Problem 1:
for (int i = 1; i <= n; i *= 2) {  // i = 1, 2, 4, 8, ... → O(log n) iterations
    for (int j = 0; j < n; j++) {  // O(n) each
        // O(1) work
    }
}
// Answer: O(n log n)

// Problem 2: (tricky!)
for (int i = 0; i < n; i++) {
    for (int j = i; j < n; j++) {   // j starts from i, NOT 0
        // O(1) work
    }
}
// Total iterations: n + (n-1) + (n-2) + ... + 1 = n(n+1)/2 = O(n²)

// Problem 3:
void func(int n) {
    if (n <= 1) return;
    func(n/2);
    func(n/2);          // Two recursive calls, each on n/2
    for (int i = 0; i < n; i++) { }  // O(n) work
}
// T(n) = 2T(n/2) + O(n) → O(n log n) by Master Theorem

// Problem 4: (tricky!)
int i = n;
while (i > 0) i = i / 2;        // O(log n)
// ... then
for (int j = 0; j < i; j++) { } // j never executes! i=0 after loop
// Total: O(log n)
```

---

## Key Formulas for Interviews

```
Geometric series: 1 + 2 + 4 + ... + 2^k = 2^(k+1) - 1 ≈ 2 * 2^k
Arithmetic series: 1 + 2 + ... + n = n(n+1)/2 ≈ n²/2
Log identity: log(ab) = log(a) + log(b)
Log identity: log(a^b) = b*log(a)
log₂(n) ≈ 10 when n = 1024 (≈ 10³)
log₂(10^6) ≈ 20
log₂(10^9) ≈ 30
```

---

*Next: [Section 4 — Complete DSA Pattern System](./Section4_DSA_Patterns.md)*
