class Interpreter:
    def __init__(self):
        self.variables = {}

    # -------------------------
    # Program execution
    # -------------------------

    def run(self, program):
        for statement in program:
            self.execute_statement(statement)

    # -------------------------
    # Statements
    # -------------------------

    def execute_statement(self, statement):
        statement_type = statement["type"]

        if statement_type == "set":
            self.execute_set(statement)
            return

        if statement_type == "say":
            self.execute_say(statement)
            return

        raise RuntimeError(
            f"EHX Error: unknown statement type "
            f"'{statement_type}'"
        )

    def execute_set(self, statement):
        name = statement["name"]
        value = self.evaluate(statement["value"])

        self.variables[name] = value

    def execute_say(self, statement):
        value = self.evaluate(statement["value"])

        print(value)

    # -------------------------
    # Expressions
    # -------------------------

    def evaluate(self, expression):
        expression_type = expression["type"]

        if expression_type == "string":
            return expression["value"]

        if expression_type == "number":
            return expression["value"]

        if expression_type == "boolean":
            return expression["value"]

        if expression_type == "identifier":
            return self.evaluate_identifier(expression)

        if expression_type == "binary":
            return self.evaluate_binary(expression)

        if expression_type == "comparison":
            return self.evaluate_comparison(expression)

        if expression_type == "logical":
            return self.evaluate_logical(expression)

        if expression_type == "unary":
            return self.evaluate_unary(expression)

        raise RuntimeError(
            f"EHX Error: unknown expression type "
            f"'{expression_type}'"
        )

    # -------------------------
    # Variables
    # -------------------------

    def evaluate_identifier(self, expression):
        name = expression["name"]

        if name not in self.variables:
            raise RuntimeError(
                f"EHX Error: variable "
                f"'{name}' is not defined"
            )

        return self.variables[name]

    # -------------------------
    # Unary
    # -------------------------

    def evaluate_unary(self, expression):
        value = self.evaluate(expression["value"])
        operator = expression["operator"]

        if operator == "-":
            if not self.is_number(value):
                raise RuntimeError(
                    "EHX Error: unary '-' "
                    "requires a number"
                )

            return -value

        if operator == "not":
            if not isinstance(value, bool):
                raise RuntimeError(
                    "EHX Error: 'not' "
                    "requires a boolean"
                )

            return not value

        raise RuntimeError(
            f"EHX Error: unknown unary operator "
            f"'{operator}'"
        )

    # -------------------------
    # Arithmetic
    # -------------------------

    def evaluate_binary(self, expression):
        left = self.evaluate(expression["left"])
        right = self.evaluate(expression["right"])

        operator = expression["operator"]

        if operator == "+":
            if isinstance(left, str) and isinstance(right, str):
                return left + right

            if self.is_number(left) and self.is_number(right):
                return left + right

            raise RuntimeError(
                "EHX Error: cannot add "
                f"{self.type_name(left)} and "
                f"{self.type_name(right)}"
            )

        if operator == "-":
            if not self.is_number(left) or not self.is_number(right):
                raise RuntimeError(
                    "EHX Error: cannot subtract "
                    f"{self.type_name(left)} and "
                    f"{self.type_name(right)}"
                )

            return left - right

        if operator == "*":
            if not self.is_number(left) or not self.is_number(right):
                raise RuntimeError(
                    "EHX Error: cannot multiply "
                    f"{self.type_name(left)} and "
                    f"{self.type_name(right)}"
                )

            return left * right

        if operator == "/":
            if not self.is_number(left) or not self.is_number(right):
                raise RuntimeError(
                    "EHX Error: cannot divide "
                    f"{self.type_name(left)} and "
                    f"{self.type_name(right)}"
                )

            if right == 0:
                raise RuntimeError(
                    "EHX Error: division by zero"
                )

            return left / right

        raise RuntimeError(
            f"EHX Error: unknown operator '{operator}'"
        )

    # -------------------------
    # Comparisons
    # -------------------------

    def evaluate_comparison(self, expression):
        left = self.evaluate(expression["left"])
        right = self.evaluate(expression["right"])

        operator = expression["operator"]

        if operator == "==":
            return left == right

        if operator == "!=":
            return left != right

        if operator == ">":
            return self.compare_values(left, right, ">")

        if operator == "<":
            return self.compare_values(left, right, "<")

        if operator == ">=":
            return self.compare_values(left, right, ">=")

        if operator == "<=":
            return self.compare_values(left, right, "<=")

        raise RuntimeError(
            f"EHX Error: unknown comparison operator "
            f"'{operator}'"
        )

    def compare_values(self, left, right, operator):
        if type(left) != type(right):
            raise RuntimeError(
                "EHX Error: cannot compare "
                f"{self.type_name(left)} and "
                f"{self.type_name(right)}"
            )

        if not (
            self.is_number(left)
            or isinstance(left, str)
        ):
            raise RuntimeError(
                "EHX Error: values are not orderable"
            )

        if operator == ">":
            return left > right

        if operator == "<":
            return left < right

        if operator == ">=":
            return left >= right

        if operator == "<=":
            return left <= right

        raise RuntimeError(
            f"EHX Error: unknown comparison '{operator}'"
        )

    # -------------------------
    # Logical operators
    # -------------------------

    def evaluate_logical(self, expression):
        operator = expression["operator"]

        left = self.evaluate(expression["left"])

        if not isinstance(left, bool):
            raise RuntimeError(
                f"EHX Error: '{operator}' "
                "requires boolean values"
            )

        # Short-circuit evaluation
        if operator == "and":
            if not left:
                return False

            right = self.evaluate(expression["right"])

            if not isinstance(right, bool):
                raise RuntimeError(
                    "EHX Error: 'and' "
                    "requires boolean values"
                )

            return left and right

        if operator == "or":
            if left:
                return True

            right = self.evaluate(expression["right"])

            if not isinstance(right, bool):
                raise RuntimeError(
                    "EHX Error: 'or' "
                    "requires boolean values"
                )

            return left or right

        raise RuntimeError(
            f"EHX Error: unknown logical operator "
            f"'{operator}'"
        )

    # -------------------------
    # Type helpers
    # -------------------------

    def is_number(self, value):
        return (
            isinstance(value, int)
            and not isinstance(value, bool)
        ) or isinstance(value, float)

    def type_name(self, value):
        if isinstance(value, bool):
            return "boolean"

        if isinstance(value, str):
            return "string"

        if isinstance(value, int):
            return "integer"

        if isinstance(value, float):
            return "float"

        return type(value).__name__