# Section 2.3 — Set: HashSet and TreeSet

---

## The Set Interface

```java
// Set: collection with NO duplicates
Set<Integer> hashSet = new HashSet<>();      // unordered, O(1) ops
Set<Integer> treeSet = new TreeSet<>();      // sorted, O(log n)
Set<Integer> linkedSet = new LinkedHashSet<>(); // insertion order

// Core operations
set.add(10);           // adds if not present
set.remove(10);        // removes if present
set.contains(10);      // O(1) for HashSet, O(log n) for TreeSet
set.size();
set.isEmpty();
set.clear();
```

---

## HashSet

### Internal Working

```
HashSet = HashMap internally (key → dummy PRESENT object)
- All HashSet operations delegate to an internal HashMap
- add(e) → map.put(e, PRESENT)
- contains(e) → map.containsKey(e)
- remove(e) → map.remove(e)

Same characteristics as HashMap:
- Unordered
- O(1) avg for add/remove/contains
- Allows one null
- Not thread-safe
```

### Time Complexity

| Operation | Complexity |
|-----------|-----------|
| `add(e)` | O(1) avg |
| `remove(e)` | O(1) avg |
| `contains(e)` | O(1) avg |
| `size()` | O(1) |
| Iteration | O(n) |

### Complete HashSet API

```java
Set<Integer> set = new HashSet<>();
Set<Integer> set2 = new HashSet<>(Arrays.asList(1, 2, 3, 4, 5));
Set<Integer> set3 = new HashSet<>(set2);  // copy constructor

// Add elements
set.add(1);     // true (added)
set.add(1);     // false (already present — no duplicate)
set.addAll(Arrays.asList(2, 3, 4));

// Check
set.contains(1);   // true
set.contains(99);  // false

// Remove
set.remove(1);          // true (removed)
set.remove(99);         // false (not present)
set.removeAll(Arrays.asList(2, 3));  // remove multiple

// Iterate (order is not guaranteed)
for (int val : set) {
    System.out.println(val);
}
set.forEach(System.out::println);

// Set operations
Set<Integer> a = new HashSet<>(Arrays.asList(1, 2, 3, 4));
Set<Integer> b = new HashSet<>(Arrays.asList(3, 4, 5, 6));

// Union
Set<Integer> union = new HashSet<>(a);
union.addAll(b);           // {1, 2, 3, 4, 5, 6}

// Intersection
Set<Integer> intersection = new HashSet<>(a);
intersection.retainAll(b); // {3, 4}

// Difference (A - B)
Set<Integer> diff = new HashSet<>(a);
diff.removeAll(b);         // {1, 2}

// Is subset?
a.containsAll(b);  // false (b has 5, 6 not in a)

// Convert to sorted list
List<Integer> sorted = new ArrayList<>(set);
Collections.sort(sorted);

// Convert to array
Integer[] arr = set.toArray(new Integer[0]);
```

### HashSet DSA Patterns

```java
// Pattern 1: Duplicate detection
public boolean hasDuplicate(int[] nums) {
    Set<Integer> seen = new HashSet<>();
    for (int n : nums) {
        if (!seen.add(n)) return true;  // add returns false if already present
    }
    return false;
}

// Pattern 2: Lookup in O(1) — convert array to set first
Set<Integer> numSet = new HashSet<>();
for (int n : nums) numSet.add(n);
if (numSet.contains(target)) { }

// Pattern 3: Longest consecutive sequence
public int longestConsecutive(int[] nums) {
    Set<Integer> numSet = new HashSet<>();
    for (int n : nums) numSet.add(n);

    int maxLen = 0;
    for (int n : numSet) {
        if (!numSet.contains(n - 1)) {  // start of sequence
            int curr = n, len = 1;
            while (numSet.contains(curr + 1)) { curr++; len++; }
            maxLen = Math.max(maxLen, len);
        }
    }
    return maxLen;
}

// Pattern 4: Two Sum with Set
public boolean twoSum(int[] nums, int target) {
    Set<Integer> seen = new HashSet<>();
    for (int n : nums) {
        if (seen.contains(target - n)) return true;
        seen.add(n);
    }
    return false;
}

// Pattern 5: Remove duplicates while preserving order
public int[] removeDuplicates(int[] nums) {
    Set<Integer> seen = new LinkedHashSet<>();
    for (int n : nums) seen.add(n);
    return seen.stream().mapToInt(Integer::intValue).toArray();
}

// Pattern 6: Character set for sliding window
Set<Character> charSet = new HashSet<>();
int left = 0, maxLen = 0;
for (int right = 0; right < s.length(); right++) {
    while (charSet.contains(s.charAt(right))) {
        charSet.remove(s.charAt(left++));
    }
    charSet.add(s.charAt(right));
    maxLen = Math.max(maxLen, right - left + 1);
}
```

---

## TreeSet

### Internal Working

```
TreeSet = TreeMap internally (element → dummy PRESENT object)
- Elements stored in a Red-Black Tree
- Sorted order maintained automatically
- NavigableSet interface allows range operations
```

### Time Complexity

| Operation | Complexity |
|-----------|-----------|
| `add(e)` | O(log n) |
| `remove(e)` | O(log n) |
| `contains(e)` | O(log n) |
| `first()` / `last()` | O(log n) |
| `floor(e)` / `ceiling(e)` | O(log n) |
| Iteration | O(n) |

```java
TreeSet<Integer> tset = new TreeSet<>(Arrays.asList(5, 1, 3, 7, 9, 2));
// Internally sorted: [1, 2, 3, 5, 7, 9]

// Navigation operations
tset.first();          // 1 (smallest)
tset.last();           // 9 (largest)
tset.floor(4);         // 3 (largest element <= 4)
tset.ceiling(4);       // 5 (smallest element >= 4)
tset.lower(5);         // 3 (strictly less than 5)
tset.higher(5);        // 7 (strictly greater than 5)
tset.pollFirst();      // 1 (removes and returns smallest)
tset.pollLast();       // 9 (removes and returns largest)

// Sub-set operations
tset.subSet(2, true, 7, true);  // [2, 3, 5, 7]
tset.headSet(5);                 // [1, 2, 3] (strictly less than 5)
tset.tailSet(5);                 // [5, 7, 9] (>= 5)
tset.descendingSet();            // reverse order view

// Custom ordering with Comparator
TreeSet<String> byLength = new TreeSet<>(
    Comparator.comparingInt(String::length).thenComparing(Comparator.naturalOrder())
);
byLength.add("banana");
byLength.add("fig");
byLength.add("apple");
// Iteration: fig, apple, banana (by length, then alphabetical)
```

### TreeSet DSA Patterns

```java
// Pattern 1: Kth smallest/largest element dynamically
// (More commonly done with PriorityQueue, but TreeSet works too)
TreeSet<Integer> sorted = new TreeSet<>();
for (int n : stream) {
    sorted.add(n);
    if (sorted.size() > k) sorted.pollLast(); // keep k smallest
}
int kthSmallest = sorted.last();

// Pattern 2: Count of elements in range
TreeSet<Integer> set = new TreeSet<>();
// Elements in [lo, hi]:
NavigableSet<Integer> sub = set.subSet(lo, true, hi, true);
int count = sub.size();

// Pattern 3: Closest value to target
TreeSet<Integer> values = new TreeSet<>();
// ... populate ...
Integer floor = values.floor(target);    // closest ≤ target
Integer ceil  = values.ceiling(target);  // closest ≥ target
// Choose closer:
int closest;
if (floor == null) closest = ceil;
else if (ceil == null) closest = floor;
else closest = (target - floor <= ceil - target) ? floor : ceil;

// Pattern 4: Meeting rooms / room scheduling
TreeSet<Integer> rooms = new TreeSet<>(); // end times of ongoing meetings
for (int[] meeting : sortedByStart) {
    if (!rooms.isEmpty() && rooms.first() <= meeting[0]) {
        rooms.pollFirst(); // reuse a room
    }
    rooms.add(meeting[1]); // assign room, track end time
}
return rooms.size(); // minimum rooms needed
```

---

## LinkedHashSet

```java
// Maintains insertion order + no duplicates
Set<Integer> lhs = new LinkedHashSet<>(Arrays.asList(3, 1, 4, 1, 5, 9));
// Iteration order: 3, 1, 4, 5, 9 (insertion order, duplicates removed)

// Use case: unique elements preserving order (like Python's dict keys)
// Use case: LRU cache (with LinkedHashMap)
```

---

## Set Comparison Summary

| | HashSet | TreeSet | LinkedHashSet |
|-|---------|---------|---------------|
| Order | None | Sorted | Insertion order |
| Add/Remove/Contains | O(1) avg | O(log n) | O(1) avg |
| null allowed | Yes (one) | No | Yes (one) |
| Navigation ops | No | Yes | No |
| Use when | Fast lookup, dedup | Sorted set, range ops | Ordered dedup |
