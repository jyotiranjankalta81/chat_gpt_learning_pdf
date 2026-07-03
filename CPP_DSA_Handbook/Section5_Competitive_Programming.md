# Section 5: Competitive Programming Optimization
## Fast I/O, Memory & STL Optimization, Advanced Tricks

> **Goal:** Write code that is not just correct, but fast enough to pass tight time limits. These techniques separate good engineers from elite competitive programmers.

---

## Table of Contents
1. [Fast I/O](#1-fast-io)
2. [Memory Optimization](#2-memory-optimization)
3. [STL Optimization Tricks](#3-stl-optimization-tricks)
4. [Recursion Optimization](#4-recursion-optimization)
5. [Bitset Tricks](#5-bitset-tricks)
6. [Mathematical Optimizations](#6-mathematical-optimizations)
7. [Common Competitive Programming Templates](#7-common-competitive-programming-templates)

---

## 1. Fast I/O

### The Standard Boilerplate

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);  // Decouple C and C++ I/O
    cin.tie(NULL);                      // Untie cin from cout
    cout.tie(NULL);                     // Optional additional speedup
    
    // Your code here
    return 0;
}
```

**Why this works:**
- `sync_with_stdio(false)`: By default, C++ streams are synced with C streams (printf/scanf). Disabling this makes cin/cout much faster.
- `cin.tie(NULL)`: By default, cin is tied to cout (flushes cout before each cin). Untying avoids this overhead.
- **Warning:** After this, don't mix `cin/cout` with `scanf/printf`.

### Speed Comparison

| Method | Relative Speed | Use When |
|--------|---------------|----------|
| `scanf/printf` | 100% | C-style, legacy code |
| `cin/cout` (default) | ~50% | Normal C++ |
| `cin/cout` (fast I/O) | ~95% | Competitive programming |
| Custom fast read | ~200%+ | Extreme performance |

### Custom Fast Input (Ultra-Fast)

```cpp
// Fast integer reader — bypasses stream overhead entirely
inline int readInt() {
    int x = 0; char c = getchar_unlocked();
    while (c < '0' || c > '9') c = getchar_unlocked();
    while (c >= '0' && c <= '9') { x = x*10 + c-'0'; c = getchar_unlocked(); }
    return x;
}

// Fast output
inline void writeInt(int x) {
    if (x == 0) { putchar_unlocked('0'); putchar_unlocked('\n'); return; }
    char buf[20]; int len = 0;
    while (x > 0) { buf[len++] = '0' + x%10; x /= 10; }
    for (int i = len-1; i >= 0; i--) putchar_unlocked(buf[i]);
    putchar_unlocked('\n');
}
```

### Output Optimization

```cpp
// SLOW: endl flushes the buffer every time!
for (int i = 0; i < n; i++) cout << result[i] << endl;

// FAST: '\n' doesn't flush
for (int i = 0; i < n; i++) cout << result[i] << '\n';

// Even faster: build string and output once
string out = "";
for (int i = 0; i < n; i++) out += to_string(result[i]) + '\n';
cout << out;

// Or use ostringstream
ostringstream oss;
for (int i = 0; i < n; i++) oss << result[i] << '\n';
cout << oss.str();
```

---

## 2. Memory Optimization

### Stack vs Heap

```cpp
// Stack — fast, limited (~8MB default)
int arr[1000000];  // 4MB on stack — might cause stack overflow!

// Heap — large, slightly slower
vector<int> arr(1000000);  // Safe

// Global arrays — in BSS/data segment, very fast, large limit
int dp[1001][1001];  // 4MB global — SAFE and fast
int grid[1000][1000];

// Rule: For arrays > ~100KB, use global or heap allocation
```

### Memory Pools (for linked structures)

```cpp
// Instead of new/delete for each node (slow allocation):
struct Node {
    int val;
    Node* next;
};

// Memory pool — pre-allocate bulk
const int POOL_SIZE = 100000;
Node pool[POOL_SIZE];
int poolPtr = 0;

Node* newNode(int val) {
    pool[poolPtr].val = val;
    pool[poolPtr].next = nullptr;
    return &pool[poolPtr++];
}
// This is 10-20x faster than individual new
```

### Reducing Memory Usage

```cpp
// 1. Use int instead of long long when possible
//    int: 4 bytes, long long: 8 bytes
//    For a dp[1000][1000]: saves 4MB

// 2. Compress coordinates for large ranges
//    Values in [0, 1e9] but only n distinct values
vector<int> vals = /* distinct values */;
sort(vals.begin(), vals.end());
// Compress: original value → compressed index
auto compress = [&](int x) {
    return lower_bound(vals.begin(), vals.end(), x) - vals.begin();
};

// 3. Bitset instead of bool array (8x memory reduction)
bitset<1000000> visited;  // 125KB instead of 1MB
visited[i] = 1;
visited.test(i);

// 4. Rolling array (DP space optimization)
// Instead of dp[n][m], use dp[2][m] (only need previous row)
int prev[m+1] = {}, curr[m+1] = {};
// or use only 1D array with careful ordering
```

---

## 3. STL Optimization Tricks

### Vector Performance

```cpp
// ALWAYS reserve when you know the size
vector<int> v;
v.reserve(n);  // Single allocation, then n * O(1) push_back

// emplace_back > push_back for non-trivial types
vector<pair<int,int>> edges;
edges.reserve(m);
edges.emplace_back(u, v);  // No temporary object created

// Move semantics for large vectors
vector<int> buildResult() {
    vector<int> v;
    // ... build v ...
    return v;  // RVO (Return Value Optimization) — no copy!
}

// Swap trick to free memory
vector<int> v = {1,2,3,4,5};
v.clear();           // Size = 0, but capacity stays!
vector<int>().swap(v);  // Actually free the memory
// Or: v.shrink_to_fit();
```

### HashMap Performance

```cpp
// unordered_map with custom hash for better performance
struct CustomHash {
    size_t operator()(int x) const {
        x = ((x >> 16) ^ x) * 0x45d9f3b;
        x = ((x >> 16) ^ x) * 0x45d9f3b;
        x = (x >> 16) ^ x;
        return x;
    }
};
unordered_map<int, int, CustomHash> fast_map;

// Avoiding worst case O(n) due to hash collisions
// Standard hash for integers can be hacked in competitive programming
// Solution: use the above custom hash, or use map (O(log n) but reliable)

// Reserve to avoid rehashing
unordered_map<int,int> freq;
freq.reserve(1 << 20);  // Power of 2 for efficiency
freq.max_load_factor(0.25);  // Lower = fewer collisions, more memory
```

### Sort Optimization

```cpp
// Avoid comparison functions for simple types
sort(v.begin(), v.end());  // Faster than custom comparator for ints

// Partial sort — faster than full sort if only need k smallest
partial_sort(v.begin(), v.begin()+k, v.end());  // O(n log k)

// nth_element — O(n) to find kth element without fully sorting
nth_element(v.begin(), v.begin()+k, v.end());
// After: v[k] is the kth smallest, smaller elements before it

// Counting sort for bounded integers
// O(n + range) — much faster than O(n log n) for small ranges
void countSort(vector<int>& arr, int maxVal) {
    vector<int> count(maxVal+1, 0);
    for (int x : arr) count[x]++;
    int idx = 0;
    for (int i = 0; i <= maxVal; i++)
        while (count[i]-- > 0) arr[idx++] = i;
}

// Radix sort for large integer ranges
// O(d * n) where d = number of digits
```

---

## 4. Recursion Optimization

### Tail Recursion

```cpp
// NOT tail recursive (computation after recursive call)
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n-1);  // Multiplication happens AFTER return
}

// Tail recursive (accumulator pattern)
int factorial(int n, int acc = 1) {
    if (n <= 1) return acc;
    return factorial(n-1, n * acc);  // Recursive call is last operation
}
// Note: C++ compilers may optimize tail recursion to iteration
```

### Memoization vs Bottom-Up DP

```cpp
// Top-down with memoization
// Pros: Only computes needed states, natural recursion structure
// Cons: Recursion overhead, stack limit
unordered_map<int,long long> memo;
long long topDown(int n) {
    if (n <= 1) return n;
    if (memo.count(n)) return memo[n];
    return memo[n] = topDown(n-1) + topDown(n-2);
}

// Bottom-up iterative (preferred for deep recursion)
// Pros: No recursion overhead, predictable memory
// Cons: Must compute all states
long long bottomUp(int n) {
    if (n <= 1) return n;
    vector<long long> dp(n+1);
    dp[0] = 0; dp[1] = 1;
    for (int i = 2; i <= n; i++) dp[i] = dp[i-1] + dp[i-2];
    return dp[n];
}
```

### Stack Overflow Prevention

```cpp
// For deep recursion (n > 10000), convert to iterative
// or increase stack size

// Manual stack to simulate recursion
void dfsIterative(int start, vector<vector<int>>& adj) {
    stack<int> st;
    vector<bool> visited(adj.size(), false);
    st.push(start);
    
    while (!st.empty()) {
        int node = st.top(); st.pop();
        if (visited[node]) continue;
        visited[node] = true;
        // Process node
        for (int neighbor : adj[node]) {
            if (!visited[neighbor]) st.push(neighbor);
        }
    }
}

// For tree DFS with parent tracking
struct Frame {
    int node, parentEdge, childIdx;
};
void treeDP(int root) {
    stack<Frame> st;
    st.push({root, -1, 0});
    while (!st.empty()) {
        auto& [node, par, ci] = st.top();
        if (ci < children[node].size()) {
            int child = children[node][ci++];
            st.push({child, node, 0});
        } else {
            // Post-processing of node
            st.pop();
        }
    }
}
```

---

## 5. Bitset Tricks

### Basic Bitset Operations

```cpp
#include <bitset>

// Fixed-size bitset (size must be compile-time constant)
bitset<100> b;          // 100 bits, all 0
b.set(5);               // Set bit 5
b.reset(5);             // Clear bit 5
b.flip(5);              // Toggle bit 5
b.test(5);              // Check bit 5
b.count();              // Count set bits
b.none();               // True if all 0
b.any();                // True if any 1
b.all();                // True if all 1
b.size();               // Total bits (100)

// Bitwise operations between bitsets
bitset<100> a, b;
a & b;   // AND
a | b;   // OR
a ^ b;   // XOR
~a;      // NOT
a <<= 1; // Shift left
a >>= 1; // Shift right

// Initialize from string or number
bitset<8> bs("10110100");
bitset<8> bn(180);  // 180 in binary
```

### Bitset for Performance

```cpp
// Problem: Subset sum — is there a subset summing to S?
// O(n * S) standard DP vs O(n * S / 64) with bitset!

bool subsetSum(vector<int>& nums, int S) {
    bitset<10001> dp;
    dp[0] = 1;
    for (int x : nums) dp |= (dp << x);
    return dp[S];
}
// Each bitset operation processes 64 bits at once — 64x speedup!

// Problem: Count set bits in range [l, r]
bitset<1000001> primes;
primes.set();
primes.reset(0); primes.reset(1);
for (int i = 2; i < 1000; i++)
    if (primes.test(i))
        for (int j = i*i; j <= 1000000; j += i) primes.reset(j);
// Count primes in [l, r]: count bits in range
```

### Bitmask DP

```cpp
// Traveling Salesman Problem — O(2^n * n^2) with bitmask DP
int tsp(int mask, int pos, vector<vector<int>>& dist, vector<vector<int>>& dp) {
    int n = dist.size();
    if (mask == (1 << n) - 1) return dist[pos][0];
    if (dp[mask][pos] != -1) return dp[mask][pos];
    
    int result = INT_MAX;
    for (int next = 0; next < n; next++) {
        if (mask & (1 << next)) continue;
        int newMask = mask | (1 << next);
        result = min(result, dist[pos][next] + tsp(newMask, next, dist, dp));
    }
    return dp[mask][pos] = result;
}

// Enumerate all subsets of a mask
int mask = 0b1011010;
for (int sub = mask; sub > 0; sub = (sub-1) & mask) {
    // Process sub (subset of mask)
}
// Total iterations: 3^n (sum of C(n,k)*2^k)

// Enumerate all submasks of size k
// ... (more complex — see competitive programming resources)
```

---

## 6. Mathematical Optimizations

### Modular Arithmetic

```cpp
const int MOD = 1e9 + 7;

// All operations modulo MOD
long long add(long long a, long long b) { return (a + b) % MOD; }
long long mul(long long a, long long b) { return a % MOD * (b % MOD) % MOD; }
long long sub(long long a, long long b) { return ((a - b) % MOD + MOD) % MOD; }

// Modular exponentiation: a^b mod m
long long power(long long a, long long b, long long mod = MOD) {
    long long res = 1;
    a %= mod;
    while (b > 0) {
        if (b & 1) res = res * a % mod;
        a = a * a % mod;
        b >>= 1;
    }
    return res;
}

// Modular inverse (when MOD is prime): a^(MOD-2) mod MOD
long long modInverse(long long a) { return power(a, MOD-2); }

// Modular division
long long divide(long long a, long long b) { return a % MOD * modInverse(b) % MOD; }

// Precompute factorials for combinations
vector<long long> fact(n+1), inv_fact(n+1);
fact[0] = 1;
for (int i = 1; i <= n; i++) fact[i] = fact[i-1] * i % MOD;
inv_fact[n] = modInverse(fact[n]);
for (int i = n-1; i >= 0; i--) inv_fact[i] = inv_fact[i+1] * (i+1) % MOD;

// nCr mod p
long long nCr(int n, int r) {
    if (r < 0 || r > n) return 0;
    return fact[n] % MOD * inv_fact[r] % MOD * inv_fact[n-r] % MOD;
}
```

### GCD and LCM

```cpp
// C++17 built-in
#include <numeric>
int g = gcd(48, 18);  // 6
int l = lcm(4, 6);    // 12

// Manual implementation
int gcd(int a, int b) { return b == 0 ? a : gcd(b, a%b); }
long long lcm(long long a, long long b) { return a / gcd(a, b) * b; }

// Extended GCD (for modular inverse when MOD not prime)
long long extGCD(long long a, long long b, long long& x, long long& y) {
    if (b == 0) { x = 1; y = 0; return a; }
    long long x1, y1;
    long long g = extGCD(b, a%b, x1, y1);
    x = y1;
    y = x1 - (a/b) * y1;
    return g;
}
```

### Sieve of Eratosthenes

```cpp
// O(n log log n) — find all primes up to n
vector<bool> sieve(int n) {
    vector<bool> isPrime(n+1, true);
    isPrime[0] = isPrime[1] = false;
    for (int i = 2; (long long)i*i <= n; i++) {
        if (isPrime[i]) {
            for (int j = i*i; j <= n; j += i) isPrime[j] = false;
        }
    }
    return isPrime;
}

// Linear sieve — O(n) strict
vector<int> linearSieve(int n) {
    vector<int> primes;
    vector<int> minPrime(n+1, 0);
    for (int i = 2; i <= n; i++) {
        if (!minPrime[i]) { minPrime[i] = i; primes.push_back(i); }
        for (int p : primes) {
            if (p > minPrime[i] || (long long)i*p > n) break;
            minPrime[i*p] = p;
        }
    }
    return primes;
}
```

### Segment Tree (for range queries)

```cpp
class SegTree {
    int n;
    vector<int> tree;
public:
    SegTree(int n) : n(n), tree(4*n, 0) {}
    
    void build(vector<int>& arr, int node, int start, int end) {
        if (start == end) { tree[node] = arr[start]; return; }
        int mid = (start + end) / 2;
        build(arr, 2*node, start, mid);
        build(arr, 2*node+1, mid+1, end);
        tree[node] = tree[2*node] + tree[2*node+1];
    }
    
    void update(int node, int start, int end, int idx, int val) {
        if (start == end) { tree[node] = val; return; }
        int mid = (start + end) / 2;
        if (idx <= mid) update(2*node, start, mid, idx, val);
        else update(2*node+1, mid+1, end, idx, val);
        tree[node] = tree[2*node] + tree[2*node+1];
    }
    
    int query(int node, int start, int end, int l, int r) {
        if (r < start || end < l) return 0;
        if (l <= start && end <= r) return tree[node];
        int mid = (start + end) / 2;
        return query(2*node, start, mid, l, r) +
               query(2*node+1, mid+1, end, l, r);
    }
    
    void update(int idx, int val) { update(1, 0, n-1, idx, val); }
    int query(int l, int r) { return query(1, 0, n-1, l, r); }
};
```

---

## 7. Common Competitive Programming Templates

### Complete Competitive Programming Header

```cpp
#include <bits/stdc++.h>
using namespace std;

// Type aliases
typedef long long ll;
typedef unsigned long long ull;
typedef long double ld;
typedef pair<int,int> pii;
typedef pair<ll,ll> pll;
typedef vector<int> vi;
typedef vector<ll> vll;
typedef vector<pii> vpii;
typedef vector<vector<int>> vvi;

// Macros (use sparingly — reduce readability)
#define pb push_back
#define mp make_pair
#define fi first
#define se second
#define all(x) (x).begin(), (x).end()
#define rall(x) (x).rbegin(), (x).rend()
#define sz(x) (int)(x).size()
#define rep(i,a,b) for(int i=(a);i<(b);i++)
#define F0R(i,n) for(int i=0;i<n;i++)

// Constants
const int INF = 1e9;
const ll LINF = 1e18;
const int MOD = 1e9 + 7;
const double PI = acos(-1.0);
const int dx[] = {0,0,1,-1};  // 4-directional grid
const int dy[] = {1,-1,0,0};
const int dx8[] = {0,0,1,-1,1,1,-1,-1};  // 8-directional
const int dy8[] = {1,-1,0,0,1,-1,1,-1};

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    
    int t;
    cin >> t;
    while (t--) {
        // solve
    }
    return 0;
}
```

### Debug Helper

```cpp
// Only active when DEBUG is defined: compile with -DDEBUG
#ifdef DEBUG
    #define dbg(x) cerr << #x << " = " << x << "\n"
    #define dbgv(v) { cerr << #v << " = ["; for (auto x : v) cerr << x << ","; cerr << "]\n"; }
    #define dbg2d(v) { cerr << #v << ":\n"; for (auto& row : v) { for (auto x : row) cerr << x << "\t"; cerr << "\n"; } }
#else
    #define dbg(x)
    #define dbgv(v)
    #define dbg2d(v)
#endif

// Usage:
int x = 42;
dbg(x);  // In debug mode: x = 42
         // In release mode: no output, no overhead
```

### Binary Indexed Tree (Fenwick Tree)

```cpp
class BIT {
    vector<int> tree;
    int n;
public:
    BIT(int n) : n(n), tree(n+1, 0) {}
    
    void update(int i, int delta) {  // O(log n)
        for (i++; i <= n; i += i & (-i)) tree[i] += delta;
    }
    
    int query(int i) {  // Prefix sum [0, i] O(log n)
        int sum = 0;
        for (i++; i > 0; i -= i & (-i)) sum += tree[i];
        return sum;
    }
    
    int query(int l, int r) { return query(r) - (l > 0 ? query(l-1) : 0); }
};
```

### Sparse Table (Range Minimum Query in O(1))

```cpp
class SparseTable {
    vector<vector<int>> table;
    vector<int> log2_;
    int n;
public:
    SparseTable(vector<int>& arr) : n(arr.size()), log2_(arr.size()+1, 0) {
        int LOG = __lg(n) + 1;
        table.assign(LOG, vector<int>(n));
        table[0] = arr;
        
        for (int i = 2; i <= n; i++) log2_[i] = log2_[i/2] + 1;
        
        for (int j = 1; j < LOG; j++)
            for (int i = 0; i + (1<<j) <= n; i++)
                table[j][i] = min(table[j-1][i], table[j-1][i + (1<<(j-1))]);
    }
    
    int query(int l, int r) {  // O(1) range minimum
        int k = log2_[r-l+1];
        return min(table[k][l], table[k][r - (1<<k) + 1]);
    }
};
```

---

## Performance Tips Summary

| Technique | Speedup | Memory Impact | When to Use |
|-----------|---------|---------------|-------------|
| Fast I/O | 2-4x I/O speed | None | Always in competitive programming |
| Global arrays | Slight | No stack limit | Large arrays |
| reserve() for vectors | Avoids reallocations | None | Known size beforehand |
| emplace_back | Small | None | Complex objects |
| unordered_map vs map | 5-10x avg | Slightly more | No ordered iteration needed |
| Bitset for DP | 64x | Less | Boolean DP on large sets |
| Bitmask DP | Algorithmic | Exponential | Small n (≤20) with subsets |
| Counting sort | O(n) vs O(n log n) | O(range) | Bounded integers |
| nth_element | O(n) vs O(n log n) | None | Only need kth element |
| '\n' vs endl | Avoids flush | None | Always in output loops |

---

*Next: [Section 6 — Interview Preparation](./Section6_Interview_Preparation.md)*
