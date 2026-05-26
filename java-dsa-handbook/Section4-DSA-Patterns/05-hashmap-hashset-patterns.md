# Pattern 5 — HashMap / HashSet Patterns

---

## Core Insight

Hash tables provide O(1) average lookup, enabling many O(n²) problems to be solved in O(n).

**Key applications:** frequency counting, grouping, seen-before checks, complement lookups.

---

## Pattern 1: Frequency Counting

```java
// Count occurrences of each element
Map<Integer, Integer> freq = new HashMap<>();
for (int n : nums) freq.merge(n, 1, Integer::sum);

// OR with getOrDefault:
for (int n : nums) freq.put(n, freq.getOrDefault(n, 0) + 1);

// Character frequency
int[] charFreq = new int[26];
for (char c : s.toCharArray()) charFreq[c - 'a']++;

// Top K frequent elements
List<Map.Entry<Integer, Integer>> entries = new ArrayList<>(freq.entrySet());
entries.sort((a, b) -> b.getValue() - a.getValue());
```

---

## Pattern 2: Two Sum Variants

```java
// Two Sum (LC 1) — exact indices
int[] twoSum(int[] nums, int target) {
    Map<Integer, Integer> seen = new HashMap<>();  // value → index
    for (int i = 0; i < nums.length; i++) {
        int complement = target - nums[i];
        if (seen.containsKey(complement)) {
            return new int[]{seen.get(complement), i};
        }
        seen.put(nums[i], i);
    }
    return new int[]{};
}

// Two Sum II (sorted) — use two pointers instead
// Two Sum IV (BST) — use HashSet + traversal
boolean findTarget(TreeNode root, int k) {
    Set<Integer> seen = new HashSet<>();
    return dfs(root, k, seen);
}
boolean dfs(TreeNode node, int k, Set<Integer> seen) {
    if (node == null) return false;
    if (seen.contains(k - node.val)) return true;
    seen.add(node.val);
    return dfs(node.left, k, seen) || dfs(node.right, k, seen);
}
```

---

## Pattern 3: Grouping / Bucketing

```java
// Group Anagrams (LC 49)
List<List<String>> groupAnagrams(String[] strs) {
    Map<String, List<String>> groups = new HashMap<>();
    for (String s : strs) {
        char[] chars = s.toCharArray();
        Arrays.sort(chars);
        String key = new String(chars);
        groups.computeIfAbsent(key, k -> new ArrayList<>()).add(s);
    }
    return new ArrayList<>(groups.values());
}

// Alternative key without sorting (faster):
String getKey(String s) {
    int[] freq = new int[26];
    for (char c : s.toCharArray()) freq[c - 'a']++;
    return Arrays.toString(freq);  // "#2#0#0#..." style key
}
```

---

## Pattern 4: Seen-Before / Duplicate Detection

```java
// Contains Duplicate (LC 217)
boolean containsDuplicate(int[] nums) {
    Set<Integer> seen = new HashSet<>();
    for (int n : nums) {
        if (!seen.add(n)) return true;  // add returns false if already present
    }
    return false;
}

// Contains Duplicate II (LC 219) — within k distance
boolean containsNearbyDuplicate(int[] nums, int k) {
    Map<Integer, Integer> indexMap = new HashMap<>();
    for (int i = 0; i < nums.length; i++) {
        if (indexMap.containsKey(nums[i]) && i - indexMap.get(nums[i]) <= k) {
            return true;
        }
        indexMap.put(nums[i], i);
    }
    return false;
}
```

---

## Pattern 5: Complement Pattern

```java
// Find all pairs with difference = k
List<int[]> findPairsWithDiff(int[] nums, int k) {
    Set<Integer> numSet = new HashSet<>();
    Set<String> seen = new HashSet<>();
    List<int[]> result = new ArrayList<>();

    for (int n : nums) numSet.add(n);

    for (int n : nums) {
        int complement = n - k;
        if (numSet.contains(complement) && complement != n) {
            String key = Math.min(n, complement) + "," + Math.max(n, complement);
            if (seen.add(key)) result.add(new int[]{complement, n});
        }
    }
    return result;
}
```

---

## Pattern 6: LRU Cache (Design Problem)

```java
// LRU Cache (LC 146) — O(1) get and put
class LRUCache {
    private final int capacity;
    private final Map<Integer, Node> map;
    private final Node head, tail;  // dummy head and tail

    static class Node {
        int key, val;
        Node prev, next;
        Node(int k, int v) { key = k; val = v; }
    }

    public LRUCache(int capacity) {
        this.capacity = capacity;
        map = new HashMap<>();
        head = new Node(0, 0);
        tail = new Node(0, 0);
        head.next = tail;
        tail.prev = head;
    }

    public int get(int key) {
        if (!map.containsKey(key)) return -1;
        Node node = map.get(key);
        remove(node);
        insertToFront(node);
        return node.val;
    }

    public void put(int key, int value) {
        if (map.containsKey(key)) {
            remove(map.get(key));
        }
        if (map.size() == capacity) {
            Node lru = tail.prev;  // least recently used
            remove(lru);
            map.remove(lru.key);
        }
        Node node = new Node(key, value);
        insertToFront(node);
        map.put(key, node);
    }

    private void remove(Node node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }

    private void insertToFront(Node node) {
        node.next = head.next;
        node.prev = head;
        head.next.prev = node;
        head.next = node;
    }
}

// Simpler implementation using LinkedHashMap:
class LRUCacheSimple extends LinkedHashMap<Integer, Integer> {
    private final int capacity;

    public LRUCacheSimple(int capacity) {
        super(capacity, 0.75f, true);  // true = access order
        this.capacity = capacity;
    }

    public int get(int key) { return super.getOrDefault(key, -1); }
    public void put(int key, int value) { super.put(key, value); }

    @Override
    protected boolean removeEldestEntry(Map.Entry<Integer, Integer> eldest) {
        return size() > capacity;
    }
}
```

---

## Pattern 7: Isomorphic / Pattern Matching

```java
// Isomorphic Strings (LC 205)
boolean isIsomorphic(String s, String t) {
    Map<Character, Character> sToT = new HashMap<>();
    Map<Character, Character> tToS = new HashMap<>();

    for (int i = 0; i < s.length(); i++) {
        char sc = s.charAt(i), tc = t.charAt(i);

        if (sToT.containsKey(sc) && sToT.get(sc) != tc) return false;
        if (tToS.containsKey(tc) && tToS.get(tc) != sc) return false;

        sToT.put(sc, tc);
        tToS.put(tc, sc);
    }
    return true;
}

// Word Pattern (LC 290)
boolean wordPattern(String pattern, String s) {
    String[] words = s.split(" ");
    if (pattern.length() != words.length) return false;

    Map<Character, String> charToWord = new HashMap<>();
    Map<String, Character> wordToChar = new HashMap<>();

    for (int i = 0; i < pattern.length(); i++) {
        char p = pattern.charAt(i);
        String w = words[i];

        if (charToWord.containsKey(p) && !charToWord.get(p).equals(w)) return false;
        if (wordToChar.containsKey(w) && wordToChar.get(w) != p) return false;

        charToWord.put(p, w);
        wordToChar.put(w, p);
    }
    return true;
}
```

---

## Complexity Summary

| Operation | HashMap | HashSet |
|-----------|---------|---------|
| Insert | O(1) avg | O(1) avg |
| Lookup | O(1) avg | O(1) avg |
| Delete | O(1) avg | O(1) avg |
| Iterate | O(n) | O(n) |
| Space | O(n) | O(n) |

> **Interview Tip:** "I'll use a HashMap to trade space for time" — this is one of the most frequent optimizations in interviews. Master the frequency map pattern and its variants.
