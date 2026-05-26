# Section 1.5 — Generics, Lambda Expressions, and Streams

---

## 1. Lambda Expressions (Java 8+)

> Lambdas replace anonymous inner classes for functional interfaces. Essential for sorting, filtering, and custom comparators in interviews.

### Syntax

```java
// Old way (anonymous inner class)
Comparator<Integer> oldComp = new Comparator<Integer>() {
    @Override
    public int compare(Integer a, Integer b) {
        return a - b;
    }
};

// Lambda way
Comparator<Integer> comp = (a, b) -> a - b;

// Lambda forms
() -> expression                     // no args
(x) -> expression                    // one arg
(x, y) -> expression                 // two args
(x, y) -> { statement1; statement2; return result; }  // block body
```

### Lambda in Sorting (Most Common DSA Use)

```java
// Sort integers descending
Integer[] arr = {3, 1, 4, 1, 5, 9};
Arrays.sort(arr, (a, b) -> b - a);  // descending

// WARNING: (b - a) can overflow for large values. Use Integer.compare instead:
Arrays.sort(arr, (a, b) -> Integer.compare(b, a));  // safe descending

// Sort strings by length
String[] words = {"banana", "fig", "apple", "kiwi"};
Arrays.sort(words, (a, b) -> a.length() - b.length());

// Sort 2D array by first element, then second
int[][] points = {{1,2}, {1,0}, {2,1}};
Arrays.sort(points, (a, b) -> a[0] != b[0] ? a[0] - b[0] : a[1] - b[1]);

// Sort by multiple criteria (chain comparators)
List<String> names = Arrays.asList("Bob", "Alice", "Charlie", "Dave", "Ann");
names.sort(Comparator.comparingInt(String::length)
           .thenComparing(Comparator.naturalOrder()));

// Sort with null safety
List<Integer> list = Arrays.asList(3, null, 1, null, 2);
list.sort(Comparator.nullsLast(Integer::compareTo));
```

### Method References

```java
// lambda: x -> System.out.println(x)
// method ref: System.out::println

// Types of method references:
// 1. Static method
Function<String, Integer> parser = Integer::parseInt;

// 2. Instance method of a specific object
String prefix = "Hello";
Predicate<String> startsWith = prefix::startsWith;

// 3. Instance method of arbitrary instance of a type
Function<String, String> toUpper = String::toUpperCase;

// 4. Constructor
Supplier<ArrayList<Integer>> listFactory = ArrayList::new;
```

---

## 2. Functional Interfaces (from java.util.function)

```java
// Predicate<T>: T → boolean
Predicate<Integer> isEven = n -> n % 2 == 0;
isEven.test(4);         // true
isEven.negate().test(4); // false
Predicate<Integer> isPositive = n -> n > 0;
isEven.and(isPositive).test(4);  // true (both)
isEven.or(isPositive).test(-2);  // true (one)

// Function<T, R>: T → R
Function<String, Integer> strLen = String::length;
strLen.apply("hello");  // 5
// Chaining: andThen, compose
Function<Integer, Integer> triple = x -> x * 3;
Function<Integer, Integer> addTen = x -> x + 10;
Function<Integer, Integer> tripleAndAdd = triple.andThen(addTen);
tripleAndAdd.apply(5);  // 25

// BiFunction<T, U, R>: (T, U) → R
BiFunction<String, Integer, String> repeat = (s, n) -> s.repeat(n);

// Supplier<T>: () → T
Supplier<List<Integer>> newList = ArrayList::new;

// Consumer<T>: T → void
Consumer<String> printer = System.out::println;
printer.accept("Hello");

// UnaryOperator<T>: T → T (special Function where input = output type)
UnaryOperator<String> trim = String::trim;

// BinaryOperator<T>: (T, T) → T
BinaryOperator<Integer> max = Math::max;
```

---

## 3. Streams (Java 8+)

> Streams allow declarative, pipeline-style data processing. Not always needed in DSA, but useful for clean code in simpler problems.

### Stream Pipeline

```java
// source → intermediate operations → terminal operation
List<Integer> nums = Arrays.asList(5, 3, 1, 4, 2, 6, 8, 7);

// Example pipeline:
int result = nums.stream()         // source
    .filter(n -> n > 3)            // intermediate: keep elements > 3
    .map(n -> n * 2)               // intermediate: double each
    .sorted()                       // intermediate: sort
    .reduce(0, Integer::sum);       // terminal: sum

System.out.println(result);  // (4*2 + 5*2 + 6*2 + 7*2 + 8*2) = 60
```

### Creating Streams

```java
// From collection
List<Integer> list = Arrays.asList(1, 2, 3);
Stream<Integer> s1 = list.stream();
Stream<Integer> s2 = list.parallelStream();  // parallel processing

// From array
int[] arr = {1, 2, 3};
IntStream is = Arrays.stream(arr);           // primitive stream (more efficient)
Stream<Integer> bs = Arrays.stream(arr).boxed(); // to object stream

// From values
Stream<String> s3 = Stream.of("a", "b", "c");

// Range streams (useful in DSA)
IntStream range = IntStream.range(0, 10);       // [0, 10)
IntStream rangeClosed = IntStream.rangeClosed(1, 10); // [1, 10]

// Generate (infinite — must use limit)
Stream<Integer> zeros = Stream.generate(() -> 0).limit(5);
Stream<Integer> seq = Stream.iterate(0, n -> n + 1).limit(10);
```

### Intermediate Operations

```java
List<String> words = Arrays.asList("hello", "world", "java", "stream");

// filter: keep elements matching predicate
words.stream().filter(s -> s.length() > 4)  // ["hello", "world", "stream"]

// map: transform each element
words.stream().map(String::toUpperCase)  // ["HELLO", "WORLD", "JAVA", "STREAM"]
words.stream().mapToInt(String::length)  // IntStream: [5, 5, 4, 6]

// flatMap: flatten nested streams
List<List<Integer>> nested = Arrays.asList(
    Arrays.asList(1, 2), Arrays.asList(3, 4)
);
nested.stream().flatMap(Collection::stream)  // [1, 2, 3, 4]

// distinct: remove duplicates
Stream.of(1, 2, 2, 3, 3, 3).distinct()  // [1, 2, 3]

// sorted
words.stream().sorted()                          // alphabetical
words.stream().sorted(Comparator.reverseOrder()) // reverse
words.stream().sorted(Comparator.comparingInt(String::length)) // by length

// limit / skip
words.stream().limit(2)   // first 2 elements
words.stream().skip(1)    // skip first 1, return rest

// peek (for debugging — same as forEach but intermediate)
words.stream().peek(System.out::println).filter(s -> s.length() > 4)
```

### Terminal Operations

```java
// collect: gather into collection
List<String> filtered = words.stream()
    .filter(s -> s.length() > 4)
    .collect(Collectors.toList());

// Collect to different collection types
Set<String> set = words.stream().collect(Collectors.toSet());
List<String> unmodifiable = words.stream().collect(Collectors.toUnmodifiableList());

// Joining strings
String joined = words.stream().collect(Collectors.joining(", "));  // "hello, world, java, stream"
String joined2 = words.stream().collect(Collectors.joining(", ", "[", "]")); // "[hello, world, ...]"

// Grouping (very useful for frequency maps)
Map<Integer, List<String>> byLength = words.stream()
    .collect(Collectors.groupingBy(String::length));
// {5=[hello, world], 4=[java], 6=[stream]}

// Counting by group
Map<Integer, Long> countByLength = words.stream()
    .collect(Collectors.groupingBy(String::length, Collectors.counting()));

// Partitioning (split into two groups)
Map<Boolean, List<String>> partition = words.stream()
    .collect(Collectors.partitioningBy(s -> s.length() > 4));
// {true=[hello, world, stream], false=[java]}

// Convert to Map
Map<String, Integer> wordLengths = words.stream()
    .collect(Collectors.toMap(
        w -> w,           // key function
        String::length    // value function
    ));

// forEach
words.stream().forEach(System.out::println);

// count
long count = words.stream().filter(s -> s.length() > 4).count();

// reduce
int sum = IntStream.rangeClosed(1, 10).reduce(0, Integer::sum);
Optional<Integer> product = IntStream.rangeClosed(1, 5).boxed()
    .reduce((a, b) -> a * b);

// min / max
Optional<String> shortest = words.stream().min(Comparator.comparingInt(String::length));
Optional<String> longest = words.stream().max(Comparator.comparingInt(String::length));

// findFirst / findAny
Optional<String> first = words.stream().filter(s -> s.startsWith("j")).findFirst();

// anyMatch / allMatch / noneMatch
boolean any = words.stream().anyMatch(s -> s.contains("ava")); // true
boolean all = words.stream().allMatch(s -> s.length() > 2);   // true
boolean none = words.stream().noneMatch(s -> s.contains("z")); // true

// toArray
Object[] arr = words.stream().toArray();
String[] strArr = words.stream().toArray(String[]::new);
```

### IntStream for DSA

```java
// Sum of array
int sum = IntStream.of(arr).sum();

// Average
OptionalDouble avg = IntStream.of(arr).average();

// Statistics
IntSummaryStatistics stats = IntStream.of(arr).summaryStatistics();
stats.getMax();
stats.getMin();
stats.getSum();
stats.getAverage();
stats.getCount();

// Convert int[] to List<Integer>
List<Integer> list = IntStream.of(arr).boxed().collect(Collectors.toList());

// Convert List<Integer> to int[]
int[] arr2 = list.stream().mapToInt(Integer::intValue).toArray();

// Range sum
int rangeSum = IntStream.rangeClosed(1, 100).sum();  // 5050
```

---

## 4. Optional

```java
// Avoid null checks with Optional
Optional<String> opt = Optional.of("hello");
Optional<String> empty = Optional.empty();
Optional<String> nullable = Optional.ofNullable(null);  // null → empty Optional

// Checking
opt.isPresent()    // true
opt.isEmpty()      // false (Java 11+)
empty.isPresent()  // false

// Getting value
opt.get()          // "hello" (throws NoSuchElementException if empty)
opt.orElse("default")           // value or default
opt.orElseGet(() -> compute())  // lazy default
opt.orElseThrow(() -> new RuntimeException("missing"))

// Transforming
opt.map(String::toUpperCase)    // Optional<String>["HELLO"]
opt.filter(s -> s.length() > 3) // Optional<String>["hello"] (length 5 > 3)
opt.flatMap(s -> Optional.of(s.toUpperCase())) // flatten nested Optional

// Usage pattern
Optional<User> user = findUser(id);
String name = user.map(User::getName).orElse("Unknown");
```

---

## Summary

| Feature | DSA Use Case |
|---------|-------------|
| Lambda | Custom comparators, sort logic |
| Method reference | Cleaner function passing |
| Stream.filter | Data filtering problems |
| Stream.map | Element transformation |
| Collectors.groupingBy | Frequency map, grouping problems |
| IntStream | Numeric computations, range operations |
| Optional | Null-safe return types |

> **Interview Tip:** Don't over-use streams in interviews — they can obscure your algorithmic thinking. Use them for simple transformations, but for complex logic (nested loops, conditions), stick to explicit code. Interviewers want to see your logic, not your lambda fluency.
