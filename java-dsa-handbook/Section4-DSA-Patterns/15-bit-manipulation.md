# Pattern 15 — Bit Manipulation

---

## Core Tricks

```java
// Bit operations reference
n & 1        // last bit (0=even, 1=odd)
n >> 1       // divide by 2
n << 1       // multiply by 2
n & (n-1)    // clear lowest set bit
n | (1<<k)   // set kth bit
n & ~(1<<k)  // clear kth bit
n ^ (1<<k)   // toggle kth bit
(n >> k) & 1 // get kth bit value
Integer.bitCount(n)  // count set bits
```

---

## XOR Tricks

```java
// Single Number (LC 136) — find the one non-duplicate
// XOR: same ^ same = 0, any ^ 0 = any
int singleNumber(int[] nums) {
    int result = 0;
    for (int n : nums) result ^= n;
    return result;
}

// Single Number II (appears once, rest 3 times) — bit counting
int singleNumberII(int[] nums) {
    int result = 0;
    for (int i = 0; i < 32; i++) {
        int sum = 0;
        for (int n : nums) sum += (n >> i) & 1;
        result |= (sum % 3) << i;
    }
    return result;
}

// Find two single numbers (rest appear twice) — LC 260
int[] singleNumberIII(int[] nums) {
    int xor = 0;
    for (int n : nums) xor ^= n;

    // Find rightmost bit that differs between the two numbers
    int diffBit = xor & (-xor);  // lowest set bit

    int a = 0, b = 0;
    for (int n : nums) {
        if ((n & diffBit) != 0) a ^= n;
        else b ^= n;
    }
    return new int[]{a, b};
}
```

---

## Missing and Duplicate Numbers

```java
// Missing Number (LC 268) — [0, n] with one missing
int missingNumber(int[] nums) {
    int xor = nums.length;
    for (int i = 0; i < nums.length; i++) xor ^= i ^ nums[i];
    return xor;
}

// Missing Number (sum approach)
int missingNumberSum(int[] nums) {
    int n = nums.length;
    int expected = n * (n + 1) / 2;
    int actual = 0;
    for (int n2 : nums) actual += n2;
    return expected - actual;
}
```

---

## Power of 2 Checks

```java
boolean isPowerOfTwo(int n) { return n > 0 && (n & (n - 1)) == 0; }
boolean isPowerOfFour(int n) {
    // Power of 4: power of 2 AND in odd bit positions (0x55555555)
    return n > 0 && (n & (n - 1)) == 0 && (n & 0x55555555) != 0;
}
```

---

## Counting Bits (LC 338)

```java
int[] countBits(int n) {
    int[] dp = new int[n + 1];
    for (int i = 1; i <= n; i++) {
        dp[i] = dp[i >> 1] + (i & 1);
        // i >> 1 = i/2 (same bits except last), i & 1 = last bit
    }
    return dp;
}
```

---

## Bitmask DP

```java
// Traveling Salesman Problem (small n)
// State: visited cities as bitmask
int tsp(int[][] dist, int n) {
    int states = 1 << n;
    int[][] dp = new int[states][n];
    for (int[] row : dp) Arrays.fill(row, Integer.MAX_VALUE / 2);
    dp[1][0] = 0;  // start at city 0

    for (int mask = 1; mask < states; mask++) {
        for (int last = 0; last < n; last++) {
            if ((mask & (1 << last)) == 0) continue;
            for (int next = 0; next < n; next++) {
                if ((mask & (1 << next)) != 0) continue;
                int newMask = mask | (1 << next);
                dp[newMask][next] = Math.min(dp[newMask][next],
                                             dp[mask][last] + dist[last][next]);
            }
        }
    }

    int result = Integer.MAX_VALUE;
    for (int last = 1; last < n; last++) {
        result = Math.min(result, dp[states - 1][last] + dist[last][0]);
    }
    return result;
}
```

---

## Complexity Summary

| Bit Operation | Time |
|---------------|------|
| Single number XOR | O(n) |
| Count set bits | O(log n) or O(1) with `Integer.bitCount` |
| Power of 2 check | O(1) |
| Bitmask DP (2^n states) | O(2^n * n) |

> **Interview Tip:** Bit manipulation problems often have elegant O(n) solutions. When you see "duplicate/missing in array" or "appear once vs twice/thrice", think XOR first.
