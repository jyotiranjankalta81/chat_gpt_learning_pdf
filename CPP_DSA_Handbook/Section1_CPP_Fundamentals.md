# Section 1: C++ Fundamentals
## From Syntax to Advanced OOP — Interview-Ready C++

> **Goal:** Get fully comfortable writing C++ in interviews. Coming from JavaScript/MERN, this section bridges the gap.

---

## Table of Contents
1. [Basic Syntax & Structure](#1-basic-syntax--structure)
2. [Variables & Data Types](#2-variables--data-types)
3. [Operators](#3-operators)
4. [Conditions](#4-conditions)
5. [Loops](#5-loops)
6. [Functions](#6-functions)
7. [Arrays](#7-arrays)
8. [Strings](#8-strings)
9. [References & Pointers](#9-references--pointers)
10. [Memory Basics](#10-memory-basics)
11. [Structs](#11-structs)
12. [Classes & Objects](#12-classes--objects)
13. [Constructors & Destructors](#13-constructors--destructors)
14. [OOP Concepts](#14-oop-concepts)
15. [Inheritance](#15-inheritance)
16. [Polymorphism](#16-polymorphism)
17. [Templates](#17-templates)
18. [Exception Handling](#18-exception-handling)
19. [Lambda Functions](#19-lambda-functions)

---

## 1. Basic Syntax & Structure

```cpp
#include <iostream>         // Include standard I/O library
#include <bits/stdc++.h>    // Include ALL headers (use in interviews)
using namespace std;        // Avoid std:: prefix everywhere

int main() {
    // Entry point of every C++ program
    cout << "Hello, FAANG!" << endl;  // Output
    cin >> variable;                   // Input
    return 0;
}
```

### Key Differences from JavaScript

| Feature | JavaScript | C++ |
|---------|-----------|-----|
| Typing | Dynamic | Static (must declare type) |
| Compilation | Interpreted (JIT) | Compiled |
| Memory | Garbage collected | Manual (RAII/smart ptrs) |
| Entry point | None (or module) | `int main()` |
| Semicolons | Optional | **Required** |
| Null | `null`/`undefined` | `nullptr`/`NULL` |

---

## 2. Variables & Data Types

```cpp
// Integer types
int a = 42;                    // 32-bit, -2B to 2B
long long b = 1e18;            // 64-bit — USE THIS for large numbers
short c = 100;                 // 16-bit
unsigned int d = 4294967295;   // Only positive

// Floating point
float f = 3.14f;               // 32-bit (avoid in interviews — precision issues)
double g = 3.14159265358979;   // 64-bit — USE THIS
long double h = 3.14L;        // 80/128-bit

// Characters & Boolean
char ch = 'A';                 // Single character, 1 byte
bool flag = true;              // true/false

// String
string s = "Hello";           // std::string (preferred)

// Auto (type deduction — very useful in interviews)
auto x = 42;                   // int
auto y = 3.14;                 // double
auto z = "hello";              // const char*
auto w = string("hello");      // string

// Constants
const int MAX = 1e9 + 7;       // Cannot be changed
constexpr int SIZE = 100;       // Compile-time constant
```

### Important Constants for Interviews

```cpp
#include <climits>

INT_MAX    = 2147483647        // 2^31 - 1
INT_MIN    = -2147483648       // -2^31
LLONG_MAX  = 9223372036854775807  // 2^63 - 1
LLONG_MIN  = -9223372036854775808
DBL_MAX    = 1.79769e+308

// Common interview values
const int MOD = 1e9 + 7;       // Modular arithmetic
const int INF = 1e9;           // Infinity approximation
const long long LINF = 1e18;   // Long long infinity
```

### Type Casting

```cpp
int a = 5, b = 2;
double result = (double)a / b;          // C-style cast: 2.5
double result2 = static_cast<double>(a) / b;  // C++ style (preferred)

// Implicit conversion pitfall
int x = 1000000;
int y = 1000000;
long long z = (long long)x * y;  // MUST cast BEFORE multiplication!
// long long z = x * y;  // WRONG: overflow happens before assignment
```

---

## 3. Operators

```cpp
// Arithmetic
+  -  *  /  %               // Standard arithmetic
a = b = c = 0;               // Chained assignment

// Comparison
== != < > <= >=

// Logical
&&  ||  !                    // AND, OR, NOT

// Bitwise (critical for competitive programming)
&   // AND
|   // OR
^   // XOR
~   // NOT (complement)
<<  // Left shift (multiply by 2^n)
>>  // Right shift (divide by 2^n)

// Examples
5 & 3   = 1    // 101 & 011 = 001
5 | 3   = 7    // 101 | 011 = 111
5 ^ 3   = 6    // 101 ^ 011 = 110
~5      = -6   // Flip all bits
5 << 1  = 10   // 5 * 2
5 >> 1  = 2    // 5 / 2

// Increment/Decrement
i++   // Post-increment (use value, then increment)
++i   // Pre-increment (increment, then use value) — FASTER in loops
i--   // Post-decrement
--i   // Pre-decrement

// Compound assignment
a += b;  a -= b;  a *= b;  a /= b;  a %= b;
a &= b;  a |= b;  a ^= b;  a <<= 1;  a >>= 1;

// Ternary
int max_val = (a > b) ? a : b;
```

---

## 4. Conditions

```cpp
// if-else
if (n == 0) {
    cout << "zero";
} else if (n > 0) {
    cout << "positive";
} else {
    cout << "negative";
}

// switch (for discrete values)
switch (n) {
    case 1:
        cout << "one";
        break;
    case 2:
        cout << "two";
        break;
    default:
        cout << "other";
}

// Short-circuit evaluation
if (ptr != nullptr && ptr->val > 0) {  // Safe: checks ptr first
    // ...
}

// Conditional with initialization (C++17)
if (auto it = map.find(key); it != map.end()) {
    // Use it->second
}
```

---

## 5. Loops

```cpp
// for loop
for (int i = 0; i < n; i++) {
    // ...
}

// Range-based for (C++11) — very clean
vector<int> v = {1, 2, 3, 4, 5};
for (int x : v) cout << x << " ";           // Read only
for (int& x : v) x *= 2;                    // Modify in place
for (auto& [key, val] : myMap) {            // Structured binding C++17
    cout << key << ": " << val << "\n";
}

// while loop
while (condition) { /* ... */ }

// do-while (executes at least once)
do { /* ... */ } while (condition);

// Loop control
break;     // Exit loop immediately
continue;  // Skip to next iteration

// Nested loop with label-like break
bool found = false;
for (int i = 0; i < n && !found; i++) {
    for (int j = 0; j < m; j++) {
        if (grid[i][j] == target) {
            found = true;
            break;
        }
    }
}
```

---

## 6. Functions

```cpp
// Basic function
int add(int a, int b) {
    return a + b;
}

// Pass by value (copy) — changes don't affect original
void modifyValue(int x) { x = 100; }

// Pass by reference — changes affect original (use in interviews!)
void modifyRef(int& x) { x = 100; }

// Pass by const reference — efficient read, no copy
void print(const string& s) { cout << s; }
void processVector(const vector<int>& v) { /* read-only */ }

// Default parameters
int power(int base, int exp = 2) { /* ... */ }

// Function overloading
int max(int a, int b) { return a > b ? a : b; }
double max(double a, double b) { return a > b ? a : b; }

// Inline functions (hint to compiler for small functions)
inline int square(int x) { return x * x; }

// Returning multiple values
pair<int, int> minMax(vector<int>& v) {
    return {*min_element(v.begin(), v.end()),
            *max_element(v.begin(), v.end())};
}

// auto return type (C++14)
auto divide(double a, double b) {
    return a / b;
}

// Recursive function
int fibonacci(int n) {
    if (n <= 1) return n;
    return fibonacci(n-1) + fibonacci(n-2);
}
```

---

## 7. Arrays

```cpp
// C-style arrays (avoid in modern C++)
int arr[5] = {1, 2, 3, 4, 5};
int matrix[3][3] = {{1,2,3},{4,5,6},{7,8,9}};

// std::array (fixed size, use over C-style)
#include <array>
array<int, 5> arr = {1, 2, 3, 4, 5};
arr.size();    // 5
arr.front();   // 1
arr.back();    // 5

// std::vector (dynamic array — USE THIS in interviews)
vector<int> v;                    // Empty
vector<int> v(5);                 // Size 5, default 0
vector<int> v(5, -1);            // Size 5, all -1
vector<int> v = {1, 2, 3, 4, 5}; // Initializer list
vector<vector<int>> grid(n, vector<int>(m, 0)); // 2D grid

// Vector operations
v.push_back(6);           // Add to end: O(1) amortized
v.pop_back();             // Remove from end: O(1)
v.size();                 // Number of elements
v.empty();                // Check if empty
v[i];                     // Access: O(1)
v.at(i);                  // Access with bounds check: O(1)
v.front();                // First element
v.back();                 // Last element
v.insert(v.begin()+2, 99); // Insert at index: O(n)
v.erase(v.begin()+2);      // Erase at index: O(n)
v.clear();                 // Remove all elements
v.resize(10);              // Resize
v.reserve(100);            // Reserve capacity (performance!)

// Sorting
sort(v.begin(), v.end());                           // Ascending
sort(v.begin(), v.end(), greater<int>());           // Descending
sort(v.begin(), v.end(), [](int a, int b){ return a > b; }); // Custom

// Searching
auto it = find(v.begin(), v.end(), target);
bool found = binary_search(v.begin(), v.end(), target); // Sorted required
auto lb = lower_bound(v.begin(), v.end(), x); // First >= x
auto ub = upper_bound(v.begin(), v.end(), x); // First > x
```

---

## 8. Strings

```cpp
#include <string>
string s = "Hello, World!";

// Length
s.length();   // or s.size()

// Access
s[0];         // 'H'
s.front();    // 'H'
s.back();     // '!'

// Substring
s.substr(7, 5);  // "World" (start, length)

// Find
s.find("World");         // Returns index or string::npos
s.find("xyz") == string::npos;  // Not found

// Modify
s += " Extra";           // Concatenation
s.append(" More");       // Same as +=
s.replace(0, 5, "Hi");  // Replace "Hello" with "Hi"
s.erase(0, 7);           // Erase from start
s.insert(0, "Prefix ");  // Insert at position

// Conversion
to_string(42);           // int → string
stoi("42");              // string → int
stoll("1234567890");     // string → long long
stod("3.14");            // string → double

// Character operations
#include <cctype>
isalpha('A');   // true
isdigit('5');   // true
isalnum('a');   // true
isupper('A');   // true
islower('a');   // true
toupper('a');   // 'A'
tolower('A');   // 'a'

// String comparison
s1 == s2;       // Equality
s1 < s2;        // Lexicographic

// Split string (no built-in, use stringstream)
#include <sstream>
string line = "hello world foo";
stringstream ss(line);
string word;
vector<string> words;
while (ss >> word) words.push_back(word);

// Iterate string
for (char c : s) { /* ... */ }
for (int i = 0; i < s.size(); i++) { /* s[i] */ }

// Reverse string
reverse(s.begin(), s.end());

// Sort string characters
sort(s.begin(), s.end());

// String to char array
const char* cstr = s.c_str();
```

---

## 9. References & Pointers

### References

```cpp
int x = 10;
int& ref = x;    // ref is an alias for x

ref = 20;        // x is now 20
cout << x;       // Prints 20

// Reference in functions — avoids expensive copy
void swap(int& a, int& b) {
    int temp = a;
    a = b;
    b = temp;
}

// Const reference — read-only, no copy
void display(const vector<int>& v) {
    for (const int& x : v) cout << x;
}

// Rules:
// - Must be initialized when declared
// - Cannot be re-assigned to another variable
// - Cannot be null
```

### Pointers

```cpp
int x = 10;
int* ptr = &x;   // ptr holds address of x

*ptr = 20;       // Dereference: change x to 20
cout << *ptr;    // 20
cout << ptr;     // Memory address (e.g., 0x7fff...)

// Null pointer
int* nullPtr = nullptr;  // C++ style (use over NULL)

// Pointer arithmetic
int arr[] = {1, 2, 3, 4, 5};
int* p = arr;
p++;        // Point to next element
*(p+2);     // Element 2 positions ahead

// Pointer to pointer
int** pp = &ptr;
**pp = 30;

// Function pointer
int (*funcPtr)(int, int) = &add;
funcPtr(3, 4);  // Calls add(3,4)

// Dangling pointer — AVOID
int* badPtr;
{
    int local = 5;
    badPtr = &local;
}  // local destroyed — badPtr is now dangling!
```

### Smart Pointers (Modern C++)

```cpp
#include <memory>

// unique_ptr — sole ownership, auto-deleted
unique_ptr<int> p1 = make_unique<int>(42);
cout << *p1;

// shared_ptr — shared ownership, ref-counted
shared_ptr<int> p2 = make_shared<int>(42);
shared_ptr<int> p3 = p2;  // Both point to same memory

// weak_ptr — non-owning reference (breaks circular refs)
weak_ptr<int> wp = p2;
```

---

## 10. Memory Basics

```cpp
// Stack memory — automatic, fast, limited size
int arr[1000];  // Stack allocated

// Heap memory — manual, large, must be freed
int* p = new int(42);     // Allocate single int
int* arr = new int[100];  // Allocate array
delete p;                  // Free single
delete[] arr;              // Free array

// RAII — Resource Acquisition Is Initialization
// Use smart pointers, vectors, strings — they manage memory automatically

// Memory layout
// Stack: local variables, function calls
// Heap: dynamic allocation (new/delete)
// Text: compiled code
// Data: global/static variables

// Common memory errors (AVOID)
// 1. Memory leak: allocate but forget to delete
// 2. Double free: delete same memory twice
// 3. Use after free: use pointer after deleting
// 4. Buffer overflow: write past array bounds
// 5. Stack overflow: too deep recursion
```

---

## 11. Structs

```cpp
struct Point {
    int x, y;
};

struct TreeNode {
    int val;
    TreeNode* left;
    TreeNode* right;
    TreeNode(int v) : val(v), left(nullptr), right(nullptr) {}
};

struct ListNode {
    int val;
    ListNode* next;
    ListNode(int v) : val(v), next(nullptr) {}
};

// Usage
Point p = {3, 4};
Point q;
q.x = 1;
q.y = 2;

// Struct with methods (essentially a class)
struct Rectangle {
    int width, height;
    int area() { return width * height; }
    int perimeter() { return 2 * (width + height); }
};

// Comparison operator for sort
struct Interval {
    int start, end;
    bool operator<(const Interval& other) const {
        return start < other.start;
    }
};
```

---

## 12. Classes & Objects

```cpp
class Animal {
private:           // Only accessible within class
    string name;
    int age;

protected:         // Accessible in class + derived classes
    string type;

public:            // Accessible everywhere
    // Constructor
    Animal(string n, int a) : name(n), age(a) {}

    // Getters
    string getName() const { return name; }
    int getAge() const { return age; }

    // Setters
    void setName(const string& n) { name = n; }

    // Methods
    void display() const {
        cout << name << " (Age: " << age << ")\n";
    }

    // Static member (shared across all instances)
    static int count;
    static int getCount() { return count; }
};

int Animal::count = 0;  // Define static outside class

// Create objects
Animal a("Dog", 5);
Animal* ptr = new Animal("Cat", 3);  // Heap
ptr->display();       // Arrow for pointer
a.display();          // Dot for object
delete ptr;
```

---

## 13. Constructors & Destructors

```cpp
class MyClass {
    int* data;
    int size;

public:
    // Default constructor
    MyClass() : data(nullptr), size(0) {}

    // Parameterized constructor
    MyClass(int s) : size(s) {
        data = new int[size];
    }

    // Copy constructor (deep copy)
    MyClass(const MyClass& other) : size(other.size) {
        data = new int[size];
        copy(other.data, other.data + size, data);
    }

    // Move constructor (C++11) — efficient transfer
    MyClass(MyClass&& other) noexcept : data(other.data), size(other.size) {
        other.data = nullptr;
        other.size = 0;
    }

    // Copy assignment operator
    MyClass& operator=(const MyClass& other) {
        if (this != &other) {  // Self-assignment check
            delete[] data;
            size = other.size;
            data = new int[size];
            copy(other.data, other.data + size, data);
        }
        return *this;
    }

    // Destructor (called automatically when object goes out of scope)
    ~MyClass() {
        delete[] data;
    }

    // Initializer list (preferred — more efficient)
    MyClass(int s, int val) : size(s), data(new int[s]) {
        fill(data, data + size, val);
    }
};
```

---

## 14. OOP Concepts

### Encapsulation
```cpp
class BankAccount {
private:
    double balance;     // Hidden from outside

public:
    void deposit(double amount) {
        if (amount > 0) balance += amount;
    }
    double getBalance() const { return balance; }
};
```

### Abstraction
```cpp
class Shape {
public:
    virtual double area() = 0;   // Pure virtual — must be overridden
    virtual ~Shape() {}
};
```

### Operator Overloading
```cpp
class Vector2D {
public:
    int x, y;
    Vector2D(int x, int y) : x(x), y(y) {}

    Vector2D operator+(const Vector2D& other) const {
        return {x + other.x, y + other.y};
    }

    bool operator==(const Vector2D& other) const {
        return x == other.x && y == other.y;
    }

    // For use in map/set
    bool operator<(const Vector2D& other) const {
        return x < other.x || (x == other.x && y < other.y);
    }

    // Output stream operator
    friend ostream& operator<<(ostream& os, const Vector2D& v) {
        os << "(" << v.x << ", " << v.y << ")";
        return os;
    }
};
```

---

## 15. Inheritance

```cpp
class Animal {
protected:
    string name;
public:
    Animal(string n) : name(n) {}
    virtual void speak() { cout << name << " makes a sound\n"; }
    virtual ~Animal() {}  // Always virtual destructor in base class!
};

class Dog : public Animal {
public:
    Dog(string n) : Animal(n) {}
    void speak() override { cout << name << " barks\n"; }
    void fetch() { cout << name << " fetches!\n"; }
};

class Cat : public Animal {
public:
    Cat(string n) : Animal(n) {}
    void speak() override { cout << name << " meows\n"; }
};

// Multiple inheritance
class FlyingFish : public Fish, public Bird {
    // ...
};
```

---

## 16. Polymorphism

```cpp
// Runtime polymorphism (virtual functions)
Animal* animals[] = { new Dog("Rex"), new Cat("Whiskers") };
for (Animal* a : animals) {
    a->speak();  // Calls correct version at runtime
}

// Compile-time polymorphism (templates/overloading)
template<typename T>
T maximum(T a, T b) { return a > b ? a : b; }

// Pure virtual (Abstract class)
class Shape {
public:
    virtual double area() = 0;
    virtual double perimeter() = 0;
    virtual ~Shape() {}
};

class Circle : public Shape {
    double r;
public:
    Circle(double r) : r(r) {}
    double area() override { return 3.14159 * r * r; }
    double perimeter() override { return 2 * 3.14159 * r; }
};
```

---

## 17. Templates

```cpp
// Function template
template<typename T>
T add(T a, T b) { return a + b; }

add(1, 2);        // int
add(1.5, 2.5);    // double

// Multiple type parameters
template<typename T, typename U>
auto multiply(T a, U b) { return a * b; }

// Class template
template<typename T>
class Stack {
    vector<T> data;
public:
    void push(T val) { data.push_back(val); }
    T pop() {
        T top = data.back();
        data.pop_back();
        return top;
    }
    bool empty() { return data.empty(); }
};

Stack<int> intStack;
Stack<string> strStack;

// Template specialization
template<>
string add<string>(string a, string b) {
    return a + " " + b;  // Custom behavior for strings
}

// Non-type template parameters
template<int N>
class FixedArray {
    int data[N];
public:
    int size() { return N; }
};

FixedArray<10> arr;
```

---

## 18. Exception Handling

```cpp
#include <stdexcept>

// Basic try-catch
try {
    int result = divide(10, 0);
} catch (const exception& e) {
    cout << "Error: " << e.what() << "\n";
}

// Throw custom exception
void divide(int a, int b) {
    if (b == 0) throw runtime_error("Division by zero");
    return a / b;
}

// Multiple catch blocks
try {
    // risky code
} catch (const invalid_argument& e) {
    // Handle invalid argument
} catch (const out_of_range& e) {
    // Handle out of range
} catch (...) {
    // Catch everything else
}

// Exception hierarchy
// std::exception
//   ├── logic_error
//   │   ├── invalid_argument
//   │   ├── out_of_range
//   │   └── domain_error
//   └── runtime_error
//       ├── overflow_error
//       └── underflow_error

// noexcept (promise not to throw)
int safeAdd(int a, int b) noexcept { return a + b; }
```

---

## 19. Lambda Functions

```cpp
// Basic lambda
auto square = [](int x) { return x * x; };
cout << square(5);  // 25

// Lambda with capture
int base = 10;
auto addBase = [base](int x) { return base + x; };  // Capture by value
auto addBaseRef = [&base](int x) { return base + x; };  // Capture by ref
auto captureAll = [=](int x) { return base + x; };  // Capture all by value
auto captureAllRef = [&](int x) { return base + x; };  // Capture all by ref

// Lambda as function argument (sort, transform, etc.)
vector<int> v = {5, 2, 8, 1, 9, 3};
sort(v.begin(), v.end(), [](int a, int b) { return a > b; });

// Lambda with STL algorithms
vector<int> v = {1, 2, 3, 4, 5, 6};
auto it = find_if(v.begin(), v.end(), [](int x) { return x > 3; });

// Lambda in priority queue (custom comparator)
auto cmp = [](pair<int,int> a, pair<int,int> b) {
    return a.second > b.second;  // Min-heap by second element
};
priority_queue<pair<int,int>, vector<pair<int,int>>, decltype(cmp)> pq(cmp);

// Mutable lambda (can modify captured copies)
int count = 0;
auto increment = [count]() mutable { return ++count; };
```

---

## Interview-Ready C++ Patterns

### Fast I/O Setup (Always put at top of main)
```cpp
int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    // your code
}
```

### Common Interview Boilerplate
```cpp
#include <bits/stdc++.h>
using namespace std;

typedef long long ll;
typedef vector<int> vi;
typedef pair<int,int> pii;
typedef vector<pair<int,int>> vpii;

const int MOD = 1e9 + 7;
const int INF = 1e9;
const ll LINF = 1e18;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    
    int t;
    cin >> t;
    while (t--) {
        // solve each test case
    }
    return 0;
}
```

---

*Next: [Section 2 — STL Deep Dive](./Section2_STL_Deep_Dive.md)*
