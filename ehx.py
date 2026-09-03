import sys

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter


VERSION = "0.1.0"


def print_help():
    print(f"""EHXLang {VERSION}

Usage:
  ehx run <file.ehx>
  ehx help
""")


def run_file(filename):
    if not filename.endswith(".ehx"):
        raise RuntimeError(
            "EHX Error: source file must have .ehx extension"
        )

    try:
        with open(filename, "r", encoding="utf-8") as file:
            source = file.read()

    except FileNotFoundError:
        raise RuntimeError(
            f"EHX Error: file '{filename}' not found"
        )

    lexer = Lexer(source)
    tokens = lexer.tokenize()

    parser = Parser(tokens)
    program = parser.parse()

    interpreter = Interpreter()
    interpreter.run(program)


def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1]

    if command == "help":
        print_help()
        return

    if command == "run":
        if len(sys.argv) < 3:
            print(
                "EHX Error: missing source file\n"
            )
            print_help()
            return

        try:
            run_file(sys.argv[2])

        except (RuntimeError, SyntaxError) as error:
            print(error)

        return

    print(
        f"EHX Error: unknown command '{command}'\n"
    )

    print_help()


if __name__ == "__main__":
    main()