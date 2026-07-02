#!/usr/bin/env python3
"""Rebuild DAILY_ASSIGNMENTS: Day 1 = 15 qns, Day 31 = 35+ qns, ~12% Easy, rest M/H."""

import sys
import os

TOPIC_ORDER = [
    "Arrays", "Strings", "HashMap", "Sorting", "Two Pointers", "Sliding Window",
    "Binary Search", "Stack", "Queue", "Linked List", "Trees", "BST", "Heap",
    "Trie", "Graph", "Topological Sort", "Union Find", "Backtracking", "Greedy",
    "Intervals", "Dynamic Programming", "Advanced Graph", "Hard Interview Problems",
]

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Additional Medium/Hard interview problems to expand pool
EXTRA_PROBLEMS = {
    2: ("Add Two Numbers", "M", "Linked List", "Digit carry chain", 25, "445", "VH"),
    8: ("String to Integer (atoi)", "M", "String", "Overflow handling", 25, "65", "H"),
    12: ("Integer to Roman", "M", "Greedy", "Symbol subtraction", 20, "13", "M"),
    13: ("Roman to Integer", "E", "String", "Pair parsing", 15, "12", "M"),
    28: ("Find the Index of the First Occurrence", "E", "String", "KMP / built-in", 15, "214", "H"),
    31: ("Next Permutation", "M", "Array", "In-place rearrange", 25, "60", "H"),
    40: ("Combination Sum II", "M", "Backtracking", "No reuse combos", 25, "39", "H"),
    43: ("Multiply Strings", "M", "String", "Grade-school multiply", 30, "415", "M"),
    44: ("Wildcard Matching", "H", "DP", "Pattern matching", 40, "10", "H"),
    47: ("Permutations II", "M", "Backtracking", "Duplicate handling", 25, "46", "H"),
    48: ("Rotate Image", "M", "Matrix", "Transpose + reverse", 20, "54", "H"),
    50: ("Pow(x, n)", "M", "Binary Search", "Fast exponentiation", 20, "372", "H"),
    54: ("Spiral Matrix", "M", "Matrix", "Boundary walk", 25, "59", "H"),
    59: ("Spiral Matrix II", "M", "Matrix", "Fill spiral", 25, "54", "M"),
    61: ("Rotate List", "M", "Linked List", "Circular rotate", 25, "19", "M"),
    62: ("Unique Paths", "M", "DP", "Grid combinatorics", 20, "63", "VH"),
    63: ("Unique Paths II", "M", "DP", "Obstacle grid", 20, "64", "H"),
    64: ("Minimum Path Sum", "M", "DP", "Grid min sum", 20, "120", "H"),
    65: ("Valid Number", "H", "String", "State machine parse", 35, "8", "M"),
    73: ("Set Matrix Zeroes", "M", "Matrix", "In-place markers", 25, "289", "H"),
    81: ("Search in Rotated Sorted Array II", "M", "Binary Search", "Duplicates", 25, "33", "H"),
    82: ("Remove Duplicates from Sorted List II", "M", "Linked List", "Skip all dupes", 20, "83", "M"),
    86: ("Partition List", "M", "Linked List", "Before/after pivot", 25, "328", "M"),
    87: ("Scramble String", "H", "DP", "Recursion + memo", 40, "44", "M"),
    88: ("Merge Sorted Array", "E", "Two Pointers", "Fill from end", 15, "977", "H"),
    90: ("Subsets II", "M", "Backtracking", "Sorted dedupe", 25, "78", "H"),
    91: ("Decode Ways", "M", "DP", "String segmentation", 25, "639", "H"),
    93: ("Restore IP Addresses", "M", "Backtracking", "IP segment validation", 30, "17", "M"),
    95: ("Unique Binary Search Trees II", "M", "Tree", "Generate all BSTs", 30, "96", "M"),
    96: ("Unique Binary Search Trees", "M", "DP", "Catalan number", 25, "95", "H"),
    97: ("Interleaving String", "M", "DP", "2D boolean DP", 30, "72", "H"),
    100: ("Same Tree", "E", "Tree", "Structural compare", 10, "101", "H"),
    101: ("Symmetric Tree", "E", "Tree", "Mirror check", 12, "226", "H"),
    103: ("Binary Tree Zigzag Level Order", "M", "Tree BFS", "Alternate direction", 25, "102", "H"),
    105: ("Construct BT from Preorder Inorder", "M", "Tree", "Divide by root", 30, "106", "VH"),
    106: ("Construct BT from Inorder Postorder", "M", "Tree", "Postorder root", 30, "105", "H"),
    109: ("Convert Sorted List to BST", "M", "Tree", "Inorder simulation", 30, "108", "M"),
    111: ("Minimum Depth of Binary Tree", "E", "Tree BFS", "First leaf depth", 12, "104", "H"),
    113: ("Path Sum II", "M", "Tree DFS", "All root-leaf paths", 25, "437", "H"),
    114: ("Flatten Binary Tree to Linked List", "M", "Tree", "Morris / reverse", 30, "430", "H"),
    116: ("Populating Next Right Pointers", "M", "Tree BFS", "Level connect", 25, "117", "M"),
    117: ("Populating Next Right Pointers II", "M", "Tree BFS", "Imperfect tree", 25, "116", "M"),
    120: ("Triangle", "M", "DP", "Bottom-up min path", 20, "64", "M"),
    129: ("Sum Root to Leaf Numbers", "M", "Tree DFS", "Path digit sum", 20, "437", "M"),
    132: ("Palindrome Partitioning II", "H", "DP", "Min cuts", 35, "131", "M"),
    135: ("Candy", "H", "Greedy", "Two-pass ratings", 30, "134", "H"),
    136: ("Single Number", "E", "Bit", "XOR cancel", 10, "137", "H"),
    137: ("Single Number II", "M", "Bit", "Mod 3 bits", 25, "137", "H"),
    140: ("Word Break II", "H", "Backtracking+DP", "All segmentations", 40, "139", "H"),
    143: ("Reorder List", "M", "Linked List", "Mid reverse merge", 30, "234", "H"),
    148: ("Sort List", "M", "Linked List", "Merge sort LL", 35, "21", "H"),
    149: ("Max Points on a Line", "H", "HashMap", "Slope counting", 35, "228", "M"),
    150: ("Evaluate Reverse Polish Notation", "M", "Stack", "RPN eval", 20, "224", "H"),
    151: ("Reverse Words in a String", "M", "String", "Two-pass reverse", 20, "186", "H"),
    154: ("Find Minimum in Rotated II", "H", "Binary Search", "Dupes in rotated", 30, "153", "H"),
    155: ("Min Stack", "M", "Stack", "O(1) min", 20, "716", "VH"),
    156: ("Binary Tree Upside Down", "M", "Tree", "Pointer rewrite", 25, "226", "M"),
    157: ("Read N Characters Given Read4", "E", "Array", "Buffer read", 15, "158", "M"),
    158: ("Read N Characters Given Read4 II", "H", "Array", "Multiple calls", 30, "157", "M"),
    161: ("One Edit Distance", "M", "String", "Edit check", 20, "72", "M"),
    163: ("Missing Ranges", "E", "Array", "Gap enumeration", 15, "228", "M"),
    165: ("Compare Version Numbers", "M", "String", "Segment compare", 20, "43", "M"),
    166: ("Fraction to Recurring Decimal", "M", "HashMap", "Cycle detection", 25, "141", "M"),
    173: ("Binary Search Tree Iterator", "M", "Stack", "Controlled inorder", 25, "230", "H"),
    174: ("Dungeon Game", "H", "DP", "Reverse min health", 35, "64", "M"),
    186: ("Reverse Words in a String II", "M", "String", "In-place reverse", 20, "151", "M"),
    188: ("Best Time to Buy and Sell Stock IV", "H", "DP", "k transactions", 40, "123", "H"),
    189: ("Rotate Array", "M", "Array", "Reverse segments", 20, "61", "H"),
    190: ("Reverse Bits", "E", "Bit", "Bit manipulation", 12, "191", "M"),
    191: ("Number of 1 Bits", "E", "Bit", "Hamming weight", 10, "338", "H"),
    199: ("Binary Tree Right Side View", "M", "Tree BFS", "Last per level", 20, "545", "H"),
    201: ("Bitwise AND of Numbers Range", "M", "Bit", "Common prefix", 20, "191", "M"),
    203: ("Remove Linked List Elements", "E", "Linked List", "Dummy head delete", 12, "237", "M"),
    204: ("Count Primes", "M", "Math", "Sieve of Eratosthenes", 20, "264", "M"),
    205: ("Isomorphic Strings", "E", "HashMap", "Bijection mapping", 15, "290", "M"),
    213: ("House Robber II", "M", "DP", "Circular robber", 25, "198", "VH"),
    214: ("Shortest Palindrome", "H", "String", "KMP prefix", 35, "5", "M"),
    218: ("The Skyline Problem", "H", "Heap", "Sweep line", 45, "699", "H"),
    219: ("Contains Duplicate II", "E", "HashMap", "Index distance", 12, "220", "H"),
    220: ("Contains Duplicate III", "H", "Bucket/SortedSet", "Window abs diff", 35, "219", "H"),
    221: ("Maximal Square", "M", "DP", "Side length DP", 25, "85", "H"),
    224: ("Basic Calculator", "H", "Stack", "Expression + parens", 35, "227", "H"),
    228: ("Summary Ranges", "E", "Array", "Consecutive ranges", 15, "163", "M"),
    229: ("Majority Element II", "M", "HashMap", "Boyer-Moore II", 25, "169", "M"),
    230: ("Kth Smallest in BST", "M", "BST", "Inorder kth", 20, "98", "VH"),
    231: ("Power of Two", "E", "Bit", "n & (n-1)", 10, "326", "M"),
    237: ("Delete Node in a Linked List", "E", "Linked List", "Copy next", 10, "19", "M"),
    241: ("Different Ways to Add Parentheses", "M", "Divide Conquer", "Split operators", 30, "95", "M"),
    279: ("Perfect Squares", "M", "DP/BFS", "Min squares sum", 25, "322", "H"),
    280: ("Wiggle Sort", "M", "Greedy", "Peak valley", 25, "324", "M"),
    281: ("Zigzag Iterator", "M", "Design", "Interleave lists", 25, "1424", "M"),
    285: ("Inorder Successor in BST", "M", "BST", "Successor walk", 20, "510", "M"),
    286: ("Walls and Gates", "M", "Graph BFS", "Multi-source BFS", 25, "994", "H"),
    289: ("Game of Life", "M", "Matrix", "In-place state", 25, "73", "M"),
    290: ("Word Pattern", "E", "HashMap", "Bijection check", 15, "205", "M"),
    295: ("Find Median from Data Stream", "H", "Heap", "Two heap balance", 35, "480", "VH"),
    296: ("Best Meeting Point", "H", "Math", "Manhattan median", 30, "286", "M"),
    301: ("Remove Invalid Parentheses", "H", "BFS/Backtrack", "Min removals", 40, "22", "H"),
    305: ("Number of Islands II", "H", "Union Find", "Dynamic connectivity", 35, "200", "M"),
    307: ("Range Sum Query Mutable", "M", "Segment Tree", "Point update", 30, "315", "M"),
    308: ("Range Sum Query 2D Mutable", "H", "Segment Tree", "2D fenwick", 40, "307", "M"),
    309: ("Best Time Buy Sell Cooldown", "M", "DP", "State machine", 25, "714", "H"),
    311: ("Sparse Matrix Multiplication", "M", "Matrix", "Skip zeros", 25, "73", "M"),
    313: ("Super Ugly Number", "M", "Heap/DP", "Multi-pointer", 30, "264", "M"),
    314: ("Binary Tree Vertical Order", "M", "Tree BFS", "Column map", 25, "987", "H"),
    315: ("Count of Smaller Numbers After Self", "H", "Merge Sort/BIT", "Inversion count", 40, "493", "H"),
    316: ("Remove Duplicate Letters", "M", "Stack/Greedy", "Lex smallest", 25, "1081", "H"),
    317: ("Shortest Distance from All Buildings", "H", "Graph BFS", "Multi-source sum", 40, "286", "M"),
    318: ("Maximum Product of Word Lengths", "M", "Bit", "Bitmask words", 25, "191", "M"),
    319: ("Bulb Switcher", "M", "Math", "Perfect squares", 20, "1178", "M"),
    320: ("Generalized Abbreviation", "M", "Backtracking", "Bit mask abbr", 25, "78", "M"),
    322: ("Coin Change", "M", "DP", "Min coins", 25, "518", "VH"),
    325: ("Maximum Size Subarray Sum Equals k", "M", "HashMap", "Prefix sum", 25, "560", "H"),
    327: ("Count of Range Sum", "H", "Merge Sort", "Range count", 45, "315", "M"),
    328: ("Odd Even Linked List", "M", "Linked List", "Partition nodes", 20, "86", "M"),
    330: ("Patching Array", "H", "Greedy", "Missing coverage", 35, "45", "M"),
    334: ("Increasing Triplet Subsequence", "M", "Greedy", "Three pointers", 20, "300", "H"),
    337: ("House Robber III", "M", "Tree DP", "Include/exclude", 25, "198", "H"),
    338: ("Counting Bits", "M", "DP/Bit", "DP on bits", 20, "191", "H"),
    341: ("Flatten Nested List Iterator", "M", "Stack/DFS", "Lazy flatten", 30, "385", "M"),
    343: ("Integer Break", "M", "DP/Math", "Max product split", 20, "279", "M"),
    347: ("Top K Frequent Elements", "M", "Heap/Bucket", "Frequency top-k", 25, "692", "VH"),
    348: ("Design Tic-Tac-Toe", "M", "Design", "Row/col/diag track", 25, "794", "M"),
    349: ("Intersection of Two Arrays", "E", "HashSet", "Set intersection", 12, "350", "M"),
    350: ("Intersection of Two Arrays II", "E", "HashMap", "Freq intersection", 15, "349", "M"),
    352: ("Data Stream as Disjoint Intervals", "H", "Binary Search", "Merge intervals", 35, "56", "M"),
    353: ("Design Snake Game", "M", "Design", "Queue + set", 30, "499", "M"),
    354: ("Russian Doll Envelopes", "H", "DP/Binary Search", "LIS variant", 35, "300", "H"),
    355: ("Design Twitter", "M", "Design", "Feed + follow", 35, "Tweet", "H"),
    358: ("Rearrange String k Distance Apart", "H", "Heap/Greedy", "K distance apart", 35, "767", "M"),
    359: ("Logger Rate Limiter", "E", "HashMap", "Message throttle", 12, "362", "M"),
    362: ("Design Hit Counter", "M", "Queue", "Sliding window count", 20, "359", "M"),
    363: ("Max Sum of Rectangle No Larger Than K", "H", "TreeSet/DP", "Submatrix sum", 40, "53", "M"),
    368: ("Largest Divisible Subset", "M", "DP/Sort", "Chain divisibility", 30, "300", "M"),
    369: ("Plus One Linked List", "M", "Linked List", "Reverse add", 20, "2", "M"),
    370: ("Range Addition", "M", "Prefix Diff", "Difference array", 20, "1109", "M"),
    372: ("Super Pow", "M", "Math/DP", "Modular exponent", 25, "50", "M"),
    373: ("Find K Pairs with Smallest Sums", "M", "Heap", "K-way merge", 30, "23", "H"),
    374: ("Guess Number Higher or Lower", "E", "Binary Search", "Classic guess", 10, "278", "M"),
    375: ("Guess Number Higher or Lower II", "M", "DP", "Minimax cost", 30, "464", "M"),
    376: ("Wiggle Subsequence", "M", "Greedy/DP", "Alternating seq", 20, "300", "M"),
    377: ("Combination Sum IV", "M", "DP", "Order matters", 25, "518", "H"),
    378: ("Kth Smallest in Sorted Matrix", "M", "Heap/Binary Search", "Matrix kth", 30, "373", "H"),
    379: ("Design Phone Directory", "M", "Design", "Available number pool", 25, "362", "M"),
    380: ("Insert Delete GetRandom O(1)", "M", "HashMap+Array", "Swap delete", 30, "381", "H"),
    381: ("Insert Delete GetRandom O(1) Duplicates", "H", "HashMap+Set", "Dup allowed", 35, "380", "M"),
    382: ("Linked List Random Node", "M", "Reservoir", "Reservoir sampling", 20, "398", "M"),
    384: ("Shuffle an Array", "M", "Design", "Fisher-Yates", 20, "382", "M"),
    385: ("Mini Parser", "M", "Stack", "Nested integer", 25, "341", "M"),
    386: ("Lexicographical Numbers", "M", "DFS", "Lex order nums", 25, "440", "M"),
    387: ("First Unique Character", "E", "HashMap", "Freq scan", 10, "442", "M"),
    388: ("Longest Absolute File Path", "M", "Stack", "Path depth", 25, "71", "M"),
    389: ("Find the Difference", "E", "Bit/HashMap", "XOR or count", 10, "136", "M"),
    390: ("Elimination Game", "M", "Math", "Josephus variant", 25, "779", "M"),
    391: ("Perfect Rectangle", "H", "HashMap", "Area + corners", 35, "85", "M"),
    392: ("Is Subsequence", "E", "Two Pointers", "Greedy match", 12, "1143", "H"),
    393: ("UTF-8 Validation", "M", "Bit", "Byte sequence", 25, "385", "M"),
    394: ("Decode String", "M", "Stack", "Nested decode", 25, "20", "H"),
    395: ("Longest Substring K Distinct", "M", "Sliding Window", "At most K", 25, "340", "H"),
    396: ("Rotate Function", "M", "Math", "Prefix rotation", 25, "189", "M"),
    397: ("Integer Replacement", "M", "Greedy/DP", "Collatz steps", 25, "343", "M"),
    398: ("Random Pick Index", "M", "Reservoir", "Equal probability", 20, "382", "M"),
    399: ("Evaluate Division", "M", "Graph/UnionFind", "Weighted graph", 30, "947", "H"),
    400: ("Nth Digit", "M", "Math", "Digit sequence", 25, "386", "M"),
    402: ("Remove K Digits", "M", "Stack/Greedy", "Monotonic stack", 25, "316", "H"),
    403: ("Frog Jump", "H", "DP/HashSet", "Stone jump", 35, "55", "M"),
    406: ("Queue Reconstruction by Height", "M", "Greedy", "Sort insert", 25, "763", "H"),
    407: ("Trapping Rain Water II", "H", "Heap/BFS", "3D rain water", 40, "42", "M"),
    410: ("Split Array Largest Sum", "H", "Binary Search", "Minimize max sum", 35, "875", "H"),
    413: ("Arithmetic Slices", "M", "DP", "Subarray count", 20, "446", "M"),
    415: ("Add Strings", "E", "String", "Digit add", 15, "2", "M"),
    416: ("Partition Equal Subset Sum", "M", "DP", "0/1 knapsack", 30, "494", "VH"),
    417: ("Pacific Atlantic Water Flow", "M", "Graph DFS", "Multi-source", 30, "130", "H"),
    418: ("Sentence Screen Fitting", "M", "DP/Greedy", "Word wrap cycle", 25, "68", "M"),
    419: ("Battleships in a Board", "M", "Matrix", "One-pass count", 25, "200", "M"),
    420: ("Strong Password Checker", "H", "Greedy", "Edit distance rules", 35, "72", "M"),
    421: ("Maximum XOR of Two Numbers", "M", "Trie/Bit", "Max XOR pair", 30, "136", "H"),
    424: ("Longest Repeating Character Replacement", "M", "Sliding Window", "Max freq", 30, "1004", "VH"),
    427: ("Construct Quad Tree", "M", "Divide Conquer", "Quad tree build", 30, "308", "M"),
    428: ("Serialize N-ary Tree", "M", "Tree", "N-ary codec", 30, "297", "M"),
    429: ("N-ary Tree Level Order", "M", "Tree BFS", "N-ary levels", 20, "102", "M"),
    430: ("Flatten Multilevel Doubly LL", "M", "Linked List", "DFS flatten", 30, "114", "M"),
    432: ("All O`one Data Structure", "H", "HashMap+DLL", "Freq buckets", 40, "460", "M"),
    433: ("Minimum Genetic Mutation", "M", "Graph BFS", "Word ladder variant", 25, "127", "M"),
    435: ("Non-overlapping Intervals", "M", "Greedy", "Interval scheduling", 25, "452", "VH"),
    436: ("Find Right Interval", "M", "Binary Search", "Interval lookup", 25, "56", "M"),
    437: ("Path Sum III", "M", "Tree DFS", "Prefix on path", 30, "112", "H"),
    438: ("Find All Anagrams", "M", "Sliding Window", "Fixed window", 25, "567", "H"),
    440: ("K-th Smallest in Lex Order", "H", "Math/DFS", "Lex order nums", 35, "386", "M"),
    442: ("Find All Duplicates", "M", "Array", "Index marking", 20, "448", "H"),
    443: ("String Compression", "M", "Two Pointers", "In-place compress", 20, "38", "M"),
    445: ("Add Two Numbers II", "M", "Stack/LL", "Reverse add", 25, "2", "M"),
    446: ("Arithmetic Slices II Subsequence", "H", "DP", "Subseq AP count", 40, "413", "M"),
    447: ("Number of Boomerangs", "M", "HashMap", "Slope counting", 35, "149", "M"),
    448: ("Find Disappeared Numbers", "E", "Array", "Index marking", 20, "442", "M"),
    449: ("Serialize Deserialize BST", "M", "Tree", "BST codec", 30, "297", "M"),
    451: ("Sort Characters By Frequency", "M", "Heap/HashMap", "Freq sort", 20, "347", "M"),
    452: ("Min Arrows Burst Balloons", "M", "Greedy", "End-point sort", 25, "435", "H"),
    453: ("Minimum Moves Equal Array", "M", "Math", "Increment/decrement", 20, "462", "M"),
    454: ("4Sum II", "M", "HashMap", "Pair sum count", 25, "18", "M"),
    456: ("132 Pattern", "M", "Stack", "Monotonic stack", 25, "84", "H"),
    457: ("Circular Array Loop", "M", "Fast/Slow", "Cycle direction", 25, "141", "M"),
    458: ("Poor Pigs", "H", "Math", "Information theory", 30, "319", "M"),
    460: ("LFU Cache", "H", "HashMap+DLL", "Freq eviction", 45, "146", "H"),
    464: ("Can I Win", "M", "DP/Bitmask", "Game theory", 30, "375", "M"),
    465: ("Optimal Account Balancing", "H", "Backtracking", "Min transfers", 40, "1300", "M"),
    466: ("Count The Repetitions", "H", "DP", "String cycle", 35, "418", "M"),
    468: ("Validate IP Address", "M", "String", "IPv4/IPv6 parse", 25, "93", "M"),
    470: ("Implement Rand7 via Rand10", "M", "Math", "Rejection sampling", 25, "382", "M"),
    473: ("Matchsticks to Square", "M", "Backtracking", "Partition 4", 30, "416", "M"),
    474: ("Ones and Zeroes", "M", "DP Knapsack", "2D knapsack", 30, "416", "H"),
    475: ("Heaters", "M", "Binary Search", "Min radius", 25, "875", "M"),
    477: ("Total Hamming Distance", "M", "Bit", "Bit contribution", 25, "461", "M"),
    480: ("Sliding Window Median", "H", "Heap/BST", "Window median", 40, "295", "H"),
    481: ("Magical String", "M", "Greedy", "Pattern generation", 25, "390", "M"),
    483: ("Smallest Good Base", "H", "Math", "Base conversion", 40, "168", "M"),
    486: ("Predict Winner", "M", "DP", "Minimax game", 30, "464", "M"),
    487: ("Max Consecutive Ones II", "M", "Sliding Window", "Flip at most 1", 20, "1004", "M"),
    490: ("The Maze", "M", "Graph DFS/BFS", "Rolling ball", 25, "505", "M"),
    493: ("Reverse Pairs", "H", "Merge Sort", "Inversion variant", 40, "315", "H"),
    494: ("Target Sum", "M", "DP", "+/- subset", 30, "416", "VH"),
    497: ("Random Point in Non-overlapping Rectangles", "M", "Reservoir", "Weighted pick", 30, "398", "M"),
    498: ("Diagonal Traverse", "M", "Matrix", "Diagonal walk", 25, "1424", "M"),
    499: ("Max Value of Equation", "H", "Heap", "Line equation", 35, "149", "M"),
    502: ("IPO", "H", "Heap", "Capital max", 35, "621", "M"),
    503: ("Next Greater Element II", "M", "Monotonic Stack", "Circular NGE", 20, "739", "M"),
    505: ("The Maze II", "M", "Dijkstra", "Shortest stop", 30, "490", "M"),
    510: ("Inorder Successor BST II", "M", "BST", "Parent pointer", 20, "285", "M"),
    513: ("Find Bottom Left Tree Value", "M", "Tree BFS", "Last left leaf", 20, "102", "M"),
    514: ("Freedom Trail", "H", "DP", "Ring typing", 40, "72", "M"),
    516: ("Longest Palindromic Subsequence", "M", "DP", "Subseq palindrome", 30, "5", "H"),
    518: ("Coin Change II", "M", "DP", "Combination count", 25, "322", "H"),
    519: ("Random Flip Matrix", "M", "Reservoir", "Uniform flip", 30, "384", "M"),
    523: ("Continuous Subarray Sum", "M", "HashMap", "Mod prefix", 25, "560", "H"),
    525: ("Contiguous Array", "M", "HashMap", "0/1 balance", 30, "560", "H"),
    526: ("Beautiful Arrangement", "M", "Backtracking", "Divisibility perm", 25, "46", "M"),
    528: ("Random Pick with Weight", "M", "Binary Search", "Weighted pick", 25, "398", "H"),
    529: ("Minesweeper", "M", "Graph DFS/BFS", "Grid reveal", 25, "733", "M"),
    531: ("Lonely Pixel I", "M", "Matrix", "Row/col scan", 20, "533", "M"),
    532: ("K-diff Pairs", "M", "HashMap", "Two sum variant", 20, "1", "M"),
    535: ("Encode and Decode TinyURL", "M", "HashMap", "Bijection encode", 20, "271", "M"),
    536: ("Construct BST from Preorder", "M", "BST", "Upper bound DFS", 25, "105", "M"),
    537: ("Complex Number Multiply", "M", "Math", "Complex arithmetic", 15, "415", "M"),
    538: ("Convert BST to Greater Tree", "M", "Tree", "Reverse inorder", 20, "230", "H"),
    539: ("Minimum Time Difference", "M", "Sorting", "Circular time", 25, "253", "M"),
    540: ("Single Element in Sorted Array", "M", "Binary Search", "Odd occurrence", 20, "136", "H"),
    541: ("Reverse String II", "E", "String", "Chunk reverse", 12, "344", "M"),
    542: ("01 Matrix", "M", "Graph BFS", "Nearest 0", 25, "994", "H"),
    545: ("Boundary of Binary Tree", "M", "Tree DFS", "Anti-clockwise", 25, "199", "M"),
    547: ("Number of Provinces", "M", "Union Find", "Connected comps", 25, "200", "VH"),
    548: ("Split Array with Equal Sum", "H", "Prefix Sum", "4-partition", 35, "416", "M"),
    549: ("Binary Tree Longest Consecutive II", "M", "Tree DFS", "Up/down seq", 30, "298", "M"),
    554: ("Brick Wall", "M", "HashMap", "Min cross count", 25, "391", "M"),
    556: ("Next Greater Element III", "M", "String/Math", "Next permutation", 25, "31", "M"),
    560: ("Subarray Sum Equals K", "M", "HashMap", "Prefix count", 25, "974", "VH"),
    565: ("Array Nesting", "M", "Graph/UnionFind", "Longest cycle", 25, "684", "M"),
    567: ("Permutation in String", "M", "Sliding Window", "Anagram window", 25, "438", "H"),
    576: ("Out of Boundary Paths", "M", "DP", "Grid paths mod", 30, "62", "M"),
    581: ("Shortest Unsorted Continuous Subarray", "M", "Two Pointers", "Sort boundary", 25, "280", "H"),
    583: ("Delete Operation for Two Strings", "M", "DP", "LCS delete", 25, "1143", "M"),
    587: ("Erect the Fence", "H", "Geometry", "Convex hull", 40, "149", "M"),
    588: ("Design In-Memory File System", "H", "Trie/HashMap", "Path trie", 45, "1166", "M"),
    593: ("Valid Square", "M", "HashMap", "Distance set", 25, "149", "M"),
    609: ("Find Duplicate File in System", "M", "HashMap", "Content hash", 25, "49", "M"),
    611: ("Valid Triangle Number", "M", "Two Pointers", "Sorted triple", 25, "15", "M"),
    621: ("Task Scheduler", "M", "Greedy/Heap", "Cooldown slots", 25, "767", "VH"),
    622: ("Design Circular Queue", "M", "Queue", "Ring buffer", 25, "641", "M"),
    623: ("Add One Row to Tree", "M", "Tree BFS", "Level insert", 20, "429", "M"),
    624: ("Maximum Distance in Arrays", "M", "Greedy", "Min/max cross", 20, "149", "M"),
    629: ("K Inverse Pairs Array", "H", "DP", "Inversion count", 40, "315", "M"),
    632: ("Smallest Range Covering K Lists", "H", "Heap/Two Ptr", "Range cover", 35, "373", "H"),
    636: ("Exclusive Time of Functions", "M", "Stack", "Call stack sim", 30, "227", "M"),
    638: ("Shopping Offers", "M", "Backtracking/DP", "Offer bundles", 30, "39", "M"),
    639: ("Decode Ways II", "H", "DP", "Wildcard decode", 35, "91", "M"),
    641: ("Design Circular Deque", "M", "Deque", "Double-ended ring", 25, "622", "M"),
    646: ("Maximum Length of Pair Chain", "M", "Greedy", "Interval chain", 20, "435", "H"),
    647: ("Palindromic Substrings", "M", "Expand", "Count palindromes", 25, "5", "H"),
    648: ("Replace Words", "M", "Trie", "Prefix replace", 20, "208", "M"),
    649: ("Dota2 Senate", "M", "Queue/Greedy", "Ban simulation", 25, "621", "M"),
    650: ("2 Keys Keyboard", "M", "DP/Math", "Copy paste ops", 25, "343", "M"),
    652: ("Find Duplicate Subtrees", "M", "Tree", "Serialize hash", 30, "297", "H"),
    654: ("Maximum Binary Tree", "M", "Tree", "Max build", 25, "105", "M"),
    658: ("Find K Closest Elements", "M", "Binary Search", "Window shrink", 25, "973", "H"),
    659: ("Split Array into Consecutive Subsequences", "M", "Greedy/Heap", "Consecutive groups", 30, "846", "H"),
    662: ("Maximum Width of Binary Tree", "M", "Tree BFS", "Index width", 25, "102", "H"),
    665: ("Non-decreasing Array", "E", "Greedy", "One fix allowed", 15, "581", "M"),
    667: ("Beautiful Arrangement II", "M", "Greedy", "Diff sequence", 25, "526", "M"),
    668: ("Kth Smallest in Lex Order", "H", "Math", "Lex order", 35, "440", "M"),
    673: ("Number of Longest Increasing Subsequence", "M", "DP", "LIS count", 30, "300", "H"),
    674: ("Longest Continuous Increasing Subsequence", "E", "Array", "Run length", 12, "300", "M"),
    675: ("Cut Off Trees for Golf Event", "H", "BFS", "Multi-target BFS", 40, "994", "M"),
    676: ("Implement Magic Dictionary", "M", "Trie", "One char diff", 25, "211", "M"),
    677: ("Map Sum Pairs", "M", "Trie", "Prefix sum", 25, "208", "M"),
    678: ("Valid Parenthesis String", "M", "Greedy", "Wildcard paren", 25, "32", "H"),
    679: ("24 Game", "H", "Backtracking", "Expression build", 35, "241", "M"),
    684: ("Redundant Connection", "M", "Union Find", "Cycle edge", 25, "685", "H"),
    685: ("Redundant Connection II", "H", "Union Find", "Directed cycle", 35, "684", "M"),
    686: ("Repeated String Match", "M", "String", "Period check", 25, "28", "M"),
    687: ("Longest Univalue Path", "M", "Tree DFS", "Same value path", 25, "124", "H"),
    688: ("Knight Probability in Chessboard", "M", "DP", "Random walk", 30, "576", "M"),
    689: ("Maximum Sum of 3 Non-Overlapping Subarrays", "H", "DP/Prefix", "Three windows", 35, "53", "H"),
    691: ("Stickers to Spell Word", "H", "Backtracking/DP", "Sticker cover", 40, "638", "M"),
    692: ("Top K Frequent Words", "M", "Heap/Trie", "Lex tie-break", 30, "347", "H"),
    693: ("Binary Number with Alternating Bits", "E", "Bit", "Alternate check", 12, "191", "M"),
    694: ("Number of Distinct Islands", "M", "Graph DFS", "Shape hash", 25, "200", "M"),
    695: ("Max Area of Island", "M", "Graph DFS", "Component area", 20, "200", "H"),
    698: ("Partition to K Equal Sum Subsets", "M", "Backtracking", "K partition", 35, "416", "H"),
    699: ("Falling Squares", "H", "Segment Tree", "Height timeline", 40, "218", "M"),
    701: ("Insert into BST", "M", "BST", "BST insert", 15, "450", "M"),
    702: ("Search in Sorted Array", "M", "Binary Search", "Unknown size", 20, "278", "M"),
    703: ("Kth Largest in Stream", "E", "Heap", "Min heap k", 15, "215", "H"),
    705: ("Design HashSet", "E", "HashMap", "Basic hash set", 15, "706", "M"),
    706: ("Design HashMap", "E", "HashMap", "Basic hash map", 15, "705", "M"),
    707: ("Design Linked List", "M", "Linked List", "Full LL API", 30, "146", "M"),
    708: ("Insert Sorted Circular LL", "M", "Linked List", "Circular insert", 25, "61", "M"),
    709: ("To Lower Case", "E", "String", "ASCII convert", 8, "344", "L"),
    710: ("Random Pick with Blacklist", "H", "HashMap", "Remap indices", 35, "398", "M"),
    712: ("Minimum ASCII Delete Sum", "M", "DP", "LCS variant", 30, "1143", "M"),
    713: ("Subarray Product Less Than K", "M", "Sliding Window", "Product window", 25, "209", "H"),
    714: ("Best Time Buy Sell with Fee", "M", "DP", "Transaction fee", 25, "309", "H"),
    715: ("Range Module", "H", "TreeMap", "Interval module", 40, "352", "M"),
    718: ("Maximum Length Repeated Subarray", "M", "DP", "Common subarray", 30, "1143", "H"),
    719: ("Find K-th Smallest Pair Distance", "H", "Binary Search", "Pair distance", 40, "658", "H"),
    721: ("Accounts Merge", "M", "Union Find", "Email merge", 30, "547", "VH"),
    722: ("Remove Comments", "M", "Stack", "Source parse", 25, "227", "M"),
    723: ("Candy Crush", "M", "Matrix", "Gravity sim", 30, "289", "M"),
    724: ("Find Pivot Index", "E", "Prefix Sum", "Balance index", 15, "1991", "M"),
    729: ("My Calendar I", "M", "TreeMap", "Overlap check", 25, "715", "H"),
    730: ("Count Different Palindromes", "H", "DP", "Distinct palins", 45, "647", "M"),
    731: ("My Calendar II", "M", "TreeMap", "Double booking", 30, "729", "M"),
    732: ("My Calendar III", "H", "TreeMap", "Triple overlap", 35, "731", "M"),
    735: ("Asteroid Collision", "M", "Stack", "Collision sim", 25, "739", "H"),
    736: ("Parse Lisp Expression", "H", "Stack/Recursion", "Mini interpreter", 45, "224", "M"),
    737: ("Sentence Similarity II", "M", "Union Find", "Word groups", 25, "721", "M"),
    738: ("Monotone Increasing Digits", "M", "Greedy", "Digit decrease", 20, "402", "M"),
    739: ("Daily Temperatures", "M", "Monotonic Stack", "NGE template", 25, "496", "VH"),
    740: ("Delete and Earn", "M", "DP", "House robber variant", 25, "198", "M"),
    741: ("Cherry Pickup", "H", "DP", "Grid two-pass", 40, "174", "M"),
    743: ("Network Delay Time", "M", "Dijkstra", "Shortest path", 30, "787", "VH"),
    746: ("Min Cost Climbing Stairs", "E", "DP", "Stair cost", 15, "70", "H"),
    747: ("Largest Number At Least Twice", "E", "Array", "Max/second max", 10, "215", "M"),
    752: ("Open the Lock", "M", "Graph BFS", "Combo lock", 30, "127", "H"),
    753: ("Cracking the Safe", "H", "Graph/Euler", "De Bruijn seq", 40, "332", "M"),
    754: ("Reach a Number", "M", "Math/Binary Search", "Sum target", 25, "45", "M"),
    757: ("Set Intersection Size At Least Two", "H", "Greedy", "Interval cover", 35, "435", "M"),
    759: ("Employee Free Time", "H", "Heap/Intervals", "Common free", 35, "253", "M"),
    763: ("Partition Labels", "M", "Greedy", "Last occurrence", 20, "856", "H"),
    767: ("Reorganize String", "M", "Heap", "No adjacent dup", 25, "621", "H"),
    768: ("Max Chunks To Make Sorted II", "H", "Stack/Greedy", "Monotonic chunks", 35, "763", "M"),
    769: ("Max Chunks To Make Sorted", "M", "Greedy", "Max reach chunk", 20, "768", "H"),
    770: ("Basic Calculator IV", "H", "Stack", "Polynomial eval", 45, "224", "M"),
    772: ("Basic Calculator III", "H", "Stack", "Nested parens", 40, "224", "M"),
    773: ("Sliding Puzzle", "H", "Graph BFS", "Board BFS", 40, "127", "M"),
    778: ("Swim in Rising Water", "H", "Dijkstra/UF", "Min max path", 35, "743", "M"),
    779: ("K-th Symbol in Grammar", "M", "Recursion", "Tree path", 25, "390", "M"),
    781: ("Rabbits in Forest", "M", "HashMap", "Group sizing", 20, "649", "M"),
    787: ("Cheapest Flights K Stops", "M", "Bellman-Ford", "K-stop path", 35, "743", "VH"),
    790: ("Domino and Tromino Tiling", "M", "DP", "Board tiling", 30, "70", "M"),
    792: ("Number of Matching Subsequences", "M", "HashMap/Trie", "Stream match", 30, "392", "H"),
    797: ("All Paths Source Target", "M", "Graph DFS", "Path enum", 20, "113", "M"),
    799: ("Champagne Tower", "M", "DP", "Liquid flow", 25, "790", "M"),
    802: ("Find Eventual Safe States", "M", "Topological Sort", "Safe nodes", 30, "207", "H"),
    815: ("Bus Routes", "H", "Graph BFS", "Route as node", 40, "127", "M"),
    839: ("Similar String Groups", "H", "Union Find", "Swap similarity", 35, "721", "M"),
    846: ("Hand of Straights", "M", "Greedy/HashMap", "Consecutive groups", 25, "1296", "M"),
    847: ("Shortest Path All Keys", "H", "BFS+Bitmask", "State compression", 45, "127", "M"),
    853: ("Car Fleet", "M", "Stack/Sort", "Fleet merge", 25, "735", "H"),
    854: ("K Similar Strings", "H", "BFS", "Swap distance", 35, "72", "M"),
    855: ("Exam Room", "M", "TreeSet", "Seat distance", 30, "849", "M"),
    856: ("Score of Parentheses", "M", "Stack", "Nested score", 20, "32", "H"),
    862: ("Shortest Subarray Sum K", "H", "Monotonic Deque", "Prefix deque", 35, "239", "H"),
    863: ("All Nodes Distance K", "M", "Tree DFS+Graph", "Parent pointers", 30, "236", "M"),
    864: ("Shortest Path All Keys", "H", "BFS+Bitmask", "Keys bitmask", 45, "847", "M"),
    865: ("Smallest Subtree All Deepest", "M", "Tree DFS", "Deepest LCA", 25, "236", "M"),
    866: ("Prime Palindrome", "M", "Math", "Palindrome prime", 25, "204", "M"),
    871: ("Minimum Number Refueling Stops", "H", "Heap/DP", "Max heap greedy", 35, "134", "H"),
    875: ("Koko Eating Bananas", "M", "Binary Search", "Answer space", 25, "1011", "VH"),
    877: ("Stone Game", "M", "DP", "Minimax piles", 25, "486", "M"),
    881: ("Boats to Save People", "M", "Two Pointers", "Greedy pair", 20, "167", "H"),
    886: ("Possible Bipartition", "M", "Graph BFS", "2-coloring", 25, "207", "H"),
    889: ("Construct BT Preorder Postorder", "M", "Tree", "Divide conquer", 30, "105", "H"),
    904: ("Fruit Into Baskets", "M", "Sliding Window", "At most 2 distinct", 25, "992", "H"),
    907: ("Sum Subarray Mins", "M", "Monotonic Stack", "Contribution", 30, "84", "H"),
    909: ("Snakes and Ladders", "M", "Graph BFS", "Board shortest", 30, "127", "M"),
    910: ("Smallest Range I", "E", "Math", "Range shift", 12, "658", "M"),
    912: ("Sort an Array", "M", "Merge/Quick", "Classic sort", 30, "215", "M"),
    918: ("Max Sum Circular Subarray", "M", "Kadane", "Circular wrap", 25, "53", "M"),
    919: ("Complete Binary Tree Inserter", "M", "Tree BFS", "Level fill", 30, "116", "M"),
    921: ("Minimum Add Parentheses", "M", "Stack/Greedy", "Balance parens", 20, "32", "H"),
    922: ("Sort Array By Parity", "E", "Two Pointers", "Even first", 10, "905", "M"),
    923: ("3Sum With Multiplicity", "M", "HashMap", "Count triplets", 30, "15", "H"),
    926: ("Flip String to Monotone Increasing", "M", "DP/Prefix", "Min flips", 25, "152", "H"),
    931: ("Minimum Falling Path Sum", "M", "DP", "Grid min path", 25, "64", "H"),
    934: ("Shortest Bridge", "M", "Graph DFS+BFS", "Bridge connect", 35, "200", "H"),
    935: ("Knight Dialer", "M", "DP", "Phone keypad hops", 25, "688", "H"),
    939: ("Minimum Area Rectangle", "M", "HashMap", "Diagonal pairs", 30, "149", "H"),
    940: ("Distinct Subsequences II", "H", "DP", "Mod count subseq", 35, "115", "M"),
    947: ("Most Stones Removed", "M", "Union Find", "Row/col union", 25, "547", "H"),
    948: ("Bag of Tokens", "M", "Two Pointers", "Greedy tokens", 25, "881", "M"),
    973: ("K Closest Points to Origin", "M", "Heap", "k nearest", 20, "215", "VH"),
    974: ("Subarray Sums Divisible by K", "M", "HashMap", "Mod prefix", 25, "560", "H"),
    977: ("Squares of Sorted Array", "E", "Two Pointers", "Merge ends", 12, "88", "M"),
    980: ("Unique Paths III", "H", "Backtracking", "Visit all cells", 35, "62", "H"),
    981: ("Time Based Key-Value Store", "M", "Binary Search", "Timestamp lookup", 25, "362", "H"),
    983: ("Minimum Cost For Tickets", "M", "DP", "Travel planning", 30, "322", "H"),
    986: ("Interval List Intersections", "M", "Two Pointers", "Merge intervals", 25, "56", "H"),
    987: ("Vertical Order Traversal", "H", "Tree BFS", "Column sort", 35, "314", "H"),
    990: ("Satisfiability Equality Equations", "M", "Union Find", "Var union", 25, "684", "H"),
    992: ("Subarrays K Different Integers", "H", "Sliding Window", "At-most K trick", 35, "904", "H"),
    994: ("Rotting Oranges", "M", "Graph BFS", "Multi-source", 25, "286", "VH"),
    996: ("Number of Squareful Arrays", "H", "Backtracking", "Perfect square adj", 40, "46", "M"),
    997: ("Find Town Judge", "E", "Graph", "In-degree n-1", 12, "207", "M"),
    1004: ("Max Consecutive Ones III", "M", "Sliding Window", "Flip K zeros", 25, "485", "VH"),
    1011: ("Capacity Ship Packages", "M", "Binary Search", "Feasibility", 30, "875", "H"),
    1014: ("Best Sightseeing Pair", "M", "DP", "Max score pair", 20, "121", "H"),
    1024: ("Video Stitching", "M", "Greedy", "Min clips cover", 30, "45", "H"),
    1035: ("Uncrossed Lines", "M", "DP", "LCS variant", 25, "1143", "H"),
    1048: ("Longest String Chain", "M", "DP/Sort", "Word chain", 25, "139", "H"),
    1052: ("Grumpy Bookstore Owner", "M", "Sliding Window", "Fixed window tech", 25, "1004", "H"),
    1091: ("Shortest Path Binary Matrix", "M", "Graph BFS", "8-direction", 25, "200", "H"),
    1094: ("Car Pooling", "M", "Prefix Diff", "Capacity timeline", 25, "253", "H"),
    1109: ("Corporate Flight Bookings", "M", "Prefix Diff", "Range update", 20, "370", "M"),
    1130: ("Min Valid Parenthesis Remove", "M", "Stack", "Min removals", 25, "301", "H"),
    1135: ("Connecting Cities Min Cost", "M", "MST", "Kruskal/Prim", 30, "1584", "H"),
    1143: ("Longest Common Subsequence", "M", "DP", "2D string DP", 25, "72", "VH"),
    1155: ("Number of Dice Rolls Target", "M", "DP", "Combination count", 25, "518", "M"),
    1166: ("Design File System", "M", "Trie", "Path trie", 30, "588", "M"),
    1197: ("Min Knight Moves", "M", "Graph BFS", "Chess BFS", 25, "1091", "H"),
    1203: ("Sort Items Groups", "H", "Topological Sort", "Grouped topo", 40, "269", "M"),
    1249: ("Min Remove Valid Parentheses", "M", "Stack", "Balance remove", 25, "301", "H"),
    1268: ("Search Suggestions System", "M", "Trie", "Autocomplete", 25, "208", "H"),
    1283: ("Find Smallest Divisor", "M", "Binary Search", "Threshold sum", 25, "875", "M"),
    1296: ("Divide Array Sets", "M", "HashMap", "K consecutive", 25, "846", "M"),
    1319: ("Network Connected", "M", "Union Find", "Extra cables", 25, "547", "M"),
    1334: ("Find City With Threshold", "M", "Floyd-Warshall", "All pairs", 35, "743", "M"),
    1343: ("Subarray Size K Avg", "M", "Sliding Window", "Fixed window avg", 20, "209", "M"),
    1352: ("Last K Product", "M", "Design", "Product stream", 25, "295", "M"),
    1383: ("Max Performance Team", "H", "Greedy/Sort", "Speed * efficiency", 35, "502", "H"),
    1424: ("Diagonal Traverse II", "M", "Heap", "Diagonal order", 25, "498", "M"),
    1438: ("Longest K Absolute Diff", "M", "Sliding Window", "Sorted window", 30, "992", "H"),
    1456: ("Max Vowels Substring", "M", "Sliding Window", "Fixed window", 20, "438", "M"),
    1466: ("Reorder Routes", "M", "Graph DFS", "Edge reorient", 25, "207", "H"),
    1481: ("Least Unique Integers", "M", "Heap/HashMap", "K unique remove", 25, "347", "M"),
    1497: ("Subarray Sum Divisible", "M", "HashMap", "Mod count", 25, "974", "M"),
    1514: ("Path Max Probability", "M", "Dijkstra", "Max prob path", 30, "743", "M"),
    1524: ("Odd Even Linked List", "M", "Linked List", "Reorder", 20, "328", "M"),
    1539: ("Kth Missing Positive", "M", "Binary Search", "Missing count", 20, "41", "H"),
    1584: ("Min Cost Connect Points", "M", "MST", "Manhattan MST", 30, "743", "H"),
    1631: ("Path Minimum Effort", "M", "Dijkstra", "Min max edge", 30, "778", "H"),
    1642: ("Furthest Building Can Reach", "M", "Heap/Greedy", "Ladders/bricks", 30, "871", "H"),
    1658: ("Min Ops Reduce X Zero", "M", "Sliding Window", "Two ends shrink", 30, "209", "H"),
    1670: ("Design Front Middle Back Queue", "M", "Design", "Dual deque", 30, "622", "M"),
    1695: ("Max Erasure Value", "M", "Sliding Window", "Unique subarray", 25, "3", "H"),
    1762: ("Buildings Ocean View", "M", "Monotonic Stack", "Right view", 25, "739", "H"),
    1834: ("Single Thread CPU", "M", "Heap", "Task scheduling", 30, "621", "H"),
    1851: ("Min Interval Include Query", "H", "Binary Search", "Interval query", 40, "56", "H"),
    1899: ("Merge Triplets Form Target", "M", "Greedy", "Triplet merge", 25, "39", "H"),
    1926: ("Nearest Exit Maze", "M", "Graph BFS", "Grid BFS", 25, "994", "H"),
    1980: ("Find Unique Binary String", "M", "Backtracking", "Cantor diagonal", 25, "78", "M"),
    1991: ("Find Middle Index", "E", "Prefix Sum", "Balance index", 12, "724", "M"),
    2009: ("Min Ops Make Continuous", "M", "Sliding Window", "Sorted window", 25, "128", "H"),
    2131: ("Longest Palindrome Two Letters", "M", "HashMap", "Pair count", 20, "409", "M"),
    2157: ("Groups Strings Connected", "H", "Union Find", "One char diff", 35, "839", "M"),
    2211: ("Count Collisions Road", "M", "Stack", "Direction sim", 25, "735", "M"),
    2279: ("Max Bags Full Capacity", "M", "Greedy", "Sort fill", 20, "881", "M"),
    2300: ("Successful Pairs Spells Potions", "M", "Binary Search", "Pair count", 25, "875", "H"),
    2337: ("Move Pieces Obtain String", "M", "Two Pointers", "L/R move sim", 25, "777", "M"),
    2353: ("Shared Flavor Pizza", "M", "HashMap", "Set intersection", 20, "349", "M"),
}


PATTERN_TO_TOPIC = {
    "HashMap": "HashMap", "HashSet": "HashMap", "Prefix/Suffix": "Arrays",
    "Prefix sum": "Arrays", "Prefix + HashMap": "HashMap", "Prefix + HashMap": "HashMap",
    "Kadane": "Arrays", "Arrays": "Arrays", "Array": "Arrays", "Matrix": "Arrays",
    "String": "Strings", "Expand center": "Strings", "Trie / scan": "Trie",
    "Sliding Window": "Sliding Window", "Two Pointers": "Two Pointers",
    "Binary Search": "Binary Search", "Stack": "Stack", "Monotonic Stack": "Stack",
    "Monotonic Deque": "Stack", "Queue": "Queue", "Linked List": "Linked List",
    "Tree": "Trees", "Tree DFS": "Trees", "Tree BFS": "Trees", "BST": "BST",
    "BFS": "Trees", "Heap": "Heap", "Heap / divide": "Heap", "Trie": "Trie",
    "Graph DFS/BFS": "Graph", "Graph BFS/DFS": "Graph", "Graph DFS": "Graph",
    "Graph BFS": "Graph", "Graph": "Graph", "Topological Sort": "Topological Sort",
    "Union Find": "Union Find", "Backtracking": "Backtracking", "Greedy": "Greedy",
    "Greedy / heap": "Greedy", "Sorting": "Sorting", "Intervals": "Intervals",
    "DP": "Dynamic Programming", "DP / greedy subarray": "Dynamic Programming",
    "Dijkstra": "Advanced Graph", "Bellman-Ford": "Advanced Graph",
    "BFS + backtrack": "Advanced Graph", "Eulerian path": "Advanced Graph",
    "HashMap + DLL": "Hard Interview Problems", "Design": "Hard Interview Problems",
    "Bit": "Arrays", "Math": "Arrays", "Fast/slow": "Linked List",
    "Divide Conquer": "Dynamic Programming", "Segment Tree": "Hard Interview Problems",
    "Reservoir": "Hard Interview Problems", "Geometry": "Hard Interview Problems",
    "State machine": "Dynamic Programming", "Game theory": "Dynamic Programming",
    "Mini interpreter": "Hard Interview Problems", "Custom sort": "Sorting",
    "Dutch Flag": "Sorting", "Merge/Quick sort": "Sorting", "Merge/Quick": "Sorting",
    "MST": "Advanced Graph", "MST / Kruskal": "Advanced Graph", "Floyd-Warshall": "Advanced Graph",
    "Sweep line": "Hard Interview Problems", "Line equation": "Hard Interview Problems",
    "Bitmask": "Advanced Graph", "BFS+Bitmask": "Advanced Graph",
    "Graph/Euler": "Advanced Graph", "Graph/UnionFind": "Graph",
    "Graph DFS+Graph": "Graph", "Graph DFS+Memo": "Dynamic Programming",
    "Graph DFS+BFS": "Graph", "Priority Queue": "Heap", "Heap/Two Ptr": "Heap",
    "TreeMap": "Hard Interview Problems", "TreeSet/DP": "Hard Interview Problems",
    "Bucket/SortedSet": "HashMap", "Inorder simulation": "BST",
    "Controlled inorder": "BST", "Codec design": "Hard Interview Problems",
    "RPN eval": "Stack", "Expression parsing": "Stack", "Path normalization": "Stack",
    "Bijection mapping": "HashMap", "Bijection check": "HashMap",
    "Freq sort": "HashMap", "Frequency count": "HashMap",
    "Quickselect / heap": "Heap", "Heap/Binary Search": "Binary Search",
    "Heap/BST": "Heap", "Heap/Greedy": "Greedy", "Greedy/Heap": "Greedy",
    "Greedy/HashMap": "Greedy", "Greedy/Stack": "Stack", "Greedy shrink": "Two Pointers",
    "Greedy pairing": "Two Pointers", "Greedy/Intervals": "Intervals",
    "Interval scheduling": "Intervals", "Interval merge": "Intervals",
    "Interval DP": "Dynamic Programming", "2D histogram reduce": "Stack",
    "Bar expansion": "Stack", "Next greater element": "Stack",
    "NGE template": "Stack", "Circular NGE": "Stack",
    "Linear choice DP": "Dynamic Programming", "Fibonacci pattern": "Dynamic Programming",
    "Levenshtein distance": "Dynamic Programming", "2D string DP": "Dynamic Programming",
    "Unbounded knapsack": "Dynamic Programming", "0/1 knapsack": "Dynamic Programming",
    "LIS O(n log n)": "Dynamic Programming", "Partition merge": "Binary Search",
    "Answer space search": "Binary Search", "Feasibility check": "Binary Search",
    "Boundary search": "Binary Search", "Lower bound": "Binary Search",
    "Classic template": "Binary Search", "Pivot detection": "Binary Search",
    "Min in rotated": "Binary Search", "Flattened search": "Binary Search",
    "Peak finding": "Binary Search", "Integer sqrt": "Binary Search",
    "First true predicate": "Binary Search", "Sorted pair search": "Two Pointers",
    "Left/right max": "Two Pointers", "In-place swap": "Two Pointers",
    "In-place overwrite": "Two Pointers", "Partition array": "Two Pointers",
    "Alphanumeric filter": "Two Pointers", "One deletion allowed": "Two Pointers",
    "Merge from ends": "Two Pointers", "Even-first partition": "Two Pointers",
    "Fixed-size average": "Queue", "Sliding window queue": "Queue",
    "Stack from queues": "Queue", "Queue from stacks": "Stack",
    "Ring buffer": "Queue", "Double-ended ring": "Queue",
    "Iterative reverse": "Linked List", "Dummy head merge": "Linked List",
    "Cycle detection": "Linked List", "Cycle entry point": "Linked List",
    "HashMap clone": "Linked List", "Two-pointer gap": "Linked List",
    "k-group reverse": "Linked List", "Partial reverse": "Linked List",
    "Pointer switch trick": "Linked List", "Midpoint detection": "Linked List",
    "Find mid + reverse": "Linked List", "Merge sort LL": "Linked List",
    "Carry propagation": "Linked List", "Mirror swap": "Trees",
    "Recursive depth": "Trees", "Level-by-level": "Trees", "Range validation": "BST",
    "Compare with root": "BST", "LCA postorder": "Trees", "Global max path": "Trees",
    "Height computation": "Trees", "Inorder traversal": "BST",
    "Connected components": "Graph", "Graph deep copy": "Graph",
    "Cycle detection graph": "Graph", "Order construction": "Topological Sort",
    "Safe node detection": "Topological Sort", "Shortest transform": "Advanced Graph",
    "All shortest paths": "Advanced Graph", "Min-heap distances": "Advanced Graph",
    "K-stop shortest path": "Advanced Graph", "Subset enumeration": "Backtracking",
    "Unbounded combinations": "Backtracking", "Permutation generation": "Backtracking",
    "Grid path search": "Backtracking", "Valid paren generation": "Backtracking",
    "Constraint placement": "Backtracking", "Constraint propagation": "Backtracking",
    "Reachability": "Greedy", "Min jumps": "Greedy", "Interval scheduling greedy": "Greedy",
    "Min rooms needed": "Greedy", "Cooldown scheduling": "Greedy",
    "Multi-source BFS": "Graph", "Grid flood fill": "Graph",
    "Shortest path time": "Advanced Graph", "Capital maximization": "Heap",
    "Two-heap median": "Heap", "k-way merge": "Heap",
    "Wildcard search": "Trie", "Board word search": "Trie",
    "Prefix tree ops": "Trie", "Autocomplete": "Trie",
    "Ordered eviction": "Hard Interview Problems", "Freq eviction": "Hard Interview Problems",
    "Expression eval": "Stack", "Multi-word window": "Sliding Window",
    "Cover all chars": "Sliding Window", "Anagram window": "Sliding Window",
    "Distinct limit": "Sliding Window", "K distinct limit": "Sliding Window",
    "At-most K trick": "Sliding Window", "Flip at most K": "Sliding Window",
    "Product window": "Sliding Window", "Fixed window freq": "Sliding Window",
    "Window max": "Sliding Window", "Running sum count": "HashMap",
    "Sequence start detection": "HashMap", "Sorted key grouping": "HashMap",
    "Complement lookup": "HashMap", "Set membership": "HashMap",
    "Bracket matching": "Stack", "Valid paren length": "Stack",
    "Auxiliary min stack": "Stack", "Matching pairs": "Stack",
    "Three-way partition": "Sorting", "Interval merge sort": "Sorting",
    "Merge on insert": "Intervals", "Merge two lists intervals": "Intervals",
    "Arrow scheduling": "Greedy", "Last occurrence map": "Greedy",
    "Max reach tracking": "Greedy", "Circuit feasibility": "Greedy",
    "Segmentation DP": "Dynamic Programming", "Min/max product track": "Dynamic Programming",
    "Palindrome expansion": "Strings", "Count palindromes": "Strings",
    "Pattern matching": "Dynamic Programming", "Subseq palindrome": "Dynamic Programming",
    "Min cuts": "Dynamic Programming", "Interval DP burst": "Dynamic Programming",
    "Reverse min health": "Dynamic Programming", "Grid paths mod": "Dynamic Programming",
    "State compression": "Advanced Graph", "Board BFS": "Advanced Graph",
    "Manhattan MST": "Advanced Graph", "Min max elevation": "Advanced Graph",
    "Max prob path": "Advanced Graph", "All pairs shortest": "Advanced Graph",
}


def get_daily_count(day):
    """Day 1 = 15, Day 31 = 35, Days 32-39 = 36-38."""
    if day <= 31:
        return round(15 + (35 - 15) * (day - 1) / 30)
    return min(38, 35 + (day - 31))


def build_assignments(full_db):
    easy = [n for n, v in full_db.items() if v[1] == "E"]
    medium = [n for n, v in full_db.items() if v[1] == "M"]
    hard = [n for n, v in full_db.items() if v[1] == "H"]

    # Sort by VH/H frequency within each tier
    freq_order = {"VH": 0, "H": 1, "M": 2, "L": 3}
    easy.sort(key=lambda n: freq_order.get(full_db[n][6], 9))
    medium.sort(key=lambda n: freq_order.get(full_db[n][6], 9))
    hard.sort(key=lambda n: freq_order.get(full_db[n][6], 9))

    # Topic-ordered pools
    topic_pools = {t: {"E": [], "M": [], "H": []} for t in TOPIC_ORDER}
    for num, val in full_db.items():
        diff = val[1]
        pattern = val[2]
        topic = PATTERN_TO_TOPIC.get(pattern, "Arrays")
        if topic not in topic_pools:
            topic = "Hard Interview Problems"
        if diff in topic_pools[topic]:
            topic_pools[topic][diff].append(num)

    assignments = {}
    used_recently = []
    ei = mi = hi = 0
    topic_idx = 0

    def pick_from_pool(pool, idx_attr):
        nonlocal ei, mi, hi
        pools = [easy, medium, hard]
        idxs = [ei, mi, hi]
        for pi, pool_list in enumerate(pools):
            if pool == "E" and ei < len(easy):
                n = easy[ei]; ei += 1; return n
            if pool == "M" and mi < len(medium):
                n = medium[mi]; mi += 1; return n
            if pool == "H" and hi < len(hard):
                n = hard[hi]; hi += 1; return n
        return None

    def pick_topic_problem(diff):
        nonlocal topic_idx
        for _ in range(len(TOPIC_ORDER)):
            topic = TOPIC_ORDER[topic_idx % len(TOPIC_ORDER)]
            topic_idx += 1
            pool = topic_pools[topic][diff]
            while pool:
                num = pool.pop(0)
                if num not in used_recently[-20:]:
                    return num
        return None

    for day in range(1, 40):
        count = get_daily_count(day)
        easy_n = max(1, round(count * 0.13))
        hard_n = max(1, round(count * 0.37))
        med_n = count - easy_n - hard_n
        if med_n < 1:
            med_n = 1
            hard_n = count - easy_n - med_n
        day_probs = []

        for _ in range(easy_n):
            n = pick_topic_problem("E") or pick_from_pool("E", None)
            if n is None:
                n = easy[ei % len(easy)]; ei += 1
            day_probs.append(n)
            used_recently.append(n)

        for _ in range(med_n):
            n = pick_topic_problem("M") or pick_from_pool("M", None)
            if n is None:
                n = medium[mi % len(medium)]; mi += 1
            day_probs.append(n)
            used_recently.append(n)

        for _ in range(hard_n):
            n = pick_topic_problem("H") or pick_from_pool("H", None)
            if n is None:
                n = hard[hi % len(hard)]; hi += 1
            day_probs.append(n)
            used_recently.append(n)

        assignments[day] = day_probs

    return assignments


def main():
    full_db = {**PROBLEM_DB, **EXTRA_PROBLEMS}
    assignments = build_assignments(full_db)

    easy_c = sum(1 for v in full_db.values() if v[1] == "E")
    med_c = sum(1 for v in full_db.values() if v[1] == "M")
    hard_c = sum(1 for v in full_db.values() if v[1] == "H")
    total = sum(len(v) for v in assignments.values())

    print(f"Pool: {len(full_db)} problems (E={easy_c}, M={med_c}, H={hard_c})")
    print(f"Total assignments: {total}")
    for d in [1, 7, 15, 31, 39]:
        probs = assignments[d]
        diffs = [full_db[p][1] for p in probs]
        e = diffs.count("E"); m = diffs.count("M"); h = diffs.count("H")
        print(f"Day {d}: {len(probs)} qns (E={e} {e/len(probs)*100:.0f}%, M={m}, H={h})")

    # Write updated leetcode_roadmap.py
    out_path = os.path.join(os.path.dirname(__file__), "..", "data", "leetcode_roadmap.py")
    with open(out_path, "r") as f:
        content = f.read()

    # Keep everything before DAILY_ASSIGNMENTS
    idx = content.index("DAILY_ASSIGNMENTS = {")
    header = content[:idx]

    lines = ["DAILY_ASSIGNMENTS = {"]
    for day in range(1, 40):
        probs = assignments[day]
        lines.append(f"    {day}: {probs},")
    lines.append("}")
    lines.append("")

    # Keep from TOPIC_ORDER onward
    rest_idx = content.index("TOPIC_ORDER = [")
    rest = content[rest_idx:]

    # Merge extra problems into PROBLEM_DB in header
    if "EXTRA merged" not in header:
        # Find end of PROBLEM_DB
        pdb_end = header.rindex("}")
        extra_lines = []
        for num in sorted(set(EXTRA_PROBLEMS.keys()) - set(PROBLEM_DB.keys())):
            v = EXTRA_PROBLEMS[num]
            extra_lines.append(
                f'    {num}: ("{v[0]}", "{v[1]}", "{v[2]}", "{v[3]}", {v[4]}, "{v[5]}", "{v[6]}"),'
            )
        header = header[:pdb_end] + ",\n" + "\n".join(extra_lines) + "\n" + header[pdb_end:]

    new_content = header + "\n".join(lines) + "\n" + rest
    with open(out_path, "w") as f:
        f.write(new_content)
    print(f"Written {out_path}")


if __name__ == "__main__":
    main()
