# Pattern 6 — Stack Patterns

---

## Core Insight

Stacks excel at problems where you need to **process elements in reverse order** or where the answer to the current element depends on **previous unseen elements**.

---

## Pattern 1: Monotonic Stack (Most Important)

A monotonic stack maintains elements in sorted order (increasing or decreasing), popping elements when the order is violated.

**Use for:** Next Greater/Smaller Element, Histogram, Stock Span

### Next Greater Element Template

```java
// For each element, find the next greater element to its right
int[] nextGreaterElement(int[] nums) {
    int n = nums.length;
    int[] result = new int[n];
    Arrays.fill(result, -1);  // default: no greater element
    Deque<Integer> stack = new ArrayDeque<>();  // stores INDICES

    for (int i = 0; i < n; i++) {
        // Pop all elements smaller than current → current is their "next greater"
        while (!stack.isEmpty() && nums[stack.peek()] < nums[i]) {
            result[stack.pop()] = nums[i];
        }
        stack.push(i);
    }
    return result;
}

// Dry run: nums = [2, 1, 2, 4, 3]
// i=0: stack=[0(val=2)]
// i=1: 1 < 2, push → stack=[0,1]
// i=2: 2 >= 1, pop 1 → result[1]=2; 2 == 2, no pop → stack=[0,2]
// i=3: 4 > 2, pop 2 → result[2]=4; 4 > 2, pop 0 → result[0]=4 → stack=[3]
// i=4: 3 < 4, push → stack=[3,4]
// result: [4, 2, 4, -1, -1]
```

### Next Greater Element — Circular Array (LC 503)

```java
int[] nextGreaterElementsCircular(int[] nums) {
    int n = nums.length;
    int[] result = new int[n];
    Arrays.fill(result, -1);
    Deque<Integer> stack = new ArrayDeque<>();

    // Loop twice to simulate circular behavior
    for (int i = 0; i < 2 * n; i++) {
        while (!stack.isEmpty() && nums[stack.peek()] < nums[i % n]) {
            result[stack.pop()] = nums[i % n];
        }
        if (i < n) stack.push(i);
    }
    return result;
}
```

---

## Pattern 2: Largest Rectangle in Histogram (LC 84)

```java
// Classic monotonic stack problem
int largestRectangleArea(int[] heights) {
    int n = heights.length;
    Deque<Integer> stack = new ArrayDeque<>();
    int maxArea = 0;

    for (int i = 0; i <= n; i++) {
        int h = (i == n) ? 0 : heights[i];  // sentinel 0 at end to flush stack

        while (!stack.isEmpty() && heights[stack.peek()] > h) {
            int height = heights[stack.pop()];
            int width = stack.isEmpty() ? i : i - stack.peek() - 1;
            maxArea = Math.max(maxArea, height * width);
        }
        stack.push(i);
    }
    return maxArea;
}

// Maximal Rectangle in Binary Matrix (LC 85) — builds on histogram
int maximalRectangle(char[][] matrix) {
    if (matrix.length == 0) return 0;
    int n = matrix[0].length;
    int[] heights = new int[n];
    int maxArea = 0;

    for (char[] row : matrix) {
        for (int j = 0; j < n; j++) {
            heights[j] = row[j] == '0' ? 0 : heights[j] + 1;
        }
        maxArea = Math.max(maxArea, largestRectangleArea(heights));
    }
    return maxArea;
}
```

---

## Pattern 3: Stock Span / Daily Temperatures (LC 739)

```java
// For each day, how many days until a warmer temperature?
int[] dailyTemperatures(int[] temps) {
    int n = temps.length;
    int[] result = new int[n];
    Deque<Integer> stack = new ArrayDeque<>();  // indices of unresolved days

    for (int i = 0; i < n; i++) {
        while (!stack.isEmpty() && temps[stack.peek()] < temps[i]) {
            int prevDay = stack.pop();
            result[prevDay] = i - prevDay;  // days to wait
        }
        stack.push(i);
    }
    return result;  // remaining elements = 0 (no warmer day found)
}
```

---

## Pattern 4: Bracket Matching

```java
// Valid Parentheses (LC 20)
boolean isValid(String s) {
    Deque<Character> stack = new ArrayDeque<>();
    for (char c : s.toCharArray()) {
        if (c == '(' || c == '[' || c == '{') {
            stack.push(c);
        } else {
            if (stack.isEmpty()) return false;
            char top = stack.pop();
            if ((c == ')' && top != '(') ||
                (c == ']' && top != '[') ||
                (c == '}' && top != '{')) return false;
        }
    }
    return stack.isEmpty();
}

// Minimum Remove to Make Valid Parentheses (LC 1249)
String minRemoveToMakeValid(String s) {
    Deque<Integer> stack = new ArrayDeque<>();  // unmatched '(' indices
    Set<Integer> remove = new HashSet<>();

    for (int i = 0; i < s.length(); i++) {
        char c = s.charAt(i);
        if (c == '(') {
            stack.push(i);
        } else if (c == ')') {
            if (stack.isEmpty()) remove.add(i);  // unmatched ')'
            else stack.pop();
        }
    }

    while (!stack.isEmpty()) remove.add(stack.pop());  // unmatched '('

    StringBuilder sb = new StringBuilder();
    for (int i = 0; i < s.length(); i++) {
        if (!remove.contains(i)) sb.append(s.charAt(i));
    }
    return sb.toString();
}
```

---

## Pattern 5: Calculator Problems

```java
// Basic Calculator II (LC 227) — +, -, *, /
int calculate(String s) {
    Deque<Integer> stack = new ArrayDeque<>();
    int curr = 0;
    char op = '+';

    for (int i = 0; i < s.length(); i++) {
        char c = s.charAt(i);

        if (Character.isDigit(c)) {
            curr = curr * 10 + (c - '0');
        }

        if ((!Character.isDigit(c) && c != ' ') || i == s.length() - 1) {
            switch (op) {
                case '+': stack.push(curr); break;
                case '-': stack.push(-curr); break;
                case '*': stack.push(stack.pop() * curr); break;
                case '/': stack.push(stack.pop() / curr); break;
            }
            op = c;
            curr = 0;
        }
    }

    int result = 0;
    while (!stack.isEmpty()) result += stack.pop();
    return result;
}
```

---

## Pattern 6: Decode String (LC 394)

```java
// "3[a]2[bc]" → "aaabcbc"
// "3[a2[c]]" → "accaccacc"
String decodeString(String s) {
    Deque<Integer> countStack = new ArrayDeque<>();
    Deque<StringBuilder> strStack = new ArrayDeque<>();
    StringBuilder curr = new StringBuilder();
    int k = 0;

    for (char c : s.toCharArray()) {
        if (Character.isDigit(c)) {
            k = k * 10 + (c - '0');
        } else if (c == '[') {
            countStack.push(k);
            strStack.push(curr);
            curr = new StringBuilder();
            k = 0;
        } else if (c == ']') {
            int count = countStack.pop();
            StringBuilder prev = strStack.pop();
            for (int i = 0; i < count; i++) prev.append(curr);
            curr = prev;
        } else {
            curr.append(c);
        }
    }
    return curr.toString();
}
```

---

## Monotonic Stack — Choosing Direction

| Problem | Stack Type | Direction |
|---------|-----------|-----------|
| Next greater to right | Decreasing | Left to right |
| Next greater to left | Decreasing | Right to left |
| Next smaller to right | Increasing | Left to right |
| Next smaller to left | Increasing | Right to left |

```java
// Template for next smaller to the LEFT
int[] prevSmaller(int[] nums) {
    int n = nums.length;
    int[] result = new int[n];
    Deque<Integer> stack = new ArrayDeque<>();

    for (int i = 0; i < n; i++) {
        while (!stack.isEmpty() && nums[stack.peek()] >= nums[i]) stack.pop();
        result[i] = stack.isEmpty() ? -1 : nums[stack.peek()];
        stack.push(i);
    }
    return result;
}
```

---

## Complexity

| Pattern | Time | Space |
|---------|------|-------|
| Monotonic stack | O(n) | O(n) |
| Histogram area | O(n) | O(n) |
| Bracket matching | O(n) | O(n) |
| Calculator | O(n) | O(n) |

> **Interview Tip:** When you see "next greater/smaller element", immediately think monotonic stack. It's the key pattern for histogram problems, stock prices, and temperature-change problems.
