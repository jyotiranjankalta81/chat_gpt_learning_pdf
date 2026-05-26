# Section 1.2 — Operators, Conditions, and Loops

---

## 1. Operators

### Arithmetic Operators

```java
int a = 17, b = 5;
int sum  = a + b;   // 22
int diff = a - b;   // 12
int prod = a * b;   // 85
int quot = a / b;   // 3  (integer division — truncates toward zero)
int rem  = a % b;   // 2  (modulo)

// DSA trap: negative modulo
int neg = -7 % 3;   // -1 in Java (NOT 2!)
// To always get positive result:
int posMod = ((n % m) + m) % m;  // canonical positive modulo formula

// Integer division rules — critical for binary search
int mid = (left + right) / 2;       // can overflow if left+right > MAX_VALUE
int safeMid = left + (right - left) / 2;  // preferred — overflow safe
```

### Comparison Operators

```java
a == b   // equal
a != b   // not equal
a <  b   // less than
a >  b   // greater than
a <= b   // less than or equal
a >= b   // greater than or equal

// WARNING: never use == to compare objects (Strings, Integer wrappers, etc.)
String s1 = new String("hello");
String s2 = new String("hello");
s1 == s2          // FALSE (compares references, not content)
s1.equals(s2)     // TRUE (compares content) — always use this

// Integer wrapper caching trap (common interview trick):
Integer x = 127;
Integer y = 127;
x == y      // TRUE (Integer cache: -128 to 127 are cached objects)
Integer p = 128;
Integer q = 128;
p == q      // FALSE (beyond cache range, different objects)
p.equals(q) // TRUE  — always use equals() for objects
```

### Logical Operators

```java
// Short-circuit evaluation
boolean a = true, b = false;
a && b    // AND: false (short-circuits if a is false)
a || b    // OR:  true  (short-circuits if a is true)
!a        // NOT: false

// Short-circuit safety pattern (avoid NullPointerException)
if (node != null && node.val == target) { ... }
// If node is null, the second condition is never evaluated

// Bitwise logical (operate on bits)
a & b     // bitwise AND
a | b     // bitwise OR
a ^ b     // bitwise XOR (different bits = 1)
~a        // bitwise complement
```

### Bitwise Shift Operators

```java
int n = 8;  // binary: 1000
n << 1      // = 16  (1000 → 10000): multiply by 2
n >> 1      // = 4   (1000 → 0100):  divide by 2 (arithmetic, preserves sign)
n >>> 1     // = 4   (unsigned right shift: fills with 0, not sign bit)

// Useful patterns
int pow2 = 1 << k;          // 2^k
boolean kthBitSet = (n >> k & 1) == 1;
int setKthBit = n | (1 << k);
int clearKthBit = n & ~(1 << k);
int toggleKthBit = n ^ (1 << k);
```

---

## 2. Conditional Statements

### if / else if / else

```java
int score = 85;

if (score >= 90) {
    System.out.println("A");
} else if (score >= 80) {
    System.out.println("B");
} else if (score >= 70) {
    System.out.println("C");
} else {
    System.out.println("F");
}
```

### Ternary Operator

```java
// condition ? valueIfTrue : valueIfFalse
int max = (a > b) ? a : b;
String label = (n % 2 == 0) ? "even" : "odd";

// Nested ternary (use sparingly — reduces readability)
int sign = (n > 0) ? 1 : (n < 0) ? -1 : 0;
```

### Switch Statement

```java
// Classic switch (Java 7+)
int day = 3;
switch (day) {
    case 1: System.out.println("Mon"); break;
    case 2: System.out.println("Tue"); break;
    case 3: System.out.println("Wed"); break;
    default: System.out.println("Other");
}

// Switch expression (Java 14+) — cleaner syntax
String result = switch (day) {
    case 1 -> "Monday";
    case 2 -> "Tuesday";
    case 3 -> "Wednesday";
    default -> "Other";
};

// String switch (Java 7+)
String direction = "NORTH";
switch (direction) {
    case "NORTH": break;
    case "SOUTH": break;
    // ...
}
```

---

## 3. Loops

### for Loop

```java
// Standard indexed loop
for (int i = 0; i < n; i++) {
    // forward iteration
}

// Reverse iteration
for (int i = n - 1; i >= 0; i--) {
    // backward iteration
}

// Step iteration
for (int i = 0; i < n; i += 2) {
    // every other element
}

// 2D array traversal
int[][] matrix = new int[rows][cols];
for (int i = 0; i < rows; i++) {
    for (int j = 0; j < cols; j++) {
        // process matrix[i][j]
    }
}
```

### Enhanced for Loop (for-each)

```java
int[] arr = {1, 2, 3, 4, 5};

// Array
for (int num : arr) {
    System.out.println(num);
}

// Collection
List<Integer> list = new ArrayList<>();
for (int val : list) { }

// Map
Map<String, Integer> map = new HashMap<>();
for (Map.Entry<String, Integer> entry : map.entrySet()) {
    String key = entry.getKey();
    int val = entry.getValue();
}
for (String key : map.keySet()) { }
for (int val : map.values()) { }

// String characters
String s = "hello";
for (char c : s.toCharArray()) { }
```

### while Loop

```java
// Standard while
int i = 0;
while (i < n) {
    i++;
}

// do-while (executes at least once)
do {
    // process
} while (condition);

// Pattern: while with two pointers
int left = 0, right = n - 1;
while (left < right) {
    // two pointer logic
    left++;
    right--;
}

// Pattern: process digits
int num = 12345;
while (num > 0) {
    int digit = num % 10;
    num /= 10;
}
```

### Loop Control Statements

```java
// break — exit the loop immediately
for (int i = 0; i < n; i++) {
    if (arr[i] == target) {
        break;
    }
}

// continue — skip current iteration
for (int i = 0; i < n; i++) {
    if (arr[i] < 0) continue;  // skip negative numbers
    process(arr[i]);
}

// Labeled break (for nested loops)
outer:
for (int i = 0; i < rows; i++) {
    for (int j = 0; j < cols; j++) {
        if (matrix[i][j] == target) {
            System.out.println("Found at " + i + ", " + j);
            break outer;  // breaks out of BOTH loops
        }
    }
}
```

---

## 4. DSA-Critical Loop Patterns

### Binary Search Loop Template

```java
// Iterative binary search (memorize this exactly)
int left = 0, right = n - 1;
while (left <= right) {
    int mid = left + (right - left) / 2;  // overflow-safe
    if (arr[mid] == target) {
        return mid;
    } else if (arr[mid] < target) {
        left = mid + 1;
    } else {
        right = mid - 1;
    }
}
return -1;
```

### Sliding Window Loop Pattern

```java
int left = 0, maxLen = 0;
for (int right = 0; right < n; right++) {
    // expand window: add arr[right] to window

    while (/* window is invalid */) {
        // shrink window: remove arr[left] from window
        left++;
    }

    maxLen = Math.max(maxLen, right - left + 1);
}
```

### Two Pointer Loop Pattern

```java
int left = 0, right = n - 1;
while (left < right) {
    int sum = arr[left] + arr[right];
    if (sum == target) {
        // found pair
        left++; right--;
    } else if (sum < target) {
        left++;
    } else {
        right--;
    }
}
```

### Counting Loop Patterns

```java
// Count elements satisfying condition
int count = 0;
for (int num : arr) {
    if (num % 2 == 0) count++;
}

// Running sum (prefix sum building block)
int[] prefix = new int[n + 1];
for (int i = 0; i < n; i++) {
    prefix[i + 1] = prefix[i] + arr[i];
}
// Range sum [l, r] = prefix[r+1] - prefix[l]
```

---

## 5. Performance Considerations

| Loop Type | Time | When to Use |
|-----------|------|-------------|
| Simple for | O(n) | Indexed access needed |
| Enhanced for | O(n) | Read-only, cleaner syntax |
| while with two pointers | O(n) | Searching in sorted data |
| Nested loops | O(n²) | Usually brute force — try to optimize |
| Binary search loop | O(log n) | Sorted data, answer space search |

> **Interview Tip:** When you write a nested loop (O(n²)), explicitly call it out: "This is O(n²) — let me think if we can do better." Interviewers award points for identifying complexity, even before you optimize.
