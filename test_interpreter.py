import unittest

from interpreter import Interpreter


class InterpreterTest(unittest.TestCase):
    def exec_interpreter(
        self, source, local_vars=None, dump_code=False, trace_stack=False
    ):
        interpreter = Interpreter(source, local_vars, dump_code, trace_stack)
        interpreter.exec()
        return interpreter

    def test_add(self):
        source = "n = a + 1"
        interpreter = self.exec_interpreter(source, {"a": 2})
        self.assertEqual(3, interpreter.get_local("n"))

    def test_call_func(self):
        source = "n = divmod(a, 2)"
        interpreter = self.exec_interpreter(source, {"a": 11}, False, False)
        self.assertEqual((5, 1), interpreter.get_local("n"))

    def test_if(self):
        source = """
if a > 10:
  b = True
else:
  b = False
                """.strip()
        interpreter = self.exec_interpreter(source, {"a": 11}, True, True)
        self.assertEqual(True, interpreter.get_local("b"))

        interpreter = self.exec_interpreter(source, {"a": 3}, False, False)
        self.assertEqual(False, interpreter.get_local("b"))


# if __name__ == "__main__":
#     unittest.main()
