import os
import unittest
import textwrap

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter


def run_ehx(source):
    source = textwrap.dedent(source).strip()
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    parser = Parser(tokens)
    program = parser.parse()

    interpreter = Interpreter()
    interpreter.run(program)

    return interpreter


class TestEHXLang(unittest.TestCase):

    # -------------------------
    # Variables & Types
    # -------------------------

    def test_integer_variable(self):
        interpreter = run_ehx("let x = 10")
        self.assertEqual(interpreter.variables["x"], 10)

    def test_float_variable(self):
        interpreter = run_ehx("let score = 95.5")
        self.assertEqual(interpreter.variables["score"], 95.5)

    def test_string_variable(self):
        interpreter = run_ehx('let name = "EHX"')
        self.assertEqual(interpreter.variables["name"], "EHX")

    def test_single_quoted_string(self):
        interpreter = run_ehx("let name = 'Ethio Hacker X'")
        self.assertEqual(interpreter.variables["name"], "Ethio Hacker X")

    def test_boolean_true(self):
        interpreter = run_ehx("let active = true")
        self.assertEqual(interpreter.variables["active"], True)

    def test_boolean_false(self):
        interpreter = run_ehx("let active = false")
        self.assertEqual(interpreter.variables["active"], False)

    def test_variable_reference(self):
        interpreter = run_ehx(
            """
            let x = 10
            let y = x
            """
        )
        self.assertEqual(interpreter.variables["y"], 10)

    # -------------------------
    # Arithmetic Operations
    # -------------------------

    def test_addition(self):
        interpreter = run_ehx("let result = 10 + 20")
        self.assertEqual(interpreter.variables["result"], 30)

    def test_subtraction(self):
        interpreter = run_ehx("let result = 20 - 5")
        self.assertEqual(interpreter.variables["result"], 15)

    def test_multiplication(self):
        interpreter = run_ehx("let result = 10 * 5")
        self.assertEqual(interpreter.variables["result"], 50)

    def test_division(self):
        interpreter = run_ehx("let result = 20 / 5")
        self.assertEqual(interpreter.variables["result"], 4)

    def test_string_concatenation(self):
        interpreter = run_ehx('let result = "Ethio " + "Hacker X"')
        self.assertEqual(interpreter.variables["result"], "Ethio Hacker X")

    def test_operator_precedence(self):
        interpreter = run_ehx("let result = 10 + 20 * 2")
        self.assertEqual(interpreter.variables["result"], 50)

    def test_parentheses(self):
        interpreter = run_ehx("let result = (10 + 20) * 2")
        self.assertEqual(interpreter.variables["result"], 60)

    def test_unary_minus(self):
        interpreter = run_ehx("let result = -10")
        self.assertEqual(interpreter.variables["result"], -10)

    def test_unary_parentheses(self):
        interpreter = run_ehx("let result = -(10 + 5)")
        self.assertEqual(interpreter.variables["result"], -15)

    def test_complex_expression(self):
        interpreter = run_ehx(
            """
            let x = 10
            let y = 20
            let result = -(x + y) * 2
            """
        )
        self.assertEqual(interpreter.variables["result"], -60)

    # -------------------------
    # Comparisons & Logic
    # -------------------------

    def test_equal(self):
        interpreter = run_ehx("let result = 10 == 10")
        self.assertTrue(interpreter.variables["result"])

    def test_not_equal(self):
        interpreter = run_ehx("let result = 10 != 20")
        self.assertTrue(interpreter.variables["result"])

    def test_greater(self):
        interpreter = run_ehx("let result = 20 > 10")
        self.assertTrue(interpreter.variables["result"])

    def test_less(self):
        interpreter = run_ehx("let result = 10 < 20")
        self.assertTrue(interpreter.variables["result"])

    def test_greater_equal(self):
        interpreter = run_ehx("let result = 10 >= 10")
        self.assertTrue(interpreter.variables["result"])

    def test_less_equal(self):
        interpreter = run_ehx("let result = 10 <= 20")
        self.assertTrue(interpreter.variables["result"])

    def test_and(self):
        interpreter = run_ehx("let result = true and true")
        self.assertTrue(interpreter.variables["result"])

    def test_or(self):
        interpreter = run_ehx("let result = false or true")
        self.assertTrue(interpreter.variables["result"])

    def test_not(self):
        interpreter = run_ehx("let result = not true")
        self.assertFalse(interpreter.variables["result"])

    def test_logic_precedence(self):
        interpreter = run_ehx("let result = 10 > 5 and 20 > 10")
        self.assertTrue(interpreter.variables["result"])

    def test_parentheses_logic(self):
        interpreter = run_ehx("let result = (10 > 5) and (20 < 30)")
        self.assertTrue(interpreter.variables["result"])

    # -------------------------
    # Comments & Indentation
    # -------------------------

    def test_comments(self):
        interpreter = run_ehx(
            """
            # This is a comment
            let x = 10

            # Another comment
            let y = 20
            """
        )
        self.assertEqual(interpreter.variables["x"], 10)
        self.assertEqual(interpreter.variables["y"], 20)

    # -------------------------
    # Control Flow: when / otherwise
    # -------------------------

    def test_when_branch(self):
        interpreter = run_ehx(
            """
            let status = "pending"
            let age = 20
            when age >= 18:
                let status = "adult"
            otherwise:
                let status = "minor"
            """
        )
        self.assertEqual(interpreter.variables["status"], "adult")

    def test_when_or_when_branch(self):
        interpreter = run_ehx(
            """
            let grade = ""
            let score = 85
            when score >= 90:
                let grade = "A"
            or when score >= 80:
                let grade = "B"
            otherwise:
                let grade = "C"
            """
        )
        self.assertEqual(interpreter.variables["grade"], "B")

    def test_when_otherwise_branch(self):
        interpreter = run_ehx(
            """
            let grade = ""
            let score = 50
            when score >= 90:
                let grade = "A"
            or when score >= 80:
                let grade = "B"
            otherwise:
                let grade = "F"
            """
        )
        self.assertEqual(interpreter.variables["grade"], "F")

    # -------------------------
    # Loops: while & for
    # -------------------------

    def test_while_loop(self):
        interpreter = run_ehx(
            """
            let count = 0
            while count < 5:
                let count = count + 1
            """
        )
        self.assertEqual(interpreter.variables["count"], 5)

    def test_for_range_loop_forward(self):
        interpreter = run_ehx(
            """
            let total = 0
            for i in 1..4:
                let total = total + i
            """
        )
        self.assertEqual(interpreter.variables["total"], 10)

    def test_for_range_loop_backward(self):
        interpreter = run_ehx(
            """
            let total = 0
            for i in 4..1:
                let total = total + i
            """
        )
        self.assertEqual(interpreter.variables["total"], 10)

    def test_nested_control_flow(self):
        interpreter = run_ehx(
            """
            let count = 0
            let active = true
            when active:
                for i in 1..3:
                    let count = count + 1
            """
        )
        self.assertEqual(interpreter.variables["count"], 3)

    # -------------------------
    # Errors
    # -------------------------

    def test_undefined_variable(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "variable 'unknown' is not defined"
        ):
            run_ehx("show(unknown)")

    def test_division_by_zero(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "division by zero"
        ):
            run_ehx("let x = 10 / 0")

    def test_string_number_concatenation(self):
        interpreter = run_ehx(
            """
            let x = 10
            let name = "Port: "
            let result = name + x
            """
        )
        self.assertEqual(interpreter.variables["result"], "Port: 10")

    def test_invalid_subtraction(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "requires numbers"
        ):
            run_ehx(
                """
                let name = "EHX"
                let result = name - "Lang"
                """
            )

    def test_invalid_multiplication(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "requires numbers"
        ):
            run_ehx(
                """
                let name = "EHX"
                let result = name * 5
                """
            )

    def test_invalid_unary_minus(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "'-' requires a number"
        ):
            run_ehx('let result = -"EHX"')

    def test_tabs_error(self):
        with self.assertRaisesRegex(
            SyntaxError,
            "tabs are not allowed"
        ):
            run_ehx("when true:\n\tshow(1)")

    def test_show_without_parentheses_raises_error(self):
        with self.assertRaisesRegex(
            SyntaxError,
            "expected '\\(' after 'show'"
        ):
            run_ehx('show "hello"')

    def test_show_multiple_arguments(self):
        # We can verify it executes without error
        interpreter = run_ehx('show("Port:", 80, true)')
        self.assertIsNotNone(interpreter)

    # -------------------------
    # Phase 2: Functions & Scopes
    # -------------------------

    def test_function_definition_and_call(self):
        interpreter = run_ehx(
            """
            fn greet(name):
                return "Hello " + name

            let msg = greet("EHX")
            """
        )
        self.assertEqual(interpreter.variables["msg"], "Hello EHX")

    def test_function_with_multiple_parameters(self):
        interpreter = run_ehx(
            """
            fn add3(a, b, c):
                return a + b + c

            let result = add3(10, 20, 30)
            """
        )
        self.assertEqual(interpreter.variables["result"], 60)

    def test_function_recursion(self):
        interpreter = run_ehx(
            """
            fn factorial(n):
                when n <= 1:
                    return 1
                return n * factorial(n - 1)

            let result = factorial(5)
            """
        )
        self.assertEqual(interpreter.variables["result"], 120)

    def test_local_scope_does_not_leak(self):
        interpreter = run_ehx(
            """
            let global_var = 100

            fn compute():
                let local_var = 42
                return local_var + global_var

            let total = compute()
            """
        )
        self.assertEqual(interpreter.variables["total"], 142)
        self.assertNotIn("local_var", interpreter.variables)

    def test_function_without_return_returns_none(self):
        interpreter = run_ehx(
            """
            fn no_return():
                let x = 10

            let result = no_return()
            """
        )
        self.assertIsNone(interpreter.variables["result"])

    def test_argument_count_mismatch(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "expects 2 argument\\(s\\), got 1"
        ):
            run_ehx(
                """
                fn add(a, b):
                    return a + b

                add(10)
                """
            )

    def test_return_outside_function(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "'return' outside of a function"
        ):
            run_ehx("return 42")

    def test_calling_non_function(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "'not_a_func' is not a function"
        ):
            run_ehx(
                """
                let not_a_func = 123
                not_a_func()
                """
            )

    # -------------------------
    # Phase 3: Collections & Methods
    # -------------------------

    def test_list_literal_and_indexing(self):
        interpreter = run_ehx(
            """
            let ports = [80, 443, 8080]
            let p0 = ports[0]
            let p_last = ports[-1]
            """
        )
        self.assertEqual(interpreter.variables["ports"], [80, 443, 8080])
        self.assertEqual(interpreter.variables["p0"], 80)
        self.assertEqual(interpreter.variables["p_last"], 8080)

    def test_list_index_assignment(self):
        interpreter = run_ehx(
            """
            let targets = ["192.168.1.1", "10.0.0.1"]
            targets[0] = "192.168.1.254"
            """
        )
        self.assertEqual(interpreter.variables["targets"], ["192.168.1.254", "10.0.0.1"])

    def test_list_out_of_bounds_error(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "list index out of range: 5"
        ):
            run_ehx(
                """
                let arr = [1, 2]
                let x = arr[5]
                """
            )

    def test_list_methods(self):
        interpreter = run_ehx(
            """
            let items = [10]
            items.add(20)
            items.add(30)
            let popped = items.rm()
            let length = items.len()
            let has_20 = items.contains(20)
            let has_99 = items.contains(99)
            """
        )
        self.assertEqual(interpreter.variables["items"], [10, 20])
        self.assertEqual(interpreter.variables["popped"], 30)
        self.assertEqual(interpreter.variables["length"], 2)
        self.assertTrue(interpreter.variables["has_20"])
        self.assertFalse(interpreter.variables["has_99"])

    def test_dict_literal_and_access(self):
        interpreter = run_ehx(
            """
            let server = {"host": "127.0.0.1", "port": 8080, "ssl": false}
            let host = server["host"]
            let port = server["port"]
            server["port"] = 9000
            server["status"] = "online"
            """
        )
        self.assertEqual(interpreter.variables["host"], "127.0.0.1")
        self.assertEqual(interpreter.variables["port"], 8080)
        self.assertEqual(interpreter.variables["server"]["port"], 9000)
        self.assertEqual(interpreter.variables["server"]["status"], "online")

    def test_dict_missing_key_error(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "key 'missing' not found in dictionary"
        ):
            run_ehx(
                """
                let d = {"a": 1}
                let x = d["missing"]
                """
            )

    def test_dict_methods(self):
        interpreter = run_ehx(
            """
            let info = {"os": "linux", "arch": "x64"}
            let has_os = info.has("os")
            let has_ip = info.has("ip")
            let k = info.keys()
            let v = info.values()
            let l = info.len()
            """
        )
        self.assertTrue(interpreter.variables["has_os"])
        self.assertFalse(interpreter.variables["has_ip"])
        self.assertEqual(set(interpreter.variables["k"]), {"os", "arch"})
        self.assertEqual(set(interpreter.variables["v"]), {"linux", "x64"})
        self.assertEqual(interpreter.variables["l"], 2)

    def test_for_in_list(self):
        interpreter = run_ehx(
            """
            let ports = [21, 22, 80]
            let total = 0
            for p in ports:
                total = total + p
            """
        )
        self.assertEqual(interpreter.variables["total"], 123)

    def test_for_in_string(self):
        interpreter = run_ehx(
            """
            let word = "EHX"
            let joined = ""
            for ch in word:
                joined = joined + ch + "-"
            """
        )
        self.assertEqual(interpreter.variables["joined"], "E-H-X-")

    def test_string_methods(self):
        interpreter = run_ehx(
            """
            let raw_ip = "  192.168.1.1  "
            let trimmed = raw_ip.trim()
            let parts = trimmed.split(".")
            let has_sub = trimmed.contains("168")
            let banner = "hello world".upper()
            """
        )
        self.assertEqual(interpreter.variables["trimmed"], "192.168.1.1")
        self.assertEqual(interpreter.variables["parts"], ["192", "168", "1", "1"])
        self.assertTrue(interpreter.variables["has_sub"])
        self.assertEqual(interpreter.variables["banner"], "HELLO WORLD")

    def test_builtins_len_type_str(self):
        interpreter = run_ehx(
            """
            let l_list = len([1, 2, 3])
            let l_str = len("hello")
            let t_num = type(123)
            let t_lst = type([1])
            let t_dic = type({"a": 1})
            let s_val = str(456)
            """
        )
        self.assertEqual(interpreter.variables["l_list"], 3)
        self.assertEqual(interpreter.variables["l_str"], 5)
        self.assertEqual(interpreter.variables["t_num"], "int")
        self.assertEqual(interpreter.variables["t_lst"], "list")
        self.assertEqual(interpreter.variables["t_dic"], "dict")
        self.assertEqual(interpreter.variables["s_val"], "456")

    def test_list_concatenation(self):
        interpreter = run_ehx(
            """
            let a = [1, 2]
            let b = [3, 4]
            let combined = a + b
            """
        )
        self.assertEqual(interpreter.variables["combined"], [1, 2, 3, 4])

    # -------------------------
    # Phase 4: System & Automation
    # -------------------------

    def test_file_io_operations(self):
        test_file = "scratch_test_phase4.txt"
        try:
            interpreter = run_ehx(
                f"""
                let created = file_write("{test_file}", "Line 1\\nLine 2")
                let exists = file_exists("{test_file}")
                let appended = file_append("{test_file}", "\\nLine 3")
                let content = file_read("{test_file}")
                let lines = file_lines("{test_file}")
                """
            )
            self.assertTrue(interpreter.variables["created"])
            self.assertTrue(interpreter.variables["exists"])
            self.assertTrue(interpreter.variables["appended"])
            self.assertIn("Line 1", interpreter.variables["content"])
            self.assertIn("Line 3", interpreter.variables["content"])
            self.assertEqual(interpreter.variables["lines"], ["Line 1", "Line 2", "Line 3"])
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_exec_process(self):
        interpreter = run_ehx(
            """
            let res = exec("python -c \\"print(100 + 200)\\"")
            let exit_code = res["code"]
            let out = res["stdout"].trim()
            """
        )
        self.assertEqual(interpreter.variables["exit_code"], 0)
        self.assertEqual(interpreter.variables["out"], "300")

    def test_time_and_sleep(self):
        interpreter = run_ehx(
            """
            let t1 = timestamp()
            sleep(0.01)
            let t2 = time_now()
            """
        )
        self.assertIsInstance(interpreter.variables["t1"], int)
        self.assertIsInstance(interpreter.variables["t2"], float)
        self.assertGreaterEqual(interpreter.variables["t2"], interpreter.variables["t1"])

    def test_env_lookup(self):
        os.environ["EHX_TEST_SECRET"] = "EHX_SUPER_TOKEN_99"
        try:
            interpreter = run_ehx(
                """
                let secret = env("EHX_TEST_SECRET")
                let fallback = env("NON_EXISTENT_VAR", "default_val")
                """
            )
            self.assertEqual(interpreter.variables["secret"], "EHX_SUPER_TOKEN_99")
            self.assertEqual(interpreter.variables["fallback"], "default_val")
        finally:
            os.environ.pop("EHX_TEST_SECRET", None)

    def test_regex_operations(self):
        interpreter = run_ehx(
            """
            let is_ip = regex_match("^\\\\d+\\\\.\\\\d+\\\\.\\\\d+\\\\.\\\\d+$", "192.168.1.1")
            let is_not_ip = regex_match("^\\\\d+\\\\.\\\\d+\\\\.\\\\d+\\\\.\\\\d+$", "invalid.ip")
            let nums = regex_find("\\\\d+", "port 80 and port 443 and 8080")
            let sanitized = regex_replace("admin", "root", "user: admin")
            """
        )
        self.assertTrue(interpreter.variables["is_ip"])
        self.assertFalse(interpreter.variables["is_not_ip"])
        self.assertEqual(interpreter.variables["nums"], ["80", "443", "8080"])
        self.assertEqual(interpreter.variables["sanitized"], "user: root")

    # -------------------------
    # Phase 5: Universal Standard Library & Modules
    # -------------------------

    def test_math_primitives(self):
        interpreter = run_ehx(
            """
            let s = math_sqrt(16)
            let p = math_pow(2, 8)
            let f = math_floor(4.9)
            let c = math_ceil(4.1)
            let r = math_round(4.6)
            let a = math_abs(-42)
            let ri = math_randint(10, 20)
            let rf = math_random(0, 1)
            """
        )
        self.assertEqual(interpreter.variables["s"], 4.0)
        self.assertEqual(interpreter.variables["p"], 256.0)
        self.assertEqual(interpreter.variables["f"], 4)
        self.assertEqual(interpreter.variables["c"], 5)
        self.assertEqual(interpreter.variables["r"], 5)
        self.assertEqual(interpreter.variables["a"], 42)
        self.assertTrue(10 <= interpreter.variables["ri"] <= 20)
        self.assertTrue(0.0 <= interpreter.variables["rf"] <= 1.0)

    def test_crypto_and_encoding(self):
        interpreter = run_ehx(
            """
            let h_md5 = md5("hello")
            let h_sha = sha256("hello")
            let b_enc = base64_encode("EHX Lang")
            let b_dec = base64_decode(b_enc)
            """
        )
        self.assertEqual(interpreter.variables["h_md5"], "5d41402abc4b2a76b9719d911017c592")
        self.assertEqual(interpreter.variables["h_sha"], "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824")
        self.assertEqual(interpreter.variables["b_dec"], "EHX Lang")

    def test_tcp_socket_echo(self):
        import socket
        import threading

        # Start a local echo server
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind(("127.0.0.1", 0))
        server_sock.listen(1)
        port = server_sock.getsockname()[1]

        def echo_server():
            conn, _ = server_sock.accept()
            data = conn.recv(1024)
            conn.sendall(data)
            conn.close()
            server_sock.close()

        th = threading.Thread(target=echo_server, daemon=True)
        th.start()

        interpreter = run_ehx(
            f"""
            let sock = tcp_connect("127.0.0.1", {port})
            sock.send("EHX PING")
            let reply = sock.recv(1024)
            sock.close()
            """
        )
        self.assertEqual(interpreter.variables["reply"], "EHX PING")

    def test_http_get_mock(self):
        # We can test http_get failure handling gracefully or valid URL if available,
        # but in test we test invalid url raises or custom local server
        import http.server
        import threading

        class QuickHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"OK from EHX test server")

            def log_message(self, format, *args):
                pass

        httpd = http.server.HTTPServer(("127.0.0.1", 0), QuickHandler)
        port = httpd.server_port

        th = threading.Thread(target=httpd.handle_request, daemon=True)
        th.start()

        try:
            interpreter = run_ehx(
                f"""
                let res = http_get("http://127.0.0.1:{port}/")
                let status = res["status"]
                let body = res["body"]
                """
            )
            self.assertEqual(interpreter.variables["status"], 200)
            self.assertIn("OK from EHX test server", interpreter.variables["body"])
        finally:
            httpd.server_close()

    def test_import_module(self):
        mod_file = "test_math_module.ehx"
        try:
            with open(mod_file, "w", encoding="utf-8") as f:
                f.write(textwrap.dedent(
                    """
                    fn square(x):
                        return x * x

                    let MODULE_VERSION = 100
                    """
                ).strip())

            interpreter = run_ehx(
                f"""
                import "{mod_file}"
                let result = square(9)
                let ver = MODULE_VERSION
                """
            )
            self.assertEqual(interpreter.variables["result"], 81)
            self.assertEqual(interpreter.variables["ver"], 100)
        finally:
            if os.path.exists(mod_file):
                os.remove(mod_file)


    # -------------------------
    # Phase 6: Error Handling & Concurrency
    # -------------------------

    def test_try_catch_handles_error(self):
        interpreter = run_ehx(
            """
            let recovered = false
            let caught_err = ""
            try:
                let x = 10 / 0
            catch err:
                recovered = true
                caught_err = err
            """
        )
        self.assertTrue(interpreter.variables["recovered"])
        self.assertEqual(interpreter.variables["caught_err"], "division by zero")

    def test_try_catch_without_variable(self):
        interpreter = run_ehx(
            """
            let status = "initial"
            try:
                panic("Critical failure simulated")
            catch:
                status = "handled"
            """
        )
        self.assertEqual(interpreter.variables["status"], "handled")

    def test_loop_break(self):
        interpreter = run_ehx(
            """
            let found = 0
            for i in 1..10:
                when i == 4:
                    found = i
                    break
            """
        )
        self.assertEqual(interpreter.variables["found"], 4)

    def test_loop_continue(self):
        interpreter = run_ehx(
            """
            let odds = []
            for i in 1..6:
                when i == 2 or i == 4 or i == 6:
                    continue
                odds.add(i)
            """
        )
        self.assertEqual(interpreter.variables["odds"], [1, 3, 5])

    def test_concurrency_spawn_and_join(self):
        interpreter = run_ehx(
            """
            fn compute_heavy(n):
                sleep(0.01)
                return n * 10

            let task1 = spawn(compute_heavy, 5)
            let task2 = spawn(compute_heavy, 8)

            let res1 = task1.join()
            let res2 = task2.join()
            let is_d = task1.is_done()
            """
        )
        self.assertEqual(interpreter.variables["res1"], 50)
        self.assertEqual(interpreter.variables["res2"], 80)
        self.assertTrue(interpreter.variables["is_d"])

    # -------------------------
    # Enhanced Ergonomics (None, %, Compound Assignments, Range, Format)
    # -------------------------

    def test_none_literal(self):
        interpreter = run_ehx(
            """
            let empty_val = none
            let is_empty = (empty_val == none)
            """
        )
        self.assertIsNone(interpreter.variables["empty_val"])
        self.assertTrue(interpreter.variables["is_empty"])

    def test_modulo_operator(self):
        interpreter = run_ehx(
            """
            let rem1 = 10 % 3
            let rem2 = 14 % 7
            """
        )
        self.assertEqual(interpreter.variables["rem1"], 1)
        self.assertEqual(interpreter.variables["rem2"], 0)

    def test_compound_assignments(self):
        interpreter = run_ehx(
            """
            let x = 10
            x += 5
            x -= 3
            x *= 2
            x /= 4

            let arr = [100]
            arr[0] += 50
            """
        )
        self.assertEqual(interpreter.variables["x"], 6.0)
        self.assertEqual(interpreter.variables["arr"], [150])

    def test_range_in_for_loop(self):
        interpreter = run_ehx(
            """
            let nums = []
            for i in range(5):
                nums.add(i)

            let evens = []
            for j in range(2, 10, 2):
                evens.add(j)
            """
        )
        self.assertEqual(interpreter.variables["nums"], [0, 1, 2, 3, 4])
        self.assertEqual(interpreter.variables["evens"], [2, 4, 6, 8])

    def test_format_function(self):
        interpreter = run_ehx(
            """
            let msg = format("Host: {}, Port: {}", "127.0.0.1", 8080)
            """
        )
        self.assertEqual(interpreter.variables["msg"], "Host: 127.0.0.1, Port: 8080")

    def test_enhanced_string_and_list_methods(self):
        interpreter = run_ehx(
            """
            let s = "hello world"
            let rep = s.replace("world", "EHX")
            let sw = s.starts_with("hello")
            let ew = s.ends_with("world")
            let sl = s.slice(0, 5)

            let lst = [1, 2, 3, 4]
            let rev = lst.reverse()
            let sub = lst.slice(0, 2)
            """
        )
        self.assertEqual(interpreter.variables["rep"], "hello EHX")
        self.assertTrue(interpreter.variables["sw"])
        self.assertTrue(interpreter.variables["ew"])
        self.assertEqual(interpreter.variables["sl"], "hello")
        self.assertEqual(interpreter.variables["rev"], [4, 3, 2, 1])
        self.assertEqual(interpreter.variables["sub"], [4, 3])


    def test_list_functional_methods(self):
        interpreter = run_ehx(
            """
            fn double(x):
                return x * 2

            fn is_even(n):
                return n % 2 == 0

            let nums = [1, 2, 3, 4, 5]
            let doubled = nums.map(double)
            let evens = nums.filter(is_even)

            let collected = []
            fn collect(item):
                collected.add(item * 10)

            nums.for_each(collect)
            """
        )
        self.assertEqual(interpreter.variables["doubled"], [2, 4, 6, 8, 10])
        self.assertEqual(interpreter.variables["evens"], [2, 4])
        self.assertEqual(interpreter.variables["collected"], [10, 20, 30, 40, 50])

    def test_js_style_builtins(self):
        interpreter = run_ehx(
            """
            let p1 = parse_int("42")
            let p2 = parse_float("3.14")
            let nan1 = is_nan("hello")
            let nan2 = is_nan("123")
            let nan3 = is_nan(99)
            """
        )
        self.assertEqual(interpreter.variables["p1"], 42)
        self.assertAlmostEqual(interpreter.variables["p2"], 3.14)
        self.assertTrue(interpreter.variables["nan1"])
        self.assertFalse(interpreter.variables["nan2"])
        self.assertFalse(interpreter.variables["nan3"])


    def test_plain_english_builtins(self):
        test_file = "test_plain_temp.txt"
        try:
            interpreter = run_ehx(
                """
                let filename = "test_plain_temp.txt"
                save(filename, "First Line\\n")
                add_to(filename, "Second Line\\n")
                let content = read(filename)
                let all_lines = lines(filename)
                let exists = has_file(filename)
                let b1 = bool(1)
                let b2 = bool(0)
                let b3 = bool("")
                let b4 = bool("hello")
                """
            )
            self.assertTrue(interpreter.variables["exists"])
            self.assertEqual(interpreter.variables["content"], "First Line\nSecond Line\n")
            self.assertEqual(interpreter.variables["all_lines"], ["First Line", "Second Line"])
            self.assertTrue(interpreter.variables["b1"])
            self.assertFalse(interpreter.variables["b2"])
            self.assertFalse(interpreter.variables["b3"])
            self.assertTrue(interpreter.variables["b4"])
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)


    def test_security_and_automation_features(self):
        # 1. Hashes & Custom Pure EHXLang Wordlist Generation
        interpreter = run_ehx(
            """
            let s1 = sha1("admin")
            let s512 = sha512("admin")

            # Users can write their own wordlist generator in pure EHXLang!
            let chars = ["a", "b"]
            let words = []
            for c1 in chars:
                for c2 in chars:
                    words.add(c1 + c2)
            """
        )
        self.assertEqual(interpreter.variables["s1"], "d033e22ae348aeb5660fc2140aec35850c4da997")
        self.assertTrue(len(interpreter.variables["s512"]) == 128)
        self.assertEqual(interpreter.variables["words"], ["aa", "ab", "ba", "bb"])

        # 2. JSON Serialization & Deserialization
        interpreter_json = run_ehx(
            """
            let orig = {"target": "127.0.0.1", "port": 80, "active": true}
            let j_str = to_json(orig)
            let back = from_json(j_str)
            let tgt = back["target"]
            let p = back["port"]
            let act = back["active"]
            """
        )
        self.assertEqual(interpreter_json.variables["tgt"], "127.0.0.1")
        self.assertEqual(interpreter_json.variables["p"], 80)
        self.assertTrue(interpreter_json.variables["act"])

        # 3. Zip Archiving & Extraction
        temp_src = "test_src.txt"
        temp_zip = "test_archive.zip"
        temp_out = "test_extracted"
        try:
            with open(temp_src, "w", encoding="utf-8") as f:
                f.write("Secret Payload for Testing")

            run_ehx(
                f"""
                zip_pack("{temp_src}", "{temp_zip}")
                zip_unpack("{temp_zip}", "{temp_out}")
                """
            )
            extracted_file = os.path.join(temp_out, temp_src)
            self.assertTrue(os.path.exists(extracted_file))
            with open(extracted_file, "r", encoding="utf-8") as f:
                self.assertEqual(f.read(), "Secret Payload for Testing")
        finally:
            if os.path.exists(temp_src):
                os.remove(temp_src)
            if os.path.exists(temp_zip):
                os.remove(temp_zip)
            if os.path.exists(temp_out):
                import shutil
                shutil.rmtree(temp_out)


    def test_advanced_arithmetic_operators(self):
        interpreter = run_ehx(
            """
            let p1 = 2 ** 3
            let p2 = 3 ** 2 ** 2  # right-associative: 3 ** 4 = 81
            let f1 = 17 // 5      # 3
            let f2 = 20 // 4      # 5
            let m1 = 17 % 5       # 2
            let x = 10
            x %= 4                 # 2
            """
        )
        self.assertEqual(interpreter.variables["p1"], 8)
        self.assertEqual(interpreter.variables["p2"], 81)
        self.assertEqual(interpreter.variables["f1"], 3)
        self.assertEqual(interpreter.variables["f2"], 5)
        self.assertEqual(interpreter.variables["m1"], 2)
        self.assertEqual(interpreter.variables["x"], 2)

    def test_list_string_enhancements_and_min_max(self):
        interpreter = run_ehx(
            """
            # List fuse and order
            let words = ["Ethio", "Hacker", "X"]
            let fused = words.fuse("-")
            let nums = [45, 12, 89, 3]
            nums.order()

            # String find and count
            let s = "programming in ehx lang is cool"
            let pos = s.find("ehx")
            let cnt = s.count("o")

            # min and max builtins
            let m_val = min(10, 5, 20, 2)
            let mx_val = max(10, 5, 20, 2)
            let m_list = min([50, 100, 25])
            let mx_list = max([50, 100, 25])
            """
        )
        self.assertEqual(interpreter.variables["fused"], "Ethio-Hacker-X")
        self.assertEqual(interpreter.variables["nums"], [3, 12, 45, 89])
        self.assertEqual(interpreter.variables["pos"], 15)
        self.assertEqual(interpreter.variables["cnt"], 3)
        self.assertEqual(interpreter.variables["m_val"], 2)
        self.assertEqual(interpreter.variables["mx_val"], 20)
        self.assertEqual(interpreter.variables["m_list"], 25)
        self.assertEqual(interpreter.variables["mx_list"], 100)

    def test_fstring_interpolation(self):
        interpreter = run_ehx(
            """
            set name = "Ethio Hacker X"
            set version = 1.0
            set port = 8080
            set msg = f"Hello {name}, welcome to version {version} on port {port}!"
            set calc = f"Calculation: 2 ** 4 = {2 ** 4}"
            set raw_bracket = f"Escaped: {{literal}} and var={port}"
            """
        )
        self.assertEqual(interpreter.variables["msg"], "Hello Ethio Hacker X, welcome to version 1.0 on port 8080!")
        self.assertEqual(interpreter.variables["calc"], "Calculation: 2 ** 4 = 16")
        self.assertEqual(interpreter.variables["raw_bracket"], "Escaped: {literal} and var=8080")

    def test_unique_syntax_and_vocabulary(self):
        interpreter = run_ehx(
            """
            # 1. 'set' variable declaration
            set host = "127.0.0.1"
            set ports = [443, 80, 8080]

            # 2. Array .add(), .rm(), .order(), and .fuse()
            ports.add(22)
            let dropped = ports.rm()
            ports.order()
            let fused_ports = ports.fuse(":")

            # 3. 'kind' type inspection
            let host_kind = kind(host)
            let ports_kind = kind(ports)

            # 4. 'lowest', 'highest', 'low', 'high'
            let min_port = lowest(ports)
            let max_port = highest(ports)
            let low_val = low(50, 10, 80)
            let high_val = high(50, 10, 80)

            # 5. 'pause' alias for sleep/wait
            pause(0.01)
            """
        )
        self.assertEqual(interpreter.variables["host"], "127.0.0.1")
        self.assertEqual(interpreter.variables["dropped"], 22)
        self.assertEqual(interpreter.variables["ports"], [80, 443, 8080])
        self.assertEqual(interpreter.variables["fused_ports"], "80:443:8080")
        self.assertEqual(interpreter.variables["host_kind"], "string")
        self.assertEqual(interpreter.variables["ports_kind"], "list")
        self.assertEqual(interpreter.variables["min_port"], 80)
        self.assertEqual(interpreter.variables["max_port"], 8080)
        self.assertEqual(interpreter.variables["low_val"], 10)
        self.assertEqual(interpreter.variables["high_val"], 80)


if __name__ == "__main__":
    unittest.main()