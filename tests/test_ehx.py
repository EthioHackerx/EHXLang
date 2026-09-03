import unittest

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter


def run_ehx(source):
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    parser = Parser(tokens)
    program = parser.parse()

    interpreter = Interpreter()
    interpreter.run(program)

    return interpreter


class TestEHXLang(unittest.TestCase):

    def test_integer_variable(self):
        interpreter = run_ehx(
            "set x = 10"
        )

        self.assertEqual(
            interpreter.variables["x"],
            10
        )

    def test_float_variable(self):
        interpreter = run_ehx(
            "set score = 95.5"
        )

        self.assertEqual(
            interpreter.variables["score"],
            95.5
        )

    def test_string_variable(self):
        interpreter = run_ehx(
            'set name = "EHX"'
        )

        self.assertEqual(
            interpreter.variables["name"],
            "EHX"
        )

    def test_addition(self):
        interpreter = run_ehx(
            "set result = 10 + 20"
        )

        self.assertEqual(
            interpreter.variables["result"],
            30
        )

    def test_subtraction(self):
        interpreter = run_ehx(
            "set result = 20 - 5"
        )

        self.assertEqual(
            interpreter.variables["result"],
            15
        )

    def test_multiplication(self):
        interpreter = run_ehx(
            "set result = 10 * 5"
        )

        self.assertEqual(
            interpreter.variables["result"],
            50
        )

    def test_division(self):
        interpreter = run_ehx(
            "set result = 20 / 5"
        )

        self.assertEqual(
            interpreter.variables["result"],
            4
        )

    def test_string_concatenation(self):
        interpreter = run_ehx(
            'set result = "Ethio " + "Hacker X"'
        )

        self.assertEqual(
            interpreter.variables["result"],
            "Ethio Hacker X"
        )

    def test_variable_reference(self):
        interpreter = run_ehx(
            """
            set x = 10
            set y = x
            """
        )

        self.assertEqual(
            interpreter.variables["y"],
            10
        )

    def test_operator_precedence(self):
        interpreter = run_ehx(
            "set result = 10 + 20 * 2"
        )

        self.assertEqual(
            interpreter.variables["result"],
            50
        )

    def test_parentheses(self):
        interpreter = run_ehx(
            "set result = (10 + 20) * 2"
        )

        self.assertEqual(
            interpreter.variables["result"],
            60
        )

    def test_unary_minus(self):
        interpreter = run_ehx(
            "set result = -10"
        )

        self.assertEqual(
            interpreter.variables["result"],
            -10
        )

    def test_unary_parentheses(self):
        interpreter = run_ehx(
            "set result = -(10 + 5)"
        )

        self.assertEqual(
            interpreter.variables["result"],
            -15
        )

    def test_comments(self):
        interpreter = run_ehx(
            """
            # This is a comment

            set x = 10

            # Another comment
            set y = 20
            """
        )

        self.assertEqual(
            interpreter.variables["x"],
            10
        )

        self.assertEqual(
            interpreter.variables["y"],
            20
        )

    def test_complex_expression(self):
        interpreter = run_ehx(
            """
            set x = 10
            set y = 20
            set result = -(x + y) * 2
            """
        )

        self.assertEqual(
            interpreter.variables["result"],
            -60
        )

    def test_undefined_variable(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "variable 'unknown' is not defined"
        ):
            run_ehx("say unknown")

    def test_division_by_zero(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "division by zero"
        ):
            run_ehx("set x = 10 / 0")

    def test_invalid_addition(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "cannot add"
        ):
            run_ehx(
                """
                set x = 10
                set name = "EHX"
                set result = x + name
                """
            )

    def test_invalid_subtraction(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "cannot subtract"
        ):
            run_ehx(
                """
                set name = "EHX"
                set result = name - "Lang"
                """
            )

    def test_invalid_multiplication(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "cannot multiply"
        ):
            run_ehx(
                """
                set name = "EHX"
                set result = name * 5
                """
            )

    def test_invalid_unary_minus(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "unary '-' requires a number"
        ):
            run_ehx(
                'set result = -"EHX"'
            )


if __name__ == "__main__":
    unittest.main()