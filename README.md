# py-interpreter

![Image.png](https://res.craft.do/user/full/ef363a0d-96e2-ce0d-d615-edb486d8a754/doc/9594BCBF-D290-4437-B58E-995AC6FB58E9/A38020D1-0703-42F6-8E6D-2FF10F05854C_2/c7gLR8bx3SWpoqvlCIxDu5jgN5VLuYxaE6iglFLBrPAz/Image.png)

lexer  -> parser -> compiler -> interpreter

token → ast        → pyc          → interptreter

# A Python Interpreter

Python 解释器，狭义上来说，是以Python字节码（更确切说是 code 对象）为输入，执行字节码执行的虚拟机。该虚拟机以 stack 核心数据结构，stack 存储了程序运行状态，所有的操作都在 stack 上进行。

> The interpreter uses a stack-based approach to evaluate expressions and keep track of the execution context.

# Python 字节码

Python 虽然是解释性语言，但为了执行效率会首先将源码编译（compile）为二进制的字节码，存储在`*.pyc`文件中。即从工作原理上讲，Python 和 Java、C# 更为相近。区别是，Python 编译（compile）的工作较为简单，把更多的工作交给解释器在运行时中完成。因此 PVM 执行时需要执行更多检查，相比Java、C#等执行效率较低。

经典书籍《Python 学习手册》中有这样一张插图，可以帮助我们理解 Python 程序的执行过程：

![Image.png](https://res.craft.do/user/full/ef363a0d-96e2-ce0d-d615-edb486d8a754/doc/9594BCBF-D290-4437-B58E-995AC6FB58E9/90B2CBC3-AB43-4C21-962D-49245E9CE391_2/JDIByV0xDV6UTpwJWBHvpBxenfGM30VgYhPkyTiIU54z/Image.png)

字节码，从类型化角度来说，就是一个带有执行信息的 `code` 对象，可以使用`compile()`或直接从`__code__`属性中获取。使用 `dis` 模块可以解析 `code` 对象并以列表形式进行展示。一般来说，这个列表会有 5 列，从左到右，它们的内容包括：

- 对应源码的行号
- 指令在整个字节码中的偏移量
- 指令名称
- 指令的参数（如果有的话）
- 对指令参数的含义进行补充说明，以便于理解

# Python 解释器工作模型

Python 解释器是一个基于堆栈（`Stack`）的工作模型。许多指令都是从堆栈中获取需要的参数，并且执行的结果通常也要再次推到堆栈中。通常，这些指令也会对堆栈的状态做出一定的假设，比如 `BINARY_OP` 指令就假定在它执行的时候，需要的两个操作数都已经在栈上，所以就不要额外的参数了。

## 核心组件

![interpreter-callstack.png](https://aosabook.org/en/500L/interpreter-images/interpreter-callstack.png)

1. Stack：Call Stack、Data Stack、Block Stack
2. Frame
3. Class：VirtualMachine Class、Frame Class、Function Class、Block Class
   - A `VirtualMachine` class, which manages the highest-level structure, particularly the call stack of frames, and contains a mapping of instructions to operations. This is a more complex version of the `Intepreter` object above.
   - A `Frame` class. Every `Frame` instance has one code object and manages a few other necessary bits of state, particularly the global and local namespaces, a reference to the calling frame, and the last bytecode instruction executed.
   - A `Function` class, which will be used in place of real Python functions. Recall that calling a function creates a new frame in the interpreter. We implement Function so that we control the creation of new Frames.
   - A `Block` class, which just wraps the three attributes of blocks. (The details of blocks aren't central to the Python interpreter, so we won't spend much time on them, but they're included here so that Byterun can run real Python code.)

参考：

[重写 500 Lines or Less 项目 - A Python Interpreter Written in Python - SHUHARI 的博客](https://shuhari.dev/blog/2020/12/500lines-rewrite-interpreter)

[500 Lines or Less: A Python Interpreter Written in Python](https://aosabook.org/en/500L/a-python-interpreter-written-in-python.html)

