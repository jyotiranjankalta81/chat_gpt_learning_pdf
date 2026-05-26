# Pattern 12 — Intervals

---

## Core Insight

Interval problems usually require sorting by start time, then deciding whether consecutive intervals overlap.

**Overlap condition:** `a.end >= b.start` (when a starts before b)

---

## Pattern 1: Merge Intervals (LC 56)

```java
int[][] merge(int[][] intervals) {
    Arrays.sort(intervals, (a, b) -> a[0] - b[0]);  // sort by start time

    List<int[]> merged = new ArrayList<>();
    int[] current = intervals[0];

    for (int i = 1; i < intervals.length; i++) {
        if (intervals[i][0] <= current[1]) {
            // Overlap: extend current interval
            current[1] = Math.max(current[1], intervals[i][1]);
        } else {
            // No overlap: save current, start new
            merged.add(current);
            current = intervals[i];
        }
    }
    merged.add(current);

    return merged.toArray(new int[0][]);
}

// Dry run: [[1,3],[2,6],[8,10],[15,18]]
// After sort: same
// current=[1,3], i=1: [2,6] overlaps (2<=3), current=[1,6]
// i=2: [8,10] no overlap (8>6), add [1,6], current=[8,10]
// i=3: [15,18] no overlap, add [8,10], current=[15,18]
// Add [15,18]
// Result: [[1,6],[8,10],[15,18]]
```

---

## Pattern 2: Insert Interval (LC 57)

```java
int[][] insert(int[][] intervals, int[] newInterval) {
    List<int[]> result = new ArrayList<>();
    int i = 0, n = intervals.length;

    // Phase 1: Add all intervals that end before newInterval starts
    while (i < n && intervals[i][1] < newInterval[0]) {
        result.add(intervals[i++]);
    }

    // Phase 2: Merge all overlapping intervals
    while (i < n && intervals[i][0] <= newInterval[1]) {
        newInterval[0] = Math.min(newInterval[0], intervals[i][0]);
        newInterval[1] = Math.max(newInterval[1], intervals[i][1]);
        i++;
    }
    result.add(newInterval);

    // Phase 3: Add remaining intervals
    while (i < n) result.add(intervals[i++]);

    return result.toArray(new int[0][]);
}
```

---

## Pattern 3: Meeting Rooms I (LC 252)

```java
// Can attend all meetings? (no overlaps allowed)
boolean canAttendMeetings(int[][] intervals) {
    Arrays.sort(intervals, (a, b) -> a[0] - b[0]);

    for (int i = 1; i < intervals.length; i++) {
        if (intervals[i][0] < intervals[i-1][1]) return false;  // overlap
    }
    return true;
}
```

---

## Pattern 4: Meeting Rooms II (LC 253)

```java
// Minimum meeting rooms required
int minMeetingRooms(int[][] intervals) {
    Arrays.sort(intervals, (a, b) -> a[0] - b[0]);

    // Min-heap of end times (when will rooms be free)
    PriorityQueue<Integer> endTimes = new PriorityQueue<>();

    for (int[] interval : intervals) {
        if (!endTimes.isEmpty() && endTimes.peek() <= interval[0]) {
            endTimes.poll();  // room is free, reuse it
        }
        endTimes.offer(interval[1]);  // assign/reuse room, note end time
    }
    return endTimes.size();  // rooms in use = answer
}

// Alternative: two sorted arrays (start times, end times)
int minMeetingRoomsAlt(int[][] intervals) {
    int n = intervals.length;
    int[] starts = new int[n], ends = new int[n];

    for (int i = 0; i < n; i++) {
        starts[i] = intervals[i][0];
        ends[i] = intervals[i][1];
    }
    Arrays.sort(starts);
    Arrays.sort(ends);

    int rooms = 0, endPtr = 0;
    for (int startPtr = 0; startPtr < n; startPtr++) {
        if (starts[startPtr] < ends[endPtr]) rooms++;  // need new room
        else endPtr++;                                   // room freed
    }
    return rooms;
}
```

---

## Pattern 5: Non-Overlapping Intervals (LC 435) — Greedy

```java
// Minimum intervals to remove so none overlap
int eraseOverlapIntervals(int[][] intervals) {
    Arrays.sort(intervals, (a, b) -> a[1] - b[1]);  // sort by END time (greedy!)

    int count = 0;
    int prevEnd = Integer.MIN_VALUE;

    for (int[] interval : intervals) {
        if (interval[0] >= prevEnd) {
            prevEnd = interval[1];  // no overlap, keep this interval
        } else {
            count++;  // overlap, remove this interval
        }
    }
    return count;
}
// Key insight: sorting by end time maximizes intervals we can keep (greedy)
```

---

## Pattern 6: Interval List Intersections (LC 986)

```java
int[][] intervalIntersection(int[][] first, int[][] second) {
    List<int[]> result = new ArrayList<>();
    int i = 0, j = 0;

    while (i < first.length && j < second.length) {
        int lo = Math.max(first[i][0], second[j][0]);
        int hi = Math.min(first[i][1], second[j][1]);

        if (lo <= hi) result.add(new int[]{lo, hi});  // intersection exists

        // Move pointer for interval that ends earlier
        if (first[i][1] < second[j][1]) i++;
        else j++;
    }
    return result.toArray(new int[0][]);
}
```

---

## Summary

| Problem | Approach | Sort by |
|---------|----------|---------|
| Merge Intervals | Greedy merge | Start time |
| Insert Interval | 3-phase scan | Pre-sorted |
| Meetings I | Check overlap | Start time |
| Meetings II | Min-heap of ends | Start time |
| Min Removal | Greedy keep | End time |
| Intersection | Two pointers | Pre-sorted |
