# Pattern 8 — Graph Patterns

---

## Graph Representations

```java
// Adjacency List (most common)
Map<Integer, List<Integer>> adj = new HashMap<>();
// Add undirected edge
adj.computeIfAbsent(u, k -> new ArrayList<>()).add(v);
adj.computeIfAbsent(v, k -> new ArrayList<>()).add(u);

// Adjacency Matrix (dense graphs, O(1) edge check)
int[][] matrix = new int[n][n];
matrix[u][v] = 1;

// Edge List (for Kruskal's MST)
int[][] edges = {{0,1,4}, {1,2,1}, ...};  // [u, v, weight]

// Grid as Graph (4-directional)
int[][] dirs = {{0,1},{0,-1},{1,0},{-1,0}};
int[][] grid = new int[rows][cols];
```

---

## 1. BFS — Shortest Path in Unweighted Graph

```java
int[] bfsShortestPath(Map<Integer, List<Integer>> adj, int src, int n) {
    int[] dist = new int[n];
    Arrays.fill(dist, -1);
    dist[src] = 0;

    Queue<Integer> queue = new ArrayDeque<>();
    queue.offer(src);

    while (!queue.isEmpty()) {
        int node = queue.poll();
        for (int neighbor : adj.getOrDefault(node, new ArrayList<>())) {
            if (dist[neighbor] == -1) {
                dist[neighbor] = dist[node] + 1;
                queue.offer(neighbor);
            }
        }
    }
    return dist;
}

// BFS on Grid (Number of Islands BFS approach)
int numIslands(char[][] grid) {
    int islands = 0;
    int rows = grid.length, cols = grid[0].length;
    int[][] dirs = {{0,1},{0,-1},{1,0},{-1,0}};

    for (int r = 0; r < rows; r++) {
        for (int c = 0; c < cols; c++) {
            if (grid[r][c] == '1') {
                islands++;
                Queue<int[]> queue = new ArrayDeque<>();
                queue.offer(new int[]{r, c});
                grid[r][c] = '0';  // mark visited

                while (!queue.isEmpty()) {
                    int[] curr = queue.poll();
                    for (int[] dir : dirs) {
                        int nr = curr[0] + dir[0], nc = curr[1] + dir[1];
                        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols
                            && grid[nr][nc] == '1') {
                            grid[nr][nc] = '0';
                            queue.offer(new int[]{nr, nc});
                        }
                    }
                }
            }
        }
    }
    return islands;
}
```

---

## 2. DFS — Connected Components, Path Finding

```java
// DFS template (iterative)
void dfs(Map<Integer, List<Integer>> adj, int start, boolean[] visited) {
    Deque<Integer> stack = new ArrayDeque<>();
    stack.push(start);
    visited[start] = true;

    while (!stack.isEmpty()) {
        int node = stack.pop();
        // process node

        for (int neighbor : adj.getOrDefault(node, new ArrayList<>())) {
            if (!visited[neighbor]) {
                visited[neighbor] = true;
                stack.push(neighbor);
            }
        }
    }
}

// DFS recursive
void dfsRecursive(int node, boolean[] visited, Map<Integer, List<Integer>> adj) {
    visited[node] = true;
    // process node
    for (int neighbor : adj.getOrDefault(node, new ArrayList<>())) {
        if (!visited[neighbor]) {
            dfsRecursive(neighbor, visited, adj);
        }
    }
}
```

---

## 3. Cycle Detection

### Undirected Graph

```java
boolean hasCycleUndirected(int n, int[][] edges) {
    UnionFind uf = new UnionFind(n);
    for (int[] edge : edges) {
        if (!uf.union(edge[0], edge[1])) return true;  // already connected
    }
    return false;
}

// Or DFS approach
boolean hasCycleDFS(Map<Integer, List<Integer>> adj, int n) {
    boolean[] visited = new boolean[n];
    for (int i = 0; i < n; i++) {
        if (!visited[i] && dfsHasCycle(adj, i, -1, visited)) return true;
    }
    return false;
}

boolean dfsHasCycle(Map<Integer, List<Integer>> adj, int node, int parent, boolean[] visited) {
    visited[node] = true;
    for (int neighbor : adj.getOrDefault(node, new ArrayList<>())) {
        if (!visited[neighbor]) {
            if (dfsHasCycle(adj, neighbor, node, visited)) return true;
        } else if (neighbor != parent) {
            return true;  // back edge = cycle
        }
    }
    return false;
}
```

### Directed Graph

```java
// Use 3-color DFS: 0=white(unvisited), 1=gray(in stack), 2=black(done)
boolean hasCycleDirected(int n, Map<Integer, List<Integer>> adj) {
    int[] color = new int[n];  // 0=unvisited, 1=in stack, 2=done
    for (int i = 0; i < n; i++) {
        if (color[i] == 0 && dfsCycle(adj, i, color)) return true;
    }
    return false;
}

boolean dfsCycle(Map<Integer, List<Integer>> adj, int node, int[] color) {
    color[node] = 1;  // gray (in recursion stack)
    for (int neighbor : adj.getOrDefault(node, new ArrayList<>())) {
        if (color[neighbor] == 1) return true;  // back edge = cycle
        if (color[neighbor] == 0 && dfsCycle(adj, neighbor, color)) return true;
    }
    color[node] = 2;  // black (done)
    return false;
}
```

---

## 4. Topological Sort (Directed Acyclic Graph)

```java
// Kahn's Algorithm (BFS-based) — also detects cycles
List<Integer> topologicalSort(int n, int[][] prerequisites) {
    int[] indegree = new int[n];
    Map<Integer, List<Integer>> adj = new HashMap<>();

    for (int[] pre : prerequisites) {
        adj.computeIfAbsent(pre[1], k -> new ArrayList<>()).add(pre[0]);
        indegree[pre[0]]++;
    }

    Queue<Integer> queue = new ArrayDeque<>();
    for (int i = 0; i < n; i++) {
        if (indegree[i] == 0) queue.offer(i);  // nodes with no dependencies
    }

    List<Integer> order = new ArrayList<>();
    while (!queue.isEmpty()) {
        int node = queue.poll();
        order.add(node);
        for (int next : adj.getOrDefault(node, new ArrayList<>())) {
            if (--indegree[next] == 0) queue.offer(next);
        }
    }

    return order.size() == n ? order : new ArrayList<>();  // empty if cycle
}

// Course Schedule (LC 207) — can you finish all courses?
boolean canFinish(int numCourses, int[][] prerequisites) {
    return topologicalSort(numCourses, prerequisites).size() == numCourses;
}
```

---

## 5. Union Find (Disjoint Set Union)

```java
class UnionFind {
    private int[] parent, rank;
    private int components;

    public UnionFind(int n) {
        parent = new int[n];
        rank = new int[n];
        components = n;
        for (int i = 0; i < n; i++) parent[i] = i;
    }

    public int find(int x) {
        if (parent[x] != x) parent[x] = find(parent[x]);  // path compression
        return parent[x];
    }

    public boolean union(int x, int y) {
        int px = find(x), py = find(y);
        if (px == py) return false;

        if (rank[px] < rank[py]) parent[px] = py;
        else if (rank[px] > rank[py]) parent[py] = px;
        else { parent[py] = px; rank[px]++; }

        components--;
        return true;
    }

    public boolean connected(int x, int y) { return find(x) == find(y); }
    public int getComponents() { return components; }
}

// Applications
// - Number of Connected Components
// - Redundant Connection (find cycle)
// - Accounts Merge
// - Making a Large Island
```

---

## 6. Dijkstra's Algorithm (Weighted Shortest Path)

```java
int[] dijkstra(int n, Map<Integer, List<int[]>> adj, int src) {
    int[] dist = new int[n];
    Arrays.fill(dist, Integer.MAX_VALUE);
    dist[src] = 0;

    // [node, distance]
    PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> a[1] - b[1]);
    pq.offer(new int[]{src, 0});

    while (!pq.isEmpty()) {
        int[] curr = pq.poll();
        int node = curr[0], d = curr[1];

        if (d > dist[node]) continue;  // skip outdated entry

        for (int[] edge : adj.getOrDefault(node, new ArrayList<>())) {
            int next = edge[0], weight = edge[1];
            if (dist[node] + weight < dist[next]) {
                dist[next] = dist[node] + weight;
                pq.offer(new int[]{next, dist[next]});
            }
        }
    }
    return dist;
}
// Time: O((V + E) log V)  Space: O(V + E)
```

---

## 7. Bellman-Ford (Handles Negative Weights)

```java
int[] bellmanFord(int n, int[][] edges, int src) {
    int[] dist = new int[n];
    Arrays.fill(dist, Integer.MAX_VALUE);
    dist[src] = 0;

    // Relax all edges n-1 times
    for (int i = 0; i < n - 1; i++) {
        for (int[] edge : edges) {
            int u = edge[0], v = edge[1], w = edge[2];
            if (dist[u] != Integer.MAX_VALUE && dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
            }
        }
    }

    // Check for negative cycles
    for (int[] edge : edges) {
        int u = edge[0], v = edge[1], w = edge[2];
        if (dist[u] != Integer.MAX_VALUE && dist[u] + w < dist[v]) {
            return null;  // negative cycle detected
        }
    }
    return dist;
}
```

---

## 8. Graph Coloring / Bipartite Check

```java
boolean isBipartite(int[][] graph) {
    int n = graph.length;
    int[] color = new int[n];  // 0=uncolored, 1=red, -1=blue

    for (int start = 0; start < n; start++) {
        if (color[start] != 0) continue;

        Queue<Integer> queue = new ArrayDeque<>();
        queue.offer(start);
        color[start] = 1;

        while (!queue.isEmpty()) {
            int node = queue.poll();
            for (int neighbor : graph[node]) {
                if (color[neighbor] == 0) {
                    color[neighbor] = -color[node];  // opposite color
                    queue.offer(neighbor);
                } else if (color[neighbor] == color[node]) {
                    return false;  // same color = not bipartite
                }
            }
        }
    }
    return true;
}
```

---

## Algorithm Selection Guide

| Scenario | Algorithm | Time |
|----------|-----------|------|
| Unweighted shortest path | BFS | O(V+E) |
| Weighted shortest path (no neg) | Dijkstra | O((V+E)logV) |
| Weighted shortest path (with neg) | Bellman-Ford | O(VE) |
| All-pairs shortest path | Floyd-Warshall | O(V³) |
| Connected components | DFS/BFS/UnionFind | O(V+E) |
| Topological order | Kahn's/DFS | O(V+E) |
| Minimum spanning tree | Kruskal/Prim | O(E log E) |
| Cycle detection (undirected) | UnionFind/DFS | O(V+E) |
| Cycle detection (directed) | DFS (3-color) | O(V+E) |
