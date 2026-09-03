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

        if expression_type == "identifier":
            return self.evaluate_identifier(expression)

        if expression_type == "binary":
            return self.evaluate_binary(expression)

        if expression_type == "unary":
            return self.evaluate_unary(expression)

        raise RuntimeError(
            f"EHX Error: unknown expression type "
            f"'{expression_type}'"
        )

    def evaluate_identifier(self, expression):
        name = expression["name"]

        if name not in self.variables:
            raise RuntimeError(
                f"EHX Error: variable "
                f"'{name}' is not defined"
            )

        return self.variables[name]

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

        raise RuntimeError(
            f"EHX Error: unknown unary operator "
            f"'{operator}'"
        )

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
    # Type helpers
    # -------------------------

    def is_number(self, value):
        return (
            isinstance(value, int)
            and not isinstance(value, bool)
        ) or isinstance(value, float)

    def type_name(self, value):
        if isinstance(value, str):
            return "string"

        if isinstance(value, int):
            return "integer"

        if isinstance(value, float):
            return "float"

        return type(value).__name__