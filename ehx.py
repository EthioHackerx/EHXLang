import os
import sys

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter


VERSION = "1.0.0"

# Enable Windows virtual terminal escape sequences & UTF-8 output
if sys.platform == "win32":
    try:
        os.system("")
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Terminal ANSI styling codes
C_CYAN = "\033[96m"
C_BOLD = "\033[1m"
C_WHITE = "\033[97m"
C_GRAY = "\033[90m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_MAGENTA = "\033[95m"
C_RESET = "\033[0m"

BANNER = r"""
███████╗██╗  ██╗██╗  ██╗██╗      █████╗ ███╗   ██╗ ██████╗ 
██╔════╝██║  ██║╚██╗██╔╝██║     ██╔══██╗████╗  ██║██╔════╝ 
█████╗  ███████║ ╚███╔╝ ██║     ███████║██╔██╗ ██║██║  ███╗
██╔══╝  ██╔══██║ ██╔██╗ ██║     ██╔══██║██║╚██╗██║██║   ██║
███████╗██║  ██║██╔╝ ██╗███████╗██║  ██║██║ ╚████║╚██████╔╝
╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ 
"""


def print_banner():
    print(C_CYAN + C_BOLD + BANNER + C_RESET)
    print(C_GRAY + "  =====================================================================" + C_RESET)
    print("  " + C_WHITE + C_BOLD + "EHXLang v" + VERSION + C_RESET + " " + C_GRAY + "|" + C_RESET + " " + C_GREEN + "A Simple & Powerful Language for Everyone" + C_RESET)
    print("  " + C_GRAY + "Developed by " + C_WHITE + C_BOLD + "Yonatan Muluken ( ETHIO HACKER X )" + C_RESET)
    print(C_GRAY + "  =====================================================================" + C_RESET)


def print_version():
    print_banner()
    print("  " + C_GREEN + "Status:" + C_RESET + "    v" + VERSION + " Production Release (All Systems Operational)")
    print("  " + C_YELLOW + "Community & Official Channels:" + C_RESET)
    print("    " + C_CYAN + "[*] Telegram:" + C_RESET + "  @EthioHackerX")
    print("    " + C_MAGENTA + "[*] TikTok:" + C_RESET + "    @ethio_hacker_x")
    print("    " + C_YELLOW + "[*] YouTube:" + C_RESET + "   @EthioHackerX")
    print("    " + C_WHITE + "[*] GitHub:" + C_RESET + "    https://github.com/EthioHackerX")
    print()


def print_help():
    print_banner()
    print("""
  Usage:
    ehx <file.ehx>            Run an EHXLang script directly
    ehx run <file.ehx>        Run an EHXLang script
    ehx repl                  Start the interactive REPL shell
    ehx --version, -v         Display version information & banner
    ehx help, --help, -h      Display this help menu
""")


def start_repl():
    print_banner()
    print("  " + C_YELLOW + "Commands:" + C_RESET + " Type " + C_BOLD + "help" + C_RESET + " for guide, " + C_BOLD + "exit" + C_RESET + " or " + C_BOLD + "quit" + C_RESET + " to leave.\n")

    interpreter = Interpreter()

    prompt = C_CYAN + C_BOLD + "ehx" + C_RESET + C_WHITE + "> " + C_RESET

    while True:
        try:
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print("\nExiting EHXLang.")
            break

        cleaned = line.strip()
        if not cleaned:
            continue

        if cleaned in ("exit", "quit"):
            print("Goodbye!")
            break

        if cleaned == "help":
            print("Enter any valid EHXLang statement or expression.")
            print("Examples: let x = 5 | show(x * 2) | show(read('notes.txt'))\n")
            continue

        # Execute single line in persistent interpreter
        try:
            # Check if it's an expression that can be evaluated and shown directly
            source = line
            # Ensure line ends with newline for lexer
            if not source.endswith("\n"):
                source += "\n"

            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            program = parser.parse()

            for stmt in program["statements"]:
                # If it's an expression statement, display its result like Python REPL
                if stmt.get("type") == "expression_statement":
                    val = interpreter.evaluate(stmt["expression"])
                    if val is not None:
                        print(interpreter.to_representation(val))
                else:
                    interpreter.execute(stmt)

        except (RuntimeError, SyntaxError) as err:
            print(err)
        except Exception as e:
            print(f"Error: {e}")


def run_file(filename):
    if not filename.endswith(".ehx"):
        raise RuntimeError(
            "EHX Error: source file must have .ehx extension"
        )

    try:
        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as file:
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
        # If no arguments provided, launch interactive REPL shell!
        start_repl()
        return

    first_arg = sys.argv[1]

    if first_arg in ("--version", "-v"):
        print_version()
        return

    if first_arg in ("help", "--help", "-h"):
        print_help()
        return

    if first_arg == "repl":
        start_repl()
        return

    if first_arg == "run":
        if len(sys.argv) < 3:
            print("EHX Error: missing source file\n")
            print_help()
            return

        try:
            run_file(sys.argv[2])
        except (RuntimeError, SyntaxError) as error:
            print(error)
        return

    # Direct script execution: ehx script.ehx
    if first_arg.endswith(".ehx"):
        try:
            run_file(first_arg)
        except (RuntimeError, SyntaxError) as error:
            print(error)
        return

    print(f"EHX Error: unknown command '{first_arg}'\n")
    print_help()


if __name__ == "__main__":
    main()