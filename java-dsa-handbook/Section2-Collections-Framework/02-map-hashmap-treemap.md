# Section 2.2 — Map: HashMap and TreeMap

---

## The Map Interface

```java
// Map stores key-value pairs, keys are unique
Map<String, Integer> map = new HashMap<>();     // unordered, O(1) ops
Map<String, Integer> tree = new TreeMap<>();    // sorted by key, O(log n)
Map<String, Integer> linked = new LinkedHashMap<>(); // insertion order

// Common operations
map.put("a", 1);
map.get("a");           // 1
map.containsKey("a");   // true
map.containsValue(1);   // true (O(n)!)
map.remove("a");
map.size();
map.isEmpty();
```

---

## HashMap

### Internal Working (Critical for Interviews)

```
HashMap = Hash Table with Separate Chaining (Java 8+: with Tree optimization)

Internal structure:
- Array of buckets (default size: 16)
- Each bucket: LinkedList or Red-Black Tree (Java 8+)
- Load factor: 0.75 (default) — resize at 75% full
- Resize doubles capacity and rehashes all entries

Hash computation:
1. hashCode() of key is computed
2. Hash is spread (XOR with right-shifted high bits)
3. Bucket index = hash & (capacity - 1)

Java 8 optimization:
- When a bucket chain has > 8 entries AND table has >= 64 buckets:
  → Chain converts to Red-Black Tree (O(log n) ops in that bucket)
- When entries drop below 6: reverts to linked list
```

### Time Complexity

| Operation | Average | Worst Case | Notes |
|-----------|---------|-----------|-------|
| `put(k, v)` | O(1) | O(n) | Worst: all keys hash to same bucket |
| `get(k)` | O(1) | O(log n) | Java 8+: tree buckets |
| `remove(k)` | O(1) | O(log n) | |
| `containsKey(k)` | O(1) | O(log n) | |
| `containsValue(v)` | O(n) | O(n) | Must scan all values |
| Iteration | O(n) | O(n) | Visits all entries |

### Complete HashMap API

```java
Map<String, Integer> map = new HashMap<>();

// Put / Get
map.put("apple", 3);
map.put("banana", 5);
int val = map.get("apple");         // 3
int def = map.getOrDefault("cherry", 0);  // 0 (key not present)

// Check existence
map.containsKey("apple");   // true
map.containsValue(5);       // true (O(n))

// Remove
map.remove("apple");                    // remove key, returns old value
map.remove("banana", 5);               // conditional remove (only if value matches)

// Size
map.size();
map.isEmpty();

// Iteration
for (Map.Entry<String, Integer> entry : map.entrySet()) {
    String key = entry.getKey();
    int value = entry.getValue();
}
for (String key : map.keySet()) { }
for (int value : map.values()) { }
map.forEach((k, v) -> System.out.println(k + ": " + v));

// Advanced operations (Java 8+)
// putIfAbsent — only put if key not present
map.putIfAbsent("apple", 10);  // doesn't overwrite existing

// computeIfAbsent — compute and put if absent
map.computeIfAbsent("cherry", k -> k.length());  // "cherry" → 6
// Very useful for building adjacency lists:
adjList.computeIfAbsent(node, k -> new ArrayList<>()).add(neighbor);

// computeIfPresent — update only if key exists
map.computeIfPresent("banana", (k, v) -> v + 1);  // 5 → 6

// compute — always compute new value
map.compute("apple", (k, v) -> (v == null) ? 1 : v + 1);

// merge — merge with existing value
map.merge("apple", 1, Integer::sum);  // if absent: put 1; if present: sum

// replaceAll
map.replaceAll((k, v) -> v * 2);

// getOrDefault chaining for frequency maps
Map<Character, Integer> freq = new HashMap<>();
for (char c : s.toCharArray()) {
    freq.put(c, freq.getOrDefault(c, 0) + 1);
}
// Or using merge:
for (char c : s.toCharArray()) {
    freq.merge(c, 1, Integer::sum);
}
// Or using compute:
for (char c : s.toCharArray()) {
    freq.compute(c, (k, v) -> v == null ? 1 : v + 1);
}
```

### HashMap DSA Patterns

```java
// Pattern 1: Frequency map (most common)
Map<Integer, Integer> count = new HashMap<>();
for (int n : nums) count.put(n, count.getOrDefault(n, 0) + 1);

// Pattern 2: Two Sum
Map<Integer, Integer> seen = new HashMap<>(); // val → index
for (int i = 0; i < nums.length; i++) {
    int complement = target - nums[i];
    if (seen.containsKey(complement)) return new int[]{seen.get(complement), i};
    seen.put(nums[i], i);
}

// Pattern 3: Group anagrams
Map<String, List<String>> groups = new HashMap<>();
for (String word : words) {
    char[] chars = word.toCharArray();
    Arrays.sort(chars);
    String key = new String(chars);
    groups.computeIfAbsent(key, k -> new ArrayList<>()).add(word);
}

// Pattern 4: Track first occurrence index
Map<Integer, Integer> firstSeen = new HashMap<>();
for (int i = 0; i < nums.length; i++) {
    if (!firstSeen.containsKey(nums[i])) firstSeen.put(nums[i], i);
}

// Pattern 5: Adjacency list (graph)
Map<Integer, List<Integer>> adj = new HashMap<>();
for (int[] edge : edges) {
    adj.computeIfAbsent(edge[0], k -> new ArrayList<>()).add(edge[1]);
    adj.computeIfAbsent(edge[1], k -> new ArrayList<>()).add(edge[0]);
}

// Pattern 6: Count subarrays with target sum (prefix sum + hashmap)
Map<Integer, Integer> prefixCount = new HashMap<>();
prefixCount.put(0, 1);  // empty subarray has sum 0
int sum = 0, count = 0;
for (int n : nums) {
    sum += n;
    count += prefixCount.getOrDefault(sum - target, 0);
    prefixCount.put(sum, prefixCount.getOrDefault(sum, 0) + 1);
}
```

---

## LinkedHashMap

```java
// Maintains insertion order
Map<String, Integer> lhm = new LinkedHashMap<>();
lhm.put("c", 3);
lhm.put("a", 1);
lhm.put("b", 2);
// Iteration order: c, a, b (insertion order)

// Access order (most recently accessed last) — LRU Cache foundation
Map<Integer, Integer> lru = new LinkedHashMap<>(16, 0.75f, true);
// access-ordered: get() moves key to end

// LRU Cache with LinkedHashMap (FAANG favorite)
class LRUCache extends LinkedHashMap<Integer, Integer> {
    private final int capacity;

    public LRUCache(int capacity) {
        super(capacity, 0.75f, true);  // access-order
        this.capacity = capacity;
    }

    public int get(int key) {
        return super.getOrDefault(key, -1);
    }

    public void put(int key, int value) {
        super.put(key, value);
    }

    @Override
    protected boolean removeEldestEntry(Map.Entry<Integer, Integer> eldest) {
        return size() > capacity;
    }
}
```

---

## TreeMap

### Internal Working

```
TreeMap = Red-Black Tree (self-balancing BST)
- Keys are stored in sorted order
- All operations: O(log n)
- Allows range queries (floorKey, ceilingKey, subMap)
```

### Time Complexity

| Operation | Complexity |
|-----------|-----------|
| `put(k, v)` | O(log n) |
| `get(k)` | O(log n) |
| `remove(k)` | O(log n) |
| `containsKey(k)` | O(log n) |
| `firstKey()` / `lastKey()` | O(log n) |
| `floorKey(k)` / `ceilingKey(k)` | O(log n) |
| Iteration | O(n) |

```java
TreeMap<Integer, String> tree = new TreeMap<>();
tree.put(5, "five");
tree.put(1, "one");
tree.put(3, "three");
tree.put(7, "seven");

// Sorted iteration
for (Map.Entry<Integer, String> e : tree.entrySet()) {
    System.out.println(e.getKey() + ": " + e.getValue());
}
// 1:one, 3:three, 5:five, 7:seven

// NavigableMap operations (unique to TreeMap)
tree.firstKey();          // 1 (smallest)
tree.lastKey();           // 7 (largest)
tree.floorKey(4);         // 3 (largest key <= 4)
tree.ceilingKey(4);       // 5 (smallest key >= 4)
tree.lowerKey(5);         // 3 (strictly less than 5)
tree.higherKey(5);        // 7 (strictly greater than 5)
tree.pollFirstEntry();    // removes and returns entry with smallest key
tree.pollLastEntry();     // removes and returns entry with largest key

// SubMap operations (range queries)
tree.subMap(1, true, 5, true);   // keys in [1, 5] inclusive
tree.headMap(5);                  // keys strictly less than 5
tree.tailMap(3);                  // keys >= 3
tree.descendingMap();             // reverse order view
tree.descendingKeySet();          // reverse order keys

// Use case: find k-th smallest sum, sliding window maximum
// Use case: count smaller numbers — TreeMap + rank
```

### TreeMap DSA Patterns

```java
// Pattern 1: Range counting
TreeMap<Integer, Integer> freqMap = new TreeMap<>();
// How many keys in range [lo, hi]?
int count = freqMap.subMap(lo, true, hi, true).values().stream()
                   .mapToInt(Integer::intValue).sum();

// Pattern 2: Sliding window maximum (monotonic approach usually better, but TreeMap works)
TreeMap<Integer, Integer> window = new TreeMap<>();
for (int val : nums) {
    window.merge(val, 1, Integer::sum);
    if (window.size() > k) {
        // remove oldest element
    }
    window.lastKey();  // current maximum
}

// Pattern 3: Difference array problems
TreeMap<Integer, Integer> diff = new TreeMap<>();
// Book a room from start to end:
diff.merge(start, 1, Integer::sum);
diff.merge(end, -1, Integer::sum);
// Check if all slots free: scan prefix sum

// Pattern 4: Coordinate compression
TreeMap<Integer, Integer> compress = new TreeMap<>();
int rank = 0;
for (int val : sortedUniqueValues) compress.put(val, rank++);
```

---

## HashMap vs TreeMap vs LinkedHashMap

| | HashMap | TreeMap | LinkedHashMap |
|-|---------|---------|---------------|
| Order | None | Sorted by key | Insertion order |
| Get/Put/Remove | O(1) avg | O(log n) | O(1) avg |
| null keys | 1 allowed | Not allowed | 1 allowed |
| Thread safe | No | No | No |
| Use when | Fast lookup | Sorted order needed, range queries | Maintain insertion order |

> **Interview Tip:** "Should I use HashMap or TreeMap?" — if you need sorted keys or range queries, TreeMap. Otherwise, HashMap. This distinction alone wins you points.
