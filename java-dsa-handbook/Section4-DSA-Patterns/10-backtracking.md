# Pattern 10 — Backtracking

---

## Core Insight

Backtracking = DFS with pruning. Explore all possibilities, but abandon a branch as soon as you know it can't lead to a solution.

**Think of it as:** Making choices → Exploring → Undoing choices if they don't work

---

## Universal Backtracking Template

```java
void backtrack(result, current, choices, start) {
    // Base case: solution complete
    if (isSolution()) {
        result.add(new ArrayList<>(current));
        return;
    }

    for (choice : choices[start..end]) {
        if (!isValid(choice)) continue;  // pruning

        current.add(choice);              // make choice
        backtrack(result, current, choices, nextStart);
        current.remove(current.size() - 1);  // undo choice (backtrack)
    }
}
```

---

## Problem 1: Subsets (LC 78)

```java
List<List<Integer>> subsets(int[] nums) {
    List<List<Integer>> result = new ArrayList<>();
    backtrackSubsets(nums, 0, new ArrayList<>(), result);
    return result;
}

void backtrackSubsets(int[] nums, int start, List<Integer> current, List<List<Integer>> result) {
    result.add(new ArrayList<>(current));  // add at each step (every subset is valid)

    for (int i = start; i < nums.length; i++) {
        current.add(nums[i]);
        backtrackSubsets(nums, i + 1, current, result);
        current.remove(current.size() - 1);
    }
}

// Dry run: nums = [1, 2, 3]
// start=0: add [] → explore i=0,1,2
//   current=[1], start=1: add [1] → explore i=1,2
//     current=[1,2], start=2: add [1,2] → explore i=2
//       current=[1,2,3], start=3: add [1,2,3], return
//     current=[1,3], start=3: add [1,3], return
//   current=[2], start=2: add [2] → explore i=2
//     current=[2,3], start=3: add [2,3], return
//   current=[3], start=3: add [3], return
// Result: [[], [1], [1,2], [1,2,3], [1,3], [2], [2,3], [3]] = 8 subsets = 2^3
```

---

## Problem 2: Subsets II (with duplicates, LC 90)

```java
List<List<Integer>> subsetsWithDup(int[] nums) {
    Arrays.sort(nums);  // MUST sort to group duplicates
    List<List<Integer>> result = new ArrayList<>();
    backtrackSubsetsII(nums, 0, new ArrayList<>(), result);
    return result;
}

void backtrackSubsetsII(int[] nums, int start, List<Integer> current, List<List<Integer>> result) {
    result.add(new ArrayList<>(current));

    for (int i = start; i < nums.length; i++) {
        // Skip duplicates at same level
        if (i > start && nums[i] == nums[i - 1]) continue;

        current.add(nums[i]);
        backtrackSubsetsII(nums, i + 1, current, result);
        current.remove(current.size() - 1);
    }
}
```

---

## Problem 3: Permutations (LC 46)

```java
List<List<Integer>> permute(int[] nums) {
    List<List<Integer>> result = new ArrayList<>();
    backtrackPermute(nums, new boolean[nums.length], new ArrayList<>(), result);
    return result;
}

void backtrackPermute(int[] nums, boolean[] used, List<Integer> current, List<List<Integer>> result) {
    if (current.size() == nums.length) {
        result.add(new ArrayList<>(current));
        return;
    }

    for (int i = 0; i < nums.length; i++) {
        if (used[i]) continue;  // skip already chosen

        used[i] = true;
        current.add(nums[i]);
        backtrackPermute(nums, used, current, result);
        current.remove(current.size() - 1);
        used[i] = false;
    }
}
// Total permutations: n! (n=3 → 6, n=4 → 24)
```

---

## Problem 4: Combination Sum (LC 39)

```java
// Same number can be used multiple times
List<List<Integer>> combinationSum(int[] candidates, int target) {
    List<List<Integer>> result = new ArrayList<>();
    Arrays.sort(candidates);  // optional but enables early pruning
    backtrackCombSum(candidates, target, 0, new ArrayList<>(), result);
    return result;
}

void backtrackCombSum(int[] candidates, int remaining, int start,
                       List<Integer> current, List<List<Integer>> result) {
    if (remaining == 0) {
        result.add(new ArrayList<>(current));
        return;
    }

    for (int i = start; i < candidates.length; i++) {
        if (candidates[i] > remaining) break;  // pruning: sorted, no need to continue

        current.add(candidates[i]);
        backtrackCombSum(candidates, remaining - candidates[i], i, current, result);  // i (not i+1) for reuse
        current.remove(current.size() - 1);
    }
}
```

---

## Problem 5: Combination Sum II (with duplicates, LC 40)

```java
// Each number used once, no duplicate combinations
List<List<Integer>> combinationSum2(int[] candidates, int target) {
    Arrays.sort(candidates);
    List<List<Integer>> result = new ArrayList<>();
    backtrackCombSum2(candidates, target, 0, new ArrayList<>(), result);
    return result;
}

void backtrackCombSum2(int[] candidates, int remaining, int start,
                        List<Integer> current, List<List<Integer>> result) {
    if (remaining == 0) {
        result.add(new ArrayList<>(current));
        return;
    }

    for (int i = start; i < candidates.length; i++) {
        if (candidates[i] > remaining) break;
        if (i > start && candidates[i] == candidates[i - 1]) continue;  // skip dups

        current.add(candidates[i]);
        backtrackCombSum2(candidates, remaining - candidates[i], i + 1, current, result);
        current.remove(current.size() - 1);
    }
}
```

---

## Problem 6: N-Queens (LC 51)

```java
List<List<String>> solveNQueens(int n) {
    List<List<String>> result = new ArrayList<>();
    int[] queens = new int[n];  // queens[row] = column of queen in that row
    Arrays.fill(queens, -1);

    Set<Integer> cols = new HashSet<>();
    Set<Integer> diag1 = new HashSet<>();  // row - col
    Set<Integer> diag2 = new HashSet<>();  // row + col

    backtrackQueens(n, 0, queens, cols, diag1, diag2, result);
    return result;
}

void backtrackQueens(int n, int row, int[] queens,
                      Set<Integer> cols, Set<Integer> diag1, Set<Integer> diag2,
                      List<List<String>> result) {
    if (row == n) {
        result.add(buildBoard(queens, n));
        return;
    }

    for (int col = 0; col < n; col++) {
        if (cols.contains(col)) continue;
        if (diag1.contains(row - col)) continue;
        if (diag2.contains(row + col)) continue;

        queens[row] = col;
        cols.add(col);
        diag1.add(row - col);
        diag2.add(row + col);

        backtrackQueens(n, row + 1, queens, cols, diag1, diag2, result);

        queens[row] = -1;
        cols.remove(col);
        diag1.remove(row - col);
        diag2.remove(row + col);
    }
}

List<String> buildBoard(int[] queens, int n) {
    List<String> board = new ArrayList<>();
    for (int row = 0; row < n; row++) {
        char[] line = new char[n];
        Arrays.fill(line, '.');
        line[queens[row]] = 'Q';
        board.add(new String(line));
    }
    return board;
}
```

---

## Problem 7: Word Search (LC 79)

```java
boolean exist(char[][] board, String word) {
    int rows = board.length, cols = board[0].length;
    for (int r = 0; r < rows; r++) {
        for (int c = 0; c < cols; c++) {
            if (dfsWordSearch(board, word, r, c, 0)) return true;
        }
    }
    return false;
}

boolean dfsWordSearch(char[][] board, String word, int r, int c, int idx) {
    if (idx == word.length()) return true;
    if (r < 0 || r >= board.length || c < 0 || c >= board[0].length) return false;
    if (board[r][c] != word.charAt(idx)) return false;

    char temp = board[r][c];
    board[r][c] = '#';  // mark visited

    boolean found = dfsWordSearch(board, word, r+1, c, idx+1) ||
                    dfsWordSearch(board, word, r-1, c, idx+1) ||
                    dfsWordSearch(board, word, r, c+1, idx+1) ||
                    dfsWordSearch(board, word, r, c-1, idx+1);

    board[r][c] = temp;  // restore (backtrack)
    return found;
}
```

---

## Key Differences Between Problems

| Problem | Duplicates | Reuse | Order Matters |
|---------|-----------|-------|---------------|
| Subsets | No | No | No |
| Subsets II | Yes | No | No |
| Permutations | No | No | Yes |
| Combination Sum | No | Yes | No |
| Combination Sum II | Yes | No | No |

---

## Pruning Techniques

```java
// 1. Early termination: sort + break
if (candidates[i] > remaining) break;

// 2. Skip duplicates at same level
if (i > start && nums[i] == nums[i-1]) continue;

// 3. Mark visited (for grids, permutations)
visited[i] = true; // ... recurse ... visited[i] = false;

// 4. Constraint check before recursion
if (!isValid(choice)) continue;
```

> **Interview Tip:** Backtracking has exponential time complexity (O(2^n) or O(n!)). Always mention this, then say: "Let me see if DP can solve this instead." Sometimes backtracking IS the intended solution (N-Queens, word search).
