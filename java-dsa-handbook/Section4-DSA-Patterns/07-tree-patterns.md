# Pattern 7 — Tree Patterns

---

## Tree Node Definition

```java
class TreeNode {
    int val;
    TreeNode left, right;
    TreeNode(int val) { this.val = val; }
}
```

---

## 1. Tree Traversals

### DFS — Recursive (Cleaner)

```java
// Inorder: Left → Root → Right (gives sorted order for BST)
void inorder(TreeNode root, List<Integer> result) {
    if (root == null) return;
    inorder(root.left, result);
    result.add(root.val);
    inorder(root.right, result);
}

// Preorder: Root → Left → Right (good for serialization/copying)
void preorder(TreeNode root, List<Integer> result) {
    if (root == null) return;
    result.add(root.val);
    preorder(root.left, result);
    preorder(root.right, result);
}

// Postorder: Left → Right → Root (good for deletion, size calculation)
void postorder(TreeNode root, List<Integer> result) {
    if (root == null) return;
    postorder(root.left, result);
    postorder(root.right, result);
    result.add(root.val);
}
```

### DFS — Iterative with Stack

```java
// Iterative inorder
List<Integer> inorderIterative(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    Deque<TreeNode> stack = new ArrayDeque<>();
    TreeNode curr = root;

    while (curr != null || !stack.isEmpty()) {
        while (curr != null) {
            stack.push(curr);
            curr = curr.left;
        }
        curr = stack.pop();
        result.add(curr.val);
        curr = curr.right;
    }
    return result;
}

// Iterative preorder
List<Integer> preorderIterative(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    if (root == null) return result;
    Deque<TreeNode> stack = new ArrayDeque<>();
    stack.push(root);

    while (!stack.isEmpty()) {
        TreeNode node = stack.pop();
        result.add(node.val);
        if (node.right != null) stack.push(node.right);  // right first (LIFO)
        if (node.left != null) stack.push(node.left);
    }
    return result;
}
```

### BFS — Level Order

```java
List<List<Integer>> levelOrder(TreeNode root) {
    List<List<Integer>> result = new ArrayList<>();
    if (root == null) return result;

    Queue<TreeNode> queue = new ArrayDeque<>();
    queue.offer(root);

    while (!queue.isEmpty()) {
        int size = queue.size();
        List<Integer> level = new ArrayList<>();

        for (int i = 0; i < size; i++) {
            TreeNode node = queue.poll();
            level.add(node.val);
            if (node.left != null) queue.offer(node.left);
            if (node.right != null) queue.offer(node.right);
        }
        result.add(level);
    }
    return result;
}
```

---

## 2. Height and Diameter

```java
// Height (max depth)
int height(TreeNode root) {
    if (root == null) return 0;
    return 1 + Math.max(height(root.left), height(root.right));
}

// Diameter of Binary Tree (LC 543)
// Diameter = longest path (may not pass through root)
int diameterOfBinaryTree(TreeNode root) {
    int[] maxDiam = {0};

    // Returns height, updates maxDiam as side effect
    java.util.function.Function<TreeNode, Integer> dfs = null;
    dfs = node -> {
        if (node == null) return 0;
        // Can't use lambda recursion directly — use helper method
        return 0;
    };

    // Proper implementation with helper
    maxDiamHelper(root, maxDiam);
    return maxDiam[0];
}

int maxDiamHelper(TreeNode node, int[] maxDiam) {
    if (node == null) return 0;
    int left = maxDiamHelper(node.left, maxDiam);
    int right = maxDiamHelper(node.right, maxDiam);
    maxDiam[0] = Math.max(maxDiam[0], left + right);
    return 1 + Math.max(left, right);
}
```

---

## 3. Path Sum Problems

```java
// Path Sum I — does root-to-leaf path with targetSum exist?
boolean hasPathSum(TreeNode root, int targetSum) {
    if (root == null) return false;
    if (root.left == null && root.right == null) return root.val == targetSum;
    return hasPathSum(root.left, targetSum - root.val) ||
           hasPathSum(root.right, targetSum - root.val);
}

// Path Sum II — all root-to-leaf paths with targetSum
List<List<Integer>> pathSum(TreeNode root, int targetSum) {
    List<List<Integer>> result = new ArrayList<>();
    backtrack(root, targetSum, new ArrayList<>(), result);
    return result;
}

void backtrack(TreeNode node, int remaining, List<Integer> path, List<List<Integer>> result) {
    if (node == null) return;
    path.add(node.val);

    if (node.left == null && node.right == null && remaining == node.val) {
        result.add(new ArrayList<>(path));
    } else {
        backtrack(node.left, remaining - node.val, path, result);
        backtrack(node.right, remaining - node.val, path, result);
    }
    path.remove(path.size() - 1);  // backtrack
}

// Path Sum III — any path (not just root-to-leaf), sum = target
// Approach: prefix sum + HashMap
int pathSumIII(TreeNode root, int targetSum) {
    Map<Long, Integer> prefixCount = new HashMap<>();
    prefixCount.put(0L, 1);
    return dfsPathSum(root, 0, targetSum, prefixCount);
}

int dfsPathSum(TreeNode node, long curr, int target, Map<Long, Integer> prefixCount) {
    if (node == null) return 0;
    curr += node.val;
    int count = prefixCount.getOrDefault(curr - target, 0);
    prefixCount.merge(curr, 1, Integer::sum);

    count += dfsPathSum(node.left, curr, target, prefixCount);
    count += dfsPathSum(node.right, curr, target, prefixCount);

    prefixCount.merge(curr, -1, Integer::sum);  // backtrack
    return count;
}
```

---

## 4. Lowest Common Ancestor (LCA)

```java
// LCA of Binary Tree (LC 236)
TreeNode lowestCommonAncestor(TreeNode root, TreeNode p, TreeNode q) {
    if (root == null || root == p || root == q) return root;

    TreeNode left = lowestCommonAncestor(root.left, p, q);
    TreeNode right = lowestCommonAncestor(root.right, p, q);

    // If both found in different subtrees → current is LCA
    if (left != null && right != null) return root;
    // Otherwise, return the non-null one
    return left != null ? left : right;
}

// LCA of BST (LC 235) — simpler, uses BST property
TreeNode lowestCommonAncestorBST(TreeNode root, TreeNode p, TreeNode q) {
    while (root != null) {
        if (p.val < root.val && q.val < root.val) root = root.left;
        else if (p.val > root.val && q.val > root.val) root = root.right;
        else return root;  // root is between p and q → LCA
    }
    return null;
}
```

---

## 5. BST Problems

```java
// Validate BST (LC 98)
boolean isValidBST(TreeNode root) {
    return validate(root, Long.MIN_VALUE, Long.MAX_VALUE);
}

boolean validate(TreeNode node, long min, long max) {
    if (node == null) return true;
    if (node.val <= min || node.val >= max) return false;
    return validate(node.left, min, node.val) &&
           validate(node.right, node.val, max);
}

// Kth Smallest in BST (LC 230)
int kthSmallest(TreeNode root, int k) {
    int[] count = {0, 0};  // [counter, result]
    inorderKth(root, k, count);
    return count[1];
}

void inorderKth(TreeNode node, int k, int[] count) {
    if (node == null || count[0] >= k) return;
    inorderKth(node.left, k, count);
    count[0]++;
    if (count[0] == k) { count[1] = node.val; return; }
    inorderKth(node.right, k, count);
}

// Insert in BST
TreeNode insertBST(TreeNode root, int val) {
    if (root == null) return new TreeNode(val);
    if (val < root.val) root.left = insertBST(root.left, val);
    else root.right = insertBST(root.right, val);
    return root;
}

// Delete in BST
TreeNode deleteBST(TreeNode root, int key) {
    if (root == null) return null;
    if (key < root.val) root.left = deleteBST(root.left, key);
    else if (key > root.val) root.right = deleteBST(root.right, key);
    else {
        // Node found
        if (root.left == null) return root.right;
        if (root.right == null) return root.left;
        // Has two children: replace with inorder successor
        TreeNode successor = root.right;
        while (successor.left != null) successor = successor.left;
        root.val = successor.val;
        root.right = deleteBST(root.right, successor.val);
    }
    return root;
}
```

---

## 6. Tree Serialization (LC 297)

```java
// Serialize: preorder traversal with null markers
public String serialize(TreeNode root) {
    StringBuilder sb = new StringBuilder();
    serializeHelper(root, sb);
    return sb.toString();
}

void serializeHelper(TreeNode node, StringBuilder sb) {
    if (node == null) { sb.append("N,"); return; }
    sb.append(node.val).append(',');
    serializeHelper(node.left, sb);
    serializeHelper(node.right, sb);
}

// Deserialize: rebuild from preorder string
public TreeNode deserialize(String data) {
    Deque<String> queue = new ArrayDeque<>(Arrays.asList(data.split(",")));
    return deserializeHelper(queue);
}

TreeNode deserializeHelper(Deque<String> queue) {
    String val = queue.poll();
    if ("N".equals(val)) return null;
    TreeNode node = new TreeNode(Integer.parseInt(val));
    node.left = deserializeHelper(queue);
    node.right = deserializeHelper(queue);
    return node;
}
```

---

## 7. Right Side View (LC 199)

```java
List<Integer> rightSideView(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    if (root == null) return result;

    Queue<TreeNode> queue = new ArrayDeque<>();
    queue.offer(root);

    while (!queue.isEmpty()) {
        int size = queue.size();
        for (int i = 0; i < size; i++) {
            TreeNode node = queue.poll();
            if (i == size - 1) result.add(node.val);  // rightmost of level
            if (node.left != null) queue.offer(node.left);
            if (node.right != null) queue.offer(node.right);
        }
    }
    return result;
}
```

---

## Complexity Summary

| Operation | BST (balanced) | BST (unbalanced) | General Tree |
|-----------|----------------|------------------|-------------|
| Search | O(log n) | O(n) | O(n) |
| Insert | O(log n) | O(n) | O(n) |
| Delete | O(log n) | O(n) | O(n) |
| Traversal | O(n) | O(n) | O(n) |
| Height | O(log n) | O(n) | O(n) |

> **Interview Tip:** For any tree problem, first identify: Is it a BST? If yes, use BST properties (O(log n) operations). If it's a general binary tree, you'll need O(n) traversal. Mention this distinction early.
