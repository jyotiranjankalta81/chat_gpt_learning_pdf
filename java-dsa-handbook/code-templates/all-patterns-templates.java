import java.util.*;
import java.util.stream.*;

/**
 * JAVA DSA INTERVIEW - ALL PATTERN TEMPLATES
 * Complete reusable templates for all 15 patterns
 * For FAANG / Big Tech / Global Banks Interview Preparation
 */
public class AllPatternsTemplates {

    // ==========================================
    // PATTERN 1: SLIDING WINDOW
    // ==========================================

    // Fixed window: max sum of k elements
    public int maxSumWindow(int[] arr, int k) {
        int sum = 0;
        for (int i = 0; i < k; i++) sum += arr[i];
        int max = sum;
        for (int i = k; i < arr.length; i++) {
            sum += arr[i] - arr[i - k];
            max = Math.max(max, sum);
        }
        return max;
    }

    // Variable window: longest substring with at most k distinct chars
    public int longestKDistinct(String s, int k) {
        Map<Character, Integer> freq = new HashMap<>();
        int left = 0, maxLen = 0;
        for (int right = 0; right < s.length(); right++) {
            freq.merge(s.charAt(right), 1, Integer::sum);
            while (freq.size() > k) {
                char lc = s.charAt(left++);
                freq.merge(lc, -1, Integer::sum);
                if (freq.get(lc) == 0) freq.remove(lc);
            }
            maxLen = Math.max(maxLen, right - left + 1);
        }
        return maxLen;
    }

    // ==========================================
    // PATTERN 2: TWO POINTERS
    // ==========================================

    // Two sum in sorted array
    public int[] twoSumSorted(int[] arr, int target) {
        int l = 0, r = arr.length - 1;
        while (l < r) {
            int sum = arr[l] + arr[r];
            if (sum == target) return new int[]{l, r};
            else if (sum < target) l++;
            else r--;
        }
        return new int[]{};
    }

    // Fast/slow cycle detection
    public boolean hasCycle(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) return true;
        }
        return false;
    }

    // ==========================================
    // PATTERN 3: BINARY SEARCH
    // ==========================================

    // Classic binary search
    public int binarySearch(int[] arr, int target) {
        int lo = 0, hi = arr.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (arr[mid] == target) return mid;
            else if (arr[mid] < target) lo = mid + 1;
            else hi = mid - 1;
        }
        return -1;
    }

    // Binary search on answer: find leftmost true
    // condition: arr[mid] >= target (example)
    public int lowerBound(int[] arr, int target) {
        int lo = 0, hi = arr.length;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (arr[mid] >= target) hi = mid;
            else lo = mid + 1;
        }
        return lo;
    }

    // ==========================================
    // PATTERN 4: PREFIX SUM
    // ==========================================

    // Build prefix sum
    public int[] buildPrefix(int[] arr) {
        int[] prefix = new int[arr.length + 1];
        for (int i = 0; i < arr.length; i++) prefix[i + 1] = prefix[i] + arr[i];
        return prefix;
    }

    // Range sum query O(1)
    public int rangeSum(int[] prefix, int l, int r) {
        return prefix[r + 1] - prefix[l];
    }

    // Count subarrays with sum k
    public int subarraySum(int[] nums, int k) {
        Map<Integer, Integer> prefixCount = new HashMap<>();
        prefixCount.put(0, 1);
        int sum = 0, count = 0;
        for (int n : nums) {
            sum += n;
            count += prefixCount.getOrDefault(sum - k, 0);
            prefixCount.merge(sum, 1, Integer::sum);
        }
        return count;
    }

    // ==========================================
    // PATTERN 5: HASHMAP/HASHSET
    // ==========================================

    // Two sum with HashMap
    public int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> seen = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            int comp = target - nums[i];
            if (seen.containsKey(comp)) return new int[]{seen.get(comp), i};
            seen.put(nums[i], i);
        }
        return new int[]{};
    }

    // Group anagrams
    public List<List<String>> groupAnagrams(String[] strs) {
        Map<String, List<String>> groups = new HashMap<>();
        for (String s : strs) {
            char[] chars = s.toCharArray();
            Arrays.sort(chars);
            groups.computeIfAbsent(new String(chars), k -> new ArrayList<>()).add(s);
        }
        return new ArrayList<>(groups.values());
    }

    // ==========================================
    // PATTERN 6: STACK / MONOTONIC STACK
    // ==========================================

    // Next greater element
    public int[] nextGreater(int[] nums) {
        int n = nums.length;
        int[] result = new int[n];
        Arrays.fill(result, -1);
        Deque<Integer> stack = new ArrayDeque<>();
        for (int i = 0; i < n; i++) {
            while (!stack.isEmpty() && nums[stack.peek()] < nums[i])
                result[stack.pop()] = nums[i];
            stack.push(i);
        }
        return result;
    }

    // Valid parentheses
    public boolean isValid(String s) {
        Deque<Character> stack = new ArrayDeque<>();
        for (char c : s.toCharArray()) {
            if (c == '(' || c == '[' || c == '{') stack.push(c);
            else {
                if (stack.isEmpty()) return false;
                char top = stack.pop();
                if ((c == ')' && top != '(') || (c == ']' && top != '[') || (c == '}' && top != '{'))
                    return false;
            }
        }
        return stack.isEmpty();
    }

    // ==========================================
    // PATTERN 7: TREE
    // ==========================================

    // Tree height
    public int height(TreeNode root) {
        if (root == null) return 0;
        return 1 + Math.max(height(root.left), height(root.right));
    }

    // BFS level order
    public List<List<Integer>> levelOrder(TreeNode root) {
        List<List<Integer>> result = new ArrayList<>();
        if (root == null) return result;
        Queue<TreeNode> q = new ArrayDeque<>();
        q.offer(root);
        while (!q.isEmpty()) {
            int size = q.size();
            List<Integer> level = new ArrayList<>();
            for (int i = 0; i < size; i++) {
                TreeNode node = q.poll();
                level.add(node.val);
                if (node.left != null) q.offer(node.left);
                if (node.right != null) q.offer(node.right);
            }
            result.add(level);
        }
        return result;
    }

    // LCA
    public TreeNode lca(TreeNode root, TreeNode p, TreeNode q) {
        if (root == null || root == p || root == q) return root;
        TreeNode left = lca(root.left, p, q);
        TreeNode right = lca(root.right, p, q);
        if (left != null && right != null) return root;
        return left != null ? left : right;
    }

    // ==========================================
    // PATTERN 8: GRAPH
    // ==========================================

    // BFS shortest path
    public int[] bfsShortestPath(Map<Integer, List<Integer>> adj, int src, int n) {
        int[] dist = new int[n];
        Arrays.fill(dist, -1);
        dist[src] = 0;
        Queue<Integer> q = new ArrayDeque<>();
        q.offer(src);
        while (!q.isEmpty()) {
            int node = q.poll();
            for (int nb : adj.getOrDefault(node, Collections.emptyList())) {
                if (dist[nb] == -1) { dist[nb] = dist[node] + 1; q.offer(nb); }
            }
        }
        return dist;
    }

    // Union Find
    static class UnionFind {
        int[] parent, rank;
        UnionFind(int n) {
            parent = new int[n]; rank = new int[n];
            for (int i = 0; i < n; i++) parent[i] = i;
        }
        int find(int x) {
            if (parent[x] != x) parent[x] = find(parent[x]);
            return parent[x];
        }
        boolean union(int x, int y) {
            int px = find(x), py = find(y);
            if (px == py) return false;
            if (rank[px] < rank[py]) parent[px] = py;
            else if (rank[px] > rank[py]) parent[py] = px;
            else { parent[py] = px; rank[px]++; }
            return true;
        }
        boolean connected(int x, int y) { return find(x) == find(y); }
    }

    // Topological sort (Kahn's)
    public List<Integer> topoSort(int n, int[][] edges) {
        int[] indegree = new int[n];
        Map<Integer, List<Integer>> adj = new HashMap<>();
        for (int[] e : edges) {
            adj.computeIfAbsent(e[0], k -> new ArrayList<>()).add(e[1]);
            indegree[e[1]]++;
        }
        Queue<Integer> q = new ArrayDeque<>();
        for (int i = 0; i < n; i++) if (indegree[i] == 0) q.offer(i);
        List<Integer> order = new ArrayList<>();
        while (!q.isEmpty()) {
            int node = q.poll(); order.add(node);
            for (int next : adj.getOrDefault(node, Collections.emptyList()))
                if (--indegree[next] == 0) q.offer(next);
        }
        return order.size() == n ? order : new ArrayList<>();
    }

    // ==========================================
    // PATTERN 9: DYNAMIC PROGRAMMING
    // ==========================================

    // Coin change (min coins)
    public int coinChange(int[] coins, int amount) {
        int[] dp = new int[amount + 1];
        Arrays.fill(dp, amount + 1);
        dp[0] = 0;
        for (int a = 1; a <= amount; a++)
            for (int coin : coins)
                if (coin <= a) dp[a] = Math.min(dp[a], dp[a - coin] + 1);
        return dp[amount] > amount ? -1 : dp[amount];
    }

    // LCS
    public int lcs(String s1, String s2) {
        int m = s1.length(), n = s2.length();
        int[][] dp = new int[m + 1][n + 1];
        for (int i = 1; i <= m; i++)
            for (int j = 1; j <= n; j++)
                dp[i][j] = s1.charAt(i-1) == s2.charAt(j-1)
                    ? dp[i-1][j-1] + 1
                    : Math.max(dp[i-1][j], dp[i][j-1]);
        return dp[m][n];
    }

    // 0/1 Knapsack
    public int knapsack(int[] weights, int[] values, int cap) {
        int[] dp = new int[cap + 1];
        for (int i = 0; i < weights.length; i++)
            for (int w = cap; w >= weights[i]; w--)
                dp[w] = Math.max(dp[w], dp[w - weights[i]] + values[i]);
        return dp[cap];
    }

    // ==========================================
    // PATTERN 10: BACKTRACKING
    // ==========================================

    // Subsets
    public List<List<Integer>> subsets(int[] nums) {
        List<List<Integer>> result = new ArrayList<>();
        backtrackSubsets(nums, 0, new ArrayList<>(), result);
        return result;
    }
    private void backtrackSubsets(int[] nums, int start, List<Integer> curr, List<List<Integer>> result) {
        result.add(new ArrayList<>(curr));
        for (int i = start; i < nums.length; i++) {
            curr.add(nums[i]);
            backtrackSubsets(nums, i + 1, curr, result);
            curr.remove(curr.size() - 1);
        }
    }

    // Permutations
    public List<List<Integer>> permute(int[] nums) {
        List<List<Integer>> result = new ArrayList<>();
        backtrackPermute(nums, new boolean[nums.length], new ArrayList<>(), result);
        return result;
    }
    private void backtrackPermute(int[] nums, boolean[] used, List<Integer> curr, List<List<Integer>> result) {
        if (curr.size() == nums.length) { result.add(new ArrayList<>(curr)); return; }
        for (int i = 0; i < nums.length; i++) {
            if (used[i]) continue;
            used[i] = true; curr.add(nums[i]);
            backtrackPermute(nums, used, curr, result);
            curr.remove(curr.size() - 1); used[i] = false;
        }
    }

    // ==========================================
    // PATTERN 11: HEAP
    // ==========================================

    // Kth largest
    public int kthLargest(int[] nums, int k) {
        PriorityQueue<Integer> minHeap = new PriorityQueue<>();
        for (int n : nums) {
            minHeap.offer(n);
            if (minHeap.size() > k) minHeap.poll();
        }
        return minHeap.peek();
    }

    // Merge K sorted lists
    public ListNode mergeKLists(ListNode[] lists) {
        PriorityQueue<ListNode> heap = new PriorityQueue<>((a, b) -> a.val - b.val);
        for (ListNode h : lists) if (h != null) heap.offer(h);
        ListNode dummy = new ListNode(0), curr = dummy;
        while (!heap.isEmpty()) {
            ListNode node = heap.poll();
            curr.next = node; curr = curr.next;
            if (node.next != null) heap.offer(node.next);
        }
        return dummy.next;
    }

    // ==========================================
    // PATTERN 12: INTERVALS
    // ==========================================

    // Merge intervals
    public int[][] mergeIntervals(int[][] intervals) {
        Arrays.sort(intervals, (a, b) -> a[0] - b[0]);
        List<int[]> merged = new ArrayList<>();
        int[] curr = intervals[0];
        for (int i = 1; i < intervals.length; i++) {
            if (intervals[i][0] <= curr[1]) curr[1] = Math.max(curr[1], intervals[i][1]);
            else { merged.add(curr); curr = intervals[i]; }
        }
        merged.add(curr);
        return merged.toArray(new int[0][]);
    }

    // ==========================================
    // PATTERN 13: GREEDY
    // ==========================================

    // Jump game
    public boolean canJump(int[] nums) {
        int maxReach = 0;
        for (int i = 0; i <= maxReach && i < nums.length; i++)
            maxReach = Math.max(maxReach, i + nums[i]);
        return maxReach >= nums.length - 1;
    }

    // ==========================================
    // PATTERN 14: TRIE
    // ==========================================

    static class TrieNode {
        TrieNode[] children = new TrieNode[26];
        boolean isEnd = false;
    }

    static class Trie {
        TrieNode root = new TrieNode();

        void insert(String word) {
            TrieNode curr = root;
            for (char c : word.toCharArray()) {
                int idx = c - 'a';
                if (curr.children[idx] == null) curr.children[idx] = new TrieNode();
                curr = curr.children[idx];
            }
            curr.isEnd = true;
        }

        boolean search(String word) {
            TrieNode node = find(word);
            return node != null && node.isEnd;
        }

        boolean startsWith(String prefix) { return find(prefix) != null; }

        private TrieNode find(String s) {
            TrieNode curr = root;
            for (char c : s.toCharArray()) {
                if (curr.children[c - 'a'] == null) return null;
                curr = curr.children[c - 'a'];
            }
            return curr;
        }
    }

    // ==========================================
    // PATTERN 15: BIT MANIPULATION
    // ==========================================

    // Single number (XOR)
    public int singleNumber(int[] nums) {
        int xor = 0;
        for (int n : nums) xor ^= n;
        return xor;
    }

    // Missing number
    public int missingNumber(int[] nums) {
        int xor = nums.length;
        for (int i = 0; i < nums.length; i++) xor ^= i ^ nums[i];
        return xor;
    }

    // Is power of two
    public boolean isPowerOfTwo(int n) { return n > 0 && (n & (n - 1)) == 0; }

    // Count bits (DP)
    public int[] countBits(int n) {
        int[] dp = new int[n + 1];
        for (int i = 1; i <= n; i++) dp[i] = dp[i >> 1] + (i & 1);
        return dp;
    }

    // ==========================================
    // NODE DEFINITIONS (used in templates)
    // ==========================================

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
    }
}
