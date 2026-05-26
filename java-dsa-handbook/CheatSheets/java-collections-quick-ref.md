# Java Collections Quick Reference

## Initialization One-Liners

```java
// Lists
List<Integer> list = new ArrayList<>();
List<Integer> list = new ArrayList<>(Arrays.asList(1, 2, 3));
List<Integer> list = List.of(1, 2, 3);  // immutable
List<Integer> list = Collections.nCopies(n, 0);

// Maps
Map<Integer, Integer> map = new HashMap<>();
Map<Integer, List<Integer>> adj = new HashMap<>();
Map<Character, Integer> freq = new HashMap<>();

// Sets
Set<Integer> set = new HashSet<>();
Set<Integer> set = new HashSet<>(Arrays.asList(1, 2, 3));

// Stack / Queue
Deque<Integer> stack = new ArrayDeque<>();
Queue<Integer> queue = new ArrayDeque<>();
Deque<Integer> deque = new ArrayDeque<>();

// Priority Queues
PriorityQueue<Integer> minPQ = new PriorityQueue<>();
PriorityQueue<Integer> maxPQ = new PriorityQueue<>(Collections.reverseOrder());
PriorityQueue<int[]> pqBySecond = new PriorityQueue<>((a,b) -> a[1]-b[1]);
```

## Common 1-Liners for DSA

```java
// Frequency map
Map<T, Integer> freq = new HashMap<>();
for (T item : arr) freq.merge(item, 1, Integer::sum);

// Sort descending
Arrays.sort(arr, Collections.reverseOrder()); // Integer[] only
list.sort(Comparator.reverseOrder());

// Max/min in array
int max = Arrays.stream(arr).max().getAsInt();
int min = IntStream.of(arr).min().getAsInt();

// Sum of array
int sum = IntStream.of(arr).sum();

// int[] to List<Integer>
List<Integer> list = IntStream.of(arr).boxed().collect(Collectors.toList());

// List<Integer> to int[]
int[] arr = list.stream().mapToInt(Integer::intValue).toArray();

// Prefix sum
int[] prefix = new int[n+1];
for(int i=0;i<n;i++) prefix[i+1]=prefix[i]+arr[i];

// Fill 2D array
int[][] dp = new int[m][n];
for(int[] row : dp) Arrays.fill(row, -1);
```

## Stack / Queue API

```java
// STACK (ArrayDeque)
stack.push(val)              // push to top
stack.pop()                  // remove top
stack.peek()                 // view top (null if empty)
stack.isEmpty()
stack.size()

// QUEUE (ArrayDeque)
queue.offer(val)             // enqueue
queue.poll()                 // dequeue (null if empty)
queue.peek()                 // view front
queue.isEmpty()
queue.size()

// DEQUE (ArrayDeque)
deque.addFirst(val) / deque.offerFirst(val)
deque.addLast(val)  / deque.offerLast(val)
deque.pollFirst()   // remove from head
deque.pollLast()    // remove from tail
deque.peekFirst()
deque.peekLast()
```

## Critical Java Gotchas

```java
// 1. Integer comparison: use equals() or Integer.compare()
Integer a = 128, b = 128;
a == b      // FALSE (beyond cache range)
a.equals(b) // TRUE

// 2. int[] sort vs Integer[] sort
int[] arr = {3,1,2};
Arrays.sort(arr);                           // ascending only
Integer[] arr2 = {3,1,2};
Arrays.sort(arr2, (a,b) -> b-a);          // can use comparator

// 3. Remove by index vs value in List
list.remove(0);                     // removes element at INDEX 0
list.remove(Integer.valueOf(0));    // removes element with VALUE 0

// 4. HashMap default behavior
map.getOrDefault(key, 0);          // safe default
map.computeIfAbsent(key, k -> new ArrayList<>()).add(val); // safe add to list

// 5. String immutability
String s = "hello";
s.concat(" world");  // s is UNCHANGED — must reassign
s = s + " world";    // creates new String
StringBuilder sb = new StringBuilder(s); // for mutation

// 6. Arrays.asList() returns fixed-size
List<Integer> fixed = Arrays.asList(1, 2, 3);
fixed.add(4); // THROWS UnsupportedOperationException!
new ArrayList<>(Arrays.asList(1,2,3)); // Mutable copy

// 7. Modulo negative numbers
int result = -7 % 3;  // = -1 in Java (NOT 2!)
int positive = ((n % m) + m) % m; // always positive
```
