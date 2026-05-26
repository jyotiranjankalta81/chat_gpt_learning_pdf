# Section 4: Complete DSA Pattern System
## 15 Core Patterns for FAANG Interviews

> **The Meta-Skill:** Recognizing which pattern to apply is more important than memorizing solutions. This section gives you a **pattern recognition radar** for every interview problem.

---

## Pattern Recognition Cheatsheet

| Signal in Problem | Pattern |
|------------------|---------|
| "subarray/substring of fixed length k" | Sliding Window (Fixed) |
| "longest/shortest subarray satisfying condition" | Sliding Window (Variable) |
| "sorted array, find pair summing to X" | Two Pointers |
| "search in sorted/rotated array" | Binary Search |
| "subarray sum equals k" | Prefix Sum |
| "count/check duplicates, frequency" | HashMap/HashSet |
| "matching parentheses, next greater/smaller" | Stack |
| "binary tree path, traversal" | Tree DFS/BFS |
| "shortest path, connected components, grid" | Graph BFS/DFS |
| "overlapping subproblems, optimization" | Dynamic Programming |
| "generate all combinations/permutations" | Backtracking |
| "k largest/smallest, median of stream" | Heap |
| "merge intervals, meeting rooms" | Intervals |
| "minimum coins, activity selection" | Greedy |
| "prefix search, word dictionary" | Trie |
| "XOR, check power of 2, bit count" | Bit Manipulation |

---

## Pattern 1: Sliding Window

### Concept
Move a window across an array/string. Avoid recomputing from scratch — add new element, remove old element.

```
arr = [1, 3, -1, -3, 5, 3, 6, 7]
       [1  3  -1] -3  5  3  6  7   → window [0,2], max=3
        1 [3  -1  -3] 5  3  6  7   → window [1,3], max=3
        1  3 [-1  -3  5] 3  6  7   → window [2,4], max=5
```

### Templates

```cpp
// Template 1: Fixed-size window
int maxSumWindow(vector<int>& arr, int k) {
    int windowSum = 0;
    for (int i = 0; i < k; i++) windowSum += arr[i];
    
    int maxSum = windowSum;
    for (int i = k; i < arr.size(); i++) {
        windowSum += arr[i] - arr[i-k];  // Slide: add new, remove old
        maxSum = max(maxSum, windowSum);
    }
    return maxSum;
}

// Template 2: Variable-size window (expand/shrink)
int longestSubstringKDistinct(string& s, int k) {
    unordered_map<char,int> freq;
    int left = 0, result = 0;
    
    for (int right = 0; right < s.size(); right++) {
        freq[s[right]]++;    // Expand window
        
        while (freq.size() > k) {     // Window condition violated
            freq[s[left]]--;           // Shrink from left
            if (freq[s[left]] == 0) freq.erase(s[left]);
            left++;
        }
        result = max(result, right - left + 1);
    }
    return result;
}

// Template 3: Sliding window maximum (Monotonic Deque)
vector<int> maxSlidingWindow(vector<int>& nums, int k) {
    deque<int> dq;  // Stores INDICES, decreasing order of values
    vector<int> result;
    
    for (int i = 0; i < nums.size(); i++) {
        // Remove elements outside window
        while (!dq.empty() && dq.front() <= i - k) dq.pop_front();
        // Remove smaller elements (maintain decreasing order)
        while (!dq.empty() && nums[dq.back()] <= nums[i]) dq.pop_back();
        
        dq.push_back(i);
        if (i >= k-1) result.push_back(nums[dq.front()]);  // Max = front
    }
    return result;
}
```

### Common Problems

| Problem | Pattern | Key Insight |
|---------|---------|-------------|
| Max sum subarray of size k | Fixed window | Sum = add right, remove left |
| Longest substring without repeating | Variable window | Use set/map to track |
| Minimum window substring | Variable window | Expand until valid, shrink |
| Sliding window maximum | Monotonic deque | Deque stores indices in decreasing order |
| Longest subarray with sum ≤ k | Variable window | Shrink when sum exceeds k |

### Dry Run: Minimum Window Substring

```
s = "ADOBECODEBANC", t = "ABC"
need: {A:1, B:1, C:1}, formed=0, required=3

R=0: A, freq{A:1}, formed=1
R=1: D, freq{D:1}, formed=1
R=2: O, ...
R=3: B, freq{B:1}, formed=2
R=4: E, ...
R=5: C, freq{C:1}, formed=3 ← All formed!
  → window="ADOBEC", len=6, minLen=6
  Shrink: L=0 A→freq{A:0}, formed=2, L=1
R=6: O, formed=2
...
Continue until optimal window "BANC" found
```

```cpp
string minWindow(string s, string t) {
    unordered_map<char,int> need, have;
    for (char c : t) need[c]++;
    
    int formed = 0, required = need.size();
    int left = 0, minLen = INT_MAX, minStart = 0;
    
    for (int right = 0; right < s.size(); right++) {
        have[s[right]]++;
        if (need.count(s[right]) && have[s[right]] == need[s[right]])
            formed++;
        
        while (formed == required) {
            if (right - left + 1 < minLen) {
                minLen = right - left + 1;
                minStart = left;
            }
            have[s[left]]--;
            if (need.count(s[left]) && have[s[left]] < need[s[left]])
                formed--;
            left++;
        }
    }
    return minLen == INT_MAX ? "" : s.substr(minStart, minLen);
}
```

---

## Pattern 2: Two Pointers

### Concept
Use two pointers that move toward each other or in the same direction to avoid O(n²) nested loops.

### Templates

```cpp
// Template 1: Opposite ends (sorted array)
int twoSum(vector<int>& arr, int target) {
    int left = 0, right = arr.size() - 1;
    while (left < right) {
        int sum = arr[left] + arr[right];
        if (sum == target) return {left, right};
        else if (sum < target) left++;
        else right--;
    }
    return {};
}

// Template 2: Same direction (fast/slow pointers)
// Remove duplicates from sorted array
int removeDuplicates(vector<int>& nums) {
    if (nums.empty()) return 0;
    int slow = 0;
    for (int fast = 1; fast < nums.size(); fast++) {
        if (nums[fast] != nums[slow]) {
            nums[++slow] = nums[fast];
        }
    }
    return slow + 1;
}

// Template 3: Floyd's cycle detection
bool hasCycle(ListNode* head) {
    ListNode* slow = head, *fast = head;
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) return true;
    }
    return false;
}

// 3Sum problem
vector<vector<int>> threeSum(vector<int>& nums) {
    sort(nums.begin(), nums.end());
    vector<vector<int>> result;
    
    for (int i = 0; i < nums.size()-2; i++) {
        if (i > 0 && nums[i] == nums[i-1]) continue;  // Skip duplicates
        
        int left = i+1, right = nums.size()-1;
        while (left < right) {
            int sum = nums[i] + nums[left] + nums[right];
            if (sum == 0) {
                result.push_back({nums[i], nums[left], nums[right]});
                while (left < right && nums[left] == nums[left+1]) left++;
                while (left < right && nums[right] == nums[right-1]) right--;
                left++; right--;
            } else if (sum < 0) left++;
            else right--;
        }
    }
    return result;
}
```

---

## Pattern 3: Binary Search

### Concept
Eliminate half the search space each iteration. Works on any **monotonically changing** condition.

```
Key Question: "What property changes from false → true (or true → false) 
               as we move across the search space?"
```

### Templates

```cpp
// Classic binary search
int binarySearch(vector<int>& arr, int target) {
    int l = 0, r = arr.size() - 1;
    while (l <= r) {
        int mid = l + (r - l) / 2;
        if (arr[mid] == target) return mid;
        else if (arr[mid] < target) l = mid + 1;
        else r = mid - 1;
    }
    return -1;
}

// Binary search on answer — find minimum satisfying condition
// "Is it possible to achieve X?" must be monotonic (F F F T T T)
int binarySearchOnAnswer() {
    int lo = min_possible, hi = max_possible;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (isPossible(mid)) hi = mid;  // mid might be answer, exclude nothing
        else lo = mid + 1;              // mid doesn't work, exclude it
    }
    return lo;
}
```

### Problem: Split Array Largest Sum (Hard)

```cpp
// Binary search on answer: what is the minimum possible largest sum?
bool canSplit(vector<int>& nums, int maxSum, int m) {
    int parts = 1, currSum = 0;
    for (int x : nums) {
        if (currSum + x > maxSum) { parts++; currSum = 0; }
        currSum += x;
    }
    return parts <= m;
}

int splitArray(vector<int>& nums, int m) {
    int lo = *max_element(nums.begin(), nums.end());
    int hi = accumulate(nums.begin(), nums.end(), 0);
    
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (canSplit(nums, mid, m)) hi = mid;
        else lo = mid + 1;
    }
    return lo;
}
```

---

## Pattern 4: Prefix Sum

### Concept
Precompute cumulative sums to answer range sum queries in O(1).

```
arr    = [1, 2, 3, 4, 5]
prefix = [0, 1, 3, 6, 10, 15]

sum(l, r) = prefix[r+1] - prefix[l]
sum(1, 3) = prefix[4] - prefix[1] = 10 - 1 = 9 ✓ (2+3+4=9)
```

### Templates

```cpp
// 1D Prefix Sum
vector<int> buildPrefix(vector<int>& arr) {
    int n = arr.size();
    vector<int> prefix(n+1, 0);
    for (int i = 0; i < n; i++) prefix[i+1] = prefix[i] + arr[i];
    return prefix;
}
int rangeSum(vector<int>& prefix, int l, int r) {
    return prefix[r+1] - prefix[l];  // sum of arr[l..r]
}

// 2D Prefix Sum
vector<vector<int>> build2DPrefix(vector<vector<int>>& grid) {
    int m = grid.size(), n = grid[0].size();
    vector<vector<int>> p(m+1, vector<int>(n+1, 0));
    for (int i = 1; i <= m; i++)
        for (int j = 1; j <= n; j++)
            p[i][j] = grid[i-1][j-1] + p[i-1][j] + p[i][j-1] - p[i-1][j-1];
    return p;
}
int query2D(vector<vector<int>>& p, int r1, int c1, int r2, int c2) {
    return p[r2+1][c2+1] - p[r1][c2+1] - p[r2+1][c1] + p[r1][c1];
}

// Subarray sum equals k (using prefix sum + hashmap)
int subarraySum(vector<int>& nums, int k) {
    unordered_map<int,int> prefixCount;
    prefixCount[0] = 1;
    int sum = 0, count = 0;
    for (int x : nums) {
        sum += x;
        count += prefixCount[sum - k];  // How many prefixes end at sum-k?
        prefixCount[sum]++;
    }
    return count;
}
```

---

## Pattern 5: HashMap / HashSet

### Concept
Trade space for time. Convert O(n²) lookups into O(n) with O(1) hash operations.

### Templates

```cpp
// Two Sum — classic hashmap
vector<int> twoSum(vector<int>& nums, int target) {
    unordered_map<int,int> seen;  // value → index
    for (int i = 0; i < nums.size(); i++) {
        int complement = target - nums[i];
        if (seen.count(complement)) return {seen[complement], i};
        seen[nums[i]] = i;
    }
    return {};
}

// Frequency count pattern
vector<int> topKFrequent(vector<int>& nums, int k) {
    unordered_map<int,int> freq;
    for (int x : nums) freq[x]++;
    
    // Bucket sort: index = frequency
    vector<vector<int>> buckets(nums.size() + 1);
    for (auto& [val, cnt] : freq) buckets[cnt].push_back(val);
    
    vector<int> result;
    for (int i = buckets.size()-1; i >= 0 && result.size() < k; i--)
        for (int x : buckets[i]) result.push_back(x);
    return result;
}

// Group anagrams
vector<vector<string>> groupAnagrams(vector<string>& strs) {
    unordered_map<string, vector<string>> groups;
    for (string& s : strs) {
        string key = s;
        sort(key.begin(), key.end());
        groups[key].push_back(s);
    }
    vector<vector<string>> result;
    for (auto& [key, v] : groups) result.push_back(v);
    return result;
}

// Longest consecutive sequence — O(n) with hashset
int longestConsecutive(vector<int>& nums) {
    unordered_set<int> s(nums.begin(), nums.end());
    int maxLen = 0;
    for (int n : s) {
        if (!s.count(n-1)) {  // Only start from sequence beginning
            int curr = n, len = 1;
            while (s.count(curr+1)) { curr++; len++; }
            maxLen = max(maxLen, len);
        }
    }
    return maxLen;
}
```

---

## Pattern 6: Stack Patterns

### Concept
Stack is perfect for problems requiring **last-seen** information or **monotonic** ordering.

### Monotonic Stack Template

```cpp
// Next Greater Element
vector<int> nextGreater(vector<int>& arr) {
    int n = arr.size();
    vector<int> result(n, -1);
    stack<int> st;  // Stack of indices
    
    for (int i = 0; i < n; i++) {
        while (!st.empty() && arr[st.top()] < arr[i]) {
            result[st.top()] = arr[i];
            st.pop();
        }
        st.push(i);
    }
    return result;
}

// Largest Rectangle in Histogram
int largestRectangle(vector<int>& heights) {
    stack<int> st;
    int maxArea = 0;
    heights.push_back(0);  // Sentinel to flush stack
    
    for (int i = 0; i < heights.size(); i++) {
        while (!st.empty() && heights[st.top()] > heights[i]) {
            int h = heights[st.top()]; st.pop();
            int w = st.empty() ? i : i - st.top() - 1;
            maxArea = max(maxArea, h * w);
        }
        st.push(i);
    }
    return maxArea;
}

// Valid Parentheses
bool isValid(string s) {
    stack<char> st;
    for (char c : s) {
        if (c == '(' || c == '{' || c == '[') st.push(c);
        else {
            if (st.empty()) return false;
            char top = st.top(); st.pop();
            if ((c == ')' && top != '(') ||
                (c == '}' && top != '{') ||
                (c == ']' && top != '[')) return false;
        }
    }
    return st.empty();
}

// Daily Temperatures — next warmer day
vector<int> dailyTemperatures(vector<int>& T) {
    int n = T.size();
    vector<int> result(n, 0);
    stack<int> st;
    for (int i = 0; i < n; i++) {
        while (!st.empty() && T[st.top()] < T[i]) {
            result[st.top()] = i - st.top();
            st.pop();
        }
        st.push(i);
    }
    return result;
}
```

---

## Pattern 7: Tree Patterns

### Tree Node Definition

```cpp
struct TreeNode {
    int val;
    TreeNode* left;
    TreeNode* right;
    TreeNode(int v) : val(v), left(nullptr), right(nullptr) {}
};
```

### DFS Traversals

```cpp
// Inorder (Left → Root → Right) — gives sorted order for BST
void inorder(TreeNode* root, vector<int>& result) {
    if (!root) return;
    inorder(root->left, result);
    result.push_back(root->val);
    inorder(root->right, result);
}

// Preorder (Root → Left → Right) — used to serialize tree
void preorder(TreeNode* root, vector<int>& result) {
    if (!root) return;
    result.push_back(root->val);
    preorder(root->left, result);
    preorder(root->right, result);
}

// Postorder (Left → Right → Root) — used for deletion, expression trees
void postorder(TreeNode* root, vector<int>& result) {
    if (!root) return;
    postorder(root->left, result);
    postorder(root->right, result);
    result.push_back(root->val);
}

// Iterative inorder (common follow-up question)
vector<int> inorderIterative(TreeNode* root) {
    vector<int> result;
    stack<TreeNode*> st;
    TreeNode* curr = root;
    while (curr || !st.empty()) {
        while (curr) { st.push(curr); curr = curr->left; }
        curr = st.top(); st.pop();
        result.push_back(curr->val);
        curr = curr->right;
    }
    return result;
}
```

### BFS (Level Order)

```cpp
vector<vector<int>> levelOrder(TreeNode* root) {
    if (!root) return {};
    queue<TreeNode*> q;
    q.push(root);
    vector<vector<int>> result;
    
    while (!q.empty()) {
        int size = q.size();
        vector<int> level;
        for (int i = 0; i < size; i++) {
            TreeNode* node = q.front(); q.pop();
            level.push_back(node->val);
            if (node->left) q.push(node->left);
            if (node->right) q.push(node->right);
        }
        result.push_back(level);
    }
    return result;
}
```

### Key Tree Templates

```cpp
// Tree height / depth
int height(TreeNode* root) {
    if (!root) return 0;
    return 1 + max(height(root->left), height(root->right));
}

// Diameter of Binary Tree
int diameter = 0;
int dfs(TreeNode* root) {
    if (!root) return 0;
    int left = dfs(root->left);
    int right = dfs(root->right);
    diameter = max(diameter, left + right);
    return 1 + max(left, right);
}

// Path sum — root to leaf
bool hasPathSum(TreeNode* root, int target) {
    if (!root) return false;
    if (!root->left && !root->right) return root->val == target;
    return hasPathSum(root->left, target - root->val) ||
           hasPathSum(root->right, target - root->val);
}

// Lowest Common Ancestor
TreeNode* lca(TreeNode* root, TreeNode* p, TreeNode* q) {
    if (!root || root == p || root == q) return root;
    TreeNode* left = lca(root->left, p, q);
    TreeNode* right = lca(root->right, p, q);
    if (left && right) return root;  // p and q in different subtrees
    return left ? left : right;
}

// Validate BST
bool isValidBST(TreeNode* root, long long min = LLONG_MIN, long long max = LLONG_MAX) {
    if (!root) return true;
    if (root->val <= min || root->val >= max) return false;
    return isValidBST(root->left, min, root->val) &&
           isValidBST(root->right, root->val, max);
}
```

---

## Pattern 8: Graph Patterns

### Graph Representations

```cpp
// Adjacency List (most common in interviews)
int n = 5;  // nodes
vector<vector<int>> adj(n);  // Unweighted
vector<vector<pair<int,int>>> wadj(n);  // Weighted: {neighbor, weight}

// Build from edge list
for (auto& [u, v] : edges) {
    adj[u].push_back(v);
    adj[v].push_back(u);  // For undirected
}

// Adjacency Matrix (for dense graphs)
vector<vector<int>> mat(n, vector<int>(n, 0));
mat[u][v] = 1;  // or weight
```

### DFS Template

```cpp
vector<bool> visited(n, false);

void dfs(int node, vector<vector<int>>& adj) {
    visited[node] = true;
    // Process node
    for (int neighbor : adj[node]) {
        if (!visited[neighbor]) {
            dfs(neighbor, adj);
        }
    }
}

// Count connected components
int countComponents(int n, vector<vector<int>>& adj) {
    vector<bool> visited(n, false);
    int count = 0;
    for (int i = 0; i < n; i++) {
        if (!visited[i]) { dfs(i, adj); count++; }
    }
    return count;
}
```

### BFS Template

```cpp
vector<int> bfs(int start, vector<vector<int>>& adj) {
    vector<int> dist(adj.size(), -1);
    queue<int> q;
    dist[start] = 0;
    q.push(start);
    
    while (!q.empty()) {
        int node = q.front(); q.pop();
        for (int neighbor : adj[node]) {
            if (dist[neighbor] == -1) {
                dist[neighbor] = dist[node] + 1;
                q.push(neighbor);
            }
        }
    }
    return dist;
}
```

### Topological Sort (for DAGs)

```cpp
// Kahn's Algorithm (BFS-based)
vector<int> topoSort(int n, vector<vector<int>>& adj) {
    vector<int> inDegree(n, 0);
    for (int u = 0; u < n; u++)
        for (int v : adj[u]) inDegree[v]++;
    
    queue<int> q;
    for (int i = 0; i < n; i++) if (inDegree[i] == 0) q.push(i);
    
    vector<int> order;
    while (!q.empty()) {
        int u = q.front(); q.pop();
        order.push_back(u);
        for (int v : adj[u]) if (--inDegree[v] == 0) q.push(v);
    }
    return order.size() == n ? order : {};  // Empty if cycle exists
}
```

### Union-Find (Disjoint Set Union)

```cpp
class UnionFind {
    vector<int> parent, rank;
public:
    UnionFind(int n) : parent(n), rank(n, 0) {
        iota(parent.begin(), parent.end(), 0);
    }
    
    int find(int x) {  // Path compression
        if (parent[x] != x) parent[x] = find(parent[x]);
        return parent[x];
    }
    
    bool unite(int x, int y) {  // Union by rank
        int px = find(x), py = find(y);
        if (px == py) return false;  // Already connected
        if (rank[px] < rank[py]) swap(px, py);
        parent[py] = px;
        if (rank[px] == rank[py]) rank[px]++;
        return true;
    }
    
    bool connected(int x, int y) { return find(x) == find(y); }
};

// Number of islands
int numIslands(vector<vector<char>>& grid) {
    int m = grid.size(), n = grid[0].size();
    UnionFind uf(m * n);
    int count = 0;
    int dirs[4][2] = {{0,1},{0,-1},{1,0},{-1,0}};
    
    for (int i = 0; i < m; i++) for (int j = 0; j < n; j++) {
        if (grid[i][j] == '1') {
            count++;
            for (auto& d : dirs) {
                int ni = i+d[0], nj = j+d[1];
                if (ni >= 0 && ni < m && nj >= 0 && nj < n && grid[ni][nj] == '1') {
                    if (uf.unite(i*n+j, ni*n+nj)) count--;
                }
            }
        }
    }
    return count;
}
```

### Dijkstra's Algorithm

```cpp
vector<int> dijkstra(int src, vector<vector<pair<int,int>>>& adj) {
    int n = adj.size();
    vector<int> dist(n, INT_MAX);
    priority_queue<pair<int,int>, vector<pair<int,int>>, greater<>> pq;
    
    dist[src] = 0;
    pq.push({0, src});
    
    while (!pq.empty()) {
        auto [d, u] = pq.top(); pq.pop();
        if (d > dist[u]) continue;  // Outdated entry
        
        for (auto [v, w] : adj[u]) {
            if (dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
                pq.push({dist[v], v});
            }
        }
    }
    return dist;
}
```

---

## Pattern 9: Dynamic Programming

### DP Framework

```
1. Define subproblem: dp[i] = ?
2. Recurrence: dp[i] = f(dp[i-1], dp[i-2], ...)
3. Base cases: dp[0], dp[1], ...
4. Order of computation: bottom-up
5. Answer: dp[n] or max(dp)
```

### Classic DP Problems

```cpp
// 1. Climbing Stairs / Fibonacci
int climbStairs(int n) {
    if (n <= 2) return n;
    int a = 1, b = 2;
    for (int i = 3; i <= n; i++) { int c = a+b; a=b; b=c; }
    return b;
}

// 2. House Robber
int rob(vector<int>& nums) {
    int prev2 = 0, prev1 = 0;
    for (int x : nums) {
        int curr = max(prev1, prev2 + x);
        prev2 = prev1; prev1 = curr;
    }
    return prev1;
}

// 3. Longest Increasing Subsequence — O(n log n)
int lis(vector<int>& nums) {
    vector<int> tails;  // tails[i] = smallest tail of LIS of length i+1
    for (int x : nums) {
        auto it = lower_bound(tails.begin(), tails.end(), x);
        if (it == tails.end()) tails.push_back(x);
        else *it = x;
    }
    return tails.size();
}

// 4. 0/1 Knapsack
int knapsack(int W, vector<int>& weights, vector<int>& values) {
    int n = weights.size();
    vector<int> dp(W+1, 0);
    for (int i = 0; i < n; i++) {
        for (int w = W; w >= weights[i]; w--) {  // Right to left!
            dp[w] = max(dp[w], dp[w-weights[i]] + values[i]);
        }
    }
    return dp[W];
}

// 5. Coin Change — Unbounded Knapsack
int coinChange(vector<int>& coins, int amount) {
    vector<int> dp(amount+1, INT_MAX);
    dp[0] = 0;
    for (int i = 1; i <= amount; i++) {
        for (int coin : coins) {
            if (coin <= i && dp[i-coin] != INT_MAX)
                dp[i] = min(dp[i], dp[i-coin] + 1);
        }
    }
    return dp[amount] == INT_MAX ? -1 : dp[amount];
}

// 6. Longest Common Subsequence
int lcs(string& s1, string& s2) {
    int m = s1.size(), n = s2.size();
    vector<vector<int>> dp(m+1, vector<int>(n+1, 0));
    for (int i = 1; i <= m; i++)
        for (int j = 1; j <= n; j++) {
            if (s1[i-1] == s2[j-1]) dp[i][j] = dp[i-1][j-1] + 1;
            else dp[i][j] = max(dp[i-1][j], dp[i][j-1]);
        }
    return dp[m][n];
}

// 7. Edit Distance
int editDistance(string& s, string& t) {
    int m = s.size(), n = t.size();
    vector<vector<int>> dp(m+1, vector<int>(n+1, 0));
    for (int i = 0; i <= m; i++) dp[i][0] = i;
    for (int j = 0; j <= n; j++) dp[0][j] = j;
    for (int i = 1; i <= m; i++)
        for (int j = 1; j <= n; j++) {
            if (s[i-1] == t[j-1]) dp[i][j] = dp[i-1][j-1];
            else dp[i][j] = 1 + min({dp[i-1][j], dp[i][j-1], dp[i-1][j-1]});
        }
    return dp[m][n];
}
```

---

## Pattern 10: Backtracking

### Concept
Explore all possibilities recursively. Prune branches that can't lead to valid solutions.

```
Decision Tree:
    []
   / \
  [1]  [2]
  / \
[1,2] [1,3]
```

### Templates

```cpp
// General backtracking template
void backtrack(/* state */, /* choices */, vector<result>& results) {
    if (/* goal reached */) {
        results.push_back(/* current state */);
        return;
    }
    for (/* each choice */) {
        if (/* choice is valid */) {
            // Make choice
            backtrack(/* updated state */);
            // Undo choice (backtrack)
        }
    }
}

// Subsets
vector<vector<int>> subsets(vector<int>& nums) {
    vector<vector<int>> result;
    vector<int> curr;
    function<void(int)> bt = [&](int start) {
        result.push_back(curr);
        for (int i = start; i < nums.size(); i++) {
            curr.push_back(nums[i]);
            bt(i+1);
            curr.pop_back();
        }
    };
    bt(0);
    return result;
}

// Permutations
vector<vector<int>> permute(vector<int>& nums) {
    vector<vector<int>> result;
    vector<bool> used(nums.size(), false);
    vector<int> curr;
    function<void()> bt = [&]() {
        if (curr.size() == nums.size()) { result.push_back(curr); return; }
        for (int i = 0; i < nums.size(); i++) {
            if (!used[i]) {
                used[i] = true;
                curr.push_back(nums[i]);
                bt();
                curr.pop_back();
                used[i] = false;
            }
        }
    };
    bt();
    return result;
}

// N-Queens
vector<vector<string>> solveNQueens(int n) {
    vector<vector<string>> result;
    vector<string> board(n, string(n, '.'));
    set<int> cols, diag1, diag2;
    
    function<void(int)> bt = [&](int row) {
        if (row == n) { result.push_back(board); return; }
        for (int col = 0; col < n; col++) {
            if (cols.count(col) || diag1.count(row-col) || diag2.count(row+col)) continue;
            cols.insert(col); diag1.insert(row-col); diag2.insert(row+col);
            board[row][col] = 'Q';
            bt(row+1);
            board[row][col] = '.';
            cols.erase(col); diag1.erase(row-col); diag2.erase(row+col);
        }
    };
    bt(0);
    return result;
}
```

---

## Pattern 11: Heap / Priority Queue

### Concept
Use heaps when you repeatedly need the minimum/maximum element, especially with a stream of data.

```cpp
// K Closest Points to Origin
vector<vector<int>> kClosest(vector<vector<int>>& points, int k) {
    // Max-heap of size k (keep k smallest)
    priority_queue<pair<int,int>> pq;  // {dist, index}
    
    for (int i = 0; i < points.size(); i++) {
        int d = points[i][0]*points[i][0] + points[i][1]*points[i][1];
        pq.push({d, i});
        if (pq.size() > k) pq.pop();  // Remove farthest
    }
    
    vector<vector<int>> result;
    while (!pq.empty()) {
        result.push_back(points[pq.top().second]);
        pq.pop();
    }
    return result;
}

// Merge K Sorted Lists
ListNode* mergeKLists(vector<ListNode*>& lists) {
    auto cmp = [](ListNode* a, ListNode* b) { return a->val > b->val; };
    priority_queue<ListNode*, vector<ListNode*>, decltype(cmp)> pq(cmp);
    
    for (ListNode* l : lists) if (l) pq.push(l);
    
    ListNode dummy(0);
    ListNode* curr = &dummy;
    while (!pq.empty()) {
        curr->next = pq.top(); pq.pop();
        curr = curr->next;
        if (curr->next) pq.push(curr->next);
    }
    return dummy.next;
}

// Find Median from Data Stream
class MedianFinder {
    priority_queue<int> lower;  // Max-heap (lower half)
    priority_queue<int, vector<int>, greater<int>> upper;  // Min-heap (upper half)
public:
    void addNum(int num) {
        lower.push(num);
        upper.push(lower.top()); lower.pop();
        if (upper.size() > lower.size()) {
            lower.push(upper.top()); upper.pop();
        }
    }
    double findMedian() {
        if (lower.size() > upper.size()) return lower.top();
        return (lower.top() + upper.top()) / 2.0;
    }
};
```

---

## Pattern 12: Intervals

### Concept
Sort by start time, then process greedily.

```cpp
// Merge Intervals
vector<vector<int>> merge(vector<vector<int>>& intervals) {
    sort(intervals.begin(), intervals.end());
    vector<vector<int>> result;
    
    for (auto& interval : intervals) {
        if (result.empty() || result.back()[1] < interval[0]) {
            result.push_back(interval);
        } else {
            result.back()[1] = max(result.back()[1], interval[1]);
        }
    }
    return result;
}

// Non-overlapping intervals (minimum removals)
int eraseOverlapIntervals(vector<vector<int>>& intervals) {
    sort(intervals.begin(), intervals.end(), [](auto& a, auto& b) {
        return a[1] < b[1];  // Sort by END time (greedy)
    });
    
    int count = 0, prevEnd = INT_MIN;
    for (auto& interval : intervals) {
        if (interval[0] >= prevEnd) prevEnd = interval[1];
        else count++;  // Overlap — remove this one
    }
    return count;
}

// Meeting rooms II (minimum meeting rooms)
int minMeetingRooms(vector<vector<int>>& intervals) {
    vector<int> starts, ends;
    for (auto& i : intervals) { starts.push_back(i[0]); ends.push_back(i[1]); }
    sort(starts.begin(), starts.end());
    sort(ends.begin(), ends.end());
    
    int rooms = 0, maxRooms = 0, endPtr = 0;
    for (int s : starts) {
        if (s < ends[endPtr]) rooms++;
        else endPtr++;
        maxRooms = max(maxRooms, rooms);
    }
    return maxRooms;
}
```

---

## Pattern 13: Greedy

### Concept
Make the locally optimal choice at each step. **Proof needed:** Show that greedy choice property holds.

```cpp
// Activity Selection (maximum non-overlapping activities)
int activitySelection(vector<pair<int,int>>& activities) {
    sort(activities.begin(), activities.end(), [](auto& a, auto& b) {
        return a.second < b.second;  // Sort by finish time
    });
    int count = 1, lastEnd = activities[0].second;
    for (int i = 1; i < activities.size(); i++) {
        if (activities[i].first >= lastEnd) {
            count++;
            lastEnd = activities[i].second;
        }
    }
    return count;
}

// Jump Game
bool canJump(vector<int>& nums) {
    int maxReach = 0;
    for (int i = 0; i < nums.size(); i++) {
        if (i > maxReach) return false;
        maxReach = max(maxReach, i + nums[i]);
    }
    return true;
}

// Jump Game II (minimum jumps)
int jump(vector<int>& nums) {
    int jumps = 0, currEnd = 0, farthest = 0;
    for (int i = 0; i < nums.size()-1; i++) {
        farthest = max(farthest, i + nums[i]);
        if (i == currEnd) {
            jumps++;
            currEnd = farthest;
        }
    }
    return jumps;
}

// Gas Station
int canCompleteCircuit(vector<int>& gas, vector<int>& cost) {
    int total = 0, tank = 0, start = 0;
    for (int i = 0; i < gas.size(); i++) {
        total += gas[i] - cost[i];
        tank += gas[i] - cost[i];
        if (tank < 0) { start = i+1; tank = 0; }
    }
    return total >= 0 ? start : -1;
}
```

---

## Pattern 14: Trie

### Concept
Tree-based data structure for prefix queries. Each path from root to node represents a prefix.

```cpp
struct TrieNode {
    TrieNode* children[26];
    bool isEnd;
    TrieNode() : isEnd(false) {
        fill(children, children+26, nullptr);
    }
};

class Trie {
    TrieNode* root;
public:
    Trie() : root(new TrieNode()) {}
    
    void insert(string& word) {
        TrieNode* curr = root;
        for (char c : word) {
            int idx = c - 'a';
            if (!curr->children[idx]) curr->children[idx] = new TrieNode();
            curr = curr->children[idx];
        }
        curr->isEnd = true;
    }
    
    bool search(string& word) {
        TrieNode* curr = root;
        for (char c : word) {
            int idx = c - 'a';
            if (!curr->children[idx]) return false;
            curr = curr->children[idx];
        }
        return curr->isEnd;
    }
    
    bool startsWith(string& prefix) {
        TrieNode* curr = root;
        for (char c : prefix) {
            int idx = c - 'a';
            if (!curr->children[idx]) return false;
            curr = curr->children[idx];
        }
        return true;
    }
};

// Word Search II (Trie + DFS)
// Build Trie with all words, then DFS grid pruning with Trie
```

---

## Pattern 15: Bit Manipulation

### Core Operations

```cpp
// Check if bit i is set
bool isSet(int n, int i) { return (n >> i) & 1; }

// Set bit i
int setBit(int n, int i) { return n | (1 << i); }

// Clear bit i
int clearBit(int n, int i) { return n & ~(1 << i); }

// Toggle bit i
int toggleBit(int n, int i) { return n ^ (1 << i); }

// Check if power of 2
bool isPow2(int n) { return n > 0 && (n & (n-1)) == 0; }

// Count set bits (Brian Kernighan)
int countBits(int n) {
    int count = 0;
    while (n) { n &= (n-1); count++; }  // Remove lowest set bit
    return count;
}

// Find lowest set bit
int lowestBit(int n) { return n & (-n); }

// XOR tricks
// a ^ a = 0        (self-cancel)
// a ^ 0 = a        (identity)
// XOR is commutative and associative

// Find single number (all others appear twice)
int singleNumber(vector<int>& nums) {
    int result = 0;
    for (int x : nums) result ^= x;
    return result;
}

// Missing number
int missingNumber(vector<int>& nums) {
    int n = nums.size(), xorAll = 0, xorNums = 0;
    for (int i = 0; i <= n; i++) xorAll ^= i;
    for (int x : nums) xorNums ^= x;
    return xorAll ^ xorNums;
}

// Generate all subsets using bitmask
vector<vector<int>> allSubsets(vector<int>& nums) {
    int n = nums.size();
    vector<vector<int>> result;
    for (int mask = 0; mask < (1 << n); mask++) {
        vector<int> subset;
        for (int i = 0; i < n; i++)
            if (mask & (1 << i)) subset.push_back(nums[i]);
        result.push_back(subset);
    }
    return result;
}

// Bit manipulation shortcuts
n << 1  = n * 2         // Left shift = multiply by 2
n >> 1  = n / 2         // Right shift = divide by 2
n & 1   = n % 2         // Check odd/even
~n + 1  = -n            // Two's complement negation
```

---

## Pattern Quick Summary Sheet

| Pattern | When to Use | Key Data Structure | Time | Space |
|---------|-------------|-------------------|------|-------|
| Sliding Window | Subarray/substring | deque/map | O(n) | O(k) |
| Two Pointers | Sorted array pairs | Indices | O(n) | O(1) |
| Binary Search | Sorted/monotonic | Indices | O(log n) | O(1) |
| Prefix Sum | Range sum queries | Array | O(n) precomp | O(n) |
| HashMap | Frequency/lookup | unordered_map | O(n) | O(n) |
| Stack | NGE, brackets | stack | O(n) | O(n) |
| Tree DFS | Path, subtree | recursion/stack | O(n) | O(h) |
| Tree BFS | Level order | queue | O(n) | O(w) |
| Graph DFS | Components, path | stack/recursion | O(V+E) | O(V) |
| Graph BFS | Shortest path | queue | O(V+E) | O(V) |
| DP | Optimal substructure | array/map | O(n²) | O(n) |
| Backtracking | Generate all | recursion | O(2^n) | O(n) |
| Heap | K elements, stream | priority_queue | O(n log k) | O(k) |
| Intervals | Overlapping ranges | sorted array | O(n log n) | O(n) |
| Greedy | Optimal local choice | sorted array | O(n log n) | O(1) |
| Trie | Prefix queries | TrieNode | O(L) per op | O(ALPHABET*L) |
| Bit Manip | XOR, subsets | integers | O(1)/O(2^n) | O(1) |

---

*Next: [Section 5 — Competitive Programming Optimization](./Section5_Competitive_Programming.md)*
