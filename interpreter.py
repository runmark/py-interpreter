from collections import ChainMap
import dis
import builtins


class ReturnValue(Exception):
    def __init__(self, value):
        self.value = value


def dump_recursive(code):
    def dump(acode):
        print(f"====dis code of {acode.co_name}====")
        print("co_names:", acode.co_names)
        print("co_consts:", acode.co_consts)
        print("co_code", acode.co_code)
        print("co_varnames", acode.co_varnames)
        dis.dis(acode, depth=0)

    dump(code)
    for item in code.co_consts:
        if hasattr(item, "co_code"):
            dump_recursive(item)


class Frame:
    def __init__(self, interpreter, code, scope: ChainMap):
        self._interpreter = interpreter
        self._code = code
        self.scope = scope.new_child()
        self._stack = []
        self._instructions = list(dis.get_instructions(self._code))
        self._next_instruction = 0

        # self._builtins = {
        #     x: getattr(builtins, x) for x in dir(builtins) if not x.startswith("__")
        # }
        # self._locals = {**local_vars}

    def get_local(self, var_name: str):
        return self.scope[var_name]

    def set_local(self, var_name: str, var_value):
        self.scope[var_name] = var_value

    def set_args(self, args):
        for i, v in enumerate(args):
            name = self._code.co_varnames[i]
            self.set_local(name, v)

    def get_const(self, consti):
        return self._code.co_consts[consti]

    def stack_push(self, value):
        self._stack.append(value)

    def stack_pop(self):
        return self._stack.pop(-1)

    def stack_popn(self, n):
        if n > 0:
            result = self._stack[-n:]
            self._stack = self._stack[:-n]
            return result
        return []

    def get_name(self, namei):
        return self._code.co_names[namei]

    def exec(self):
        while True:
            try:
                instruction = self._instructions[self._next_instruction]
                fn = getattr(self, "exec_" + instruction.opname)
                instruction_result = fn(instruction.arg)
                if not instruction_result:
                    self._next_instruction += 1
                if self._interpreter.trace_stack:
                    self.dump_stack(instruction)
            except ReturnValue as e:
                return e.value

    # def dump_code(self):
    #     print(f"====dis code of {self._code.co_name}====")
    #     print("co_names:", self._code.co_names)
    #     print("co_consts:", self._code.co_consts)
    #     print("co_code", self._code.co_code)
    #     print("co_varnames", self._code.co_varnames)
    #     dis.dis(self._code)

    def dump_stack(self, instruction):
        print(f"Stack after {instruction.opname}({instruction.offset}): {self._stack}")

    def exec_LOAD_NAME(self, namei):
        """
        LOAD_NAME(namei)
        Pushes the value associated with co_names[namei] onto the stack.
        """
        name = self.get_name(namei)
        if name in self.scope:
            value = self.get_local(name)
        else:
            raise NameError(name)
        self.stack_push(value)
        return False

    def exec_LOAD_CONST(self, namei):
        """
        LOAD_CONST(consti)
        Pushes co_consts[consti] onto the stack.
        """
        value = self.get_const(namei)
        self.stack_push(value)
        return False

    def exec_BINARY_ADD(self, _):
        first = self.stack_pop()
        second = self.stack_pop()
        value = first + second
        self.stack_push(value)
        return False

    def exec_STORE_NAME(self, namei):
        """
        STORE_NAME(namei)
        Implements name = TOS. namei is the index of name in the attribute co_names of the code object. The compiler tries to use STORE_FAST or STORE_GLOBAL if possible.
        """
        name = self.get_name(namei)
        value = self.stack_pop()
        self.set_local(name, value)
        return False

    def exec_RETURN_VALUE(self, _):
        """
        RETURN_VALUE
        Returns with TOS to the caller of the function.
        """
        value = self.stack_pop()
        raise ReturnValue(value)

    def exec_CALL_FUNCTION(self, args_count):
        args = self.stack_popn(args_count)
        func = self.stack_pop()
        result = func(*args)
        self.stack_push(result)
        return False

    def exec_COMPARE_OP(self, opi):
        opname = dis.cmp_op[opi]

        comparers = {
            "<": lambda x, y: x < y,
            "<=": lambda x, y: x <= y,
            "==": lambda x, y: x == y,
            "!=": lambda x, y: x != y,
            ">": lambda x, y: x > y,
            ">=": lambda x, y: x >= y,
            "in": lambda x, y: x in y,
            "not in": lambda x, y: x not in y,
            "is": lambda x, y: x is y,
            "is not": lambda x, y: x is not y,
        }

        tos1, tos = self.stack_popn(2)
        self.stack_push(comparers[opname](tos1, tos))
        return False

    def exec_POP_JUMP_IF_FALSE(self, lineno):
        state = self.stack_pop()
        if not state:
            self.jump_by_offset(lineno)
            return True
        return False

    def jump_by_offset(self, offset):
        index = [
            index
            for index, instruction in enumerate(self._instructions)
            if instruction.offset == offset
        ][0]
        self._next_instruction = index

    def jump_by_delta(self, delta):
        offset = self._instructions[self._next_instruction + 1].offset + delta
        self.jump_by_offset(offset)

    def exec_JUMP_FORWARD(self, relative_lineno):
        next_instruction_offset = (
            self._instructions[self._next_instruction + 1].offset + relative_lineno
        )
        self.jump_by_offset(next_instruction_offset)
        return True

    def exec_MAKE_FUNCTION(self, flag):
        """
        Pushes a new function object on the stack.
        From bottom to top, the consumed stack must consist of values if the argument carries a specified flag value.
        """
        name = self.stack_pop()
        code = self.stack_pop()

        freevars, annotations, defaults, kwdefaults = None, None, None, None

        if flag & 0x8:
            freevars = self.stack_pop()
        if flag & 0x4:
            annotations = self.stack_pop()
        if flag & 0x2:
            kwdefaults = self.stack_pop()
        if flag & 0x1:
            defaults = self.stack_pop()

        func = Function(
            self._interpreter, name, code, freevars, annotations, kwdefaults, defaults
        )

        self.stack_push(func)

    def exec_LOAD_FAST(self, index):
        name = self._code.co_varnames[index]
        value = self.get_local(name)
        self.stack_push(value)

    def exec_STORE_FAST(self, varindex):
        name = self._code.co_varnames[varindex]
        value = self.stack_pop()
        self.set_local(name, value)

    def exec_GET_ITER(self, _):
        """Implements TOS = iter(TOS)."""
        TOS = self.stack_pop()
        self.stack_push(iter(TOS))

    def exec_FOR_ITER(self, delta):
        """TOS is an iterator. Call its __next__() method.
        If this yields a new value, push it on the stack (leaving the iterator below it).
        If the iterator indicates it is exhausted, TOS is popped, and the byte code counter is incremented by delta.
        """
        it = self.stack_pop()
        try:
            value = next(it)
            self.stack_push(it)
            self.stack_push(value)
        except StopIteration:
            self.jump_by_delta(delta)
            return True

    def exec_BUILD_LIST(self, count):
        """Creates a list consuming count items from the stack,
        and pushes the resulting list onto the stack."""
        items = self.stack_popn(count)
        self.stack_push(items)

    def exec_LIST_APPEND(self, i):
        """Calls list.append(TOS1[-i], TOS). Used to implement list comprehensions."""
        value = self.stack_pop()
        l = self._stack[-i]
        assert isinstance(l, list)
        l.append(value)

    def exec_JUMP_ABSOLUTE(self, lineno):
        self.jump_by_offset(lineno)
        return True


class Function:
    def __init__(
        self, interpreter, name, code, freevars, annotations, kwdefaults, defaults
    ):
        self.interpreter = interpreter
        self.name = name
        self.code = code
        self.freevars = freevars
        self.annonations = annotations
        self.kwdefaults = kwdefaults
        self.defaults = defaults

    def __call__(self, *args, **kwargs):
        frame: Frame = Frame(
            self.interpreter, self.code, self.interpreter.top_frame().scope
        )
        frame.set_args(args)
        self.interpreter.frame_push(frame)
        result = frame.exec()
        self.interpreter.frame_pop()
        return result


class Interpreter:
    builtin_dict = {
        x: getattr(builtins, x) for x in dir(builtins) if not x.startswith("__")
    }

    def __init__(self, src: str, local_vars: None, dump_code=False, trace_stack=False):
        self._dump_code = dump_code
        self.trace_stack = trace_stack

        self._code = compile(src, filename="", mode="exec")
        self._scope = ChainMap(Interpreter.builtin_dict)

        self._frames = []
        main_frame = Frame(self, self._code, self._scope)
        if local_vars:
            for k, v in local_vars.items():
                main_frame.set_local(k, v)
        self._frames.append(main_frame)

    def top_frame(self):
        return self._frames[-1]

    def frame_push(self, frame):
        self._frames.append(frame)

    def frame_pop(self):
        if len(self._frames) == 1:
            raise RuntimeError("main frame cannot pop out")
        return self._frames.pop(-1)

    def get_local(self, name):
        return self.top_frame().get_local(name)

    def exec(self):
        if self._dump_code:
            dump_recursive(self._code)
        self.top_frame().exec()
