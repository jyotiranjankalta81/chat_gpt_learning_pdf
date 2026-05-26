# Pattern 3 — Binary Search

---

## Intuition

Binary search eliminates half the search space with each comparison. Works on **monotonic** data — where there's a clear "left half" and "right half" separated by the answer.

**Key insight:** You don't need a sorted array. You need a **condition** that's monotonically true/false, letting you eliminate half the space.

---

## Pattern Recognition Signals

- "Sorted array", "rotated sorted array"
- "Find minimum/maximum satisfying condition"
- "Kth smallest/largest"
- "Minimize the maximum", "Maximize the minimum"
- "Feasibility check" with a clear threshold

---

## The Universal Binary Search Template

```java
// Find the LEFTMOST position where condition(x) is TRUE
// condition must be: FFFFFFF TTTTTTT (monotonic)
int binarySearch(int lo, int hi) {
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (condition(mid)) {
            hi = mid;        // true: answer is mid or to the left
        } else {
            lo = mid + 1;    // false: answer is to the right
        }
    }
    return lo;  // lo == hi == first true position
}
```

---

## 5 Standard Binary Search Problems

### 1. Classic Search

```java
int search(int[] nums, int target) {
    int lo = 0, hi = nums.length - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (nums[mid] == target) return mid;
        if (nums[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;
}
```

### 2. First Bad Version (LC 278)

```java
// isBadVersion(n) returns whether n is bad
// Find the first bad version (all versions after it are also bad)
int firstBadVersion(int n) {
    int lo = 1, hi = n;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (isBadVersion(mid)) hi = mid;    // bad: could be the first
        else lo = mid + 1;                   // good: first bad is to the right
    }
    return lo;
}
```

### 3. Search Insert Position (LC 35)

```java
// Find index where target would be inserted to keep sorted order
int searchInsert(int[] nums, int target) {
    int lo = 0, hi = nums.length;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (nums[mid] < target) lo = mid + 1;
        else hi = mid;
    }
    return lo;
}
```

### 4. Rotated Sorted Array (LC 33)

```java
int search(int[] nums, int target) {
    int lo = 0, hi = nums.length - 1;

    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (nums[mid] == target) return mid;

        // Left portion is sorted
        if (nums[lo] <= nums[mid]) {
            if (nums[lo] <= target && target < nums[mid]) hi = mid - 1;
            else lo = mid + 1;
        }
        // Right portion is sorted
        else {
            if (nums[mid] < target && target <= nums[hi]) lo = mid + 1;
            else hi = mid - 1;
        }
    }
    return -1;
}
```

### 5. Find Minimum in Rotated Sorted Array (LC 153)

```java
int findMin(int[] nums) {
    int lo = 0, hi = nums.length - 1;

    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (nums[mid] > nums[hi]) lo = mid + 1;  // min is in right half
        else hi = mid;                             // min is in left half (or mid)
    }
    return nums[lo];
}
```

---

## Binary Search on Answer Space

### Koko Eating Bananas (LC 875)

```java
// Can finish at speed k within h hours?
boolean canFinish(int[] piles, int h, int k) {
    long hours = 0;
    for (int p : piles) hours += (p + k - 1) / k;  // ceil(p/k)
    return hours <= h;
}

int minEatingSpeed(int[] piles, int h) {
    int lo = 1, hi = 1;
    for (int p : piles) hi = Math.max(hi, p);  // max pile = upper bound

    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (canFinish(piles, h, mid)) hi = mid;
        else lo = mid + 1;
    }
    return lo;
}
```

### Capacity to Ship Packages (LC 1011)

```java
boolean canShip(int[] weights, int days, int cap) {
    int daysNeeded = 1, currLoad = 0;
    for (int w : weights) {
        if (currLoad + w > cap) { daysNeeded++; currLoad = 0; }
        currLoad += w;
    }
    return daysNeeded <= days;
}

int shipWithinDays(int[] weights, int days) {
    int lo = 0, hi = 0;
    for (int w : weights) { lo = Math.max(lo, w); hi += w; }
    // lo = max single weight (minimum possible capacity)
    // hi = sum of all (1 day capacity)

    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (canShip(weights, days, mid)) hi = mid;
        else lo = mid + 1;
    }
    return lo;
}
```

### Split Array Largest Sum (LC 410)

```java
boolean canSplit(int[] nums, int m, int maxSum) {
    int pieces = 1, curr = 0;
    for (int n : nums) {
        if (curr + n > maxSum) { pieces++; curr = 0; }
        curr += n;
    }
    return pieces <= m;
}

int splitArray(int[] nums, int m) {
    int lo = 0, hi = 0;
    for (int n : nums) { lo = Math.max(lo, n); hi += n; }

    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (canSplit(nums, m, mid)) hi = mid;
        else lo = mid + 1;
    }
    return lo;
}
```

### Aggressive Cows / Maximize Minimum Distance (Atcoder/Codeforces classic)

```java
boolean canPlace(int[] positions, int n, int minDist) {
    int count = 1, last = positions[0];
    for (int i = 1; i < positions.length; i++) {
        if (positions[i] - last >= minDist) {
            count++;
            last = positions[i];
            if (count >= n) return true;
        }
    }
    return false;
}

int maxMinDist(int[] positions, int n) {
    Arrays.sort(positions);
    int lo = 1, hi = positions[positions.length - 1] - positions[0];

    while (lo < hi) {
        int mid = lo + (hi - lo + 1) / 2;  // +1 for "maximize" problems
        if (canPlace(positions, n, mid)) lo = mid;
        else hi = mid - 1;
    }
    return lo;
}
// Note: for "minimize" use hi=mid; for "maximize" use lo=mid (with +1 in mid calc)
```

---

## Special: 2D Binary Search (LC 74)

```java
// Search in m×n matrix where rows/cols are sorted
boolean searchMatrix(int[][] matrix, int target) {
    int m = matrix.length, n = matrix[0].length;
    int lo = 0, hi = m * n - 1;

    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        int val = matrix[mid / n][mid % n];  // convert 1D index to 2D
        if (val == target) return true;
        if (val < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return false;
}
```

---

## Off-by-One Rules (The Hard Part)

```java
// RULE 1: When to use left < right vs left <= right
// - left <= right: when searching for exact target in [left, right]
// - left < right: when searching for boundary (template-based)

// RULE 2: When to use hi = mid vs hi = mid - 1
// - hi = mid: when condition is true at mid, but mid could BE the answer
// - hi = mid - 1: when you've confirmed mid is NOT the answer

// RULE 3: Mid formula for "maximize" problems
int midForMax = lo + (hi - lo + 1) / 2;  // rounds up to avoid infinite loop

// Example: lo=3, hi=4
// Standard mid = 3 + (4-3)/2 = 3 → if condition(3)=false: lo=mid=3 (infinite loop!)
// Ceiling mid = 3 + (4-3+1)/2 = 4 → lo=mid=4, breaks loop

// RULE 4: Post-condition check
// After binary search, always validate:
// - Is lo within bounds?
// - Does nums[lo] actually equal target?
```

---

## Complexity

| Type | Time | Space |
|------|------|-------|
| Basic binary search | O(log n) | O(1) |
| Binary search on answer | O(n log(range)) | O(1) |
| Recursive binary search | O(log n) | O(log n) |

> **Interview Tip:** When stuck on a problem with "minimum/maximum satisfying a constraint", ask yourself: "Is this monotonic? Can I binary search the answer?" This unlocks a whole class of hard problems.
