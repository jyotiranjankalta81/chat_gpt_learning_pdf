# Pattern 2 — Two Pointers

---

## Intuition

Use two indices (pointers) to scan the array from different positions simultaneously, eliminating the need for a nested loop.

**Key insight:** If data is sorted, two pointers let you make informed decisions about which pointer to move, achieving O(n) instead of O(n²).

---

## Pattern Recognition Signals

- "Pair with target sum in sorted array"
- "Three sum", "Four sum"
- "Palindrome check"
- "Remove duplicates in-place"
- "Merge two sorted arrays"
- "Reverse array/string"
- "Container with most water"
- "Linked list cycle" (fast/slow)

---

## Types of Two Pointers

### Type 1: Opposite Direction (converge toward center)
```
left → ← right
Used for: sum problems on sorted arrays, palindromes
```

### Type 2: Same Direction (sliding window variant)
```
left → → right
Used for: remove duplicates, fast/slow cycle detection
```

### Type 3: Two Arrays
```
i → (array 1)   j → (array 2)
Used for: merge sorted arrays, compare sequences
```

---

## Template 1: Two Sum (Sorted Array)

```java
int[] twoSum(int[] arr, int target) {
    int left = 0, right = arr.length - 1;

    while (left < right) {
        int sum = arr[left] + arr[right];

        if (sum == target) return new int[]{arr[left], arr[right]};
        else if (sum < target) left++;   // need larger sum
        else right--;                     // need smaller sum
    }
    return new int[]{};  // no pair found
}
```

---

## Template 2: Three Sum (LC 15)

```java
// All unique triplets that sum to zero
List<List<Integer>> threeSum(int[] nums) {
    Arrays.sort(nums);  // MUST sort first
    List<List<Integer>> result = new ArrayList<>();

    for (int i = 0; i < nums.length - 2; i++) {
        // Skip duplicates for first element
        if (i > 0 && nums[i] == nums[i - 1]) continue;

        int left = i + 1, right = nums.length - 1;

        while (left < right) {
            int sum = nums[i] + nums[left] + nums[right];

            if (sum == 0) {
                result.add(Arrays.asList(nums[i], nums[left], nums[right]));
                // Skip duplicates for second and third elements
                while (left < right && nums[left] == nums[left + 1]) left++;
                while (left < right && nums[right] == nums[right - 1]) right--;
                left++; right--;
            } else if (sum < 0) {
                left++;
            } else {
                right--;
            }
        }
    }
    return result;
}

// Dry run: [-1, 0, 1, 2, -1, -4] → sorted: [-4, -1, -1, 0, 1, 2]
// i=0: nums[i]=-4, l=1, r=5
//   sum=-4+(-1)+2=-3 < 0, l++
//   sum=-4+(-1)+2=-3 < 0, l++
//   sum=-4+0+2=-2 < 0, l++
//   sum=-4+1+2=-1 < 0, l++
//   l >= r, stop
// i=1: nums[i]=-1, l=2, r=5
//   sum=-1+(-1)+2=0 → add [-1,-1,2]
//   skip dups, l=3, r=4
//   sum=-1+0+1=0 → add [-1,0,1]
// i=2: nums[i]=-1 == nums[1], skip
// Result: [[-1,-1,2],[-1,0,1]]
```

---

## Template 3: Container With Most Water (LC 11)

```java
// Two pointers converging, greedy choice
int maxArea(int[] height) {
    int left = 0, right = height.length - 1;
    int maxWater = 0;

    while (left < right) {
        int h = Math.min(height[left], height[right]);
        int w = right - left;
        maxWater = Math.max(maxWater, h * w);

        // Move the pointer at the SHORTER wall
        // (moving the taller one can only decrease height, not increase)
        if (height[left] < height[right]) left++;
        else right--;
    }
    return maxWater;
}
```

---

## Template 4: Remove Duplicates from Sorted Array (LC 26)

```java
// In-place, O(1) extra space
// slow pointer marks position for next unique element
// fast pointer scans ahead
int removeDuplicates(int[] nums) {
    if (nums.length == 0) return 0;

    int slow = 0;  // last position of unique element

    for (int fast = 1; fast < nums.length; fast++) {
        if (nums[fast] != nums[slow]) {
            slow++;
            nums[slow] = nums[fast];
        }
    }
    return slow + 1;  // count of unique elements
}
```

---

## Template 5: Fast/Slow Pointers (Floyd's Cycle Detection)

```java
// Detect cycle in linked list
boolean hasCycle(ListNode head) {
    ListNode slow = head, fast = head;

    while (fast != null && fast.next != null) {
        slow = slow.next;          // moves 1 step
        fast = fast.next.next;     // moves 2 steps

        if (slow == fast) return true;  // cycle detected
    }
    return false;
}

// Find start of cycle
ListNode detectCycle(ListNode head) {
    ListNode slow = head, fast = head;

    while (fast != null && fast.next != null) {
        slow = slow.next;
        fast = fast.next.next;
        if (slow == fast) break;
    }

    if (fast == null || fast.next == null) return null;

    // Reset slow to head; fast stays at meeting point
    // Both move at speed 1; they meet at cycle start
    slow = head;
    while (slow != fast) {
        slow = slow.next;
        fast = fast.next;
    }
    return slow;
}

// Find middle of linked list
ListNode findMiddle(ListNode head) {
    ListNode slow = head, fast = head;
    while (fast != null && fast.next != null) {
        slow = slow.next;
        fast = fast.next.next;
    }
    return slow;  // for odd: exact middle; for even: upper middle
}
```

---

## Template 6: Trapping Rain Water (LC 42) — Two Pointers

```java
int trap(int[] height) {
    int left = 0, right = height.length - 1;
    int leftMax = 0, rightMax = 0;
    int water = 0;

    while (left < right) {
        if (height[left] < height[right]) {
            if (height[left] >= leftMax) leftMax = height[left];
            else water += leftMax - height[left];
            left++;
        } else {
            if (height[right] >= rightMax) rightMax = height[right];
            else water += rightMax - height[right];
            right--;
        }
    }
    return water;
}
// Key insight: water at position i = min(maxLeft[i], maxRight[i]) - height[i]
// Two pointers avoid needing O(n) precomputed arrays
```

---

## Template 7: Palindrome Verification

```java
boolean isPalindrome(String s) {
    // Clean: keep only alphanumeric, lowercase
    int left = 0, right = s.length() - 1;

    while (left < right) {
        while (left < right && !Character.isLetterOrDigit(s.charAt(left))) left++;
        while (left < right && !Character.isLetterOrDigit(s.charAt(right))) right--;

        if (Character.toLowerCase(s.charAt(left)) !=
            Character.toLowerCase(s.charAt(right))) return false;
        left++;
        right--;
    }
    return true;
}
```

---

## Merge Two Sorted Arrays

```java
void mergeSorted(int[] arr1, int m, int[] arr2, int n) {
    // Merge arr2 into arr1 (arr1 has extra space at end)
    int i = m - 1, j = n - 1, k = m + n - 1;  // start from the END

    while (i >= 0 && j >= 0) {
        if (arr1[i] > arr2[j]) arr1[k--] = arr1[i--];
        else arr1[k--] = arr2[j--];
    }
    while (j >= 0) arr1[k--] = arr2[j--];
}
```

---

## Edge Cases

```
1. Array with < 2 elements
2. All elements equal
3. Already sorted in required order
4. Target sum not achievable
5. Cycle of length 1 (linked list)
```

---

## Complexity Summary

| Problem | Brute Force | Two Pointers |
|---------|------------|-------------|
| Two Sum (sorted) | O(n²) | O(n) |
| Three Sum | O(n³) | O(n²) |
| Remove Duplicates | O(n²) | O(n) |
| Container With Most Water | O(n²) | O(n) |
| Trapping Rain Water | O(n²) | O(n) |
| Cycle Detection | O(n) space | O(1) space |
