# Section 2.1 — List: ArrayList and LinkedList

---

## The List Interface

```java
// List is an interface — ArrayList and LinkedList are implementations
List<Integer> list = new ArrayList<>();    // most common
List<Integer> list2 = new LinkedList<>();  // use when frequent head/tail ops

// Common operations (both implementations)
list.add(10);              // append to end
list.add(0, 5);            // insert at index 0
list.get(0);               // get by index
list.set(0, 100);          // update at index
list.remove(0);            // remove by index (returns removed element)
list.remove(Integer.valueOf(10));  // remove by value (must box int → Integer)
list.size();               // number of elements
list.isEmpty();            // true if size == 0
list.contains(10);         // O(n) linear search
list.indexOf(10);          // first occurrence index (-1 if not found)
list.lastIndexOf(10);      // last occurrence index
list.clear();              // remove all elements
```

---

## ArrayList

### Internal Working

```
ArrayList = dynamic array
- Backed by: Object[] array
- Initial capacity: 10 (default)
- Growth factor: 1.5x when full (newCapacity = oldCapacity + (oldCapacity >> 1))
- When full: new array allocated, all elements copied — O(n) operation
- Amortized append: O(1) (occasional resize)
```

### Time Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| `add(e)` | O(1) amortized | O(n) on resize |
| `add(i, e)` | O(n) | Shifts elements right |
| `get(i)` | O(1) | Direct array access |
| `set(i, e)` | O(1) | Direct array update |
| `remove(i)` | O(n) | Shifts elements left |
| `contains(e)` | O(n) | Linear scan |
| `indexOf(e)` | O(n) | Linear scan |
| `size()` | O(1) | Cached field |

### Complete ArrayList API

```java
import java.util.*;

List<Integer> list = new ArrayList<>();

// Adding elements
list.add(1);               // [1]
list.add(2);               // [1, 2]
list.add(3);               // [1, 2, 3]
list.add(0, 0);            // [0, 1, 2, 3] — O(n)
list.addAll(Arrays.asList(4, 5, 6));  // [0, 1, 2, 3, 4, 5, 6]
list.addAll(2, Arrays.asList(10, 11)); // insert at index 2

// Accessing elements
list.get(0);               // 0
list.size();               // size
list.isEmpty();            // false

// Modifying elements
list.set(0, 99);           // replace index 0 with 99

// Removing elements
list.remove(0);            // remove by index, returns removed element
list.remove(Integer.valueOf(99)); // remove by value (first occurrence)
list.removeAll(Arrays.asList(1, 2)); // remove all matching
list.retainAll(Arrays.asList(3, 4)); // keep only these values

// Searching
list.contains(3);          // true
list.indexOf(3);           // first occurrence
list.lastIndexOf(3);       // last occurrence

// Sorting
Collections.sort(list);                        // ascending
Collections.sort(list, Collections.reverseOrder()); // descending
list.sort((a, b) -> b - a);                   // lambda comparator

// Sub-list (view, not copy — modifications affect original)
List<Integer> sub = list.subList(1, 4);  // [1, 4) elements

// Convert to array
Object[] arr = list.toArray();
Integer[] intArr = list.toArray(new Integer[0]);
int[] primitiveArr = list.stream().mapToInt(Integer::intValue).toArray();

// Create from array
List<Integer> fromArr = Arrays.asList(1, 2, 3);    // Fixed size!
List<Integer> mutable = new ArrayList<>(Arrays.asList(1, 2, 3)); // Mutable

// Immutable list (Java 9+)
List<Integer> immutable = List.of(1, 2, 3);  // cannot add/remove/set

// Iterate
for (int val : list) { }
list.forEach(System.out::println);
Iterator<Integer> it = list.iterator();
while (it.hasNext()) {
    int val = it.next();
    if (val < 0) it.remove();  // safe removal during iteration
}

// Capacity management (optimization)
ArrayList<Integer> al = new ArrayList<>(1000);  // pre-allocate capacity
al.ensureCapacity(2000);  // grow if needed
al.trimToSize();          // release unused memory
```

### DSA Patterns with ArrayList

```java
// Dynamic array as stack
List<Integer> stack = new ArrayList<>();
stack.add(val);                          // push
stack.remove(stack.size() - 1);         // pop (O(1))
stack.get(stack.size() - 1);            // peek (O(1))

// Building result list during DFS/BFS
List<Integer> path = new ArrayList<>();
path.add(node.val);
// ... recurse ...
path.remove(path.size() - 1);  // backtrack

// Frequency counting with List
List<Integer>[] buckets = new ArrayList[n + 1];
for (int i = 0; i <= n; i++) buckets[i] = new ArrayList<>();
buckets[freq[i]].add(i);

// 2D result
List<List<Integer>> result = new ArrayList<>();
List<Integer> row = new ArrayList<>();
row.add(1); row.add(2);
result.add(row);
```

---

## LinkedList

### Internal Working

```
LinkedList = doubly linked list
- Each node has: data, prev pointer, next pointer
- No array backing — pure node chain
- Head and tail pointers maintained
- No capacity/resize overhead
- Implements both List and Deque interfaces
```

### Time Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| `addFirst(e)` / `addLast(e)` | O(1) | Head/tail pointers |
| `add(e)` | O(1) | Add to tail |
| `add(i, e)` | O(n) | Must traverse to index |
| `get(i)` | O(n) | Must traverse to index |
| `removeFirst()` / `removeLast()` | O(1) | Head/tail pointers |
| `remove(i)` | O(n) | Must traverse + O(1) removal |
| `contains(e)` | O(n) | Linear scan |

### When to Use LinkedList vs ArrayList

| Use ArrayList when | Use LinkedList when |
|-------------------|---------------------|
| Random access needed (O(1) get) | Frequent head insertions/deletions |
| Memory efficiency matters | Implementing queue/deque |
| Most operations are at end | Frequent insertions in middle (if you have the node) |
| Cache-friendly iteration | Order of insertion matters, no index access |

**In practice:** ArrayList is preferred 90% of the time. Use ArrayDeque for queue/stack operations.

```java
// LinkedList as Deque (double-ended queue)
LinkedList<Integer> deque = new LinkedList<>();
deque.addFirst(1);     // add to head
deque.addLast(2);      // add to tail
deque.removeFirst();   // remove from head
deque.removeLast();    // remove from tail
deque.peekFirst();     // head without removal
deque.peekLast();      // tail without removal

// Manual LinkedList implementation (for interviews)
class MyLinkedList {
    private static class Node {
        int val;
        Node next;
        Node(int val) { this.val = val; }
    }

    private Node head;
    private int size;

    public void addAtHead(int val) {
        Node node = new Node(val);
        node.next = head;
        head = node;
        size++;
    }

    public void addAtTail(int val) {
        if (head == null) { addAtHead(val); return; }
        Node curr = head;
        while (curr.next != null) curr = curr.next;
        curr.next = new Node(val);
        size++;
    }

    public int get(int index) {
        if (index < 0 || index >= size) return -1;
        Node curr = head;
        for (int i = 0; i < index; i++) curr = curr.next;
        return curr.val;
    }

    public void deleteAtIndex(int index) {
        if (index < 0 || index >= size) return;
        if (index == 0) { head = head.next; size--; return; }
        Node curr = head;
        for (int i = 0; i < index - 1; i++) curr = curr.next;
        curr.next = curr.next.next;
        size--;
    }
}
```

---

## Interview Traps and Tips

```java
// Trap 1: ConcurrentModificationException
List<Integer> list = new ArrayList<>(Arrays.asList(1, 2, 3, 4));
for (int val : list) {
    if (val % 2 == 0) list.remove(Integer.valueOf(val));  // THROWS CME!
}
// Fix: use Iterator.remove() or removeIf
list.removeIf(val -> val % 2 == 0);  // Java 8+ cleanest way

// Trap 2: Arrays.asList returns fixed-size List
List<Integer> fixed = Arrays.asList(1, 2, 3);
fixed.add(4);  // THROWS UnsupportedOperationException!
// Fix:
List<Integer> mutable = new ArrayList<>(Arrays.asList(1, 2, 3));

// Trap 3: remove(int) vs remove(Object)
List<Integer> list2 = new ArrayList<>(Arrays.asList(1, 2, 3));
list2.remove(1);                // removes INDEX 1 → list becomes [1, 3]
list2.remove(Integer.valueOf(1)); // removes VALUE 1 → list becomes [2, 3]

// Trap 4: subList is a view
List<Integer> original = new ArrayList<>(Arrays.asList(1, 2, 3, 4, 5));
List<Integer> sub = original.subList(1, 4);  // [2, 3, 4]
sub.set(0, 99);  // also modifies original! original = [1, 99, 3, 4, 5]
// To get independent copy:
List<Integer> copy = new ArrayList<>(original.subList(1, 4));
```

---

## Complexity Summary

| | ArrayList | LinkedList |
|-|-----------|------------|
| Access by index | O(1) | O(n) |
| Insert/Delete at end | O(1) amortized | O(1) |
| Insert/Delete at head | O(n) | O(1) |
| Insert/Delete in middle | O(n) | O(n) |
| Memory overhead | Low (array) | High (2 pointers per node) |
| Cache performance | Excellent | Poor (random memory) |
