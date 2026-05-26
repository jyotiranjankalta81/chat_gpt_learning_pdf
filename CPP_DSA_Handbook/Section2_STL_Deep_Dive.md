# Section 2: STL Deep Dive
## Complete Standard Template Library for FAANG Interviews

> **Philosophy:** Know every container's internal implementation, time complexity, and interview use case. The STL is your Swiss Army knife in C++ interviews.

---

## Table of Contents
1. [vector](#1-vector)
2. [array](#2-array)
3. [deque](#3-deque)
4. [list](#4-list)
5. [map](#5-map)
6. [unordered_map](#6-unordered_map)
7. [set](#7-set)
8. [unordered_set](#8-unordered_set)
9. [multiset](#9-multiset)
10. [multimap](#10-multimap)
11. [priority_queue](#11-priority_queue)
12. [stack](#12-stack)
13. [queue](#13-queue)
14. [pair & tuple](#14-pair--tuple)
15. [Algorithms Library](#15-algorithms-library)
16. [STL Optimization Tricks](#16-stl-optimization-tricks)

---

## 1. vector

### Internal Implementation
A **dynamic array** backed by a contiguous block of memory. When capacity is exceeded, it allocates ~2x the current capacity and copies all elements (amortized O(1) push_back).

```
Internal: [1][2][3][4][_][_][_][_]
           ^size=4     ^capacity=8
```

### Complexity Table
| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Access [i] | O(1) | Direct indexing |
| push_back | O(1) amortized | O(n) on reallocation |
| pop_back | O(1) | |
| insert at front | O(n) | Shifts all elements |
| insert at position | O(n) | Shifts elements |
| erase | O(n) | Shifts elements |
| find | O(n) | Linear scan |
| sort | O(n log n) | |
| size/empty | O(1) | |

### Complete API Reference

```cpp
#include <vector>
using namespace std;

// Construction
vector<int> v1;                    // Empty
vector<int> v2(5);                 // 5 zeros
vector<int> v3(5, 7);             // {7,7,7,7,7}
vector<int> v4 = {1,2,3,4,5};     // Initializer list
vector<int> v5(v4.begin(), v4.begin()+3);  // From iterator range
vector<vector<int>> grid(n, vector<int>(m, 0));  // 2D

// Size & Capacity
v.size();          // Number of elements
v.capacity();      // Allocated space
v.empty();         // true if size == 0
v.max_size();      // Maximum possible elements
v.resize(10);      // Resize (fills new with 0)
v.resize(10, -1);  // Resize, fill new with -1
v.reserve(100);    // Reserve capacity (avoids reallocations)
v.shrink_to_fit(); // Release excess capacity

// Element access
v[i];              // No bounds check — FASTER
v.at(i);           // Bounds check — SAFER
v.front();         // First element
v.back();          // Last element
v.data();          // Raw pointer to underlying array

// Modifiers
v.push_back(x);                    // Add to end
v.pop_back();                      // Remove from end
v.insert(v.begin(), x);            // Insert at front: O(n)
v.insert(v.begin()+i, x);         // Insert at index i
v.insert(v.end(), other.begin(), other.end());  // Append another vector
v.emplace_back(x);                 // Construct in place (faster)
v.emplace(v.begin()+i, x);        // Emplace at position
v.erase(v.begin()+i);             // Erase at index
v.erase(v.begin()+i, v.begin()+j); // Erase range [i, j)
v.clear();                         // Remove all elements
v.assign(5, 0);                   // Assign 5 zeros
swap(v1, v2);                      // Swap two vectors: O(1)

// Iterators
v.begin(); v.end();                // Forward iterators
v.rbegin(); v.rend();              // Reverse iterators
v.cbegin(); v.cend();              // Const iterators

// Common patterns
// Erase-remove idiom (remove all occurrences of value)
v.erase(remove(v.begin(), v.end(), target), v.end());

// Remove duplicates from sorted vector
v.erase(unique(v.begin(), v.end()), v.end());

// Check if element exists
bool exists = find(v.begin(), v.end(), x) != v.end();
// Or for sorted:
bool exists = binary_search(v.begin(), v.end(), x);
```

### Interview Tricks

```cpp
// Reverse vector
reverse(v.begin(), v.end());

// Rotate (shift left by k positions)
rotate(v.begin(), v.begin()+k, v.end());

// Fill with value
fill(v.begin(), v.end(), 0);
iota(v.begin(), v.end(), 1);  // Fill 1,2,3,4,...

// Min/Max element
auto minIt = min_element(v.begin(), v.end());
auto maxIt = max_element(v.begin(), v.end());
int minVal = *minIt;
int minIdx = minIt - v.begin();

// Sum of elements
int sum = accumulate(v.begin(), v.end(), 0);
long long sum = accumulate(v.begin(), v.end(), 0LL); // Use 0LL!

// Count occurrences
int cnt = count(v.begin(), v.end(), x);
int cnt = count_if(v.begin(), v.end(), [](int x){ return x > 5; });
```

---

## 2. array

### When to Use
Fixed-size arrays known at compile time. Slightly faster than vector, same as C-arrays but with STL interface.

```cpp
#include <array>
array<int, 5> a = {1, 2, 3, 4, 5};
a.size();    // 5 (compile-time constant)
a.fill(0);   // Fill all with 0
sort(a.begin(), a.end());
```

---

## 3. deque

### Internal Implementation
**Double-ended queue** backed by a sequence of fixed-size chunks. O(1) insertion/deletion at both ends.

```
Chunks: [4][5][6] [7][8][9] [10][_][_]
         ←front         back→
```

| Operation | Complexity |
|-----------|-----------|
| push_front / push_back | O(1) |
| pop_front / pop_back | O(1) |
| Access [i] | O(1) |
| Insert/erase middle | O(n) |

```cpp
#include <deque>
deque<int> dq;
dq.push_front(1);   // Add to front
dq.push_back(2);    // Add to back
dq.pop_front();     // Remove from front
dq.pop_back();      // Remove from back
dq.front();         // First element
dq.back();          // Last element
dq[i];              // Random access
```

### Interview Use Cases
- Sliding window maximum (monotonic deque)
- BFS level-order traversal (can use queue, but deque is flexible)
- Implement double-ended queue problems

---

## 4. list (Doubly Linked List)

### When to Use
When you need O(1) insertions/deletions at any known position. Rarely used in FAANG interviews — use vector or deque.

```cpp
#include <list>
list<int> l = {1, 2, 3, 4, 5};
l.push_front(0);
l.push_back(6);
l.pop_front();
l.pop_back();
// No random access: l[i] doesn't work
```

---

## 5. map

### Internal Implementation
**Red-Black Tree** (Self-balancing BST). Keys are **always sorted** in ascending order.

```
        4
       / \
      2   6
     / \ / \
    1  3 5  7
```

### Complexity Table
| Operation | Complexity |
|-----------|-----------|
| Insert | O(log n) |
| Delete | O(log n) |
| Search | O(log n) |
| Access [key] | O(log n) |
| Iteration | O(n) in sorted order |

### Complete API Reference

```cpp
#include <map>
map<string, int> freq;

// Insert/Update
freq["apple"] = 5;           // Insert or update
freq.insert({"banana", 3});  // Insert (won't overwrite if exists)
freq.emplace("cherry", 2);   // Construct in place

// Access
freq["apple"];               // Creates entry if doesn't exist! (DANGER)
freq.at("apple");            // Throws if not found (SAFE)

// Search
auto it = freq.find("apple");
if (it != freq.end()) {
    cout << it->first << ": " << it->second;
}
bool exists = freq.count("apple") > 0;  // count returns 0 or 1

// Delete
freq.erase("apple");         // By key
freq.erase(it);              // By iterator

// Size
freq.size();
freq.empty();

// Iteration (sorted by key)
for (auto& [key, val] : freq) {
    cout << key << ": " << val << "\n";
}

// Bounds (useful for range queries)
auto lb = freq.lower_bound("b");  // First key >= "b"
auto ub = freq.upper_bound("c");  // First key > "c"

// Reverse iteration
for (auto it = freq.rbegin(); it != freq.rend(); it++) {
    cout << it->first << ": " << it->second << "\n";
}
```

### Interview Patterns

```cpp
// Frequency count
for (int x : nums) freq[x]++;

// Find mode (most frequent)
int maxFreq = max_element(freq.begin(), freq.end(),
    [](auto& a, auto& b){ return a.second < b.second; })->second;

// Group anagrams — sort string as key
map<string, vector<string>> groups;
for (string& s : words) {
    string key = s;
    sort(key.begin(), key.end());
    groups[key].push_back(s);
}
```

---

## 6. unordered_map

### Internal Implementation
**Hash Table** with chaining. Average O(1) operations. In worst case (hash collisions), degrades to O(n).

### Complexity Table
| Operation | Average | Worst |
|-----------|---------|-------|
| Insert | O(1) | O(n) |
| Delete | O(1) | O(n) |
| Search | O(1) | O(n) |

```cpp
#include <unordered_map>
unordered_map<int, int> umap;

// Same API as map, but:
// - Keys NOT sorted
// - O(1) average vs O(log n)
// - Use when order doesn't matter

umap[key] = value;
umap.find(key);
umap.count(key);
umap.erase(key);

// Reserve buckets (avoids rehashing, improves performance)
umap.reserve(1000);
umap.max_load_factor(0.25);  // Lower = less collisions, more memory
```

### Custom Hash (for pairs or custom types)

```cpp
// Hash for pair<int,int>
struct PairHash {
    size_t operator()(const pair<int,int>& p) const {
        return hash<long long>()(((long long)p.first << 32) | p.second);
    }
};
unordered_map<pair<int,int>, int, PairHash> dp;

// Hash for vector<int>
struct VectorHash {
    size_t operator()(const vector<int>& v) const {
        size_t seed = v.size();
        for (auto x : v) {
            seed ^= x + 0x9e3779b9 + (seed << 6) + (seed >> 2);
        }
        return seed;
    }
};
```

### When to Use map vs unordered_map

| Use `map` when | Use `unordered_map` when |
|---------------|------------------------|
| Need sorted iteration | Just need fast lookup |
| Range queries (lower/upper bound) | Frequency counting |
| Keys are complex objects | Keys are int/string |
| Predictable performance required | Average case O(1) needed |

---

## 7. set

### Internal Implementation
**Red-Black Tree** — same as `map` but only stores keys (no values). Always sorted. No duplicates.

### Complete API

```cpp
#include <set>
set<int> s = {3, 1, 4, 1, 5, 9};  // {1, 3, 4, 5, 9} — duplicates removed, sorted

s.insert(6);
s.erase(3);
s.find(4);         // Returns iterator, or s.end() if not found
s.count(4);        // 0 or 1
s.lower_bound(4);  // First element >= 4
s.upper_bound(4);  // First element > 4
s.size();
s.empty();

// Iteration (sorted)
for (int x : s) cout << x << " ";

// Min and Max
*s.begin();        // Minimum
*s.rbegin();       // Maximum
```

### Interview Patterns

```cpp
// Sliding window with ordered set
set<int> window;
// Add/remove elements, get min with *window.begin()

// Next greater/smaller element in sorted order
auto it = s.upper_bound(x);  // First > x
if (it != s.end()) cout << *it;  // Next greater
if (it != s.begin()) cout << *prev(it);  // Previous smaller

// Check if all elements are unique
set<int> unique(v.begin(), v.end());
bool allUnique = unique.size() == v.size();
```

---

## 8. unordered_set

### When to Use
Fast O(1) membership check, no ordering needed.

```cpp
#include <unordered_set>
unordered_set<int> seen;

seen.insert(x);
seen.count(x);           // 0 or 1
seen.find(x) != seen.end();  // Check membership

// Common interview pattern: seen set for cycle/duplicate detection
for (int x : nums) {
    if (seen.count(x)) return true;  // Duplicate found
    seen.insert(x);
}
```

---

## 9. multiset

### Internal Implementation
Same Red-Black Tree as `set`, but **allows duplicate elements**. Stores all duplicates in sorted order.

```cpp
#include <set>  // multiset is in the same header
multiset<int> ms = {3, 1, 4, 1, 5, 9, 2, 6, 5};
// Stored as: {1, 1, 2, 3, 4, 5, 5, 6, 9}

ms.insert(5);   // Now has three 5s
ms.erase(ms.find(5));   // Remove ONE 5 (use find + erase)
ms.erase(5);            // Remove ALL 5s (dangerous!)
ms.count(5);            // Count occurrences

// Min/Max
*ms.begin();    // Minimum
*ms.rbegin();   // Maximum
```

### Interview Use Case: Sliding Window Median

```cpp
// Maintain two multisets: lower half (max) and upper half (min)
multiset<int> lower, upper;
// Balance sizes to get median efficiently
```

---

## 10. multimap

```cpp
multimap<string, int> mm;
mm.insert({"key", 1});
mm.insert({"key", 2});  // Same key, different values
mm.count("key");        // 2

// Get all values for a key
auto range = mm.equal_range("key");
for (auto it = range.first; it != range.second; it++) {
    cout << it->second << " ";
}
```

---

## 11. priority_queue

### Internal Implementation
**Binary Heap** stored as an array. By default a **max-heap** (largest element on top).

```
Max-Heap:
        9
       / \
      7   8
     / \ / \
    5  6 3  4
```

### Complexity Table
| Operation | Complexity |
|-----------|-----------|
| push | O(log n) |
| pop | O(log n) |
| top | O(1) |
| size/empty | O(1) |

### Complete API

```cpp
#include <queue>  // priority_queue is in <queue>

// Max-heap (default)
priority_queue<int> maxPQ;
maxPQ.push(3); maxPQ.push(1); maxPQ.push(4);
maxPQ.top();   // 4 (maximum)
maxPQ.pop();   // Remove maximum

// Min-heap
priority_queue<int, vector<int>, greater<int>> minPQ;
minPQ.push(3); minPQ.push(1); minPQ.push(4);
minPQ.top();   // 1 (minimum)

// Custom comparator with lambda
auto cmp = [](pair<int,int> a, pair<int,int> b) {
    return a.second > b.second;  // Min-heap by second element
};
priority_queue<pair<int,int>, vector<pair<int,int>>, decltype(cmp)> pq(cmp);

// Custom comparator with struct
struct Compare {
    bool operator()(pair<int,int> a, pair<int,int> b) {
        return a.second > b.second;  // Min-heap by second
    }
};
priority_queue<pair<int,int>, vector<pair<int,int>>, Compare> pq;

// Build from vector
vector<int> v = {3,1,4,1,5,9};
priority_queue<int> pq(v.begin(), v.end());
```

### Interview Patterns

```cpp
// K largest elements
priority_queue<int, vector<int>, greater<int>> minPQ;
for (int x : nums) {
    minPQ.push(x);
    if (minPQ.size() > k) minPQ.pop();  // Keep only k elements
}
// minPQ now contains k largest, top() is kth largest

// Dijkstra's algorithm
priority_queue<pair<int,int>, vector<pair<int,int>>, greater<pair<int,int>>> pq;
pq.push({0, src});  // {dist, node}
while (!pq.empty()) {
    auto [d, u] = pq.top(); pq.pop();
    for (auto [v, w] : graph[u]) {
        if (d + w < dist[v]) {
            dist[v] = d + w;
            pq.push({dist[v], v});
        }
    }
}

// Merge K sorted arrays
// Use min-heap with {value, array_index, element_index}
```

---

## 12. stack

### Internal Implementation
Adapter over `deque` (or `vector`). **LIFO** — Last In, First Out.

```cpp
#include <stack>
stack<int> st;

st.push(1);    // Push onto top
st.push(2);
st.top();      // Access top: O(1) — returns 2
st.pop();      // Remove top: O(1)
st.empty();    // Check if empty
st.size();     // Number of elements

// Interview patterns using stack
// 1. Balanced parentheses
// 2. Next greater element
// 3. Monotonic stack problems
// 4. Expression evaluation
// 5. Implement queue using stacks
```

---

## 13. queue

### Internal Implementation
Adapter over `deque`. **FIFO** — First In, First Out.

```cpp
#include <queue>
queue<int> q;

q.push(1);     // Enqueue at back
q.push(2);
q.front();     // Access front: O(1) — returns 1
q.back();      // Access back: O(1)
q.pop();       // Dequeue from front: O(1)
q.empty();
q.size();

// BFS template using queue
queue<int> bfsQ;
bfsQ.push(start);
while (!bfsQ.empty()) {
    int node = bfsQ.front();
    bfsQ.pop();
    for (int neighbor : graph[node]) {
        if (!visited[neighbor]) {
            visited[neighbor] = true;
            bfsQ.push(neighbor);
        }
    }
}
```

---

## 14. pair & tuple

### pair

```cpp
#include <utility>
pair<int, string> p = {42, "hello"};
p.first;         // 42
p.second;        // "hello"

// Make pair
auto p2 = make_pair(1, 2);

// Pair comparison (lexicographic by default)
pair<int,int> a = {1, 2}, b = {1, 3};
a < b;  // true (compares first, then second)

// Common usage: coordinate, graph edge, sorting by multiple keys
vector<pair<int,int>> edges;  // {cost, node}
sort(edges.begin(), edges.end());  // Sorts by cost, then node

// Structured bindings (C++17)
auto [x, y] = p;  // x=42, y="hello"
for (auto& [key, val] : myMap) { /* ... */ }
```

### tuple

```cpp
#include <tuple>
tuple<int, string, double> t = {1, "hello", 3.14};

get<0>(t);   // 1
get<1>(t);   // "hello"
get<2>(t);   // 3.14

auto t2 = make_tuple(1, "world", 2.71);

// Structured binding
auto [a, b, c] = t;

// Tie (assign tuple elements to variables)
int x; string s; double d;
tie(x, s, d) = t;

// Useful for returning 3+ values
tuple<int,int,int> solve() {
    return {min_val, max_val, count};
}
auto [mn, mx, cnt] = solve();
```

---

## 15. Algorithms Library

```cpp
#include <algorithm>
#include <numeric>

// ===== Sorting =====
sort(v.begin(), v.end());                                    // O(n log n)
sort(v.begin(), v.end(), greater<int>());                    // Descending
stable_sort(v.begin(), v.end());                             // Stable sort
partial_sort(v.begin(), v.begin()+k, v.end());               // Only sort first k
nth_element(v.begin(), v.begin()+k, v.end());                // kth element in O(n) avg

// ===== Searching =====
binary_search(v.begin(), v.end(), x);                        // O(log n), requires sorted
lower_bound(v.begin(), v.end(), x);                          // First >= x
upper_bound(v.begin(), v.end(), x);                          // First > x
equal_range(v.begin(), v.end(), x);                          // Range of equal elements
find(v.begin(), v.end(), x);                                 // Linear search
find_if(v.begin(), v.end(), pred);                           // Find by predicate

// ===== Min/Max =====
min(a, b);
max(a, b);
min({a, b, c, d});                                           // Multiple values
max_element(v.begin(), v.end());
min_element(v.begin(), v.end());
minmax_element(v.begin(), v.end());                          // Returns pair of iterators
clamp(x, lo, hi);                                            // Clamp to [lo, hi]

// ===== Permutations =====
next_permutation(v.begin(), v.end());                        // Next lexicographic permutation
prev_permutation(v.begin(), v.end());                        // Previous permutation

// Generate all permutations:
sort(v.begin(), v.end());
do {
    // process permutation
} while (next_permutation(v.begin(), v.end()));

// ===== Transform & Fill =====
fill(v.begin(), v.end(), 0);                                 // Fill with value
iota(v.begin(), v.end(), 1);                                 // 1, 2, 3, 4, ...
transform(v.begin(), v.end(), v.begin(), [](int x){ return x*2; });  // Double each

// ===== Set Operations (requires sorted input) =====
set_intersection(a.begin(), a.end(), b.begin(), b.end(), out.begin());
set_union(a.begin(), a.end(), b.begin(), b.end(), out.begin());
set_difference(a.begin(), a.end(), b.begin(), b.end(), out.begin());

// ===== Numeric =====
accumulate(v.begin(), v.end(), 0);                           // Sum
accumulate(v.begin(), v.end(), 1, multiplies<int>());        // Product
partial_sum(v.begin(), v.end(), prefix.begin());             // Prefix sums
adjacent_difference(v.begin(), v.end(), diff.begin());       // Differences
inner_product(a.begin(), a.end(), b.begin(), 0);             // Dot product
gcd(a, b);                                                   // GCD (C++17)
lcm(a, b);                                                   // LCM (C++17)

// ===== Manipulation =====
reverse(v.begin(), v.end());
rotate(v.begin(), v.begin()+k, v.end());                     // Left rotate by k
random_shuffle(v.begin(), v.end());                          // Shuffle
shuffle(v.begin(), v.end(), mt19937(random_device{}()));    // C++11 shuffle
unique(v.begin(), v.end());                                  // Remove consecutive dups (sorted)
remove(v.begin(), v.end(), x);                               // Move to end, returns new end
replace(v.begin(), v.end(), old_val, new_val);

// ===== Count =====
count(v.begin(), v.end(), x);                                // Count occurrences
count_if(v.begin(), v.end(), pred);                         // Count by predicate

// ===== Check =====
all_of(v.begin(), v.end(), pred);                            // All satisfy predicate
any_of(v.begin(), v.end(), pred);                            // Any satisfies predicate
none_of(v.begin(), v.end(), pred);                           // None satisfies predicate
is_sorted(v.begin(), v.end());                               // Check if sorted
```

---

## 16. STL Optimization Tricks

### 1. Reserve Capacity Before Bulk Insertions

```cpp
vector<int> v;
v.reserve(n);      // Avoids O(n log n) reallocations total
for (int i = 0; i < n; i++) v.push_back(i);
```

### 2. emplace_back vs push_back

```cpp
// push_back: constructs then copies/moves
v.push_back(pair<int,int>(1, 2));

// emplace_back: constructs in place (no copy)
v.emplace_back(1, 2);  // Faster for complex objects
```

### 3. Avoid [] Operator in Maps When Checking

```cpp
// BAD: creates entry if not found!
if (myMap["key"] == 0) { ... }

// GOOD:
if (myMap.count("key") && myMap["key"] == 0) { ... }
// OR:
if (auto it = myMap.find("key"); it != myMap.end()) { ... }
```

### 4. Use unordered_map::reserve

```cpp
unordered_map<int,int> freq;
freq.reserve(n);          // Avoids rehashing
freq.max_load_factor(0.25); // More buckets = fewer collisions
```

### 5. String Operations

```cpp
// SLOW: string concatenation in loop
string result = "";
for (string& s : v) result += s;  // O(n²) total!

// FAST: use stringstream or join then build
ostringstream oss;
for (string& s : v) oss << s;
string result = oss.str();
```

### 6. Sorting Custom Objects

```cpp
// Comparator function
bool cmp(const pair<int,int>& a, const pair<int,int>& b) {
    if (a.first != b.first) return a.first < b.first;
    return a.second > b.second;  // Tie-break: second descending
}
sort(v.begin(), v.end(), cmp);

// Lambda (cleaner for interviews)
sort(v.begin(), v.end(), [](const pair<int,int>& a, const pair<int,int>& b) {
    return a.first != b.first ? a.first < b.first : a.second > b.second;
});
```

### 7. Two-Pass Iteration Pattern

```cpp
// Count elements, then process in one pass
unordered_map<int,int> freq;
for (int x : nums) freq[x]++;
for (int x : nums) {
    if (freq[x] == 1) return x;  // First unique
}
```

---

## STL Cheat Sheet — Quick Reference

```cpp
// ========= CONTAINERS =========
// Sequential
vector<T>      // Dynamic array, O(1) random access
deque<T>       // Double-ended, O(1) both ends
list<T>        // Doubly linked, O(1) insert/delete at pointer
array<T,N>     // Fixed size, stack allocated

// Associative (sorted, tree-based)
map<K,V>       // K-V pairs, sorted by K
set<K>         // Unique keys, sorted
multimap<K,V>  // Sorted, duplicate keys allowed
multiset<K>    // Sorted, duplicates allowed

// Unordered (hash-based)
unordered_map<K,V>  // Hash table K-V
unordered_set<K>    // Hash table keys

// Adaptors
stack<T>            // LIFO
queue<T>            // FIFO
priority_queue<T>   // Max-heap by default

// ========= KEY OPERATIONS =========
// All sorted containers: lower_bound(), upper_bound()
// All containers: size(), empty(), clear()
// All sequence containers: begin(), end(), front(), back()
// Insert: push_back(), insert(), emplace_back(), emplace()
// Remove: pop_back(), erase(), pop(), pop_front()
```

---

*Next: [Section 3 — DSA Foundations](./Section3_DSA_Foundations.md)*
