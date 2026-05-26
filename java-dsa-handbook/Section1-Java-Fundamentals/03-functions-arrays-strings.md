# Section 1.3 — Functions, Arrays, and Strings

---

## 1. Functions (Methods) in Java

```java
// Method signature: modifier returnType methodName(params)
public static int add(int a, int b) {
    return a + b;
}

// void method (no return)
public static void printArray(int[] arr) {
    for (int n : arr) System.out.print(n + " ");
    System.out.println();
}

// Overloading — same name, different parameters
public static int max(int a, int b) { return a > b ? a : b; }
public static double max(double a, double b) { return a > b ? a : b; }

// Varargs — variable number of arguments
public static int sum(int... nums) {
    int total = 0;
    for (int n : nums) total += n;
    return total;
}
sum(1, 2, 3, 4, 5);  // works

// Recursive method
public static int factorial(int n) {
    if (n <= 1) return 1;          // base case
    return n * factorial(n - 1);   // recursive case
}

// Static vs instance methods
// static: belongs to class, called as ClassName.method()
// instance: belongs to object, called as obj.method()
```

### Pass by Value vs Pass by Reference

```java
// Java is ALWAYS pass-by-value
// For primitives: the value itself is copied
public static void changeInt(int x) {
    x = 100;  // only changes the local copy
}
int a = 5;
changeInt(a);
System.out.println(a);  // still 5

// For objects/arrays: the reference is copied (but points to same object)
public static void changeArray(int[] arr) {
    arr[0] = 100;  // modifies the actual array (reference was copied)
}
int[] nums = {1, 2, 3};
changeArray(nums);
System.out.println(nums[0]);  // 100 — array was modified

// To avoid mutation, copy the array:
int[] copy = arr.clone();
// or: Arrays.copyOf(arr, arr.length)
```

---

## 2. Arrays

### Declaration and Initialization

```java
// 1D arrays
int[] arr = new int[5];          // [0, 0, 0, 0, 0] — default values
int[] arr2 = {1, 2, 3, 4, 5};   // initialize with values
int[] arr3 = new int[]{1, 2, 3}; // explicit constructor

// Access and modify
arr[0] = 10;
int val = arr[2];
int len = arr.length;   // NOTE: .length (not .length() — that's for String)

// 2D arrays
int[][] matrix = new int[3][4];  // 3 rows, 4 cols
int[][] grid = {{1,2,3}, {4,5,6}, {7,8,9}};
int rows = grid.length;          // 3
int cols = grid[0].length;       // 3

// Jagged arrays (different row sizes)
int[][] jagged = new int[3][];
jagged[0] = new int[2];
jagged[1] = new int[4];
jagged[2] = new int[1];
```

### Arrays Utility Class (import java.util.Arrays)

```java
import java.util.Arrays;

int[] arr = {5, 3, 1, 4, 2};

// Sorting — O(n log n)
Arrays.sort(arr);                    // sorts in-place: [1, 2, 3, 4, 5]
Arrays.sort(arr, 1, 4);             // sort subarray [1, 4) only

// Sort in reverse (requires Integer[] not int[])
Integer[] arr2 = {5, 3, 1, 4, 2};
Arrays.sort(arr2, (a, b) -> b - a); // descending: [5, 4, 3, 2, 1]

// Searching (array must be sorted)
int idx = Arrays.binarySearch(arr, 3);  // index of 3 in sorted arr

// Filling
Arrays.fill(arr, 0);           // fill with 0
Arrays.fill(arr, 1, 4, -1);    // fill index [1,4) with -1

// Copying
int[] copy = Arrays.copyOf(arr, arr.length);     // full copy
int[] partial = Arrays.copyOfRange(arr, 1, 4);   // copy [1, 4)

// Comparing
Arrays.equals(arr, copy);      // true if same length and same elements

// Converting to String (for debugging)
System.out.println(Arrays.toString(arr));        // [1, 2, 3, 4, 5]
System.out.println(Arrays.deepToString(matrix)); // for 2D arrays

// 2D sort — sort by first element, then second
int[][] points = {{3,1}, {1,2}, {1,0}};
Arrays.sort(points, (a, b) -> a[0] != b[0] ? a[0] - b[0] : a[1] - b[1]);
```

### Critical Array Patterns for DSA

```java
// Frequency array
int[] freq = new int[26];  // for lowercase letters
for (char c : s.toCharArray()) freq[c - 'a']++;

// Prefix sum array
int[] prefix = new int[n + 1];
for (int i = 0; i < n; i++) prefix[i + 1] = prefix[i] + arr[i];
int rangeSum = prefix[r + 1] - prefix[l];  // sum from index l to r inclusive

// Difference array (for range update in O(1))
int[] diff = new int[n + 1];
// Add val to range [l, r]:
diff[l] += val;
diff[r + 1] -= val;
// Reconstruct:
int[] result = new int[n];
result[0] = diff[0];
for (int i = 1; i < n; i++) result[i] = result[i-1] + diff[i];

// Monotonic stack using array
int[] stack = new int[n];
int top = -1;
stack[++top] = 0;  // push
top--;              // pop
stack[top];         // peek
```

---

## 3. Strings

> Java Strings are **immutable** — every modification creates a new String. This is critical for performance.

### String Basics

```java
String s = "Hello World";
int len = s.length();          // 11 (method, not property — unlike array.length)
char c = s.charAt(3);          // 'l' (0-indexed)
int idx = s.indexOf('o');      // 4 (first occurrence)
int lastIdx = s.lastIndexOf('o'); // 7

// Substring — [startInclusive, endExclusive)
String sub = s.substring(6);      // "World"
String sub2 = s.substring(0, 5);  // "Hello"

// Comparison
s.equals("Hello World");          // true — always use equals() for strings
s.equalsIgnoreCase("hello world"); // true
s.compareTo("Hello");             // positive (lexicographic comparison)

// Search
s.contains("World");   // true
s.startsWith("He");    // true
s.endsWith("ld");      // true

// Case
s.toLowerCase();       // "hello world"
s.toUpperCase();       // "HELLO WORLD"

// Trim/strip
"  hello  ".trim();       // "hello" (removes leading/trailing whitespace)
"  hello  ".strip();      // "hello" (Unicode-aware, Java 11+)

// Replace
s.replace('l', 'r');              // "Herro Worrd"
s.replace("World", "Java");       // "Hello Java"
s.replaceAll("[aeiou]", "*");      // regex replace
s.replaceFirst("l", "L");         // "HeLlo World"

// Split
String[] parts = "a,b,c".split(",");  // ["a", "b", "c"]
String[] words = "hello world".split("\\s+");  // splits on whitespace

// Join
String joined = String.join("-", "a", "b", "c");  // "a-b-c"
String.join(", ", list);  // join collection

// Convert to char array
char[] chars = s.toCharArray();

// Check empty/blank
s.isEmpty();           // true if length == 0
s.isBlank();           // true if empty or only whitespace (Java 11+)
```

### String to/from Integer

```java
int n = Integer.parseInt("42");
String s = String.valueOf(42);      // "42"
String s2 = Integer.toString(42);  // "42"
String s3 = "" + 42;               // "42" (avoid — creates garbage)

// Number base conversions
Integer.toBinaryString(10);  // "1010"
Integer.toHexString(255);    // "ff"
Integer.toOctalString(8);    // "10"
Integer.parseInt("1010", 2); // 10 (parse binary string)
Integer.parseInt("ff", 16);  // 255 (parse hex string)
```

### StringBuilder — Critical for Performance

```java
// String concatenation in loop — O(n²) due to immutability!
String result = "";
for (int i = 0; i < n; i++) {
    result += chars[i];  // creates new String each time — BAD
}

// StringBuilder — O(n)
StringBuilder sb = new StringBuilder();
for (int i = 0; i < n; i++) {
    sb.append(chars[i]);
}
String result = sb.toString();

// StringBuilder methods
StringBuilder sb = new StringBuilder("Hello");
sb.append(" World");         // "Hello World"
sb.insert(5, ",");           // "Hello, World"
sb.delete(5, 7);             // "Hello World"
sb.deleteCharAt(0);          // "ello World"
sb.replace(0, 4, "Hi");      // "Hi World"
sb.reverse();                // "dlroW iH"
sb.charAt(0);                // 'd'
sb.setCharAt(0, 'D');        // "DlroW iH"
sb.length();
sb.toString();               // convert to String
sb.indexOf("World");
sb.lastIndexOf("l");

// StringBuilder as stack (for bracket matching, etc.)
StringBuilder stack = new StringBuilder();
stack.append(c);                           // push
stack.deleteCharAt(stack.length() - 1);    // pop
stack.charAt(stack.length() - 1);         // peek
stack.length() == 0;                       // isEmpty
```

### String Patterns for DSA

```java
// Palindrome check
public boolean isPalindrome(String s) {
    int l = 0, r = s.length() - 1;
    while (l < r) {
        if (s.charAt(l) != s.charAt(r)) return false;
        l++; r--;
    }
    return true;
}

// Anagram check (same characters, different order)
public boolean isAnagram(String s, String t) {
    if (s.length() != t.length()) return false;
    int[] freq = new int[26];
    for (char c : s.toCharArray()) freq[c - 'a']++;
    for (char c : t.toCharArray()) {
        freq[c - 'a']--;
        if (freq[c - 'a'] < 0) return false;
    }
    return true;
}

// Reverse words
public String reverseWords(String s) {
    String[] words = s.trim().split("\\s+");
    StringBuilder sb = new StringBuilder();
    for (int i = words.length - 1; i >= 0; i--) {
        sb.append(words[i]);
        if (i > 0) sb.append(" ");
    }
    return sb.toString();
}

// Check all characters unique
public boolean allUnique(String s) {
    boolean[] seen = new boolean[128];  // ASCII
    for (char c : s.toCharArray()) {
        if (seen[c]) return false;
        seen[c] = true;
    }
    return true;
}

// Longest common prefix
public String longestCommonPrefix(String[] strs) {
    if (strs.length == 0) return "";
    String prefix = strs[0];
    for (String s : strs) {
        while (!s.startsWith(prefix)) {
            prefix = prefix.substring(0, prefix.length() - 1);
            if (prefix.isEmpty()) return "";
        }
    }
    return prefix;
}
```

---

## 4. Complexity Reference

| Operation | Array | String |
|-----------|-------|--------|
| Access by index | O(1) | O(1) via charAt() |
| Search (unsorted) | O(n) | O(n) via indexOf() |
| Sort | O(n log n) | O(n log n) via toCharArray+sort |
| Concatenation | — | O(n) per concat, use StringBuilder |
| Substring | — | O(n) |
| StringBuilder append | — | O(1) amortized |

> **Interview Tip:** Always use `StringBuilder` for string building in loops. Mention it unprompted — it shows you understand Java internals. A senior engineer who writes `result += s` in a loop is a red flag to interviewers.
