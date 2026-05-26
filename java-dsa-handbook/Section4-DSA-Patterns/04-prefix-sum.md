# Pattern 4 — Prefix Sum

---

## Intuition

Pre-compute cumulative sums to answer range sum queries in O(1) instead of O(n).

**Key insight:** Sum of any subarray [l, r] = prefix[r+1] - prefix[l]

---

## Pattern Recognition Signals

- "Sum of subarray/range"
- "Number of subarrays with sum = k"
- "Query: sum from index l to r"
- "Count subarrays with specific sum"
- "Balanced parentheses count"
- "Range update queries"

---

## Template 1: 1D Prefix Sum

```java
// Build prefix sum array
int[] buildPrefix(int[] arr) {
    int n = arr.length;
    int[] prefix = new int[n + 1];  // prefix[0] = 0 (empty prefix)
    for (int i = 0; i < n; i++) {
        prefix[i + 1] = prefix[i] + arr[i];
    }
    return prefix;
}

// Range sum query in O(1)
int rangeSum(int[] prefix, int l, int r) {
    return prefix[r + 1] - prefix[l];  // sum of arr[l..r] inclusive
}

// Example:
// arr:    [1, 2, 3, 4, 5]
// prefix: [0, 1, 3, 6, 10, 15]
// sum(1, 3) = prefix[4] - prefix[1] = 10 - 1 = 9  ✓ (2+3+4)
```

---

## Template 2: 2D Prefix Sum

```java
// Matrix range sum query
int[][] build2DPrefix(int[][] matrix) {
    int m = matrix.length, n = matrix[0].length;
    int[][] prefix = new int[m + 1][n + 1];

    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            prefix[i][j] = matrix[i-1][j-1]
                         + prefix[i-1][j]
                         + prefix[i][j-1]
                         - prefix[i-1][j-1];  // subtract double-counted corner
        }
    }
    return prefix;
}

// Query: sum of rectangle (r1,c1) to (r2,c2) in original matrix (0-indexed)
int query(int[][] prefix, int r1, int c1, int r2, int c2) {
    return prefix[r2+1][c2+1]
         - prefix[r1][c2+1]
         - prefix[r2+1][c1]
         + prefix[r1][c1];  // add back double-subtracted corner
}
```

---

## Problem 1: Subarray Sum Equals K (LC 560)

**The most important prefix sum pattern**

```java
// Count subarrays with sum exactly k
// Key insight: if prefix[j] - prefix[i] = k, then prefix[i] = prefix[j] - k
int subarraySum(int[] nums, int k) {
    Map<Integer, Integer> prefixCount = new HashMap<>();
    prefixCount.put(0, 1);  // empty prefix (sum = 0) exists once

    int sum = 0, count = 0;

    for (int n : nums) {
        sum += n;
        count += prefixCount.getOrDefault(sum - k, 0);
        prefixCount.merge(sum, 1, Integer::sum);
    }
    return count;
}

// Dry run: nums = [1, 1, 1], k = 2
// sum=0: prefixCount={0:1}
// n=1: sum=1, need sum-k=1-2=-1, count+=0, prefixCount={0:1, 1:1}
// n=1: sum=2, need sum-k=2-2=0, count+=1, prefixCount={0:1, 1:1, 2:1}
// n=1: sum=3, need sum-k=3-2=1, count+=1, prefixCount={0:1, 1:1, 2:1, 3:1}
// Result: count=2  ✓ ([1,1] starting at 0 and [1,1] starting at 1)
```

---

## Problem 2: Continuous Subarray Sum (LC 523)

```java
// Check if any subarray of length >= 2 has sum that's multiple of k
boolean checkSubarraySum(int[] nums, int k) {
    Map<Integer, Integer> modSeen = new HashMap<>();
    modSeen.put(0, -1);  // empty prefix, seen at "index -1"

    int sum = 0;
    for (int i = 0; i < nums.length; i++) {
        sum = (sum + nums[i]) % k;

        if (modSeen.containsKey(sum)) {
            if (i - modSeen.get(sum) >= 2) return true;  // length >= 2
        } else {
            modSeen.put(sum, i);  // only store FIRST occurrence
        }
    }
    return false;
}
// Key insight: if prefix[j] % k == prefix[i] % k, then sum(i..j) % k == 0
```

---

## Problem 3: Range Sum Query — Immutable (LC 303)

```java
class NumArray {
    private int[] prefix;

    public NumArray(int[] nums) {
        prefix = new int[nums.length + 1];
        for (int i = 0; i < nums.length; i++) {
            prefix[i + 1] = prefix[i] + nums[i];
        }
    }

    public int sumRange(int left, int right) {
        return prefix[right + 1] - prefix[left];
    }
}
```

---

## Problem 4: Maximum Size Subarray Sum Equals k (LC 325)

```java
int maxSubArrayLen(int[] nums, int k) {
    Map<Integer, Integer> firstSeen = new HashMap<>();
    firstSeen.put(0, -1);  // empty prefix starts at -1

    int sum = 0, maxLen = 0;

    for (int i = 0; i < nums.length; i++) {
        sum += nums[i];

        if (firstSeen.containsKey(sum - k)) {
            maxLen = Math.max(maxLen, i - firstSeen.get(sum - k));
        }

        if (!firstSeen.containsKey(sum)) {
            firstSeen.put(sum, i);  // only store FIRST occurrence for max length
        }
    }
    return maxLen;
}
```

---

## Problem 5: Difference Array (Range Update)

```java
// Update range [l, r] by adding val — O(1) per update, O(n) to reconstruct
int[] differenceArray(int n) {
    return new int[n + 1];
}

void rangeAdd(int[] diff, int l, int r, int val) {
    diff[l] += val;
    diff[r + 1] -= val;
}

int[] reconstruct(int[] diff, int n) {
    int[] result = new int[n];
    result[0] = diff[0];
    for (int i = 1; i < n; i++) {
        result[i] = result[i - 1] + diff[i];
    }
    return result;
}

// Example: n=5, add 3 to [1,3], add -1 to [2,4]
// diff: [0, 3, -1, 0, -3, 1]  (and extra -1 at index 4+1=5: diff[5]-=1)
// Wait, recompute:
// rangeAdd(diff, 1, 3, 3): diff[1]+=3, diff[4]-=3  → diff=[0,3,0,0,-3,0]
// rangeAdd(diff, 2, 4, -1): diff[2]+=-1, diff[5]-= -1  → diff=[0,3,-1,0,-3,1]
// reconstruct: [0, 3, 2, 2, -1]  → result[1]=3, result[2]=2, result[3]=2, result[4]=-1
```

---

## Problem 6: Count of Subarrays with Balance 0 (0/1 problems)

```java
// Count subarrays with equal 0s and 1s
int countEqualZeroOne(int[] nums) {
    // Convert 0 → -1, so equal count means sum = 0
    Map<Integer, Integer> prefixCount = new HashMap<>();
    prefixCount.put(0, 1);

    int sum = 0, count = 0;
    for (int n : nums) {
        sum += (n == 0) ? -1 : 1;
        count += prefixCount.getOrDefault(sum, 0);
        prefixCount.merge(sum, 1, Integer::sum);
    }
    return count;
}
```

---

## Complexity Summary

| Pattern | Preprocessing | Query |
|---------|--------------|-------|
| 1D prefix sum | O(n) | O(1) |
| 2D prefix sum | O(m*n) | O(1) |
| Prefix sum + HashMap | O(n) | O(n) total |
| Difference array | O(1) per update | O(n) to read |

> **Interview Tip:** Whenever you see "sum of subarray" or "how many subarrays with sum = k", immediately think: prefix sum. Then ask: do I need exact count (HashMap) or just a check (check prefix values)?
