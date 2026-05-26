# Pattern 14 — Trie

---

## Core Insight

A Trie (prefix tree) stores strings where common prefixes share nodes. Enables O(m) prefix search where m = word length, regardless of dictionary size.

---

## Trie Implementation

```java
class TrieNode {
    TrieNode[] children = new TrieNode[26];
    boolean isEnd = false;
    int count = 0;  // optional: words passing through this node
}

class Trie {
    private TrieNode root = new TrieNode();

    public void insert(String word) {
        TrieNode curr = root;
        for (char c : word.toCharArray()) {
            int idx = c - 'a';
            if (curr.children[idx] == null) curr.children[idx] = new TrieNode();
            curr = curr.children[idx];
            curr.count++;
        }
        curr.isEnd = true;
    }

    public boolean search(String word) {
        TrieNode node = findNode(word);
        return node != null && node.isEnd;
    }

    public boolean startsWith(String prefix) {
        return findNode(prefix) != null;
    }

    private TrieNode findNode(String prefix) {
        TrieNode curr = root;
        for (char c : prefix.toCharArray()) {
            int idx = c - 'a';
            if (curr.children[idx] == null) return null;
            curr = curr.children[idx];
        }
        return curr;
    }
}
```

---

## Autocomplete / Word Suggestions

```java
// Find all words with given prefix
List<String> autocomplete(String prefix) {
    TrieNode node = findNode(prefix);
    List<String> results = new ArrayList<>();
    if (node != null) dfsCollect(node, new StringBuilder(prefix), results);
    return results;
}

void dfsCollect(TrieNode node, StringBuilder curr, List<String> results) {
    if (node.isEnd) results.add(curr.toString());
    for (int i = 0; i < 26; i++) {
        if (node.children[i] != null) {
            curr.append((char)('a' + i));
            dfsCollect(node.children[i], curr, results);
            curr.deleteCharAt(curr.length() - 1);
        }
    }
}
```

---

## Word Search II (LC 212) — Trie + Backtracking

```java
List<String> findWords(char[][] board, String[] words) {
    Trie trie = new Trie();
    for (String w : words) trie.insert(w);

    Set<String> result = new HashSet<>();
    int rows = board.length, cols = board[0].length;

    for (int r = 0; r < rows; r++) {
        for (int c = 0; c < cols; c++) {
            dfsWordSearch(board, r, c, trie.root, new StringBuilder(), result);
        }
    }
    return new ArrayList<>(result);
}

void dfsWordSearch(char[][] board, int r, int c, TrieNode node,
                    StringBuilder curr, Set<String> result) {
    if (r < 0 || r >= board.length || c < 0 || c >= board[0].length) return;
    char ch = board[r][c];
    if (ch == '#' || node.children[ch - 'a'] == null) return;

    curr.append(ch);
    node = node.children[ch - 'a'];
    if (node.isEnd) result.add(curr.toString());

    board[r][c] = '#';
    dfsWordSearch(board, r+1, c, node, curr, result);
    dfsWordSearch(board, r-1, c, node, curr, result);
    dfsWordSearch(board, r, c+1, node, curr, result);
    dfsWordSearch(board, r, c-1, node, curr, result);
    board[r][c] = ch;
    curr.deleteCharAt(curr.length() - 1);
}
```

---

## XOR Trie (Maximum XOR)

```java
// Maximum XOR of two numbers in array (LC 421)
// Store numbers as 32-bit binary in a Trie
class XORTrie {
    int[][] children = new int[32 * 100000][2];
    int idx = 1;

    void insert(int num) {
        int curr = 0;
        for (int i = 31; i >= 0; i--) {
            int bit = (num >> i) & 1;
            if (children[curr][bit] == 0) children[curr][bit] = idx++;
            curr = children[curr][bit];
        }
    }

    int maxXOR(int num) {
        int curr = 0, xor = 0;
        for (int i = 31; i >= 0; i--) {
            int bit = (num >> i) & 1;
            int want = 1 - bit;  // prefer opposite bit for max XOR
            if (children[curr][want] != 0) {
                xor |= (1 << i);
                curr = children[curr][want];
            } else {
                curr = children[curr][bit];
            }
        }
        return xor;
    }
}

int findMaximumXOR(int[] nums) {
    XORTrie trie = new XORTrie();
    for (int n : nums) trie.insert(n);
    int max = 0;
    for (int n : nums) max = Math.max(max, trie.maxXOR(n));
    return max;
}
```

---

## Complexity

| Operation | Time | Space |
|-----------|------|-------|
| Insert word of length m | O(m) | O(m) |
| Search word of length m | O(m) | O(1) |
| Prefix check of length m | O(m) | O(1) |
| Total space for n words | — | O(n * m) |
