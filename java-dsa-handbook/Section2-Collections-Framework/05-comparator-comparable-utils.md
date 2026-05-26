# Section 2.5 — Comparator, Comparable, and Collections Utilities

---

## 1. Comparable Interface

```java
// Comparable: "I know how to compare myself to another of my type"
// Used for natural ordering — the default sort order

class Student implements Comparable<Student> {
    String name;
    int gpa;
    int age;

    Student(String name, int gpa, int age) {
        this.name = name;
        this.gpa = gpa;
        this.age = age;
    }

    @Override
    public int compareTo(Student other) {
        // Return negative: this < other
        // Return 0: this == other
        // Return positive: this > other

        // Sort by GPA descending, then name ascending
        if (this.gpa != other.gpa) return other.gpa - this.gpa;
        return this.name.compareTo(other.name);
    }

    @Override
    public String toString() {
        return name + "(" + gpa + ")";
    }
}

// Usage
List<Student> students = new ArrayList<>();
students.add(new Student("Alice", 90, 20));
students.add(new Student("Bob", 95, 22));
students.add(new Student("Charlie", 90, 21));

Collections.sort(students);  // uses compareTo
// Result: [Bob(95), Alice(90), Charlie(90)] — by GPA desc, then name asc

// compareTo contract:
// 1. sgn(x.compareTo(y)) == -sgn(y.compareTo(x))
// 2. Transitive: if x.compareTo(y) > 0 and y.compareTo(z) > 0 → x.compareTo(z) > 0
// 3. Consistency: x.compareTo(y) == 0 → x.equals(y) (strongly recommended)
```

---

## 2. Comparator Interface

```java
// Comparator: external comparison logic (doesn't touch the class)
// More flexible than Comparable — can have multiple comparators

class Student {
    String name;
    int gpa;
    int age;
    // ... constructor, getters ...
}

// Old style (anonymous inner class)
Comparator<Student> byGpa = new Comparator<Student>() {
    @Override
    public int compare(Student a, Student b) {
        return b.gpa - a.gpa;  // descending
    }
};

// Lambda style (Java 8+)
Comparator<Student> byGpa = (a, b) -> b.gpa - a.gpa;
Comparator<Student> byName = (a, b) -> a.name.compareTo(b.name);
Comparator<Student> byAge = Comparator.comparingInt(s -> s.age);

// Chained comparators
Comparator<Student> combined = Comparator
    .comparingInt((Student s) -> s.gpa).reversed()  // desc GPA
    .thenComparing(s -> s.name)                      // asc name
    .thenComparingInt(s -> s.age);                   // asc age

// Usage
students.sort(byGpa);
Arrays.sort(arr, byGpa);
PriorityQueue<Student> pq = new PriorityQueue<>(byGpa);
TreeSet<Student> tset = new TreeSet<>(byGpa);
```

### Comparator Factory Methods (Java 8+)

```java
// Comparator.comparing — for any key
Comparator<String> byLength = Comparator.comparingInt(String::length);
Comparator<String> alphabetical = Comparator.comparing(Function.identity());
Comparator<String> natural = Comparator.naturalOrder();
Comparator<String> reverse = Comparator.reverseOrder();
Comparator<String> nullFirst = Comparator.nullsFirst(Comparator.naturalOrder());
Comparator<String> nullLast = Comparator.nullsLast(Comparator.naturalOrder());

// Chaining with thenComparing
Comparator<int[]> byFirst = Comparator.comparingInt((int[] a) -> a[0]);
Comparator<int[]> byFirstThenSecond = byFirst.thenComparingInt(a -> a[1]);

// Reversing
Comparator<Integer> descInt = Comparator.reverseOrder();
Comparator<Student> descGpa = Comparator.comparingInt(Student::getGpa).reversed();
```

### Critical Comparator Patterns for Interviews

```java
// 1. Sort intervals by start time
Arrays.sort(intervals, (a, b) -> a[0] - b[0]);

// 2. Sort by length, then lexicographically
Arrays.sort(words, (a, b) -> a.length() != b.length() ?
            a.length() - b.length() : a.compareTo(b));

// 3. Custom sort for frequency problems
// Sort by frequency desc, then value asc
int[] result = freq.entrySet().stream()
    .sorted(Map.Entry.<Integer, Integer>comparingByValue().reversed()
        .thenComparingByKey())
    .limit(k)
    .mapToInt(Map.Entry::getKey)
    .toArray();

// 4. Negative sort trick — beware of integer overflow!
// BAD (can overflow):
Comparator<Integer> bad = (a, b) -> b - a;

// SAFE:
Comparator<Integer> safe = (a, b) -> Integer.compare(b, a);
Comparator<Integer> safe2 = Collections.reverseOrder();

// When is (b - a) SAFE? Only when a,b are small ints that can't overflow.
// General rule: always use Integer.compare() for safety.

// 5. Sort 2D array
int[][] matrix = {{3,2}, {1,4}, {3,0}, {1,2}};
Arrays.sort(matrix, (a, b) -> a[0] != b[0] ? a[0] - b[0] : a[1] - b[1]);
```

---

## 3. Collections Utility Class

```java
import java.util.Collections;

List<Integer> list = new ArrayList<>(Arrays.asList(3, 1, 4, 1, 5, 9, 2, 6));

// Sorting
Collections.sort(list);                         // ascending — [1,1,2,3,4,5,6,9]
Collections.sort(list, Collections.reverseOrder()); // descending — [9,6,5,4,3,2,1,1]

// Searching (binary search — list must be sorted)
int idx = Collections.binarySearch(list, 5);    // index of 5 (or negative)
// If not found: returns -(insertion point) - 1

// Min/Max
Collections.min(list);   // 1
Collections.max(list);   // 9
Collections.min(list, Comparator.reverseOrder());  // with comparator

// Frequency
Collections.frequency(list, 1);  // 2 (count of 1s)

// Reverse
Collections.reverse(list);       // reverse in-place

// Shuffle
Collections.shuffle(list);       // random order
Collections.shuffle(list, new Random(42));  // with seed

// Fill
Collections.fill(list, 0);       // fill all with 0

// Copy
List<Integer> dest = new ArrayList<>(Collections.nCopies(list.size(), 0));
Collections.copy(dest, list);    // copy list into dest (dest must be same size)

// Swap
Collections.swap(list, 0, list.size() - 1);  // swap first and last

// Rotate
Collections.rotate(list, 2);    // rotate right by 2

// Disjoint
Collections.disjoint(list1, list2);  // true if no common elements

// Unmodifiable wrappers
List<Integer> unmod = Collections.unmodifiableList(list);
Set<Integer> unmodSet = Collections.unmodifiableSet(set);
Map<K, V> unmodMap = Collections.unmodifiableMap(map);

// Synchronized wrappers (thread-safe, but usually use ConcurrentHashMap instead)
List<Integer> syncList = Collections.synchronizedList(list);

// Empty and singleton
List<Integer> empty = Collections.emptyList();   // immutable empty list
List<Integer> single = Collections.singletonList(42); // immutable single-element

// nCopies
List<Integer> zeros = Collections.nCopies(5, 0);  // [0, 0, 0, 0, 0]
```

---

## 4. Arrays Utility

```java
import java.util.Arrays;

// Covered in Section 1 but key points:
int[] arr = {5, 2, 8, 1, 9};

Arrays.sort(arr);                    // [1, 2, 5, 8, 9] — in-place
Arrays.sort(arr, 1, 4);             // sort subarray [1,4)
Arrays.binarySearch(arr, 5);        // works only on sorted array
Arrays.fill(arr, 0);
Arrays.copyOf(arr, 3);              // [1, 2, 5]
Arrays.copyOfRange(arr, 1, 4);      // [2, 5, 8]
Arrays.equals(arr1, arr2);
Arrays.toString(arr);               // "[1, 2, 5, 8, 9]"
Arrays.deepToString(matrix);        // for 2D arrays

// Sort object array with comparator
Integer[] arr2 = {5, 2, 8, 1, 9};
Arrays.sort(arr2, Comparator.reverseOrder());

// Parallel sort (for large arrays)
Arrays.parallelSort(arr);           // uses fork/join framework

// stream
Arrays.stream(arr).sum();
Arrays.stream(arr).max().getAsInt();
Arrays.stream(arr).filter(n -> n > 3).toArray();
```

---

## 5. Interview-Ready Quick Reference

```java
// Most common operations cheat sheet

// Frequency map
Map<T, Integer> freq = new HashMap<>();
for (T item : collection) freq.merge(item, 1, Integer::sum);

// Sort with custom comparator
list.sort(Comparator.comparingInt(obj -> obj.field));

// Find max/min in list
int max = Collections.max(list);
int min = list.stream().mapToInt(Integer::intValue).min().getAsInt();

// Convert between types
int[] arr = list.stream().mapToInt(Integer::intValue).toArray();
List<Integer> list = new ArrayList<>(Arrays.asList(arr)); // won't work for int[]
List<Integer> list = IntStream.of(arr).boxed().collect(Collectors.toList());
Integer[] intArr = list.toArray(new Integer[0]);

// Reverse array
int[] arr = {1, 2, 3, 4, 5};
for (int i = 0, j = arr.length - 1; i < j; i++, j--) {
    int tmp = arr[i]; arr[i] = arr[j]; arr[j] = tmp;
}

// Swap in array
int tmp = arr[i]; arr[i] = arr[j]; arr[j] = tmp;

// Fill 2D array
for (int[] row : dp) Arrays.fill(row, -1);
// Or:
int[][] dp = new int[m][n];
for (int[] row : dp) Arrays.fill(row, Integer.MAX_VALUE);
```

---

## Cheat Sheet: Which Collection to Use?

| Requirement | Use |
|-------------|-----|
| Fast lookup by key | `HashMap` |
| Sorted keys, range ops | `TreeMap` |
| Preserve insertion order | `LinkedHashMap` |
| Fast membership check | `HashSet` |
| Sorted unique elements | `TreeSet` |
| Dynamic array, random access | `ArrayList` |
| Frequent head/tail ops | `ArrayDeque` |
| Min/Max element | `PriorityQueue` |
| LIFO (stack) | `ArrayDeque` (as stack) |
| FIFO (queue) | `ArrayDeque` (as queue) |
| Both ends | `ArrayDeque` (as deque) |
| Sliding window max/min | `ArrayDeque` (monotonic) |
| Top-K elements | `PriorityQueue` (size K) |
| Shortest path | `PriorityQueue` (Dijkstra) |
| Median stream | Two `PriorityQueue`s |
