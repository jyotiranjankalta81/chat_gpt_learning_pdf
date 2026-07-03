# Section 6: Interview Preparation
## FAANG Mindset, Communication Strategy & Problem-Solving Framework

> **The secret:** FAANG interviews test not just your code, but how you **think**, **communicate**, and **handle pressure**. This section gives you the mental framework to ace any technical interview.

---

## Table of Contents
1. [FAANG Problem-Solving Mindset](#1-faang-problem-solving-mindset)
2. [The 7-Step Interview Framework](#2-the-7-step-interview-framework)
3. [Optimal Coding Style](#3-optimal-coding-style)
4. [Communication Scripts](#4-communication-scripts)
5. [Debugging Strategy](#5-debugging-strategy)
6. [Common Traps & How to Avoid Them](#6-common-traps--how-to-avoid-them)
7. [Company-Specific Insights](#7-company-specific-insights)
8. [Pressure Handling](#8-pressure-handling)
9. [Behavioral Interview Framework](#9-behavioral-interview-framework)

---

## 1. FAANG Problem-Solving Mindset

### The Core Mental Model

```
Problem → Pattern → Template → Adapt → Code → Verify
```

**Key principles:**

1. **Never code immediately.** Think first, code second. An interviewer would rather see you think for 5 minutes than watch you code something wrong for 20 minutes.

2. **Brute force is always valid.** Start by stating the naive solution. This shows you understand the problem. Then optimize.

3. **Talk out loud constantly.** Your interviewer cannot read your mind. Narrate every thought: "I notice this array is sorted, so I'm thinking binary search..."

4. **Ask clarifying questions.** This is not a weakness — it's what senior engineers do. You never code based on incomplete requirements.

5. **Constraints are hints.** 
   - n ≤ 20 → Bitmask/Backtracking
   - n ≤ 1000 → O(n²) ok
   - n ≤ 10^6 → O(n log n) needed
   - "sorted" → Binary search
   - "distinct" or "unique" → HashMap/Set

### Mental Checklist Before Coding

```
[ ] Did I understand the problem correctly? (Restate it)
[ ] What are the input constraints? (n, value ranges, negative numbers?)
[ ] What are the output requirements? (Return value? Indices or values?)
[ ] Are there any special cases? (Empty input, single element, all same)
[ ] What is the expected time/space complexity? (Ask if unsure)
[ ] Can the input be modified? (Can I sort it?)
[ ] Do I have a brute force solution? (State it first)
[ ] Can I optimize it? (What's the bottleneck?)
```

---

## 2. The 7-Step Interview Framework

### Step 1: CLARIFY (2-3 minutes)

```
You: "Let me make sure I understand the problem..."
    - Restate the problem in your own words
    - Clarify input format and constraints
    - Ask about edge cases explicitly

Example questions to ask:
- "Can the array have negative numbers?"
- "Can we have duplicate elements?"
- "What should we return if there's no solution?"
- "Is the array guaranteed to be non-empty?"
- "Can I assume the input fits in an integer?"
- "Are we optimizing for time or space?"
```

### Step 2: EXAMPLES (2 minutes)

```
- Walk through the provided example step by step
- Create 2-3 of your own examples
- Include edge cases:
  * Empty input
  * Single element
  * All same elements
  * Already sorted / reverse sorted
  * Minimum and maximum values

"Let me trace through the example: input [1,2,3], k=2...
After step 1: ...
After step 2: ...
Final result: ..."
```

### Step 3: BRUTE FORCE (1-2 minutes)

```
"The naive approach would be to [describe O(n²) or worse solution].
This would be O(n²) time and O(1) space, which is too slow for n=10^6.
Let me think about how to optimize..."

Important: Even if you know the optimal solution, 
           ALWAYS mention brute force first.
```

### Step 4: OPTIMIZE (5-10 minutes)

```
Optimization checklist:
[ ] Is there repeated work? → Memoization/Caching
[ ] Is there a sorted structure? → Binary search
[ ] Do we need a "current max/min"? → Sliding window or heap
[ ] Do we need pair/triplet sums? → Two pointers or hash map
[ ] Is the answer monotonic? → Binary search on answer
[ ] Do subproblems overlap? → Dynamic programming
[ ] Is greedy provably correct here? → Greedy

"I notice that [observation]. This suggests [pattern].
If I use [data structure], I can reduce [operation] from O(n) to O(1),
giving overall O(n log n) time..."
```

### Step 5: CODE (10-15 minutes)

```
- Write clean, readable code
- Use meaningful variable names (left/right, not l/r for clarity)
- Add a brief comment for non-obvious sections
- Write helper functions if needed
- Don't delete code — cross it out or comment it

"Let me start coding. I'll write a helper function first...
Here, I'm using a sliding window. The left pointer marks the start..."
```

### Step 6: TEST (3-5 minutes)

```
- Trace through your code with the example
- Test edge cases you identified in step 2
- Dry-run line by line, tracking variable values

"Let me trace through with input [1,2,3,4,5], k=3:
i=0: window=[1,2,3], sum=6
i=1: window=[2,3,4], sum=9, max=9
..."
```

### Step 7: COMPLEXITY (1-2 minutes)

```
Always state both time AND space complexity:
"Time complexity: O(n) — single pass through the array
Space complexity: O(k) — the sliding window stores at most k elements

Could we do better? For time complexity, we must read all n elements,
so O(n) is optimal. For space, if we can't modify input, O(k) is optimal."
```

---

## 3. Optimal Coding Style

### Clean Code Principles for Interviews

```cpp
// GOOD: Descriptive variable names
int longestSubarray(vector<int>& nums, int k) {
    int left = 0, maxLength = 0;
    int currentSum = 0;
    
    for (int right = 0; right < nums.size(); right++) {
        currentSum += nums[right];
        
        while (currentSum > k) {
            currentSum -= nums[left];
            left++;
        }
        
        maxLength = max(maxLength, right - left + 1);
    }
    return maxLength;
}

// BAD: Cryptic names
int f(vector<int>& a, int k) {
    int l=0,r=0,mx=0,s=0;
    for(;r<a.size();r++){s+=a[r];while(s>k)s-=a[l++];mx=max(mx,r-l+1);}
    return mx;
}
```

### Style Guidelines

```cpp
// 1. Use meaningful names
int left, right;      // Good (not l, r)
int windowSum;        // Good (not ws)
int maxLength;        // Good (not ans)
TreeNode* current;    // Good (not cur)

// 2. Consistent bracing
if (condition) {
    // body
} else {
    // body
}

// 3. One statement per line
left++;           // Good
left++; right--;  // Acceptable for two related operations

// 4. Extract helper functions
bool isValid(string& s, int left, int right) { /* ... */ }
int getDistance(vector<int>& point1, vector<int>& point2) { /* ... */ }

// 5. Handle edge cases first
vector<int> solve(vector<int>& nums) {
    if (nums.empty()) return {};
    if (nums.size() == 1) return nums;
    // main logic
}

// 6. Use C++17 features appropriately
for (auto& [key, val] : map) { /* ... */ }  // Structured bindings
auto [min_it, max_it] = minmax_element(v.begin(), v.end());
if (auto it = map.find(key); it != map.end()) { /* ... */ }
```

---

## 4. Communication Scripts

### Opening Scripts

```
"Let me take a moment to understand the problem..."

"Before I start coding, let me ask a few clarifying questions..."

"I see. So the input is [restate], and we need to return [restate output]. 
Is that right?"

"Are there any constraints on [time/space/input size] I should know about?"
```

### Thinking Out Loud Scripts

```
"I'm thinking about this... A naive approach would be..."

"I notice that [observation]. This reminds me of the [pattern name] pattern."

"Let me think about the bottleneck here. Currently, [operation X] takes O(n²). 
If I could do that in O(1)..."

"What if I sort the array first? That gives me O(n log n) upfront, but then..."

"I think we can use [data structure] here. Let me think about why..."

"Actually, let me reconsider. I realize [issue with previous approach]..."

"I'm going to try a different approach. Instead of [X], what if we [Y]?"
```

### During Coding Scripts

```
"I'm initializing a hash map to store [purpose]..."

"The outer loop iterates over [what], and for each [element], we..."

"Here I'm using two pointers. Left starts at 0, right will expand..."

"This line handles the edge case where [condition]..."

"I'll add a comment here because this isn't immediately obvious..."
```

### After Writing Code Scripts

```
"Let me trace through the example to verify: input = [...]..."

"I think I need to check: what happens when the input is empty?"

"The time complexity is O(n log n) because [reason]."
"The space complexity is O(n) because we store up to n elements."

"I believe the code is correct. One possible optimization would be..."

"Is there anything you'd like me to clarify or optimize?"
```

---

## 5. Debugging Strategy

### When Your Solution Is Wrong

```
Step 1: Identify the failing case
   - "My code gives X but expected Y for input Z"

Step 2: Trace through manually
   - Walk through line by line with paper/pen
   - Track all variable values
   - Don't assume — verify each step

Step 3: Check common issues
   - Off-by-one errors (< vs <=, 0-indexed vs 1-indexed)
   - Integer overflow (should use long long?)
   - Edge cases (empty, single element, all same)
   - Loop not starting/ending correctly
   - Pointer/reference issues

Step 4: Use print statements (in practice, not interview)
   - Add cout << variable after suspicious lines
   
Step 5: Re-read the problem
   - Sometimes bugs come from misunderstanding the problem
```

### Common Bug Patterns

```cpp
// 1. Off-by-one
for (int i = 0; i < n; i++)   // OK: iterates 0 to n-1
for (int i = 0; i <= n; i++)  // DANGER: iterates 0 to n, potential OOB
for (int i = 1; i < n; i++)   // OK: starts from 1

// 2. Integer overflow
int a = 1000000, b = 1000000;
int product = a * b;           // OVERFLOW! Use long long
long long product = (long long)a * b;  // CORRECT

// 3. Uninitialized variables
int maxVal;                    // DANGER: garbage value
int maxVal = INT_MIN;          // CORRECT: explicit initialization
int maxVal = nums[0];          // CORRECT: initialize from input

// 4. Empty container access
v.front();  // CRASH if v is empty!
if (!v.empty()) v.front();  // SAFE

// 5. Wrong comparison for floating point
double a = 0.1 + 0.2;
if (a == 0.3) { }  // WRONG: floating point precision
if (abs(a - 0.3) < 1e-9) { }  // CORRECT

// 6. Modifying container while iterating
for (auto it = v.begin(); it != v.end(); ) {
    if (*it == target) it = v.erase(it);  // CORRECT: erase returns next
    else it++;
}
```

---

## 6. Common Traps & How to Avoid Them

### Trap 1: Integer Overflow

```cpp
// Problem: n up to 10^5, values up to 10^4 → sum can be 10^9 (fits int)
// But: n up to 10^5, values up to 10^9 → sum can be 10^14 (needs long long!)

// Rule: If you multiply two values both up to 10^5+, use long long
long long sum = 0LL;  // Initialize with LL
sum += (long long)a * b;  // Cast before multiplication

// Check: INT_MAX = 2.1 × 10^9, LLONG_MAX = 9.2 × 10^18
```

### Trap 2: Accessing map with [] Creates Default Entry

```cpp
map<string, int> m;
if (m["key"] == 0) { }  // BAD: creates "key" with value 0 if not present!

// CORRECT:
if (m.count("key") == 0) { }        // Check existence first
if (m.find("key") == m.end()) { }   // Use find()
```

### Trap 3: Comparators Must Be Strict Weak Ordering

```cpp
// WRONG: can cause undefined behavior!
auto cmp = [](int a, int b) { return a >= b; };  // Not strict!

// CORRECT: strict weak ordering (no equals)
auto cmp = [](int a, int b) { return a > b; };   // Strict greater
auto cmp = [](int a, int b) { return a < b; };   // Strict less
```

### Trap 4: Modifying Iterator During Loop

```cpp
// WRONG:
for (auto it = v.begin(); it != v.end(); it++) {
    if (*it == 5) v.erase(it);  // Iterator invalidated!
}

// CORRECT:
v.erase(remove(v.begin(), v.end(), 5), v.end());
```

### Trap 5: Signed/Unsigned Comparison

```cpp
int n = -1;
vector<int> v = {1,2,3};
if (n < v.size()) { }  // DANGER: v.size() is unsigned, -1 becomes huge!

// CORRECT:
if (n < (int)v.size()) { }
// Or just use signed types consistently
```

### Trap 6: Mid Calculation Overflow

```cpp
int left = 0, right = INT_MAX;
int mid = (left + right) / 2;  // OVERFLOW if left + right > INT_MAX!

int mid = left + (right - left) / 2;  // CORRECT: always use this!
```

---

## 7. Company-Specific Insights

### Google
- **Focus:** Algorithmic complexity, clean code
- **Favorite topics:** Graphs, DP, trees, system scalability
- **Style:** Multiple rounds (Coding + System Design + Behavioral)
- **Tips:**
  - Always discuss complexity proactively
  - Code must compile in Docs/Google IDE (practice on Docs)
  - Expect follow-ups to make solution more general/efficient
  - Leadership principles matter: talk about scale

### Meta (Facebook)
- **Focus:** Practical problem-solving, code quality
- **Favorite topics:** Arrays, strings, trees, graphs
- **Style:** 2 coding rounds, 1 behavioral (values)
- **Tips:**
  - Write production-quality code with error handling
  - Must know Facebook's core values (move fast, be bold, focus on impact)
  - Behavioral: STAR format, emphasize impact and metrics
  - Often asks: "Is there any other approach you considered?"

### Amazon
- **Focus:** Leadership Principles (14 principles)
- **Favorite topics:** Graphs, DP, trees, OOP design
- **Style:** 4-5 rounds (mix of LP + coding)
- **Tips:**
  - Every question has a behavioral component
  - Prepare 2-3 STAR stories for each of the 14 principles
  - Customer obsession is most important principle
  - Think about scale: "How does this work at Amazon scale?"

### Microsoft
- **Focus:** Problem solving + system design
- **Favorite topics:** Trees, graphs, strings, OOP
- **Style:** 4-5 rounds, collaborative
- **Tips:**
  - Interviewers are more collaborative — ask for hints if stuck (they want to help)
  - Focus on growing/learning stories in behavioral
  - System design rounds matter
  - Ask questions about team culture — they appreciate curiosity

### Morgan Stanley / Goldman / Citi
- **Focus:** Algorithmic correctness + finance awareness
- **Favorite topics:** Arrays, graphs, dynamic programming
- **Style:** 2-3 coding rounds + risk/trading domain questions
- **Tips:**
  - Know basic financial concepts (options, bonds, risk)
  - Stress-test your solutions (financial systems need high reliability)
  - Discuss error handling and edge cases more than in FAANG
  - Complexity of implementation matters (maintainability > cleverness)

### Uber / Airbnb
- **Focus:** Practical implementation, scalability
- **Favorite topics:** Graphs (trip routing!), trees, system design
- **Style:** 2-3 coding + system design
- **Tips:**
  - Uber: Know graph algorithms well (shortest path = routing)
  - Airbnb: Know about search/ranking systems
  - Think about real-world constraints (GPS accuracy, network failures)

---

## 8. Pressure Handling

### If You're Stuck

```
1. State what you know: "I understand the problem, and I can see that..."

2. Think out loud about approaches:
   "Let me think about what data structures would help here...
   A hashmap would give me O(1) lookup, which could help with..."

3. Ask for a hint (it's OK!):
   "I'm thinking along the lines of dynamic programming. 
   Can you give me a hint about the subproblem structure?"

4. Start with brute force:
   "Let me at least code the brute force O(n²) approach,
   and then we can optimize from there."

5. Draw examples:
   "Let me draw out what should happen with this input..."
```

### If You Make a Mistake

```
"Actually, I realize that's wrong because [reason].
Let me fix that..."

"I see the issue — I forgot to handle the case where [edge case].
Let me add that..."

Never say: "Oh that won't work" and delete everything.
Instead: "That approach has a flaw. Let me adjust..."
```

### Time Management

```
1-2 min: Clarify problem
2-3 min: Work through examples
2-3 min: Discuss brute force + optimization
10-15 min: Code the solution
3-5 min: Test and debug
2 min: Analyze complexity
2 min: Questions for interviewer
```

---

## 9. Behavioral Interview Framework

### STAR Method

```
S - Situation: Set the context (1-2 sentences)
T - Task: What was your responsibility? (1 sentence)
A - Action: What did YOU specifically do? (3-5 sentences, most important)
R - Result: What was the outcome? (quantify if possible)
```

### Prepare These Stories (with C++/Engineering context)

```
1. Most challenging technical problem you've solved
   → Focus on algorithm design, debugging, complexity

2. Time you disagreed with your team / handled conflict
   → Show technical diplomacy: "I presented benchmarks showing..."

3. Time you had to learn something quickly
   → Learning C++ for performance-critical system

4. Biggest failure and what you learned
   → Production bug, chose wrong algorithm, fix + learnings

5. Time you improved a process / mentored someone
   → Code review improvements, DSA study group

6. Most impactful project
   → Quantify: reduced latency by X%, saved $Y, handled Z requests/sec
```

### Questions to Ask Interviewers

```
Technical:
- "What are the biggest technical challenges your team faces?"
- "How does the team handle technical debt?"
- "What does the tech stack look like? Any migration happening?"

Growth:
- "What does success look like in the first 6 months?"
- "How do engineers grow from senior to staff level here?"
- "What learning opportunities exist?"

Culture:
- "How does the team handle failure?"
- "What's the on-call culture like?"
- "What's one thing you wish you'd known before joining?"
```

---

## Pre-Interview Checklist

### One Week Before
```
[ ] Review all 15 patterns — can you recognize and code from memory?
[ ] Practice 2-3 hard problems per day
[ ] Do 2 mock interviews (use Pramp, interviewing.io, or with a peer)
[ ] Review your top 5 behavioral stories
[ ] Research the company (recent news, products, engineering blog)
```

### One Day Before
```
[ ] Light review — don't learn new material
[ ] Review your cheatsheets (STL, patterns)
[ ] Sleep 7-8 hours
[ ] Prepare your setup: extra monitors, headphones, water
[ ] Know the interview format and who you're interviewing with
```

### Interview Day
```
[ ] Test audio, video, coding environment 30 minutes early
[ ] Have a pen and paper for diagrams
[ ] Keep your STL cheatsheet visible (for offline interviews)
[ ] Breathe — you've prepared well
```

---

*Next: [Section 7 — 1 Month Roadmap](./Section7_Monthly_Roadmap.md)*
