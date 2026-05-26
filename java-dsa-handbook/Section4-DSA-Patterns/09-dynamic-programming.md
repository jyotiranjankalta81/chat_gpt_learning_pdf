# Pattern 9 — Dynamic Programming

---

## Core Insight

DP solves optimization problems by breaking them into **overlapping sub-problems** and storing results to avoid recomputation.

**Two approaches:**
- **Top-Down (Memoization):** Recursion + cache
- **Bottom-Up (Tabulation):** Iterative, fill table from base case

---

## DP Recognition Signals

- "Maximum/minimum"
- "Number of ways"
- "Is it possible"
- Problem can be broken into smaller overlapping sub-problems
- Optimal substructure: optimal solution contains optimal sub-solutions

---

## 1. Knapsack Patterns

### 0/1 Knapsack

```java
// Given weights and values, maximize value within capacity
// Each item: use 0 or 1 time
int knapsack01(int[] weights, int[] values, int capacity) {
    int n = weights.length;
    int[][] dp = new int[n + 1][capacity + 1];

    for (int i = 1; i <= n; i++) {
        for (int w = 0; w <= capacity; w++) {
            dp[i][w] = dp[i-1][w];  // don't take item i
            if (weights[i-1] <= w) {
                dp[i][w] = Math.max(dp[i][w],
                           dp[i-1][w - weights[i-1]] + values[i-1]);  // take item i
            }
        }
    }
    return dp[n][capacity];
}

// Space-optimized: O(capacity) space (traverse backwards!)
int knapsack01Optimized(int[] weights, int[] values, int capacity) {
    int[] dp = new int[capacity + 1];

    for (int i = 0; i < weights.length; i++) {
        for (int w = capacity; w >= weights[i]; w--) {  // BACKWARDS to avoid using item twice
            dp[w] = Math.max(dp[w], dp[w - weights[i]] + values[i]);
        }
    }
    return dp[capacity];
}
```

### Unbounded Knapsack (Coin Change Type)

```java
// Each item can be used unlimited times
int unboundedKnapsack(int[] weights, int[] values, int capacity) {
    int[] dp = new int[capacity + 1];

    for (int w = 0; w <= capacity; w++) {
        for (int i = 0; i < weights.length; i++) {  // FORWARD (can reuse)
            if (weights[i] <= w) {
                dp[w] = Math.max(dp[w], dp[w - weights[i]] + values[i]);
            }
        }
    }
    return dp[capacity];
}

// Coin Change (LC 322) — minimum coins
int coinChange(int[] coins, int amount) {
    int[] dp = new int[amount + 1];
    Arrays.fill(dp, amount + 1);  // "infinity"
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

// Coin Change II (LC 518) — count ways
int coinChangeWays(int[] coins, int amount) {
    int[] dp = new int[amount + 1];
    dp[0] = 1;

    for (int coin : coins) {
        for (int a = coin; a <= amount; a++) {
            dp[a] += dp[a - coin];  // add ways using this coin
        }
    }
    return dp[amount];
}
```

---

## 2. Longest Increasing Subsequence (LIS)

```java
// O(n²) DP approach
int lengthOfLIS(int[] nums) {
    int n = nums.length;
    int[] dp = new int[n];
    Arrays.fill(dp, 1);  // each element is LIS of length 1

    int maxLen = 1;
    for (int i = 1; i < n; i++) {
        for (int j = 0; j < i; j++) {
            if (nums[j] < nums[i]) {
                dp[i] = Math.max(dp[i], dp[j] + 1);
            }
        }
        maxLen = Math.max(maxLen, dp[i]);
    }
    return maxLen;
}

// O(n log n) patience sorting approach
int lengthOfLIS_NLogN(int[] nums) {
    List<Integer> tails = new ArrayList<>();  // tails[i] = smallest tail of LIS length i+1

    for (int n : nums) {
        int pos = Collections.binarySearch(tails, n);
        if (pos < 0) pos = -(pos + 1);  // insertion point

        if (pos == tails.size()) tails.add(n);  // extend LIS
        else tails.set(pos, n);                  // replace to minimize tail
    }
    return tails.size();
}
```

---

## 3. Longest Common Subsequence (LCS)

```java
int longestCommonSubsequence(String text1, String text2) {
    int m = text1.length(), n = text2.length();
    int[][] dp = new int[m + 1][n + 1];

    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (text1.charAt(i-1) == text2.charAt(j-1)) {
                dp[i][j] = dp[i-1][j-1] + 1;
            } else {
                dp[i][j] = Math.max(dp[i-1][j], dp[i][j-1]);
            }
        }
    }
    return dp[m][n];
}

// Longest Common Substring (contiguous)
int longestCommonSubstring(String s1, String s2) {
    int m = s1.length(), n = s2.length(), maxLen = 0;
    int[][] dp = new int[m + 1][n + 1];

    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (s1.charAt(i-1) == s2.charAt(j-1)) {
                dp[i][j] = dp[i-1][j-1] + 1;
                maxLen = Math.max(maxLen, dp[i][j]);
            }
        }
    }
    return maxLen;
}

// Edit Distance (LC 72)
int minDistance(String word1, String word2) {
    int m = word1.length(), n = word2.length();
    int[][] dp = new int[m + 1][n + 1];

    for (int i = 0; i <= m; i++) dp[i][0] = i;
    for (int j = 0; j <= n; j++) dp[0][j] = j;

    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (word1.charAt(i-1) == word2.charAt(j-1)) {
                dp[i][j] = dp[i-1][j-1];
            } else {
                dp[i][j] = 1 + Math.min(dp[i-1][j-1],   // replace
                               Math.min(dp[i-1][j],        // delete
                                        dp[i][j-1]));       // insert
            }
        }
    }
    return dp[m][n];
}
```

---

## 4. Partition DP

```java
// Partition Equal Subset Sum (LC 416)
// Can we partition into two subsets with equal sum?
boolean canPartition(int[] nums) {
    int total = Arrays.stream(nums).sum();
    if (total % 2 != 0) return false;

    int target = total / 2;
    boolean[] dp = new boolean[target + 1];
    dp[0] = true;

    for (int n : nums) {
        for (int j = target; j >= n; j--) {  // backwards (0/1 knapsack)
            dp[j] = dp[j] || dp[j - n];
        }
    }
    return dp[target];
}

// Word Break (LC 139)
boolean wordBreak(String s, List<String> wordDict) {
    Set<String> dict = new HashSet<>(wordDict);
    int n = s.length();
    boolean[] dp = new boolean[n + 1];
    dp[0] = true;

    for (int i = 1; i <= n; i++) {
        for (int j = 0; j < i; j++) {
            if (dp[j] && dict.contains(s.substring(j, i))) {
                dp[i] = true;
                break;
            }
        }
    }
    return dp[n];
}
```

---

## 5. Matrix / Grid DP

```java
// Unique Paths (LC 62)
int uniquePaths(int m, int n) {
    int[][] dp = new int[m][n];
    for (int i = 0; i < m; i++) dp[i][0] = 1;
    for (int j = 0; j < n; j++) dp[0][j] = 1;

    for (int i = 1; i < m; i++) {
        for (int j = 1; j < n; j++) {
            dp[i][j] = dp[i-1][j] + dp[i][j-1];
        }
    }
    return dp[m-1][n-1];
}

// Minimum Path Sum (LC 64)
int minPathSum(int[][] grid) {
    int m = grid.length, n = grid[0].length;
    int[][] dp = new int[m][n];
    dp[0][0] = grid[0][0];

    for (int i = 1; i < m; i++) dp[i][0] = dp[i-1][0] + grid[i][0];
    for (int j = 1; j < n; j++) dp[0][j] = dp[0][j-1] + grid[0][j];

    for (int i = 1; i < m; i++) {
        for (int j = 1; j < n; j++) {
            dp[i][j] = grid[i][j] + Math.min(dp[i-1][j], dp[i][j-1]);
        }
    }
    return dp[m-1][n-1];
}
```

---

## 6. State Machine DP (Stock Problems)

```java
// Best Time to Buy and Sell Stock with Cooldown (LC 309)
// States: HOLD, SOLD (cooldown), REST
int maxProfitCooldown(int[] prices) {
    int hold = Integer.MIN_VALUE, sold = 0, rest = 0;

    for (int price : prices) {
        int prevHold = hold, prevSold = sold, prevRest = rest;
        hold = Math.max(prevHold, prevRest - price);  // buy (only from rest)
        sold = prevHold + price;                       // sell
        rest = Math.max(prevRest, prevSold);           // wait
    }
    return Math.max(sold, rest);
}
```

---

## DP Template Decision Guide

```
1. Is there a clear "last decision" at each step?  → State transition DP
2. Does it involve sequences? (arrays, strings) → 1D/2D DP
3. Two sequences? (LCS, Edit Distance) → 2D DP with two indices
4. Choices at each step (take/leave)? → Knapsack DP
5. Can break into left/right parts? → Interval DP
6. Multiple states (buy/sell/hold)? → State machine DP
```

> **Interview Tip:** When you identify DP, first write the recurrence relation verbally: "dp[i] represents the [maximum/minimum/count] of [subproblem] using elements 0..i". Getting the definition right is 80% of the solution.
