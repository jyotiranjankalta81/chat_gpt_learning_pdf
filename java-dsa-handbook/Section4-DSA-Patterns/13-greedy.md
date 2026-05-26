# Pattern 13 — Greedy

---

## Core Insight

Make the locally optimal choice at each step, trusting it leads to a globally optimal solution.

**When greedy works:** The problem has optimal substructure AND the greedy choice property (local optimum → global optimum).

**Prove it works:** Usually by contradiction — show that any deviation from greedy can't improve the result.

---

## Pattern 1: Jump Game (LC 55)

```java
// Can you reach the last index?
boolean canJump(int[] nums) {
    int maxReach = 0;

    for (int i = 0; i <= maxReach && i < nums.length; i++) {
        maxReach = Math.max(maxReach, i + nums[i]);
        if (maxReach >= nums.length - 1) return true;
    }
    return false;
}

// Jump Game II (LC 45) — minimum jumps to reach end
int jump(int[] nums) {
    int jumps = 0, curEnd = 0, farthest = 0;

    for (int i = 0; i < nums.length - 1; i++) {
        farthest = Math.max(farthest, i + nums[i]);

        if (i == curEnd) {  // must jump here
            jumps++;
            curEnd = farthest;
        }
    }
    return jumps;
}
```

---

## Pattern 2: Gas Station (LC 134)

```java
// Find starting station for circular tour
int canCompleteCircuit(int[] gas, int[] cost) {
    int totalGas = 0, currentGas = 0, start = 0;

    for (int i = 0; i < gas.length; i++) {
        int net = gas[i] - cost[i];
        totalGas += net;
        currentGas += net;

        if (currentGas < 0) {
            start = i + 1;  // can't start from anywhere before i+1
            currentGas = 0;
        }
    }
    return totalGas >= 0 ? start : -1;
}
```

---

## Pattern 3: Activity Selection / Maximize Non-Overlapping Intervals

```java
// Maximum number of non-overlapping intervals (same as greedy for meeting rooms)
int maxNonOverlapping(int[][] intervals) {
    Arrays.sort(intervals, (a, b) -> a[1] - b[1]);  // sort by end time

    int count = 1, prevEnd = intervals[0][1];

    for (int i = 1; i < intervals.length; i++) {
        if (intervals[i][0] >= prevEnd) {
            count++;
            prevEnd = intervals[i][1];
        }
    }
    return count;
}
```

---

## Pattern 4: Greedy String Problems

```java
// Assign Cookies (LC 455)
int findContentChildren(int[] g, int[] s) {
    Arrays.sort(g);  // greed factors
    Arrays.sort(s);  // cookie sizes

    int child = 0, cookie = 0;
    while (child < g.length && cookie < s.length) {
        if (s[cookie] >= g[child]) child++;  // satisfied
        cookie++;
    }
    return child;
}

// Lemonade Change (LC 860)
boolean lemonadeChange(int[] bills) {
    int five = 0, ten = 0;
    for (int bill : bills) {
        if (bill == 5) {
            five++;
        } else if (bill == 10) {
            if (five == 0) return false;
            five--; ten++;
        } else {  // bill == 20
            // Prefer to give 10+5 (saves 5s for more utility)
            if (ten > 0 && five > 0) { ten--; five--; }
            else if (five >= 3) { five -= 3; }
            else return false;
        }
    }
    return true;
}
```

---

## Pattern 5: Partition Labels (LC 763)

```java
// Partition string so each character appears in at most one part
List<Integer> partitionLabels(String s) {
    int[] last = new int[26];
    for (int i = 0; i < s.length(); i++) last[s.charAt(i) - 'a'] = i;

    List<Integer> result = new ArrayList<>();
    int start = 0, end = 0;

    for (int i = 0; i < s.length(); i++) {
        end = Math.max(end, last[s.charAt(i) - 'a']);  // extend partition
        if (i == end) {
            result.add(end - start + 1);
            start = i + 1;
        }
    }
    return result;
}
```

---

## Summary: When to Use Greedy

| Pattern | Greedy Choice |
|---------|--------------|
| Jump game | Always extend max reach |
| Activity selection | Pick earliest ending |
| Gas station | Skip failing starts |
| Partition labels | Extend to last occurrence |
| Assign cookies | Match smallest cookie that satisfies |

> **Interview Tip:** Greedy is tricky to prove correct. When using it, say: "I'll use a greedy approach — at each step I'll [describe choice] because [brief justification]." Even partial proof earns credit.
