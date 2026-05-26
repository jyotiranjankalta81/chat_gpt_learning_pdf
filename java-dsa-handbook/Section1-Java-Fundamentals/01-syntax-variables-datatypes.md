# Section 1.1 — Java Syntax, Variables, and Data Types

> **For experienced engineers:** Java syntax is C-like. If you know JavaScript (MERN), the concepts map directly — Java is just stricter about types and requires compilation.

---

## 1. Java Program Structure

```java
// Every Java program needs a class and a main method
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, FAANG!");
    }
}
```

**Key differences from JavaScript:**
- Strongly typed — every variable needs a declared type
- Compiled language — `javac Main.java` → `java Main`
- No hoisting, no `var` ambiguity
- Semicolons are mandatory

---

## 2. Primitive Data Types

| Type | Size | Range | Default | Use Case |
|------|------|-------|---------|----------|
| `byte` | 1 byte | -128 to 127 | 0 | Memory-sensitive arrays |
| `short` | 2 bytes | -32,768 to 32,767 | 0 | Rarely used |
| `int` | 4 bytes | -2^31 to 2^31-1 | 0 | **Most common integer type** |
| `long` | 8 bytes | -2^63 to 2^63-1 | 0L | Large numbers, timestamps |
| `float` | 4 bytes | ~7 decimal digits | 0.0f | Rarely used in DSA |
| `double` | 8 bytes | ~15 decimal digits | 0.0 | Floating point calculations |
| `char` | 2 bytes | '\u0000' to '\uffff' | '\u0000' | Character manipulation |
| `boolean` | 1 bit | true/false | false | Flags, conditions |

```java
// DSA-critical declarations
int n = 1_000_000;          // underscore for readability (Java 7+)
long bigNum = 2_000_000_000L;  // L suffix required for long literals
double pi = 3.14159;
char ch = 'A';
boolean found = false;

// Integer limits — memorize these for overflow detection
int MAX = Integer.MAX_VALUE;   // 2,147,483,647 (~2.1 billion)
int MIN = Integer.MIN_VALUE;   // -2,147,483,648
long LMAX = Long.MAX_VALUE;    // ~9.2 × 10^18

// Overflow trap — common interview bug:
int a = Integer.MAX_VALUE;
int b = a + 1;  // OVERFLOW: becomes -2147483648 (not an error!)
// Fix: use long
long safe = (long) a + 1;
```

---

## 3. Variable Declaration and Initialization

```java
// Declaration
int x;           // declared, not initialized (value is undefined, not 0)
int y = 10;      // declared and initialized

// Multiple declarations
int p = 1, q = 2, r = 3;

// final (equivalent to const in JS)
final int MAX_SIZE = 100;  // cannot be reassigned

// Type inference with var (Java 10+) — use sparingly in interviews
var list = new ArrayList<Integer>();  // compiler infers ArrayList<Integer>

// Naming conventions (follow these in interviews)
int camelCase = 1;
final int UPPER_SNAKE_CASE = 100;  // constants
class PascalCase {}
```

---

## 4. Type Casting

```java
// Widening (automatic, safe)
int i = 42;
long l = i;      // int → long (automatic)
double d = i;    // int → double (automatic)

// Narrowing (explicit cast, may lose data)
double pi = 3.99;
int truncated = (int) pi;   // = 3 (truncates, doesn't round)

// char ↔ int casting (frequently used in DSA)
char c = 'A';
int ascii = c;              // = 65
char back = (char)(ascii + 1);  // = 'B'

// String ↔ int conversion (common in DSA)
int num = Integer.parseInt("42");
long lnum = Long.parseLong("123456789");
double dnum = Double.parseDouble("3.14");
String s = String.valueOf(42);      // "42"
String s2 = Integer.toString(42);   // "42"

// DSA trick: char digit to int
char digit = '7';
int val = digit - '0';   // = 7 (subtract ASCII of '0' = 48)
int letterIdx = 'e' - 'a';  // = 4 (0-indexed position in alphabet)
```

---

## 5. Wrapper Classes

> Used with Collections (which require objects, not primitives)

| Primitive | Wrapper | Parse Method |
|-----------|---------|-------------|
| `int` | `Integer` | `Integer.parseInt(s)` |
| `long` | `Long` | `Long.parseLong(s)` |
| `double` | `Double` | `Double.parseDouble(s)` |
| `char` | `Character` | `Character.isDigit(c)` |
| `boolean` | `Boolean` | `Boolean.parseBoolean(s)` |

```java
// Autoboxing: primitive → wrapper (automatic)
Integer obj = 42;           // int → Integer

// Unboxing: wrapper → primitive (automatic)
int val = obj;              // Integer → int

// Null trap with unboxing — NullPointerException!
Integer nullObj = null;
int x = nullObj;            // THROWS NullPointerException

// Useful Integer methods for DSA
Integer.MAX_VALUE           // 2147483647
Integer.MIN_VALUE           // -2147483648
Integer.toBinaryString(42)  // "101010"
Integer.bitCount(42)        // number of set bits = 3
Integer.highestOneBit(42)   // 32 (highest power of 2 ≤ 42)
Integer.numberOfLeadingZeros(42)
Integer.reverse(42)         // bit reversal
Math.max(a, b)
Math.min(a, b)
Math.abs(-5)                // 5
Math.pow(2, 10)             // 1024.0 (returns double)
(int) Math.pow(2, 10)       // 1024

// Character utility methods (heavily used in string problems)
Character.isDigit('5')      // true
Character.isLetter('A')     // true
Character.isLetterOrDigit('a')
Character.isUpperCase('A')  // true
Character.isLowerCase('a')  // true
Character.toUpperCase('a')  // 'A'
Character.toLowerCase('A')  // 'a'
Character.isWhitespace(' ') // true
```

---

## 6. Input/Output for Competitive Coding

```java
import java.util.*;
import java.io.*;

public class Main {
    public static void main(String[] args) throws IOException {
        // Fast Input (use BufferedReader for competitive coding with large inputs)
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        int t = Integer.parseInt(br.readLine().trim()); // number of test cases
        
        while (t-- > 0) {
            StringTokenizer st = new StringTokenizer(br.readLine());
            int n = Integer.parseInt(st.nextToken());
            int k = Integer.parseInt(st.nextToken());
            
            int[] arr = new int[n];
            st = new StringTokenizer(br.readLine());
            for (int i = 0; i < n; i++) {
                arr[i] = Integer.parseInt(st.nextToken());
            }
        }
        
        // Fast Output (use StringBuilder + single print)
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 10; i++) {
            sb.append(i).append('\n');
        }
        System.out.print(sb);  // single I/O call is much faster
    }
}
```

```java
// Scanner — easier but slower (fine for LeetCode)
import java.util.Scanner;
Scanner sc = new Scanner(System.in);
int n = sc.nextInt();
String s = sc.next();      // reads one word
String line = sc.nextLine(); // reads full line
double d = sc.nextDouble();

// Standard LeetCode — no input needed, just implement the method
class Solution {
    public int someMethod(int[] nums, int k) {
        // your solution
    }
}
```

---

## 7. Common DSA Interview Patterns Using Primitives

```java
// Counting character frequencies
int[] freq = new int[26];
String s = "hello";
for (char c : s.toCharArray()) {
    freq[c - 'a']++;
}

// XOR for finding unique element
int[] nums = {1, 2, 3, 2, 1};
int xor = 0;
for (int n : nums) xor ^= n;  // xor = 3

// Bit manipulation checks
boolean isPowerOfTwo = (n > 0) && (n & (n - 1)) == 0;
boolean isEven = (n & 1) == 0;
int lastBit = n & 1;
int clearLastBit = n & (n - 1);

// Integer overflow safe comparison (avoid (a + b) overflow)
// Bad: if (a + b > Integer.MAX_VALUE)
// Good:
if (a > Integer.MAX_VALUE - b) { /* overflow */ }
// Or cast to long first:
if ((long)a + b > Integer.MAX_VALUE) { /* overflow */ }
```

---

## Summary — Key Takeaways

| Concept | DSA Relevance |
|---------|--------------|
| `int` overflow | Always check when summing large arrays |
| `char - 'a'` | Index into frequency array |
| `Integer.MAX_VALUE` | Initialize min tracking variables |
| `Integer.MIN_VALUE` | Initialize max tracking variables |
| `(int) Math.pow(2, k)` | Bit masks, knapsack sizing |
| Autoboxing trap | Never rely on `==` for Integer objects |

> **Interview Tip:** When you see "find the sum of all elements", immediately ask: can the sum exceed `Integer.MAX_VALUE`? If yes, use `long`. Interviewers love this attention to detail.
