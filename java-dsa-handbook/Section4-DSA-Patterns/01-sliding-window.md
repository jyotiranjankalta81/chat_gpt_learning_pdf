# Pattern 1 — Sliding Window

---

## Intuition

Imagine a window (a contiguous sub-array or substring) that "slides" over the input. Instead of recomputing from scratch for each position, you add the new element entering the window and remove the element leaving it.

**Key insight:** Avoid O(n²) by reusing computation from the previous window.

---

## Pattern Recognition Signals

Look for these keywords in the problem:
- "subarray" / "substring" / "contiguous"
- "maximum/minimum of length k"
- "longest/shortest with constraint"
- "at most k distinct characters"
- "sum equals k"

---

## Types of Sliding Window

### Type 1: Fixed Window Size

```
Window size is exactly k. Slide one step at a time.
- Remove element leaving the left
- Add element entering the right
```

### Type 2: Variable Window Size

```
Window grows on the right, shrinks from the left.
- Expand right pointer always
- Shrink left pointer when window becomes invalid
```

---

## Templates

### Fixed Window Template

```java
// Maximum sum of subarray of size k
int maxSumFixed(int[] arr, int k) {
    int n = arr.length;
    if (n < k) return -1;

    // Build initial window [0, k-1]
    int windowSum = 0;
    for (int i = 0; i < k; i++) windowSum += arr[i];

    int maxSum = windowSum;

    // Slide window: add arr[right], remove arr[right - k]
    for (int right = k; right < n; right++) {
        windowSum += arr[right] - arr[right - k];
        maxSum = Math.max(maxSum, windowSum);
    }
    return maxSum;
}
```

### Variable Window Template

```java
// Longest window satisfying some condition
int longestVariable(int[] arr, int constraint) {
    int left = 0, maxLen = 0;
    // Some state to track window validity (map, count, sum, etc.)

    for (int right = 0; right < arr.length; right++) {
        // 1. Add arr[right] to window (expand)
        addToWindow(arr[right]);

        // 2. Shrink window from left while invalid
        while (windowIsInvalid()) {
            removeFromWindow(arr[left]);
            left++;
        }

        // 3. Update answer (window is now valid)
        maxLen = Math.max(maxLen, right - left + 1);
    }
    return maxLen;
}
```

---

## Problem 1: Longest Substring Without Repeating Characters (LC 3)

**Brute force:** O(n²) — check every substring  
**Sliding window:** O(n)

```java
// Signal keywords: "longest substring", "no repeating characters"
int lengthOfLongestSubstring(String s) {
    Map<Character, Integer> lastSeen = new HashMap<>();
    int left = 0, maxLen = 0;

    for (int right = 0; right < s.length(); right++) {
        char c = s.charAt(right);

        // If c was seen and is inside current window
        if (lastSeen.containsKey(c) && lastSeen.get(c) >= left) {
            left = lastSeen.get(c) + 1;  // shrink window past duplicate
        }

        lastSeen.put(c, right);
        maxLen = Math.max(maxLen, right - left + 1);
    }
    return maxLen;
}

// Dry run: "abcabcbb"
// r=0: c='a', left=0, window="a", len=1
// r=1: c='b', left=0, window="ab", len=2
// r=2: c='c', left=0, window="abc", len=3
// r=3: c='a', seen at 0 >= left=0, left=1, window="bca", len=3
// r=4: c='b', seen at 1 >= left=1, left=2, window="cab", len=3
// Result: 3
```

---

## Problem 2: Longest Substring with At Most K Distinct Characters (LC 340)

```java
int lengthOfLongestSubstringKDistinct(String s, int k) {
    Map<Character, Integer> freq = new HashMap<>();
    int left = 0, maxLen = 0;

    for (int right = 0; right < s.length(); right++) {
        char c = s.charAt(right);
        freq.put(c, freq.getOrDefault(c, 0) + 1);  // expand

        // Shrink until at most k distinct
        while (freq.size() > k) {
            char leftChar = s.charAt(left);
            freq.put(leftChar, freq.get(leftChar) - 1);
            if (freq.get(leftChar) == 0) freq.remove(leftChar);
            left++;
        }

        maxLen = Math.max(maxLen, right - left + 1);
    }
    return maxLen;
}
```

---

## Problem 3: Minimum Window Substring (LC 76) — Hard

```java
// Find smallest window in s containing all chars of t
String minWindow(String s, String t) {
    if (s.length() < t.length()) return "";

    Map<Character, Integer> need = new HashMap<>();
    for (char c : t.toCharArray()) need.merge(c, 1, Integer::sum);

    int left = 0, formed = 0, required = need.size();
    Map<Character, Integer> window = new HashMap<>();
    int[] ans = {-1, 0, 0};  // {length, left, right}

    for (int right = 0; right < s.length(); right++) {
        char c = s.charAt(right);
        window.merge(c, 1, Integer::sum);

        if (need.containsKey(c) && window.get(c).equals(need.get(c))) {
            formed++;
        }

        // Shrink window while valid
        while (left <= right && formed == required) {
            if (ans[0] == -1 || right - left + 1 < ans[0]) {
                ans[0] = right - left + 1;
                ans[1] = left;
                ans[2] = right;
            }

            char leftChar = s.charAt(left);
            window.put(leftChar, window.get(leftChar) - 1);
            if (need.containsKey(leftChar) && window.get(leftChar) < need.get(leftChar)) {
                formed--;
            }
            left++;
        }
    }
    return ans[0] == -1 ? "" : s.substring(ans[1], ans[2] + 1);
}
```

---

## Problem 4: Maximum Sum Subarray of Size K (Fixed)

```java
double findMaxAverage(int[] nums, int k) {
    long sum = 0;
    for (int i = 0; i < k; i++) sum += nums[i];

    long maxSum = sum;
    for (int i = k; i < nums.length; i++) {
        sum += nums[i] - nums[i - k];  // slide: add right, remove left
        maxSum = Math.max(maxSum, sum);
    }
    return (double) maxSum / k;
}
```

---

## Problem 5: Permutation in String (LC 567)

```java
// Is any permutation of p a substring of s?
boolean checkInclusion(String p, String s) {
    if (p.length() > s.length()) return false;

    int[] pCount = new int[26];
    int[] wCount = new int[26];

    for (char c : p.toCharArray()) pCount[c - 'a']++;

    int k = p.length();
    for (int i = 0; i < s.length(); i++) {
        wCount[s.charAt(i) - 'a']++;

        if (i >= k) wCount[s.charAt(i - k) - 'a']--;  // slide

        if (Arrays.equals(pCount, wCount)) return true;
    }
    return false;
}
```

---

## Edge Cases

```
1. k > array length (fixed window)
2. All same characters
3. Empty string
4. Single character string
5. Window starts at index 0
6. Window where left == right
```

---

## Complexity Analysis

| Problem | Time | Space |
|---------|------|-------|
| Fixed window | O(n) | O(1) |
| Variable window (charset) | O(n) | O(alphabet size) |
| Minimum window substring | O(n + m) | O(n + m) |

---

## Pattern Summary Table

| Problem Type | Expand | Shrink Condition | Track |
|-------------|--------|-----------------|-------|
| No repeating chars | Always right++ | duplicate in window | lastSeen map |
| K distinct chars | Always right++ | distinct > k | freq map |
| Min window with all chars | Always right++ | all chars covered | freq map + formed count |
| Max sum of k | Fixed slide | — | running sum |
| All anagrams | Fixed slide | — | char count arrays |
