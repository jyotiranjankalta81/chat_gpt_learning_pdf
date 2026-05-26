# Section 2.4 — Queue, Stack, Deque, and PriorityQueue

---

## Stack

### Using ArrayDeque as Stack (Recommended)

```java
// Java's legacy Stack class is synchronized (slow) — use ArrayDeque instead
Deque<Integer> stack = new ArrayDeque<>();

// Push
stack.push(1);     // equivalent to addFirst() — adds to HEAD
stack.push(2);
stack.push(3);

// Pop
int top = stack.pop();  // removes and returns head — 3

// Peek
int peek = stack.peek();  // returns head without removing — 2

// Check empty
stack.isEmpty();

// Size
stack.size();
```

### Stack DSA Patterns

```java
// Pattern 1: Balanced Brackets
public boolean isValid(String s) {
    Deque<Character> stack = new ArrayDeque<>();
    for (char c : s.toCharArray()) {
        if (c == '(' || c == '[' || c == '{') {
            stack.push(c);
        } else {
            if (stack.isEmpty()) return false;
            char top = stack.pop();
            if (c == ')' && top != '(') return false;
            if (c == ']' && top != '[') return false;
            if (c == '}' && top != '{') return false;
        }
    }
    return stack.isEmpty();
}

// Pattern 2: Evaluate expression / convert infix to postfix
// (uses two stacks or one stack)
public int evalRPN(String[] tokens) {
    Deque<Integer> stack = new ArrayDeque<>();
    for (String token : tokens) {
        if (token.equals("+") || token.equals("-") ||
            token.equals("*") || token.equals("/")) {
            int b = stack.pop(), a = stack.pop();
            switch (token) {
                case "+": stack.push(a + b); break;
                case "-": stack.push(a - b); break;
                case "*": stack.push(a * b); break;
                case "/": stack.push(a / b); break;
            }
        } else {
            stack.push(Integer.parseInt(token));
        }
    }
    return stack.pop();
}

// Pattern 3: Min stack — supporting getMin in O(1)
class MinStack {
    private Deque<Integer> stack = new ArrayDeque<>();
    private Deque<Integer> minStack = new ArrayDeque<>();

    public void push(int val) {
        stack.push(val);
        int currMin = minStack.isEmpty() ? val : Math.min(val, minStack.peek());
        minStack.push(currMin);
    }

    public void pop() {
        stack.pop();
        minStack.pop();
    }

    public int top() { return stack.peek(); }
    public int getMin() { return minStack.peek(); }
}
```

---

## Queue

### Using ArrayDeque as Queue (Recommended)

```java
// FIFO: add to tail, remove from head
Queue<Integer> queue = new ArrayDeque<>();

// Enqueue (add to tail)
queue.offer(1);   // preferred (returns false on failure)
queue.add(2);     // throws exception on failure
queue.offer(3);

// Dequeue (remove from head)
int front = queue.poll();    // removes and returns head (null if empty)
int front2 = queue.remove(); // removes and returns head (throws if empty)

// Peek head
int peek = queue.peek();   // null if empty
int peek2 = queue.element(); // throws if empty

// Check
queue.isEmpty();
queue.size();
```

### BFS Queue Pattern (Most Important)

```java
// BFS template — used for trees, graphs, shortest path
public int bfs(int[][] grid, int startR, int startC) {
    int rows = grid.length, cols = grid[0].length;
    Queue<int[]> queue = new ArrayDeque<>();
    boolean[][] visited = new boolean[rows][cols];

    queue.offer(new int[]{startR, startC});
    visited[startR][startC] = true;
    int distance = 0;

    int[][] dirs = {{0,1},{0,-1},{1,0},{-1,0}};

    while (!queue.isEmpty()) {
        int size = queue.size();  // process level by level
        for (int i = 0; i < size; i++) {
            int[] curr = queue.poll();
            int r = curr[0], c = curr[1];

            if (isTarget(grid, r, c)) return distance;

            for (int[] dir : dirs) {
                int nr = r + dir[0], nc = c + dir[1];
                if (nr >= 0 && nr < rows && nc >= 0 && nc < cols
                    && !visited[nr][nc] && grid[nr][nc] != 0) {
                    queue.offer(new int[]{nr, nc});
                    visited[nr][nc] = true;
                }
            }
        }
        distance++;
    }
    return -1;  // not found
}
```

---

## Deque (Double-Ended Queue)

### ArrayDeque (Best All-Around Implementation)

```java
Deque<Integer> deque = new ArrayDeque<>();

// Add to head / tail
deque.addFirst(1);    // [1]
deque.addLast(2);     // [1, 2]
deque.offerFirst(0);  // [0, 1, 2]
deque.offerLast(3);   // [0, 1, 2, 3]

// Remove from head / tail
deque.removeFirst();  // 0 — [1, 2, 3]
deque.removeLast();   // 3 — [1, 2]
deque.pollFirst();    // 1 — [2]   (null if empty)
deque.pollLast();     // 2 — []    (null if empty)

// Peek head / tail
deque.peekFirst();    // null if empty
deque.peekLast();     // null if empty
deque.getFirst();     // throws if empty
deque.getLast();      // throws if empty

// Stack usage (LIFO)
deque.push(val);   // = addFirst
deque.pop();       // = removeFirst
deque.peek();      // = peekFirst

// Queue usage (FIFO)
deque.offer(val);  // = addLast
deque.poll();      // = removeFirst
deque.peek();      // = peekFirst
```

### Monotonic Deque (Sliding Window Maximum)

```java
// Sliding window maximum — O(n)
public int[] maxSlidingWindow(int[] nums, int k) {
    int n = nums.length;
    int[] result = new int[n - k + 1];
    Deque<Integer> deque = new ArrayDeque<>();  // stores INDICES

    for (int i = 0; i < n; i++) {
        // Remove elements out of window
        while (!deque.isEmpty() && deque.peekFirst() < i - k + 1) {
            deque.pollFirst();
        }

        // Remove elements smaller than current (maintain decreasing order)
        while (!deque.isEmpty() && nums[deque.peekLast()] < nums[i]) {
            deque.pollLast();
        }

        deque.offerLast(i);

        // Record result once window is full
        if (i >= k - 1) {
            result[i - k + 1] = nums[deque.peekFirst()];
        }
    }
    return result;
}
```

---

## PriorityQueue (Heap)

### Internal Working

```
PriorityQueue = Binary Heap
- Min-heap by default (smallest element at top)
- Backed by array
- Parent-child relationship: parent at i, children at 2i+1 and 2i+2
- Heap property: parent <= children (min-heap)
- Complete binary tree — no gaps in array
```

### Time Complexity

| Operation | Complexity |
|-----------|-----------|
| `offer(e)` / `add(e)` | O(log n) |
| `poll()` | O(log n) |
| `peek()` | O(1) |
| `contains(e)` | O(n) |
| `remove(e)` | O(n) |
| Build heap from n elements | O(n) |

### Complete PriorityQueue API

```java
// Min-heap (default)
PriorityQueue<Integer> minHeap = new PriorityQueue<>();

// Max-heap
PriorityQueue<Integer> maxHeap = new PriorityQueue<>(Collections.reverseOrder());
// Or:
PriorityQueue<Integer> maxHeap2 = new PriorityQueue<>((a, b) -> b - a);

// Custom comparator (e.g., sort by frequency)
PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> a[1] - b[1]);  // by second element

// Operations
minHeap.offer(5);    // add
minHeap.offer(1);
minHeap.offer(3);
minHeap.peek();      // 1 (min, not removed)
minHeap.poll();      // 1 (removes and returns min)
minHeap.size();
minHeap.isEmpty();

// Build from collection — O(n) (more efficient than n insertions)
PriorityQueue<Integer> pq2 = new PriorityQueue<>(Arrays.asList(5, 3, 1, 4, 2));

// Convert to sorted array
List<Integer> sorted = new ArrayList<>();
while (!minHeap.isEmpty()) sorted.add(minHeap.poll());  // O(n log n)
```

### PriorityQueue DSA Patterns

```java
// Pattern 1: Kth Largest Element — O(n log k)
public int findKthLargest(int[] nums, int k) {
    PriorityQueue<Integer> minHeap = new PriorityQueue<>();
    for (int n : nums) {
        minHeap.offer(n);
        if (minHeap.size() > k) minHeap.poll();  // keep only k largest
    }
    return minHeap.peek();  // kth largest = smallest of top-k
}

// Pattern 2: Top K Frequent Elements
public int[] topKFrequent(int[] nums, int k) {
    Map<Integer, Integer> freq = new HashMap<>();
    for (int n : nums) freq.merge(n, 1, Integer::sum);

    PriorityQueue<int[]> minHeap = new PriorityQueue<>((a, b) -> a[1] - b[1]);
    for (Map.Entry<Integer, Integer> e : freq.entrySet()) {
        minHeap.offer(new int[]{e.getKey(), e.getValue()});
        if (minHeap.size() > k) minHeap.poll();
    }

    int[] result = new int[k];
    for (int i = k - 1; i >= 0; i--) result[i] = minHeap.poll()[0];
    return result;
}

// Pattern 3: Merge K Sorted Lists
public ListNode mergeKLists(ListNode[] lists) {
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

// Pattern 4: Find Median from Data Stream
class MedianFinder {
    private PriorityQueue<Integer> maxHeap = new PriorityQueue<>(Collections.reverseOrder()); // lower half
    private PriorityQueue<Integer> minHeap = new PriorityQueue<>();  // upper half

    public void addNum(int num) {
        maxHeap.offer(num);
        minHeap.offer(maxHeap.poll());
        if (maxHeap.size() < minHeap.size()) {
            maxHeap.offer(minHeap.poll());
        }
    }

    public double findMedian() {
        if (maxHeap.size() > minHeap.size()) return maxHeap.peek();
        return (maxHeap.peek() + minHeap.peek()) / 2.0;
    }
}

// Pattern 5: Dijkstra's Shortest Path
public int[] dijkstra(int n, int[][] edges, int src) {
    Map<Integer, List<int[]>> adj = new HashMap<>();
    for (int[] e : edges) {
        adj.computeIfAbsent(e[0], k -> new ArrayList<>()).add(new int[]{e[1], e[2]});
        adj.computeIfAbsent(e[1], k -> new ArrayList<>()).add(new int[]{e[0], e[2]});
    }

    int[] dist = new int[n];
    Arrays.fill(dist, Integer.MAX_VALUE);
    dist[src] = 0;

    PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> a[1] - b[1]); // [node, distance]
    pq.offer(new int[]{src, 0});

    while (!pq.isEmpty()) {
        int[] curr = pq.poll();
        int node = curr[0], d = curr[1];
        if (d > dist[node]) continue;  // outdated entry

        for (int[] neighbor : adj.getOrDefault(node, new ArrayList<>())) {
            int next = neighbor[0], weight = neighbor[1];
            if (dist[node] + weight < dist[next]) {
                dist[next] = dist[node] + weight;
                pq.offer(new int[]{next, dist[next]});
            }
        }
    }
    return dist;
}

// Pattern 6: Task scheduling by frequency
public String reorganizeString(String s) {
    int[] freq = new int[26];
    for (char c : s.toCharArray()) freq[c - 'a']++;

    PriorityQueue<int[]> maxHeap = new PriorityQueue<>((a, b) -> b[1] - a[1]);
    for (int i = 0; i < 26; i++) {
        if (freq[i] > 0) maxHeap.offer(new int[]{i + 'a', freq[i]});
    }

    StringBuilder sb = new StringBuilder();
    while (maxHeap.size() >= 2) {
        int[] first = maxHeap.poll();
        int[] second = maxHeap.poll();
        sb.append((char) first[0]);
        sb.append((char) second[0]);
        if (--first[1] > 0) maxHeap.offer(first);
        if (--second[1] > 0) maxHeap.offer(second);
    }

    if (!maxHeap.isEmpty()) {
        int[] last = maxHeap.poll();
        if (last[1] > 1) return "";  // impossible
        sb.append((char) last[0]);
    }
    return sb.toString();
}
```

---

## Queue/Stack/Deque Summary

| | Stack | Queue | Deque |
|-|-------|-------|-------|
| Order | LIFO | FIFO | Both ends |
| Add | `push()` | `offer()` | `addFirst/Last()` |
| Remove | `pop()` | `poll()` | `pollFirst/Last()` |
| Peek | `peek()` | `peek()` | `peekFirst/Last()` |
| Best Implementation | `ArrayDeque` | `ArrayDeque` | `ArrayDeque` |
| Use case | DFS, brackets, undo | BFS, level order, scheduling | Sliding window |

> **Interview Tip:** Always say "I'll use ArrayDeque as my stack/queue — it's more efficient than Java's Stack and LinkedList." This demonstrates production-quality Java knowledge.
