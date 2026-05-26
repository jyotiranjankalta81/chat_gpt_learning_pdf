# Section 1.4 — OOP Concepts (Java)

> For DSA interviews at FAANG/Big Tech, OOP is tested through system design rounds and when implementing custom data structures (LRU Cache, Trie, Graph Node, etc.)

---

## 1. Classes and Objects

```java
// Class definition
public class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;

    // Constructor
    TreeNode(int val) {
        this.val = val;
        this.left = null;
        this.right = null;
    }

    // Overloaded constructor
    TreeNode(int val, TreeNode left, TreeNode right) {
        this.val = val;
        this.left = left;
        this.right = right;
    }
}

// Creating objects
TreeNode root = new TreeNode(5);
TreeNode node = new TreeNode(3, null, null);

// Standard LeetCode node definitions you must know by heart:
// ListNode (Linked List)
class ListNode {
    int val;
    ListNode next;
    ListNode(int val) { this.val = val; }
}

// TreeNode (Binary Tree)
class TreeNode {
    int val;
    TreeNode left, right;
    TreeNode(int val) { this.val = val; }
}
```

---

## 2. Encapsulation

```java
public class BankAccount {
    private double balance;    // private — cannot access from outside
    private String accountId;

    public BankAccount(String id, double initial) {
        this.accountId = id;
        this.balance = initial;
    }

    // Getter
    public double getBalance() { return balance; }

    // Setter with validation
    public void deposit(double amount) {
        if (amount > 0) balance += amount;
    }

    public boolean withdraw(double amount) {
        if (amount > 0 && balance >= amount) {
            balance -= amount;
            return true;
        }
        return false;
    }
}
```

---

## 3. Inheritance

```java
// Base class
public class Shape {
    protected String color;

    public Shape(String color) {
        this.color = color;
    }

    public double area() { return 0; }  // can be overridden

    public String toString() {
        return "Shape[color=" + color + "]";
    }
}

// Derived class
public class Circle extends Shape {
    private double radius;

    public Circle(String color, double radius) {
        super(color);  // call parent constructor
        this.radius = radius;
    }

    @Override
    public double area() {
        return Math.PI * radius * radius;
    }
}

public class Rectangle extends Shape {
    private double width, height;

    public Rectangle(String color, double w, double h) {
        super(color);
        this.width = w;
        this.height = h;
    }

    @Override
    public double area() { return width * height; }
}

// Usage
Shape s = new Circle("red", 5);
s.area();  // calls Circle's area() — runtime polymorphism
```

---

## 4. Polymorphism

```java
// Compile-time polymorphism: Method Overloading
class Calculator {
    int add(int a, int b) { return a + b; }
    double add(double a, double b) { return a + b; }
    int add(int a, int b, int c) { return a + b + c; }
}

// Runtime polymorphism: Method Overriding
Shape[] shapes = {new Circle("red", 3), new Rectangle("blue", 4, 5)};
for (Shape shape : shapes) {
    System.out.println(shape.area());  // calls the correct subclass method
}

// instanceof check
if (shape instanceof Circle) {
    Circle c = (Circle) shape;  // safe cast
}
// Java 16+ pattern matching:
if (shape instanceof Circle c) {
    System.out.println(c.radius);  // no explicit cast needed
}
```

---

## 5. Abstraction

```java
// Abstract class — cannot be instantiated, may have both abstract and concrete methods
abstract class Vehicle {
    String brand;

    Vehicle(String brand) { this.brand = brand; }

    // Abstract method — must be implemented by subclass
    abstract double fuelEfficiency();

    // Concrete method — inherited as-is
    public void displayInfo() {
        System.out.println("Brand: " + brand + ", Efficiency: " + fuelEfficiency());
    }
}

class Car extends Vehicle {
    double mpg;
    Car(String brand, double mpg) {
        super(brand);
        this.mpg = mpg;
    }

    @Override
    double fuelEfficiency() { return mpg; }
}
```

---

## 6. Interfaces

```java
// Interface — pure abstraction (all methods abstract by default in Java 7)
interface Comparable<T> {
    int compareTo(T other);
}

// Interface with default method (Java 8+)
interface Printable {
    void print();

    default void printTwice() {  // default implementation
        print();
        print();
    }

    static void info() {  // static method in interface
        System.out.println("Printable interface");
    }
}

// Implementing multiple interfaces (Java's answer to multiple inheritance)
class Document implements Printable, Serializable {
    String content;

    @Override
    public void print() { System.out.println(content); }
}

// Functional interface (1 abstract method) — used with lambdas
@FunctionalInterface
interface MathOperation {
    int operate(int a, int b);
}

MathOperation add = (a, b) -> a + b;
MathOperation mul = (a, b) -> a * b;
System.out.println(add.operate(3, 4));  // 7
```

### Abstract Class vs Interface — Interview Cheat Sheet

| | Abstract Class | Interface |
|--|---------------|-----------|
| Instantiation | No | No |
| Constructor | Yes | No |
| Fields | Any type | `public static final` only |
| Methods | Abstract + concrete | Abstract + default + static |
| Multiple inheritance | No (single extends) | Yes (multiple implements) |
| When to use | Shared state + partial implementation | Contract / capability definition |

---

## 7. Generics

```java
// Generic class
class Pair<A, B> {
    A first;
    B second;

    Pair(A first, B second) {
        this.first = first;
        this.second = second;
    }
}

Pair<String, Integer> p = new Pair<>("Alice", 25);

// Generic method
public static <T extends Comparable<T>> T findMax(T[] arr) {
    T max = arr[0];
    for (T item : arr) {
        if (item.compareTo(max) > 0) max = item;
    }
    return max;
}

// Bounded type parameters
class MinHeap<T extends Comparable<T>> { ... }

// Wildcard — use when you don't care about specific type
public static double sumList(List<? extends Number> list) {
    double sum = 0;
    for (Number n : list) sum += n.doubleValue();
    return sum;
}
sumList(List.of(1, 2, 3));       // works with Integer
sumList(List.of(1.1, 2.2, 3.3)); // works with Double

// Upper bounded: <? extends T> — read-only
// Lower bounded: <? super T>   — write-capable
```

---

## 8. OOP in DSA — Practical Examples

### Custom Comparator

```java
// Implementing Comparable in a custom class
class Interval implements Comparable<Interval> {
    int start, end;

    Interval(int start, int end) {
        this.start = start;
        this.end = end;
    }

    @Override
    public int compareTo(Interval other) {
        return this.start - other.start;  // sort by start time
    }
}

// Using Comparator (separate from class)
Comparator<int[]> comp = (a, b) -> a[0] - b[0];  // sort 2D array by first element
Arrays.sort(intervals, comp);
```

### LRU Cache Using OOP

```java
class LRUCache {
    private final int capacity;
    private final Map<Integer, Integer> cache;

    public LRUCache(int capacity) {
        this.capacity = capacity;
        // LinkedHashMap with access order = true implements LRU naturally
        this.cache = new LinkedHashMap<>(capacity, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry<Integer, Integer> eldest) {
                return size() > capacity;
            }
        };
    }

    public int get(int key) {
        return cache.getOrDefault(key, -1);
    }

    public void put(int key, int value) {
        cache.put(key, value);
    }
}
```

### Union-Find (Disjoint Set) — OOP Implementation

```java
class UnionFind {
    private int[] parent;
    private int[] rank;
    private int components;

    public UnionFind(int n) {
        parent = new int[n];
        rank = new int[n];
        components = n;
        for (int i = 0; i < n; i++) parent[i] = i;
    }

    public int find(int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]);  // path compression
        }
        return parent[x];
    }

    public boolean union(int x, int y) {
        int px = find(x), py = find(y);
        if (px == py) return false;  // already connected

        if (rank[px] < rank[py]) parent[px] = py;
        else if (rank[px] > rank[py]) parent[py] = px;
        else { parent[py] = px; rank[px]++; }

        components--;
        return true;
    }

    public boolean connected(int x, int y) {
        return find(x) == find(y);
    }

    public int getComponents() { return components; }
}
```

---

## Summary

| OOP Concept | DSA Application |
|-------------|----------------|
| Class/Object | Custom node types (TreeNode, ListNode, GraphNode) |
| Encapsulation | LRU Cache, Trie, Segment Tree |
| Inheritance | Problem-specific node hierarchies |
| Polymorphism | Comparator patterns, generic algorithms |
| Abstract class | Abstract graph/tree base classes |
| Interface | Comparable, Iterable, custom function interfaces |
| Generics | Generic Pair, generic data structures |
