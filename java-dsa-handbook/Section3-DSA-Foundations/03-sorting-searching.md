# Section 3.3 — Sorting and Searching

---

## 1. Sorting Algorithms

### Quick Reference

| Algorithm | Best | Average | Worst | Space | Stable |
|-----------|------|---------|-------|-------|--------|
| Bubble Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |
| Selection Sort | O(n²) | O(n²) | O(n²) | O(1) | No |
| Insertion Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) | Yes |
| Quick Sort | O(n log n) | O(n log n) | O(n²) | O(log n) | No |
| Heap Sort | O(n log n) | O(n log n) | O(n log n) | O(1) | No |
| Counting Sort | O(n+k) | O(n+k) | O(n+k) | O(k) | Yes |
| Radix Sort | O(d*n) | O(d*n) | O(d*n) | O(n+k) | Yes |
| Tim Sort (Java) | O(n) | O(n log n) | O(n log n) | O(n) | Yes |

> **Java uses:** Dual-Pivot Quicksort for primitive arrays, TimSort for Object arrays

---

### Implementations You Must Know

#### Merge Sort (Divide and Conquer)

```java
// Stable, O(n log n) guaranteed, O(n) space
void mergeSort(int[] arr, int left, int right) {
    if (left >= right) return;

    int mid = left + (right - left) / 2;
    mergeSort(arr, left, mid);
    mergeSort(arr, mid + 1, right);
    merge(arr, left, mid, right);
}

void merge(int[] arr, int left, int mid, int right) {
    int[] temp = Arrays.copyOfRange(arr, left, right + 1);
    int i = 0, j = mid - left + 1, k = left;

    while (i <= mid - left && j <= right - left) {
        if (temp[i] <= temp[j]) arr[k++] = temp[i++];
        else arr[k++] = temp[j++];
    }
    while (i <= mid - left) arr[k++] = temp[i++];
    while (j <= right - left) arr[k++] = temp[j++];
}

// Use case: count inversions (modify merge step)
long countInversions;
void mergeCount(int[] arr, int left, int right) {
    if (left >= right) return;
    int mid = left + (right - left) / 2;
    mergeCount(arr, left, mid);
    mergeCount(arr, mid + 1, right);
    mergeAndCount(arr, left, mid, right);
}
```

#### Quick Sort

```java
// Average O(n log n), O(n²) worst (mitigated by random pivot)
void quickSort(int[] arr, int left, int right) {
    if (left >= right) return;

    int pivotIdx = partition(arr, left, right);
    quickSort(arr, left, pivotIdx - 1);
    quickSort(arr, pivotIdx + 1, right);
}

int partition(int[] arr, int left, int right) {
    // Randomize pivot to avoid O(n²) worst case
    int randIdx = left + (int)(Math.random() * (right - left + 1));
    swap(arr, randIdx, right);

    int pivot = arr[right];
    int i = left - 1;

    for (int j = left; j < right; j++) {
        if (arr[j] <= pivot) {
            i++;
            swap(arr, i, j);
        }
    }
    swap(arr, i + 1, right);
    return i + 1;
}

void swap(int[] arr, int i, int j) {
    int temp = arr[i]; arr[i] = arr[j]; arr[j] = temp;
}
```

#### Counting Sort (When range is known)

```java
// O(n + k) where k = range of values
void countingSort(int[] arr, int maxVal) {
    int[] count = new int[maxVal + 1];
    for (int n : arr) count[n]++;

    int idx = 0;
    for (int i = 0; i <= maxVal; i++) {
        while (count[i]-- > 0) arr[idx++] = i;
    }
}

// Character frequency sort
void sortChars(char[] arr) {
    int[] freq = new int[26];
    for (char c : arr) freq[c - 'a']++;
    int idx = 0;
    for (int i = 0; i < 26; i++) {
        while (freq[i]-- > 0) arr[idx++] = (char)('a' + i);
    }
}
```

#### Insertion Sort (Best for small/nearly-sorted arrays)

```java
void insertionSort(int[] arr) {
    for (int i = 1; i < arr.length; i++) {
        int key = arr[i];
        int j = i - 1;
        while (j >= 0 && arr[j] > key) {
            arr[j + 1] = arr[j];
            j--;
        }
        arr[j + 1] = key;
    }
}
```

---

## 2. Binary Search — Core Variations

> "Binary search is easy to understand, but hard to implement correctly." — Donald Knuth

### Template 1: Find Exact Target

```java
// Returns index of target, or -1 if not found
int binarySearch(int[] arr, int target) {
    int left = 0, right = arr.length - 1;

    while (left <= right) {
        int mid = left + (right - left) / 2;

        if (arr[mid] == target) return mid;
        else if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}
```

### Template 2: Find Leftmost (First Occurrence)

```java
// Returns index of first occurrence of target, or -1
int findFirst(int[] arr, int target) {
    int left = 0, right = arr.length - 1;
    int result = -1;

    while (left <= right) {
        int mid = left + (right - left) / 2;

        if (arr[mid] == target) {
            result = mid;
            right = mid - 1;  // keep searching LEFT
        } else if (arr[mid] < target) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    return result;
}
// Or using the "lower bound" approach:
int lowerBound(int[] arr, int target) {
    int left = 0, right = arr.length;
    while (left < right) {           // note: left < right (not <=)
        int mid = left + (right - left) / 2;
        if (arr[mid] < target) left = mid + 1;
        else right = mid;            // include mid in search space
    }
    return left;  // index of first element >= target
}
```

### Template 3: Find Rightmost (Last Occurrence)

```java
int findLast(int[] arr, int target) {
    int left = 0, right = arr.length - 1;
    int result = -1;

    while (left <= right) {
        int mid = left + (right - left) / 2;

        if (arr[mid] == target) {
            result = mid;
            left = mid + 1;   // keep searching RIGHT
        } else if (arr[mid] < target) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    return result;
}
```

### Template 4: Rotated Sorted Array

```java
// {4,5,6,7,0,1,2} — find target
int searchRotated(int[] arr, int target) {
    int left = 0, right = arr.length - 1;

    while (left <= right) {
        int mid = left + (right - left) / 2;

        if (arr[mid] == target) return mid;

        // Left half is sorted
        if (arr[left] <= arr[mid]) {
            if (arr[left] <= target && target < arr[mid]) {
                right = mid - 1;  // target in sorted left half
            } else {
                left = mid + 1;   // target in right half
            }
        }
        // Right half is sorted
        else {
            if (arr[mid] < target && target <= arr[right]) {
                left = mid + 1;   // target in sorted right half
            } else {
                right = mid - 1;  // target in left half
            }
        }
    }
    return -1;
}
```

### Template 5: Find Peak Element

```java
// Peak: arr[i] > arr[i-1] and arr[i] > arr[i+1]
int findPeak(int[] arr) {
    int left = 0, right = arr.length - 1;

    while (left < right) {
        int mid = left + (right - left) / 2;

        if (arr[mid] > arr[mid + 1]) {
            right = mid;        // peak is at mid or left of mid
        } else {
            left = mid + 1;     // peak is right of mid
        }
    }
    return left;  // left == right == peak index
}
```

### Template 6: Binary Search on Answer Space

```java
// "Minimize the maximum" or "find the minimum that satisfies condition"
// Key insight: search on the answer itself, not the array

// Example: Koko Eating Bananas
// Can Koko eat all bananas at speed k in h hours?
boolean canFinish(int[] piles, int h, int k) {
    long hours = 0;
    for (int pile : piles) {
        hours += (pile + k - 1) / k;  // ceil division
    }
    return hours <= h;
}

int minEatingSpeed(int[] piles, int h) {
    int left = 1, right = Arrays.stream(piles).max().getAsInt();

    while (left < right) {
        int mid = left + (right - left) / 2;
        if (canFinish(piles, h, mid)) {
            right = mid;     // try smaller speed
        } else {
            left = mid + 1;  // need larger speed
        }
    }
    return left;
}

// Pattern for "minimize X such that condition(X) is satisfied":
// left = minimum possible answer
// right = maximum possible answer
// Condition must be monotonic: if condition(X) is true, condition(X+1) is also true
```

---

## 3. Search Patterns Summary

```java
// Binary search decision tree:
// 1. Is array sorted? → Direct binary search
// 2. Is array sorted and rotated? → Template 4
// 3. Find peak? → Template 5
// 4. Find first/last occurrence? → Templates 2/3
// 5. Minimize/maximize answer? → Binary search on answer space

// Signal keywords for binary search on answer:
// "minimum speed", "maximum pages", "minimize distance",
// "smallest possible", "largest valid k"
```

---

## 4. Common Sorting Interview Problems

```java
// 1. Sort Colors (Dutch National Flag)
void sortColors(int[] nums) {
    int low = 0, mid = 0, high = nums.length - 1;
    while (mid <= high) {
        if (nums[mid] == 0) swap(nums, low++, mid++);
        else if (nums[mid] == 1) mid++;
        else swap(nums, mid, high--);
    }
}

// 2. Kth Largest Element (Quick Select — O(n) average)
int findKthLargest(int[] nums, int k) {
    return quickSelect(nums, 0, nums.length - 1, nums.length - k);
}

int quickSelect(int[] nums, int left, int right, int k) {
    if (left == right) return nums[left];

    int pivotIdx = partition(nums, left, right);
    if (pivotIdx == k) return nums[pivotIdx];
    else if (pivotIdx < k) return quickSelect(nums, pivotIdx + 1, right, k);
    else return quickSelect(nums, left, pivotIdx - 1, k);
}

// 3. Meeting Rooms II (sort + min-heap)
int minMeetingRooms(int[][] intervals) {
    Arrays.sort(intervals, (a, b) -> a[0] - b[0]);
    PriorityQueue<Integer> endTimes = new PriorityQueue<>();

    for (int[] interval : intervals) {
        if (!endTimes.isEmpty() && endTimes.peek() <= interval[0]) {
            endTimes.poll();  // reuse room
        }
        endTimes.offer(interval[1]);
    }
    return endTimes.size();
}
```

> **Interview Tip:** When asked "can you sort this differently?", think about:
> 1. Custom comparator (sort by a specific field)
> 2. Partial sort (QuickSelect for Kth element)
> 3. Non-comparison sort (counting sort, bucket sort when values have bounded range)
