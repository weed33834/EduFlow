"""
Knowledge search tool - 本地知识库检索与前置知识查找

提供两个核心能力：
1. ``search_knowledge``：基于关键词匹配的本地知识库搜索，覆盖 Python、JavaScript、
   数据结构、算法、数据库、操作系统、网络等常见编程/学习主题。
2. ``get_prerequisites``：基于主题依赖关系图查找指定主题的前置知识。

说明：
- 纯本地实现，不依赖外部服务或向量数据库，保证在无 LLM / 无网络时也可用。
- 函数保持 ``async`` 以兼容现有调用约定（``await search_knowledge(...)``）。
- 当无任何匹配时，``search_knowledge`` 返回空列表；未知主题的 ``get_prerequisites``
  同样返回空列表。
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# 本地知识库
# 每个条目字段：
#   id        : 唯一编号
#   topic     : 所属主题分类（用于按主题过滤/加权）
#   title     : 知识点标题（同时作为依赖图中的主题标识）
#   keywords  : 匹配关键词列表
#   summary   : 一句话摘要
#   content   : 详细知识点说明
# 覆盖：Python / JavaScript / 数据结构 / 算法 / 数据库 / 操作系统 / 网络
# ---------------------------------------------------------------------------

KNOWLEDGE_BASE: list[dict] = [
    # ---- Python ----
    {
        "id": 1,
        "topic": "Python",
        "title": "Python变量与数据类型",
        "keywords": ["变量", "数据类型", "python", "整数", "浮点数", "字符串", "布尔",
                     "int", "float", "str", "bool", "类型转换", "type"],
        "summary": "Python 中变量的定义与基本数据类型（int/float/str/bool）及类型转换。",
        "content": (
            "Python 是动态类型语言，变量无需声明类型，赋值即定义：x = 10。"
            "基本数据类型包括：int（整数）、float（浮点数）、str（字符串）、bool（布尔值）。"
            "使用 type(x) 可查看变量类型，使用 int()、float()、str()、bool() 可进行类型转换。"
            "变量名区分大小写，不能以数字开头，不能使用关键字。"
        ),
    },
    {
        "id": 2,
        "topic": "Python",
        "title": "Python函数",
        "keywords": ["函数", "python", "def", "参数", "返回值", "return", "默认参数",
                     "可变参数", "args", "kwargs", "作用域"],
        "summary": "使用 def 定义函数，支持默认参数、可变参数 *args/**kwargs 与返回值。",
        "content": (
            "使用 def 关键字定义函数：def add(a, b): return a + b。"
            "支持默认参数（def f(a, b=1)）、可变位置参数 *args 与可变关键字参数 **kwargs。"
            "函数通过 return 返回结果，无 return 时返回 None。"
            "参数传递是「赋值传递」：不可变对象在函数内修改不影响外部，可变对象（如列表）会被影响。"
        ),
    },
    {
        "id": 3,
        "topic": "Python",
        "title": "Python列表与元组",
        "keywords": ["列表", "元组", "list", "tuple", "python", "序列", "切片", "可变",
                     "不可变", "索引"],
        "summary": "list 是可变序列，tuple 是不可变序列，均支持索引与切片操作。",
        "content": (
            "列表 list 是有序可变序列：[1, 2, 3]，支持 append/pop/sort 等原地修改方法。"
            "元组 tuple 是有序不可变序列：(1, 2, 3)，创建后不能修改，常用于固定数据与字典键。"
            "两者均支持索引访问（从 0 开始）与切片 [start:stop:step]。"
            "注意：b = a 只是引用同一对象，修改 b 会影响 a；需用 a.copy() 或 a[:] 创建副本。"
        ),
    },
    {
        "id": 4,
        "topic": "Python",
        "title": "Python字典与集合",
        "keywords": ["字典", "集合", "dict", "set", "python", "哈希", "键值对", "映射",
                     "去重", "不可变类型"],
        "summary": "dict 存储键值对映射，set 存储唯一元素集合，键/元素须为不可变（可哈希）类型。",
        "content": (
            "字典 dict 是键值对映射：{'name': 'Tom', 'age': 18}，通过键 O(1) 访问值。"
            "集合 set 存储唯一元素：{1, 2, 3}，支持交并差运算，常用于去重。"
            "字典的键与集合的元素必须是可哈希（不可变）类型，如 str/int/tuple；"
            "list/dict/set 不可哈希，不能作为键。删除用 del d[key] 或 d.pop(key)。"
        ),
    },
    {
        "id": 5,
        "topic": "Python",
        "title": "Python面向对象编程",
        "keywords": ["面向对象", "类", "对象", "python", "class", "继承", "封装", "多态",
                     "方法", "属性", "self", "init"],
        "summary": "使用 class 定义类，通过继承实现代码复用，支持封装、继承、多态三大特性。",
        "content": (
            "使用 class 定义类：class Dog:，__init__ 是构造方法，self 指向实例本身。"
            "类属性属于类，实例属性属于对象。通过 class Sub(Parent) 实现继承，"
            "子类可重写（override）父类方法，并用 super() 调用父类方法实现多态。"
            "封装通过命名约定实现：_name 受保护、__name 触发名称重整近似私有。"
        ),
    },
    {
        "id": 6,
        "topic": "Python",
        "title": "Python装饰器",
        "keywords": ["装饰器", "decorator", "python", "闭包", "高阶函数", "函数包装",
                     "语法糖", "wraps"],
        "summary": "装饰器是接收函数并返回新函数的高阶函数，用于在不修改原函数的前提下增强功能。",
        "content": (
            "装饰器本质是「接收函数、返回函数」的高阶函数，用 @decorator 语法糖应用。"
            "常见用途：日志、计时、权限校验、缓存（@functools.cache）。"
            "示例：def log(func): def wrapper(*a, **kw): print('call'); return func(*a, **kw); return wrapper。"
            "建议用 functools.wraps(func) 保留原函数元信息；带参装饰器需再多嵌套一层。"
        ),
    },
    {
        "id": 7,
        "topic": "Python",
        "title": "Python异常处理",
        "keywords": ["异常", "异常处理", "try", "except", "finally", "raise", "python",
                     "错误处理", "异常捕获"],
        "summary": "用 try/except/finally 捕获和处理运行时异常，raise 主动抛出异常。",
        "content": (
            "try 块放置可能出错的代码，except 捕获指定异常类型，finally 无论是否异常都执行。"
            "可配合 else（无异常时执行）。捕获应具体：except ValueError 而非裸 except。"
            "用 raise 主动抛出异常：raise ValueError('invalid')。"
            "可自定义异常类（继承 Exception）。合理使用异常处理可提升程序健壮性。"
        ),
    },
    {
        "id": 8,
        "topic": "Python",
        "title": "Python迭代器与生成器",
        "keywords": ["迭代器", "生成器", "iterator", "generator", "yield", "python",
                     "惰性求值", "可迭代", "iter", "next"],
        "summary": "迭代器实现 __iter__/__next__ 协议；生成器用 yield 惰性产出序列，节省内存。",
        "content": (
            "迭代器是实现 __iter__() 与 __next__() 的对象，StopIteration 表示迭代结束。"
            "生成器是用 yield 的函数，每次调用 next() 执行到 yield 暂停并返回值，"
            "实现惰性求值，适合处理大数据流而不一次性载入内存。"
            "生成器表达式 (x*x for x in range(n)) 是简洁的生成器写法。"
        ),
    },
    # ---- JavaScript ----
    {
        "id": 9,
        "topic": "JavaScript",
        "title": "JavaScript基础语法",
        "keywords": ["javascript", "js", "变量", "let", "const", "var", "数据类型",
                     "语法", "基础", "es6"],
        "summary": "JS 变量声明 let/const/var、动态类型与基本数据类型（number/string/boolean 等）。",
        "content": (
            "JavaScript 是动态弱类型语言。变量声明：let（块作用域可变）、const（块作用域常量）、"
            "var（函数作用域，已不推荐）。基本类型：number、string、boolean、null、undefined、"
            "symbol、bigint；引用类型：object。使用 typeof 判断类型。"
            "=== 严格相等（不转换类型），== 宽松相等（会转换类型），推荐始终用 ===。"
        ),
    },
    {
        "id": 10,
        "topic": "JavaScript",
        "title": "JavaScript函数与闭包",
        "keywords": ["函数", "闭包", "javascript", "function", "箭头函数", "作用域",
                     "高阶函数", "回调", "lexical scope"],
        "summary": "函数是一等公民，闭包让内层函数可访问外层作用域变量。",
        "content": (
            "JS 函数是一等公民，可作为参数传递和返回。声明方式：function f(){} 与箭头函数 (x)=>x。"
            "闭包指函数能「记住」并访问其定义时的词法作用域，即使在该作用域外执行。"
            "常见用途：数据私有化、回调、柯里化、模块模式。注意闭包持有外层变量引用，"
            "若循环中创建闭包引用循环变量需用 let 或 IIFE 隔离。"
        ),
    },
    {
        "id": 11,
        "topic": "JavaScript",
        "title": "JavaScript异步编程",
        "keywords": ["异步", "promise", "async", "await", "javascript", "回调", "callback",
                     "事件循环", "then", "并发"],
        "summary": "用 Promise 与 async/await 处理异步操作，避免回调地狱。",
        "content": (
            "JS 单线程，基于事件循环处理异步。Promise 表示异步操作的最终结果，"
            "有 pending/fulfilled/rejected 三态，用 .then/.catch 链式处理。"
            "async 函数返回 Promise，await 可「暂停」等待 Promise 完成，使异步代码像同步一样书写。"
            "并发可用 Promise.all（全部完成）、Promise.race（首个完成）、Promise.allSettled（全部落定）。"
        ),
    },
    {
        "id": 12,
        "topic": "JavaScript",
        "title": "JavaScript DOM操作",
        "keywords": ["dom", "javascript", "文档对象模型", "节点", "事件", "event",
                     "查询", "操作", "浏览器"],
        "summary": "通过 DOM API 查询和操作 HTML 元素，并绑定事件实现交互。",
        "content": (
            "DOM（文档对象模型）将 HTML 表示为树形节点。常用查询："
            "getElementById、querySelector、querySelectorAll。"
            "操作：修改 textContent/innerHTML、setAttribute、classList.add/remove、"
            "appendChild/removeChild。事件绑定：addEventListener('click', handler)。"
            "事件对象 e 包含 target、preventDefault()、stopPropagation() 等。"
        ),
    },
    # ---- 数据结构 ----
    {
        "id": 13,
        "topic": "数据结构",
        "title": "数组与链表",
        "keywords": ["数组", "链表", "array", "linked list", "线性表", "顺序存储",
                     "链式存储", "指针", "节点"],
        "summary": "数组是连续内存的顺序存储，链表是通过指针连接节点的链式存储。",
        "content": (
            "数组在内存中连续存储，支持 O(1) 随机访问，但插入/删除需移动元素为 O(n)。"
            "链表通过指针将节点串联，插入/删除（已知位置）为 O(1)，但访问第 i 个元素为 O(n)。"
            "常见变体：单链表、双链表、循环链表。选择依据：频繁随机访问用数组，"
            "频繁插入删除用链表。"
        ),
    },
    {
        "id": 14,
        "topic": "数据结构",
        "title": "栈与队列",
        "keywords": ["栈", "队列", "stack", "queue", "LIFO", "FIFO", "后进先出",
                     "先进先出", "push", "pop"],
        "summary": "栈是后进先出（LIFO）结构，队列是先进先出（FIFO）结构。",
        "content": (
            "栈是后进先出（LIFO）线性结构，主要操作 push（入栈）与 pop（出栈），均为 O(1)。"
            "应用：函数调用栈、括号匹配、表达式求值、回溯、DFS。"
            "队列是先进先出（FIFO）结构，主要操作 enqueue/dequeue，应用：BFS、任务调度、缓冲区。"
            "变体：双端队列（deque）两端均可进出，优先队列按优先级出队（常用堆实现）。"
        ),
    },
    {
        "id": 15,
        "topic": "数据结构",
        "title": "树与二叉树",
        "keywords": ["树", "二叉树", "tree", "binary tree", "遍历", "前序", "中序",
                     "后序", "BST", "二叉搜索树", "递归"],
        "summary": "树是层次结构，二叉树每个节点最多两个子节点；遍历分前/中/后序与层序。",
        "content": (
            "树是层次化的非线性结构，根、子树、叶子等概念。二叉树每个节点最多两个子节点。"
            "遍历方式：前序（根-左-右）、中序（左-根-右）、后序（左-右-根）、层序（BFS）。"
            "二叉搜索树（BST）：左子树值 < 根 < 右子树值，中序遍历得有序序列，查找/插入/删除平均 O(log n)。"
            "平衡树（AVL、红黑树）保证最坏情况性能。"
        ),
    },
    {
        "id": 16,
        "topic": "数据结构",
        "title": "哈希表",
        "keywords": ["哈希表", "散列表", "hash table", "哈希函数", "冲突", "拉链法",
                     "开放寻址", "映射", "O(1)"],
        "summary": "哈希表通过哈希函数将键映射到桶，实现平均 O(1) 的增删改查。",
        "content": (
            "哈希表（散列表）通过哈希函数将键映射到数组下标，实现平均 O(1) 的查找/插入/删除。"
            "冲突处理：拉链法（每个桶存链表/链）、开放寻址法（线性探测等）。"
            "负载因子 = 元素数/桶数，过大需扩容 rehash。"
            "Python dict、Java HashMap、JS Map 均基于哈希表。键须可哈希。"
        ),
    },
    # ---- 算法 ----
    {
        "id": 17,
        "topic": "算法",
        "title": "排序算法",
        "keywords": ["排序", "sort", "冒泡", "选择", "插入", "快排", "归并排序",
                     "时间复杂度", "稳定性", "quicksort", "mergesort"],
        "summary": "常见排序：冒泡/选择/插入 O(n²)，快排/归并 O(n log n)，需理解稳定性与复杂度。",
        "content": (
            "简单排序：冒泡、选择、插入，平均 O(n²)，适合小规模或基本有序数据。"
            "高效排序：快速排序平均 O(n log n)、最坏 O(n²)，原地但不稳定；"
            "归并排序稳定 O(n log n)，需 O(n) 额外空间；堆排序原地 O(n log n) 不稳定。"
            "选择依据：稳定性要求、是否原地、数据规模与特征。库函数多用 Timsort（归并+插入）。"
        ),
    },
    {
        "id": 18,
        "topic": "算法",
        "title": "递归",
        "keywords": ["递归", "recursion", "基线条件", "终止条件", "调用栈", "分治",
                     "自调用", "栈溢出"],
        "summary": "递归是函数自调用，须有终止条件（基线条件），将问题分解为更小的同类子问题。",
        "content": (
            "递归是函数直接或间接调用自身。两个要素：基线条件（终止，否则栈溢出）与递归条件（向基线收敛）。"
            "经典应用：阶乘、斐波那契、树遍历、分治（归并/快排）、回溯。"
            "递归优点是代码简洁贴合问题结构，缺点是有调用栈开销、可能重复计算。"
            "可用记忆化/动态规划优化重叠子问题，或改写为迭代避免栈溢出。"
        ),
    },
    {
        "id": 19,
        "topic": "算法",
        "title": "动态规划",
        "keywords": ["动态规划", "dp", "最优子结构", "重叠子问题", "状态转移",
                     "记忆化", "背包问题", "最优解"],
        "summary": "动态规划通过状态转移方程求解具有最优子结构与重叠子问题的最优化问题。",
        "content": (
            "动态规划适用于具有「最优子结构」和「重叠子问题」的问题，避免递归的重复计算。"
            "核心是定义状态与状态转移方程。实现方式：自顶向下记忆化递归、自底向上迭代填表。"
            "经典问题：斐波那契、背包、最长公共子序列（LCS）、最长递增子序列（LIS）、编辑距离。"
            "关键是识别状态定义与转移方程，常需画表格辅助推导。"
        ),
    },
    {
        "id": 20,
        "topic": "算法",
        "title": "二分查找",
        "keywords": ["二分查找", "二分搜索", "binary search", "折半", "有序数组",
                     "log n", "边界", "lower bound"],
        "summary": "在有序序列中每次折半缩小范围，时间复杂度 O(log n)。",
        "content": (
            "二分查找要求序列有序，每次比较中间元素将搜索范围减半，时间 O(log n)。"
            "循环写法：维护 left/right 指针，mid = (left+right)//2，根据比较移动边界。"
            "注意边界：左闭右闭 [l, r] 还是左闭右开 [l, r) 决定循环与更新方式。"
            "变体：查找第一个/最后一个满足条件的位置（lower_bound/upper_bound）。"
            "也可用于单调性答案的二分（二分答案）。"
        ),
    },
    # ---- 数据库 ----
    {
        "id": 21,
        "topic": "数据库",
        "title": "SQL基础",
        "keywords": ["sql", "数据库", "查询", "select", "insert", "update", "delete",
                     "join", "where", "关系型", "表"],
        "summary": "SQL 用 SELECT/INSERT/UPDATE/DELETE 操作关系型数据，JOIN 连接多表查询。",
        "content": (
            "SQL 是关系型数据库的标准查询语言。基本 CRUD：SELECT 查询、INSERT 插入、"
            "UPDATE 更新、DELETE 删除。查询结构：SELECT ... FROM ... WHERE ... GROUP BY ... "
            "HAVING ... ORDER BY ... LIMIT。"
            "JOIN 连接多表：INNER JOIN（交集）、LEFT JOIN（左表全保留）、RIGHT JOIN、FULL JOIN。"
            "聚合函数 COUNT/SUM/AVG/MAX/MIN 配合 GROUP BY 分组。"
        ),
    },
    {
        "id": 22,
        "topic": "数据库",
        "title": "数据库索引",
        "keywords": ["索引", "index", "数据库", "B树", "B+树", "哈希索引", "查询优化",
                     "聚簇索引", "覆盖索引"],
        "summary": "索引基于 B+ 树等结构加速查询，但会增加写入开销与存储空间。",
        "content": (
            "索引是提升查询速度的数据结构，关系型数据库多基于 B+ 树（适合范围查询与排序）。"
            "聚簇索引：叶节点即数据行，一张表只能有一个；非聚簇索引：叶节点存主键，需回表。"
            "覆盖索引：索引包含查询所需全部列，避免回表。"
            "索引加速查询但拖慢写入并占空间，应建在高选择性、常查询的列上，避免在低基数列建索引。"
        ),
    },
    # ---- 操作系统 ----
    {
        "id": 23,
        "topic": "操作系统",
        "title": "进程与线程",
        "keywords": ["进程", "线程", "process", "thread", "并发", "调度", "同步",
                     "上下文切换", "操作系统", "协程"],
        "summary": "进程是资源分配单位，线程是 CPU 调度单位；线程间共享进程资源。",
        "content": (
            "进程是程序运行的实例，是资源分配的基本单位，拥有独立地址空间。"
            "线程是 CPU 调度的基本单位，同一进程的线程共享内存与资源，切换开销小于进程。"
            "并发（多任务交替）与并行（多核同时执行）。线程同步需用锁、信号量等避免竞态。"
            "协程是用户态轻量级并发，由程序调度，切换开销更小。"
        ),
    },
    {
        "id": 24,
        "topic": "操作系统",
        "title": "内存管理",
        "keywords": ["内存管理", "虚拟内存", "分页", "页面置换", "内存分配", "操作系统",
                     "页表", "缺页", "碎片"],
        "summary": "操作系统通过虚拟内存与分页机制管理内存，页面置换算法决定换出哪页。",
        "content": (
            "虚拟内存使每个进程拥有独立连续地址空间，实际映射到物理内存。"
            "分页机制将内存分为固定大小页框，通过页表映射虚拟页到物理页，缺页时从磁盘调入。"
            "常见页面置换算法：FIFO、LRU（最近最少使用）、LFU、Clock。"
            "内存分配需处理内部/外部碎片。了解内存管理有助于理解程序性能与崩溃原因。"
        ),
    },
    # ---- 网络 ----
    {
        "id": 25,
        "topic": "网络",
        "title": "HTTP协议",
        "keywords": ["http", "协议", "请求", "响应", "方法", "get", "post", "状态码",
                     "https", "无状态", "header"],
        "summary": "HTTP 是无状态的应用层协议，基于请求-响应模型，常用方法 GET/POST 等。",
        "content": (
            "HTTP 是无状态的应用层协议，基于请求-响应模型。请求由方法、URL、头、体组成，"
            "常用方法：GET（获取）、POST（创建）、PUT（更新）、DELETE（删除）、PATCH。"
            "响应包含状态码：2xx 成功、3xx 重定向、4xx 客户端错误、5xx 服务端错误。"
            "HTTPS = HTTP + TLS/SSL 加密。无状态可通过 Cookie/Session/Token 维持会话。"
        ),
    },
    {
        "id": 26,
        "topic": "网络",
        "title": "TCP/IP基础",
        "keywords": ["tcp", "ip", "udp", "三次握手", "四次挥手", "可靠传输", "网络分层",
                     "协议", "拥塞控制"],
        "summary": "TCP 提供面向连接的可靠传输，UDP 提供无连接的快速传输，IP 负责寻址路由。",
        "content": (
            "TCP/IP 是互联网的基础协议族，分为四层：应用层、传输层、网络层、网络接口层。"
            "TCP 面向连接、可靠传输，通过三次握手建连、四次挥手断连，有流量与拥塞控制。"
            "UDP 无连接、不可靠但快速低延迟，适合实时音视频、DNS 等。"
            "IP 负责寻址与路由（IPv4/IPv6）。TCP 适合文件传输/Web，UDP 适合实时通信。"
        ),
    },
]

# ---------------------------------------------------------------------------
# 主题依赖关系图
# key   : 主题标题（与知识库 title 一致，亦可用基础概念名）
# value : 该主题的直接前置知识列表（学习顺序在前的主题）
# 说明：部分前置为「条件判断」「循环」等基础概念，即使没有独立知识库条目，
#       也会作为前置知识返回，提示学习者先掌握这些基础。
# ---------------------------------------------------------------------------

PREREQUISITE_GRAPH: dict[str, list[str]] = {
    # Python 进阶依赖
    "Python函数": ["Python变量与数据类型", "条件判断", "循环"],
    "Python列表与元组": ["Python变量与数据类型"],
    "Python字典与集合": ["Python列表与元组", "Python函数"],
    "Python面向对象编程": ["Python函数", "Python变量与数据类型"],
    "Python装饰器": ["Python函数", "Python面向对象编程", "闭包"],
    "Python异常处理": ["Python函数", "条件判断"],
    "Python迭代器与生成器": ["Python函数", "循环", "Python异常处理"],
    # JavaScript 依赖
    "JavaScript函数与闭包": ["JavaScript基础语法"],
    "闭包": ["JavaScript函数与闭包", "Python函数"],
    "JavaScript异步编程": ["JavaScript函数与闭包", "JavaScript基础语法"],
    "JavaScript DOM操作": ["JavaScript基础语法", "JavaScript函数与闭包"],
    # 数据结构依赖
    "栈与队列": ["数组与链表"],
    "树与二叉树": ["递归", "数组与链表"],
    "哈希表": ["数组与链表", "Python函数"],
    # 算法依赖
    "排序算法": ["数组与链表", "循环", "条件判断"],
    "递归": ["Python函数", "条件判断", "栈与队列"],
    "动态规划": ["递归", "数组与链表"],
    "二分查找": ["数组与链表", "条件判断", "循环"],
    # 数据库依赖
    "SQL基础": ["数据库基础"],
    "数据库索引": ["SQL基础", "树与二叉树"],
    # 操作系统依赖
    "进程与线程": ["操作系统基础"],
    "内存管理": ["进程与线程"],
    # 网络依赖
    "HTTP协议": ["TCP/IP基础"],
    "TCP/IP基础": ["网络基础"],
}


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

# 用于切分查询的分隔符（含中英文标点与空白）
_SPLIT_RE = re.compile(r"[\s,，、;；。.!！?？:：()\[\]{}\"'`/\\|]+")


def _tokenize(text: str) -> list[str]:
    """将查询文本切分为关键词片段。

    对中文采用「分隔符切分 + 整体保留」策略：保留较长的连续片段，
    同时也保留被标点/空白切分出的子串，兼顾中文无空格的特点。
    """
    if not text:
        return []
    text = text.strip().lower()
    parts = [p for p in _SPLIT_RE.split(text) if p]
    # 额外保留原始整体（去空白小写），用于子串匹配长中文词
    if text and text not in parts:
        parts.append(text)
    return parts


def _safe_in(needle: str, haystack: str) -> bool:
    """子串包含判断（空串不匹配）。"""
    return bool(needle) and needle in haystack


def _score_entry(
    entry: dict,
    query_lower: str,
    tokens: list[str],
    topic_filter: str,
) -> float:
    """计算单个知识条目与查询的相关性得分。

    采用「关键词包含匹配」为主、「分词匹配」为辅的混合策略，兼顾中文（无空格）
    与英文（空格分隔）两种场景：

    - 关键词包含匹配（核心，适合中文）：若某关键词作为子串出现在原始查询中
      （如关键词「递归」出现在查询「递归怎么写」中），视为命中，并按关键词长度加权
      （越长越具体，权重越高）。
    - 分词匹配：对按分隔符切分出的 token，做关键词完全相等、标题子串、内容子串匹配，
      主要服务英文与含标点的查询。
    - 标题包含匹配：标题整体作为子串出现在查询中时给予较高权重。
    当提供 topic 过滤时，主题匹配的条目额外加权。
    """
    score = 0.0
    title = entry["title"].lower()
    keywords = [kw.lower() for kw in entry["keywords"]]
    content = entry["content"].lower()
    topic = entry["topic"].lower()

    # ---- 关键词包含匹配（适合中文无分词场景）----
    for kw in keywords:
        if not kw:
            continue
        if _safe_in(kw, query_lower):
            # 基础分 + 长度奖励（越长越具体，上限 6 字符）
            score += 2.0 + min(len(kw), 6) * 0.2

    # ---- 分词级匹配（英文 / 含分隔符的查询）----
    for token in tokens:
        if not token:
            continue
        # token 与某关键词完全相等
        if token in keywords:
            score += 3.0
        # token 是标题子串
        if _safe_in(token, title):
            score += 2.5
        # token 出现在内容中（长度>=2，避免单字符噪声）
        if len(token) >= 2 and _safe_in(token, content):
            score += 1.0

    # ---- 标题包含匹配：标题整体出现在查询中 ----
    if title and _safe_in(title, query_lower):
        score += 3.5

    # ---- 主题过滤加权 ----
    if topic_filter:
        tf = topic_filter.strip().lower()
        if tf:
            if _safe_in(tf, topic) or _safe_in(topic, tf):
                score += 2.0
            if _safe_in(tf, title) or any(_safe_in(tf, kw) for kw in keywords):
                score += 1.5

    return score


# ---------------------------------------------------------------------------
# 公开接口
# ---------------------------------------------------------------------------

async def search_knowledge(query: str, topic: str = "") -> list[dict]:
    """在本地知识库中搜索与查询相关的知识点。

    基于关键词（含中文子串）匹配进行检索，按相关性排序返回。当指定 ``topic``
    时，属于该主题的条目会获得加权，从而排在更前。

    Args:
        query: 查询关键词或自然语言描述，例如 ``"递归怎么写"`` 或 ``"python 装饰器"``。
        topic: 可选的主题过滤，例如 ``"Python"``、``"算法"``。为空时不做主题过滤。

    Returns:
        匹配的知识点列表，按相关性降序排列。每个元素结构为::

            {
                "id": int,                  # 知识条目编号
                "topic": str,               # 所属主题分类
                "title": str,               # 知识点标题
                "summary": str,             # 一句话摘要
                "content": str,             # 详细知识点说明
                "relevance": float,         # 归一化相关性 [0, 1]
                "matched_keywords": list,   # 命中的关键词（便于调试/展示）
            }

        若无任何匹配，返回空列表 ``[]``。
    """
    if not query or not query.strip():
        return []

    topic_filter = (topic or "").strip()
    query_lower = query.strip().lower()
    tokens = _tokenize(query)

    scored: list[tuple[float, dict, list[str]]] = []
    for entry in KNOWLEDGE_BASE:
        score = _score_entry(entry, query_lower, tokens, topic_filter)
        if score <= 0:
            continue
        # 计算命中的关键词，便于展示
        matched = []
        for kw in entry["keywords"]:
            kw_l = kw.lower()
            if any(t == kw_l or _safe_in(t, kw_l) for t in tokens) or _safe_in(kw_l, query_lower):
                matched.append(kw)
        scored.append((score, entry, matched))

    if not scored:
        return []

    # 按得分降序排序
    scored.sort(key=lambda x: x[0], reverse=True)

    max_score = scored[0][0]
    results: list[dict] = []
    for score, entry, matched in scored[:10]:
        # 归一化到 [0, 1]，最高匹配为 1.0
        relevance = round(score / max_score, 3) if max_score > 0 else 0.0
        results.append({
            "id": entry["id"],
            "topic": entry["topic"],
            "title": entry["title"],
            "summary": entry["summary"],
            "content": entry["content"],
            "relevance": relevance,
            "matched_keywords": matched,
        })
    return results


async def get_prerequisites(topic: str) -> list[str]:
    """查找指定主题的前置知识。

    基于内置的主题依赖关系图，返回学习该主题前应先掌握的直接前置知识列表。
    前置顺序即列表顺序，反映推荐的学习先后。

    Args:
        topic: 主题名称，应与知识库中的 ``title`` 或依赖图中的 key 一致，
            例如 ``"递归"``、``"动态规划"``、``"Python装饰器"``。

    Returns:
        该主题的直接前置知识列表，如 ``["Python函数", "条件判断", "栈与队列"]``。
        若主题未知或无前置依赖，返回空列表 ``[]``。
    """
    if not topic or not topic.strip():
        return []
    key = topic.strip()
    # 直接查依赖图
    prereqs = PREREQUISITE_GRAPH.get(key)
    if prereqs:
        return list(prereqs)

    # 容错：若传入的是知识库标题但依赖图 key 大小写/写法略有差异，
    # 做一次不区分大小写的匹配
    key_lower = key.lower()
    for graph_key, deps in PREREQUISITE_GRAPH.items():
        if graph_key.lower() == key_lower:
            return list(deps)
    return []


# ---------------------------------------------------------------------------
# 便捷：获取全部主题分类与知识点标题（便于上层展示/校验）
# ---------------------------------------------------------------------------

def list_topics() -> list[str]:
    """返回知识库覆盖的全部主题分类（去重保序）。"""
    seen: list[str] = []
    for entry in KNOWLEDGE_BASE:
        if entry["topic"] not in seen:
            seen.append(entry["topic"])
    return seen


def list_knowledge_titles() -> list[str]:
    """返回知识库中全部知识点标题（按定义顺序）。"""
    return [entry["title"] for entry in KNOWLEDGE_BASE]
