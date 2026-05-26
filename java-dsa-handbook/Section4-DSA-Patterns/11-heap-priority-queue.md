# Pattern 11 — Heap / Priority Queue

---

## Core Insight

A heap gives you O(1) access to the min/max and O(log n) insert/delete. Perfect for "top K", "kth element", "streaming median", and "greedy with priority".

---

## Pattern 1: Top K Elements

```java
// Kth Largest Element (LC 215)
// Approach: min-heap of size k — maintains top k largest
int findKthLargest(int[] nums, int k) {
    PriorityQueue<Integer> minHeap = new PriorityQueue<>();  // min at top

    for (int n : nums) {
        minHeap.offer(n);
        if (minHeap.size() > k) minHeap.poll();  // remove smallest
    }
    return minHeap.peek();  // smallest of top-k = kth largest
}
// Time: O(n log k)  Space: O(k)

// Top K Frequent Elements (LC 347)
int[] topKFrequent(int[] nums, int k) {
    Map<Integer, Integer> freq = new HashMap<>();
    for (int n : nums) freq.merge(n, 1, Integer::sum);

    // Min-heap by frequency (keeps top k most frequent)
    PriorityQueue<int[]> heap = new PriorityQueue<>((a, b) -> a[1] - b[1]);

    for (Map.Entry<Integer, Integer> e : freq.entrySet()) {
        heap.offer(new int[]{e.getKey(), e.getValue()});
        if (heap.size() > k) heap.poll();
    }

    int[] result = new int[k];
    for (int i = k - 1; i >= 0; i--) result[i] = heap.poll()[0];
    return result;
}
```

---

## Pattern 2: Merge K Sorted Lists / Arrays

```java
// Merge K Sorted Lists (LC 23)
ListNode mergeKLists(ListNode[] lists) {
    PriorityQueue<ListNode> heap = new PriorityQueue<>((a, b) -> a.val - b.val);

    for (ListNode head : lists) {
        if (head != null) heap.offer(head);
    }

    ListNode dummy = new ListNode(0);
    ListNode curr = dummy;

    while (!heap.isEmpty()) {
        ListNode node = heap.poll();
        curr.next = node;
        curr = curr.next;
        if (node.next != null) heap.offer(node.next);
    }
    return dummy.next;
}
// Time: O(n log k) where n = total nodes, k = number of lists

// Merge K Sorted Arrays
int[] mergeKArrays(int[][] arrays) {
    PriorityQueue<int[]> heap = new PriorityQueue<>((a, b) -> a[0] - b[0]);
    // [value, arrayIndex, elementIndex]

    for (int i = 0; i < arrays.length; i++) {
        if (arrays[i].length > 0) {
            heap.offer(new int[]{arrays[i][0], i, 0});
        }
    }

    List<Integer> result = new ArrayList<>();
    while (!heap.isEmpty()) {
        int[] curr = heap.poll();
        result.add(curr[0]);
        int arrIdx = curr[1], elemIdx = curr[2];
        if (elemIdx + 1 < arrays[arrIdx].length) {
            heap.offer(new int[]{arrays[arrIdx][elemIdx + 1], arrIdx, elemIdx + 1});
        }
    }
    return result.stream().mapToInt(Integer::intValue).toArray();
}
```

---

## Pattern 3: Find Median from Data Stream (LC 295)

```java
// Two heaps: maxHeap for lower half, minHeap for upper half
class MedianFinder {
    private PriorityQueue<Integer> maxHeap = new PriorityQueue<>(Collections.reverseOrder());
    private PriorityQueue<Integer> minHeap = new PriorityQueue<>();

    public void addNum(int num) {
        // Step 1: Push to maxHeap
        maxHeap.offer(num);

        // Step 2: Balance: maxHeap top should be <= minHeap top
        if (!minHeap.isEmpty() && maxHeap.peek() > minHeap.peek()) {
            minHeap.offer(maxHeap.poll());
        }

        // Step 3: Rebalance sizes (maxHeap can have at most 1 more)
        if (maxHeap.size() > minHeap.size() + 1) {
            minHeap.offer(maxHeap.poll());
        } else if (minHeap.size() > maxHeap.size()) {
            maxHeap.offer(minHeap.poll());
        }
    }

    public double findMedian() {
        if (maxHeap.size() > minHeap.size()) return maxHeap.peek();
        return (maxHeap.peek() + minHeap.peek()) / 2.0;
    }
}
// Time: O(log n) per addNum, O(1) for findMedian
```

---

## Pattern 4: Task Scheduler (LC 621)

```java
int leastInterval(char[] tasks, int n) {
    int[] freq = new int[26];
    for (char t : tasks) freq[t - 'A']++;

    // Max-heap by frequency
    PriorityQueue<Integer> maxHeap = new PriorityQueue<>(Collections.reverseOrder());
    for (int f : freq) if (f > 0) maxHeap.offer(f);

    int time = 0;
    Queue<int[]> cooldown = new ArrayDeque<>();  // [freq, available_at]

    while (!maxHeap.isEmpty() || !cooldown.isEmpty()) {
        time++;

        if (!maxHeap.isEmpty()) {
            int f = maxHeap.poll() - 1;
            if (f > 0) cooldown.offer(new int[]{f, time + n});
        }

        if (!cooldown.isEmpty() && cooldown.peek()[1] == time) {
            maxHeap.offer(cooldown.poll()[0]);
        }
    }
    return time;
}
```

---

## Pattern 5: Sliding Window with Heap (Kth Largest in Stream)

```java
// Kth Largest Element in a Stream (LC 703)
class KthLargest {
    private final int k;
    private final PriorityQueue<Integer> heap;

    public KthLargest(int k, int[] nums) {
        this.k = k;
        heap = new PriorityQueue<>();  // min-heap
        for (int n : nums) add(n);
    }

    public int add(int val) {
        heap.offer(val);
        if (heap.size() > k) heap.poll();  // remove smallest
        return heap.peek();  // kth largest
    }
}
```

---

## Pattern 6: Dijkstra (Revisited as Heap Pattern)

```java
// The key insight: Dijkstra = BFS with a priority queue
// Always processes the closest unvisited node first
int networkDelayTime(int[][] times, int n, int k) {
    Map<Integer, List<int[]>> adj = new HashMap<>();
    for (int[] t : times) {
        adj.computeIfAbsent(t[0], x -> new ArrayList<>()).add(new int[]{t[1], t[2]});
    }

    int[] dist = new int[n + 1];
    Arrays.fill(dist, Integer.MAX_VALUE);
    dist[k] = 0;

    PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> a[1] - b[1]);
    pq.offer(new int[]{k, 0});

    while (!pq.isEmpty()) {
        int[] curr = pq.poll();
        int node = curr[0], d = curr[1];
        if (d > dist[node]) continue;

        for (int[] edge : adj.getOrDefault(node, new ArrayList<>())) {
            int next = edge[0], w = edge[1];
            if (dist[node] + w < dist[next]) {
                dist[next] = dist[node] + w;
                pq.offer(new int[]{next, dist[next]});
            }
        }
    }

    int max = 0;
    for (int i = 1; i <= n; i++) {
        if (dist[i] == Integer.MAX_VALUE) return -1;
        max = Math.max(max, dist[i]);
    }
    return max;
}
```

---

## Complexity Summary

| Pattern | Time | Space |
|---------|------|-------|
| Top K (n elements, k result) | O(n log k) | O(k) |
| Merge K lists (n total, k lists) | O(n log k) | O(k) |
| Add to stream + find median | O(log n) per add | O(n) |
| Dijkstra (V vertices, E edges) | O((V+E) log V) | O(V+E) |

> **Key insight:** min-heap of size k = efficient way to track top-k largest. This pattern appears everywhere: top K frequent, K closest points, K-way merge.
