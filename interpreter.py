import dis


class Interpreter:
    def __init__(self, src: str):
        self._code = compile(src, filename="", mode="exec")
        self._locals = {}
        self._stack = []

    def get_local(self, var_name: str):
        return self._locals[var_name]

    def set_local(self, var_name: str, var_value):
        self._locals[var_name] = var_value

    def get_const(self, consti):
        return self._code.co_consts[consti]

    def stack_push(self, value):
        self._stack.append(value)

    def stack_pop(self):
        return self._stack.pop(-1)

    def get_name(self, namei):
        return self._code.co_names[namei]

    def exec(self, dump_code=False, trace_stack=False):
        if dump_code:
            self.dump_code()
        for instruction in dis.get_instructions(self._code):
            fn = getattr(self, "exec_" + instruction.opname)
            fn(instruction.arg)
            if trace_stack:
                self.dump_stack(instruction)

    def dump_code(self):
        print(f"====dis code of {self._code.co_name}====")
        print("co_names:", self._code.co_names)
        print("co_consts:", self._code.co_consts)
        print("co_code", self._code.co_code)
        print("co_varnames", self._code.co_varnames)
        dis.dis(self._code)

    def dump_stack(self, instruction):
        print(f"Stack after {instruction.opname}({instruction.offset}): {self._stack}")

    def exec_LOAD_NAME(self, namei):
        """
        LOAD_NAME(namei)
        Pushes the value associated with co_names[namei] onto the stack.
        """
        name = self.get_name(namei)
        value = self.get_local(name)
        self.stack_push(value)

    def exec_LOAD_CONST(self, namei):
        """
        LOAD_CONST(consti)
        Pushes co_consts[consti] onto the stack.
        """
        value = self.get_const(namei)
        self.stack_push(value)

    def exec_BINARY_ADD(self, _):
        first = self.stack_pop()
        second = self.stack_pop()
        value = first + second
        self.stack_push(value)

    def exec_STORE_NAME(self, namei):
        """
        STORE_NAME(namei)
        Implements name = TOS. namei is the index of name in the attribute co_names of the code object. The compiler tries to use STORE_FAST or STORE_GLOBAL if possible.
        """
        name = self.get_name(namei)
        value = self.stack_pop()
        self.set_local(name, value)

    def exec_RETURN_VALUE(self, _):
        """
        RETURN_VALUE
        Returns with TOS to the caller of the function.
        """
        pass
