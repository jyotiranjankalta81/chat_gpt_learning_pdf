# Section 3.2 — Recursion and Memoization

---

## 1. Recursion Fundamentals

```
Every recursive function needs:
1. BASE CASE — when to stop
2. RECURSIVE CASE — break problem into smaller sub-problems
3. PROGRESS — each recursive call must move toward base case
```

```java
// Template
returnType solve(params) {
    // 1. Base case
    if (baseCondition) return baseValue;

    // 2. Recursive case (decompose)
    subResult = solve(smallerProblem);

    // 3. Combine
    return combine(subResult, currentElement);
}
```

---

## 2. Classic Recursion Examples

### Factorial

```java
// O(n) time, O(n) space (stack frames)
int factorial(int n) {
    if (n <= 1) return 1;           // base case
    return n * factorial(n - 1);    // recursive case
}

// Iteration equivalent (O(1) space)
int factorialIter(int n) {
    int result = 1;
    for (int i = 2; i <= n; i++) result *= i;
    return result;
}
```

### Power Function

```java
// Naive: O(n)
double power(double base, int exp) {
    if (exp == 0) return 1;
    return base * power(base, exp - 1);
}

// Fast power (Binary Exponentiation): O(log n)
double fastPower(double base, int exp) {
    if (exp == 0) return 1;
    if (exp < 0) return 1.0 / fastPower(base, -exp);

    if (exp % 2 == 0) {
        double half = fastPower(base, exp / 2);
        return half * half;  // IMPORTANT: compute once, use twice
    } else {
        return base * fastPower(base, exp - 1);
    }
}
// Used in: LeetCode 50 (Pow(x,n)), modular exponentiation
```

### Binary Search (Recursive)

```java
// O(log n) time, O(log n) space
int binarySearch(int[] arr, int target, int left, int right) {
    if (left > right) return -1;  // base case: not found

    int mid = left + (right - left) / 2;

    if (arr[mid] == target) return mid;
    if (arr[mid] < target) return binarySearch(arr, target, mid + 1, right);
    return binarySearch(arr, target, left, mid - 1);
}
```

### Merge Sort

```java
// O(n log n) time, O(n) space
void mergeSort(int[] arr, int left, int right) {
    if (left >= right) return;  // base case: single element

    int mid = left + (right - left) / 2;
    mergeSort(arr, left, mid);        // sort left half
    mergeSort(arr, mid + 1, right);   // sort right half
    merge(arr, left, mid, right);     // merge sorted halves
}

void merge(int[] arr, int left, int mid, int right) {
    int[] temp = new int[right - left + 1];
    int i = left, j = mid + 1, k = 0;

    while (i <= mid && j <= right) {
        if (arr[i] <= arr[j]) temp[k++] = arr[i++];
        else temp[k++] = arr[j++];
    }
    while (i <= mid) temp[k++] = arr[i++];
    while (j <= right) temp[k++] = arr[j++];

    for (int l = 0; l < temp.length; l++) arr[left + l] = temp[l];
}
```

---

## 3. Recursion Tree Thinking

```
Visualize the call tree to analyze:
1. How many levels deep? → O(depth) for space
2. How many calls per level? → multiply per level
3. How much work at each call? → multiply by work

Example: Fibonacci fib(5)
                    fib(5)
                   /      \
             fib(4)        fib(3)
            /    \         /    \
         fib(3) fib(2)  fib(2) fib(1)
         / \
      fib(2) fib(1)

Tree has ~2^n nodes → O(2^n) time
Depth is n → O(n) space

With memoization: each unique sub-problem solved once
Sub-problems: fib(0), fib(1), ..., fib(n) = n+1
Time: O(n), Space: O(n)
```

---

## 4. Memoization (Top-Down DP)

```java
// Pattern: cache results of sub-problems in a map/array

// Fibonacci — naive O(2^n)
int fib(int n) {
    if (n <= 1) return n;
    return fib(n-1) + fib(n-2);
}

// Fibonacci — memoized O(n)
int[] memo = new int[n + 1];
Arrays.fill(memo, -1);

int fib(int n) {
    if (n <= 1) return n;
    if (memo[n] != -1) return memo[n];       // cache hit
    return memo[n] = fib(n-1) + fib(n-2);   // compute & cache
}

// Using HashMap for non-integer keys
Map<String, Integer> memo = new HashMap<>();
int solve(String state) {
    if (memo.containsKey(state)) return memo.get(state);
    // ... compute result ...
    memo.put(state, result);
    return result;
}
```

### Memoization Template

```java
// General template for memoization
class Solution {
    private int[] memo;

    public int solve(int n) {
        memo = new int[n + 1];
        Arrays.fill(memo, -1);
        return dp(n);
    }

    private int dp(int n) {
        // Base cases
        if (n == 0) return 0;
        if (n == 1) return 1;

        // Check cache
        if (memo[n] != -1) return memo[n];

        // Compute and cache
        return memo[n] = dp(n - 1) + dp(n - 2);
    }
}
```

---

## 5. Classic Memoization Problems

### Climbing Stairs

```java
// How many ways to climb n stairs (1 or 2 at a time)?
// dp[n] = dp[n-1] + dp[n-2]

int climbStairs(int n) {
    if (n <= 2) return n;
    int[] dp = new int[n + 1];
    dp[1] = 1; dp[2] = 2;
    for (int i = 3; i <= n; i++) dp[i] = dp[i-1] + dp[i-2];
    return dp[n];
}
```

### Coin Change

```java
// Minimum coins to make amount (can reuse coins)
// dp[amount] = min(dp[amount - coin] + 1) for each coin

int coinChange(int[] coins, int amount) {
    int[] dp = new int[amount + 1];
    Arrays.fill(dp, amount + 1);  // init to "infinity"
    dp[0] = 0;

    for (int a = 1; a <= amount; a++) {
        for (int coin : coins) {
            if (coin <= a) {
                dp[a] = Math.min(dp[a], dp[a - coin] + 1);
            }
        }
    }
    return dp[amount] > amount ? -1 : dp[amount];
}
```

### House Robber

```java
// Can't rob adjacent houses
// dp[i] = max(dp[i-1], dp[i-2] + nums[i])

int rob(int[] nums) {
    int n = nums.length;
    if (n == 1) return nums[0];

    int prev2 = nums[0];
    int prev1 = Math.max(nums[0], nums[1]);

    for (int i = 2; i < n; i++) {
        int curr = Math.max(prev1, prev2 + nums[i]);
        prev2 = prev1;
        prev1 = curr;
    }
    return prev1;
}
```

### Longest Common Subsequence

```java
// dp[i][j] = LCS of s1[0..i-1] and s2[0..j-1]
int lcs(String s1, String s2) {
    int m = s1.length(), n = s2.length();
    int[][] dp = new int[m + 1][n + 1];

    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (s1.charAt(i-1) == s2.charAt(j-1)) {
                dp[i][j] = dp[i-1][j-1] + 1;
            } else {
                dp[i][j] = Math.max(dp[i-1][j], dp[i][j-1]);
            }
        }
    }
    return dp[m][n];
}
```

---

## 6. Key Recursion Patterns for DSA

### Tree Recursion (Post-order)

```java
// Pattern: compute something at each node using children's results
int height(TreeNode root) {
    if (root == null) return 0;                    // base case
    int leftH = height(root.left);                 // recurse left
    int rightH = height(root.right);               // recurse right
    return 1 + Math.max(leftH, rightH);            // combine
}

int diameter(TreeNode root) {
    int[] maxDiam = {0};  // use array to pass by reference

    int dfs(TreeNode node) {
        if (node == null) return 0;
        int left = dfs(node.left);
        int right = dfs(node.right);
        maxDiam[0] = Math.max(maxDiam[0], left + right);
        return 1 + Math.max(left, right);
    }

    dfs(root);
    return maxDiam[0];
}
```

### Backtracking Template

```java
void backtrack(result, current, choices) {
    if (isDone) {
        result.add(new ArrayList<>(current));
        return;
    }

    for (choice : choices) {
        if (isValid(choice)) {
            current.add(choice);          // make choice
            backtrack(result, current, remainingChoices);
            current.remove(current.size() - 1);  // undo choice
        }
    }
}
```

### Divide and Conquer Template

```java
T solve(int[] arr, int left, int right) {
    // Base case
    if (left == right) return base;

    int mid = left + (right - left) / 2;

    // Divide
    T leftResult = solve(arr, left, mid);
    T rightResult = solve(arr, mid + 1, right);

    // Conquer (combine)
    return merge(leftResult, rightResult);
}
```

---

## 7. Tail Recursion (Java Doesn't Optimize It)

```java
// Java does NOT optimize tail calls (unlike Haskell, Scala)
// Deep recursion will cause StackOverflowError for n > ~10,000

// Stack size limit demonstration
int deepRecurse(int n) {
    if (n == 0) return 0;
    return 1 + deepRecurse(n - 1);  // StackOverflow for n > ~8000
}

// Solution: convert to iteration or use explicit stack
int iterative(int n) {
    Deque<Integer> stack = new ArrayDeque<>();
    // ... simulate recursion with explicit stack
}

// Or increase stack size (not always possible in interviews):
// java -Xss64m Solution  (64MB stack)
```

---

## 8. Recursion vs Iteration Decision Guide

| Scenario | Prefer |
|----------|--------|
| Tree traversal | Recursion (cleaner code) |
| Graph DFS | Recursion (or iterative with explicit stack) |
| Simple loop | Iteration |
| n > 10,000 and deep recursion | Iteration (avoid StackOverflow) |
| Memoization with many states | Top-down recursion + memo |
| Multiple state transitions | Bottom-up DP (iteration) |
| Backtracking | Recursion (natural) |
| Binary search | Iteration (O(1) space) |

> **Interview Tip:** For tree problems, recursive solutions are usually cleaner and preferred. For long chains (n=10^6), mention you'd use iteration to avoid stack overflow — this shows production awareness.
