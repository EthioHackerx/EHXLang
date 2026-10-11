import os
import sys
import subprocess
import time
import re
import math
import random
import hashlib
import base64
import socket
import urllib.request
import urllib.parse
import urllib.error
import threading
import queue
import json
import zipfile


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


class Environment:
    def __init__(self, parent=None):
        self.values = {}
        self.parent = parent

    def get(self, name):
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise RuntimeError(f"EHX Error: variable '{name}' is not defined")

    def define(self, name, value):
        self.values[name] = value

    def assign(self, name, value):
        if name in self.values:
            self.values[name] = value
            return
        if self.parent is not None and self.parent.has(name):
            self.parent.assign(name, value)
            return
        self.values[name] = value

    def has(self, name):
        if name in self.values:
            return True
        if self.parent is not None:
            return self.parent.has(name)
        return False


class EHXFunction:
    def __init__(self, name, parameters, body, closure_env):
        self.name = name
        self.parameters = parameters
        self.body = body
        self.closure_env = closure_env

    def __repr__(self):
        return f"<fn {self.name}>"


class EHXSocket:
    def __init__(self, sock):
        self.sock = sock
        self.closed = False

    def close(self):
        if not self.closed:
            try:
                self.sock.close()
            except Exception:
                pass
            self.closed = True

    def __del__(self):
        self.close()

    def send(self, data):
        if self.closed:
            raise RuntimeError("EHX Error: cannot send on closed socket")
        if isinstance(data, str):
            data = data.encode("utf-8")
        elif not isinstance(data, (bytes, bytearray)):
            data = str(data).encode("utf-8")
        try:
            return self.sock.send(data)
        except Exception as e:
            raise RuntimeError(f"EHX Error: socket send failed: {e}")

    def recv(self, bufsize=1024):
        if self.closed:
            raise RuntimeError("EHX Error: cannot recv on closed socket")
        if not isinstance(bufsize, int) or isinstance(bufsize, bool) or bufsize <= 0:
            raise RuntimeError("EHX Error: socket recv buffer size must be a positive integer")
        try:
            raw = self.sock.recv(bufsize)
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                return raw.decode("latin-1", errors="replace")
        except Exception as e:
            raise RuntimeError(f"EHX Error: socket recv failed: {e}")

    def __repr__(self):
        return f"<socket {'closed' if self.closed else 'open'}>"


class EHXTask:
    def __init__(self, target_func, args, interpreter_instance):
        self.target_func = target_func
        self.args = args
        self.interpreter_instance = interpreter_instance
        self.result = None
        self.error = None
        self.completed = False

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        try:
            # Create an execution environment isolated to this task's thread
            task_interp = Interpreter()
            task_interp.global_env = self.interpreter_instance.global_env
            self.result = task_interp.invoke_callable(
                self.target_func,
                [{"type": "literal", "value": a} for a in self.args],
                getattr(self.target_func, "name", "<task>")
            )
        except Exception as e:
            self.error = str(e)
        finally:
            self.completed = True

    def join(self, timeout=None):
        self.thread.join(timeout=timeout)
        if self.error:
            raise RuntimeError(f"EHX Error in background task: {self.error}")
        return self.result

    def is_done(self):
        return self.completed

    def __repr__(self):
        return f"<task {'done' if self.completed else 'running'}>"


class EHXBuiltin:
    def __init__(self, name, func, min_args=0, max_args=None):
        self.name = name
        self.func = func
        self.min_args = min_args
        # If max_args is None, defaults to min_args. If max_args == -1, unlimited.
        if max_args == -1:
            self.max_args = None
        else:
            self.max_args = max_args if max_args is not None else min_args

    def call(self, args):
        count = len(args)
        if count < self.min_args or (self.max_args is not None and count > self.max_args):
            if self.max_args is None:
                raise RuntimeError(
                    f"EHX Error: builtin function '{self.name}' expects at least {self.min_args} argument(s), got {count}"
                )
            if self.min_args == self.max_args:
                raise RuntimeError(
                    f"EHX Error: builtin function '{self.name}' expects {self.min_args} argument(s), got {count}"
                )
            raise RuntimeError(
                f"EHX Error: builtin function '{self.name}' expects between {self.min_args} and {self.max_args} argument(s), got {count}"
            )
        return self.func(*args)

    def __repr__(self):
        return f"<builtin fn {self.name}>"


class Interpreter:

    def __init__(self):
        self.global_env = Environment()
        self.current_env = self.global_env
        self.imported_modules = set()
        self._register_builtins()

    def _register_builtins(self):
        def _builtin_len(obj):
            if isinstance(obj, (list, dict, str)):
                return len(obj)
            raise RuntimeError(f"EHX Error: len() not supported for type '{type(obj).__name__}'")

        def _builtin_push(lst, item):
            if not isinstance(lst, list):
                raise RuntimeError("EHX Error: push() requires a list as first argument")
            lst.append(item)
            return lst

        def _builtin_pop(lst):
            if not isinstance(lst, list):
                raise RuntimeError("EHX Error: pop() requires a list as first argument")
            if len(lst) == 0:
                raise RuntimeError("EHX Error: pop() from empty list")
            return lst.pop()

        def _builtin_keys(d):
            if not isinstance(d, dict):
                raise RuntimeError("EHX Error: keys() requires a dict")
            return list(d.keys())

        def _builtin_values(d):
            if not isinstance(d, dict):
                raise RuntimeError("EHX Error: values() requires a dict")
            return list(d.values())

        def _builtin_type(val):
            if val is None:
                return "none"
            if isinstance(val, bool):
                return "bool"
            if isinstance(val, int):
                return "int"
            if isinstance(val, float):
                return "float"
            if isinstance(val, str):
                return "string"
            if isinstance(val, list):
                return "list"
            if isinstance(val, dict):
                return "dict"
            if isinstance(val, (EHXFunction, EHXBuiltin)):
                return "function"
            return type(val).__name__

        def _builtin_str(val):
            return self.to_string(val)

        def _builtin_int(val):
            try:
                return int(val)
            except Exception:
                raise RuntimeError(f"EHX Error: cannot convert '{val}' to int")

        def _builtin_float(val):
            try:
                return float(val)
            except Exception:
                raise RuntimeError(f"EHX Error: cannot convert '{val}' to float")

        def _builtin_bool(val):
            if val is None:
                return False
            if isinstance(val, bool):
                return val
            if isinstance(val, (int, float)):
                return val != 0
            if isinstance(val, (str, list, dict)):
                return len(val) > 0
            return True

        # --- Phase 4: System & Automation Builtins ---

        def _builtin_file_read(filepath):
            if not isinstance(filepath, str):
                raise RuntimeError("EHX Error: file_read() expects a string filepath")
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                raise RuntimeError(f"EHX Error: file_read failed for '{filepath}': {e}")

        def _builtin_file_write(filepath, content):
            if not isinstance(filepath, str):
                raise RuntimeError("EHX Error: file_write() expects a string filepath")
            text = content if isinstance(content, str) else self.to_string(content)
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(text)
                return True
            except Exception as e:
                raise RuntimeError(f"EHX Error: file_write failed for '{filepath}': {e}")

        def _builtin_file_append(filepath, content):
            if not isinstance(filepath, str):
                raise RuntimeError("EHX Error: file_append() expects a string filepath")
            text = content if isinstance(content, str) else self.to_string(content)
            try:
                with open(filepath, "a", encoding="utf-8") as f:
                    f.write(text)
                return True
            except Exception as e:
                raise RuntimeError(f"EHX Error: file_append failed for '{filepath}': {e}")

        def _builtin_file_exists(filepath):
            if not isinstance(filepath, str):
                raise RuntimeError("EHX Error: file_exists() expects a string filepath")
            return os.path.exists(filepath)

        def _builtin_file_lines(filepath):
            if not isinstance(filepath, str):
                raise RuntimeError("EHX Error: file_lines() expects a string filepath")
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    lines = [line.rstrip("\r\n") for line in f]
                return lines
            except Exception as e:
                raise RuntimeError(f"EHX Error: file_lines failed for '{filepath}': {e}")

        def _builtin_exec(cmd):
            if not isinstance(cmd, str):
                raise RuntimeError("EHX Error: exec() expects a string command")
            try:
                proc = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                return {
                    "code": proc.returncode,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                }
            except Exception as e:
                raise RuntimeError(f"EHX Error: exec failed for '{cmd}': {e}")

        def _builtin_sleep(secs):
            if not self.is_number(secs):
                raise RuntimeError("EHX Error: sleep() expects a number of seconds")
            time.sleep(secs)
            return None

        def _builtin_timestamp():
            return int(time.time())

        def _builtin_time_now():
            return float(time.time())

        def _builtin_env(key, default_val=None):
            if not isinstance(key, str):
                raise RuntimeError("EHX Error: env() expects a string key")
            return os.environ.get(key, default_val)

        def _builtin_regex_match(pattern, text):
            if not isinstance(pattern, str) or not isinstance(text, str):
                raise RuntimeError("EHX Error: regex_match() expects pattern and text strings")
            return bool(re.search(pattern, text))

        def _builtin_regex_find(pattern, text):
            if not isinstance(pattern, str) or not isinstance(text, str):
                raise RuntimeError("EHX Error: regex_find() expects pattern and text strings")
            matches = re.findall(pattern, text)
            if matches and isinstance(matches[0], tuple):
                return [list(m) for m in matches]
            return matches

        def _builtin_regex_replace(pattern, repl, text):
            if not isinstance(pattern, str) or not isinstance(repl, str) or not isinstance(text, str):
                raise RuntimeError("EHX Error: regex_replace() expects (pattern, replacement, text) strings")
            return re.sub(pattern, repl, text)

        # --- Phase 5: Universal Standard Library Builtins ---

        # Networking
        def _builtin_tcp_connect(host, port, timeout_sec=3.0):
            if not isinstance(host, str):
                raise RuntimeError("EHX Error: tcp_connect() host must be a string")
            if not isinstance(port, int) or isinstance(port, bool):
                raise RuntimeError("EHX Error: tcp_connect() port must be an integer")
            if not self.is_number(timeout_sec):
                raise RuntimeError("EHX Error: tcp_connect() timeout must be a number")

            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(float(timeout_sec))
                s.connect((host, port))
                return EHXSocket(s)
            except Exception as e:
                raise RuntimeError(f"EHX Error: tcp_connect failed for {host}:{port}: {e}")

        def _builtin_http_get(url, timeout_sec=5.0):
            if not isinstance(url, str):
                raise RuntimeError("EHX Error: http_get() url must be a string")
            if not self.is_number(timeout_sec):
                raise RuntimeError("EHX Error: http_get() timeout must be a number")

            req = urllib.request.Request(
                url,
                headers={"User-Agent": "EHXLang/1.0.0"}
            )
            try:
                with urllib.request.urlopen(req, timeout=float(timeout_sec)) as response:
                    body_bytes = response.read()
                    try:
                        body_text = body_bytes.decode("utf-8")
                    except UnicodeDecodeError:
                        body_text = body_bytes.decode("latin-1", errors="replace")
                    return {
                        "status": response.status,
                        "body": body_text,
                        "headers": dict(response.headers),
                    }
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
                return {
                    "status": e.code,
                    "body": err_body,
                    "headers": dict(e.headers) if hasattr(e, "headers") else {},
                }
            except Exception as e:
                raise RuntimeError(f"EHX Error: http_get failed for '{url}': {e}")

        def _builtin_http_post(url, body="", headers=None, timeout_sec=5.0):
            if not isinstance(url, str):
                raise RuntimeError("EHX Error: http_post() url must be a string")
            if not self.is_number(timeout_sec):
                raise RuntimeError("EHX Error: http_post() timeout must be a number")

            post_headers = {"User-Agent": "EHXLang/1.0.0"}
            if isinstance(headers, dict):
                for k, v in headers.items():
                    post_headers[str(k)] = str(v)

            if isinstance(body, str):
                encoded_body = body.encode("utf-8")
            elif isinstance(body, dict):
                encoded_body = urllib.parse.urlencode(body).encode("utf-8")
                if "Content-Type" not in post_headers:
                    post_headers["Content-Type"] = "application/x-www-form-urlencoded"
            else:
                encoded_body = self.to_string(body).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=encoded_body,
                headers=post_headers,
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=float(timeout_sec)) as response:
                    resp_bytes = response.read()
                    try:
                        resp_text = resp_bytes.decode("utf-8")
                    except UnicodeDecodeError:
                        resp_text = resp_bytes.decode("latin-1", errors="replace")
                    return {
                        "status": response.status,
                        "body": resp_text,
                        "headers": dict(response.headers),
                    }
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
                return {
                    "status": e.code,
                    "body": err_body,
                    "headers": dict(e.headers) if hasattr(e, "headers") else {},
                }
            except Exception as e:
                raise RuntimeError(f"EHX Error: http_post failed for '{url}': {e}")

        # Crypto, Security & Encoding
        def _builtin_md5(data):
            text = data if isinstance(data, str) else self.to_string(data)
            return hashlib.md5(text.encode("utf-8")).hexdigest()

        def _builtin_sha1(data):
            text = data if isinstance(data, str) else self.to_string(data)
            return hashlib.sha1(text.encode("utf-8")).hexdigest()

        def _builtin_sha256(data):
            text = data if isinstance(data, str) else self.to_string(data)
            return hashlib.sha256(text.encode("utf-8")).hexdigest()

        def _builtin_sha512(data):
            text = data if isinstance(data, str) else self.to_string(data)
            return hashlib.sha512(text.encode("utf-8")).hexdigest()

        def _builtin_base64_encode(data):
            text = data if isinstance(data, str) else self.to_string(data)
            return base64.b64encode(text.encode("utf-8")).decode("utf-8")

        def _builtin_base64_decode(data):
            if not isinstance(data, str):
                raise RuntimeError("EHX Error: base64_decode() expects a string")
            try:
                return base64.b64decode(data.encode("utf-8")).decode("utf-8")
            except Exception as e:
                raise RuntimeError(f"EHX Error: base64_decode failed: {e}")

        # JSON Serialization & Deserialization
        def _builtin_to_json(val, pretty=False):
            try:
                if pretty:
                    return json.dumps(val, indent=2)
                return json.dumps(val)
            except Exception as e:
                raise RuntimeError(f"EHX Error: to_json failed: {e}")

        def _builtin_from_json(json_str):
            if not isinstance(json_str, str):
                raise RuntimeError("EHX Error: from_json() expects a JSON string")
            try:
                return json.loads(json_str)
            except Exception as e:
                raise RuntimeError(f"EHX Error: from_json failed to parse JSON: {e}")

        # Zip Archiving & Extraction (Security & Automation)
        def _builtin_zip_pack(source_path, zip_path):
            if not isinstance(source_path, str) or not isinstance(zip_path, str):
                raise RuntimeError("EHX Error: zip_pack() expects source_path and zip_path strings")
            try:
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    if os.path.isfile(source_path):
                        zf.write(source_path, os.path.basename(source_path))
                    elif os.path.isdir(source_path):
                        for root, _, files in os.walk(source_path):
                            for file in files:
                                full_file = os.path.join(root, file)
                                arcname = os.path.relpath(full_file, source_path)
                                zf.write(full_file, arcname)
                    else:
                        raise RuntimeError(f"EHX Error: source '{source_path}' does not exist")
                return True
            except Exception as e:
                raise RuntimeError(f"EHX Error: zip_pack failed: {e}")

        def _builtin_zip_unpack(zip_path, target_dir):
            if not isinstance(zip_path, str) or not isinstance(target_dir, str):
                raise RuntimeError("EHX Error: zip_unpack() expects zip_path and target_dir strings")
            try:
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(target_dir)
                return True
            except Exception as e:
                raise RuntimeError(f"EHX Error: zip_unpack failed: {e}")

        # Math Primitives
        def _builtin_math_sqrt(x):
            if not self.is_number(x) or x < 0:
                raise RuntimeError("EHX Error: math_sqrt() expects a non-negative number")
            return math.sqrt(x)

        def _builtin_math_pow(base_val, exp_val):
            if not self.is_number(base_val) or not self.is_number(exp_val):
                raise RuntimeError("EHX Error: math_pow() expects numbers")
            return math.pow(base_val, exp_val)

        def _builtin_math_floor(x):
            if not self.is_number(x):
                raise RuntimeError("EHX Error: math_floor() expects a number")
            return math.floor(x)

        def _builtin_math_ceil(x):
            if not self.is_number(x):
                raise RuntimeError("EHX Error: math_ceil() expects a number")
            return math.ceil(x)

        def _builtin_math_round(x):
            if not self.is_number(x):
                raise RuntimeError("EHX Error: math_round() expects a number")
            return round(x)

        def _builtin_math_abs(x):
            if not self.is_number(x):
                raise RuntimeError("EHX Error: math_abs() expects a number")
            return abs(x)

        def _builtin_min(*args):
            if len(args) == 0:
                raise RuntimeError("EHX Error: min() expects at least 1 argument")
            if len(args) == 1 and isinstance(args[0], list):
                if len(args[0]) == 0:
                    raise RuntimeError("EHX Error: min() arg is an empty sequence")
                return min(args[0])
            return min(args)

        def _builtin_max(*args):
            if len(args) == 0:
                raise RuntimeError("EHX Error: max() expects at least 1 argument")
            if len(args) == 1 and isinstance(args[0], list):
                if len(args[0]) == 0:
                    raise RuntimeError("EHX Error: max() arg is an empty sequence")
                return max(args[0])
            return max(args)

        def _builtin_math_random(low=0.0, high=1.0):
            if not self.is_number(low) or not self.is_number(high):
                raise RuntimeError("EHX Error: math_random() expects numbers")
            if low > high:
                low, high = high, low
            return random.uniform(low, high)

        def _builtin_math_randint(low, high):
            if not isinstance(low, int) or isinstance(low, bool) or not isinstance(high, int) or isinstance(high, bool):
                raise RuntimeError("EHX Error: math_randint() expects integers")
            if low > high:
                low, high = high, low
            return random.randint(low, high)

        def _builtin_spawn(func, *args):
            if not isinstance(func, (EHXFunction, EHXBuiltin)):
                raise RuntimeError("EHX Error: spawn() first argument must be a function")
            return EHXTask(func, list(args), self)

        def _builtin_panic(msg):
            text = msg if isinstance(msg, str) else self.to_string(msg)
            raise RuntimeError(f"EHX Error: {text}")

        def _builtin_range(start_or_stop, stop=None, step=1):
            if not isinstance(start_or_stop, int) or isinstance(start_or_stop, bool):
                raise RuntimeError("EHX Error: range() arguments must be integers")

            if stop is None:
                start = 0
                end = start_or_stop
            else:
                if not isinstance(stop, int) or isinstance(stop, bool):
                    raise RuntimeError("EHX Error: range() arguments must be integers")
                start = start_or_stop
                end = stop

            if not isinstance(step, int) or isinstance(step, bool) or step == 0:
                raise RuntimeError("EHX Error: range() step must be a non-zero integer")

            return list(range(start, end, step))

        def _builtin_ask(prompt=""):
            p_str = self.to_string(prompt)
            try:
                return input(p_str)
            except EOFError:
                return ""

        def _builtin_args():
            # Returns command-line arguments passed after the script filename
            if len(sys.argv) > 2:
                return list(sys.argv[2:])
            return []

        def _builtin_format(template, *args):
            if not isinstance(template, str):
                raise RuntimeError("EHX Error: format() first argument must be a string template")

            # Replace sequential {} with str(arg)
            parts = template.split("{}")
            if len(parts) == 1:
                return template

            res = []
            arg_idx = 0
            for i, p in enumerate(parts):
                res.append(p)
                if i < len(parts) - 1:
                    if arg_idx < len(args):
                        res.append(self.to_string(args[arg_idx]))
                        arg_idx += 1
                    else:
                        res.append("{}")
            return "".join(res)

        def _builtin_show_err(*args):
            text = " ".join(self.to_string(a) for a in args)
            sys.stderr.write(text + "\n")
            sys.stderr.flush()
            return None

        def _builtin_is_nan(val):
            if val is None or isinstance(val, bool):
                return True
            if isinstance(val, (int, float)):
                return math.isnan(val)
            if isinstance(val, str):
                try:
                    float(val)
                    return False
                except ValueError:
                    return True
            return True

        def _builtin_set_timeout(callback, delay_ms):
            if not isinstance(callback, (EHXFunction, EHXBuiltin)):
                raise RuntimeError("EHX Error: set_timeout() first argument must be a function")
            if not self.is_number(delay_ms) or delay_ms < 0:
                raise RuntimeError("EHX Error: set_timeout() delay must be a non-negative number")

            delay_sec = float(delay_ms) / 1000.0

            def _timer_worker():
                time.sleep(delay_sec)
                try:
                    timer_interp = Interpreter()
                    timer_interp.global_env = self.global_env
                    timer_interp.call_callable(callback, [])
                except Exception:
                    pass

            th = threading.Thread(target=_timer_worker, daemon=True)
            th.start()
            return None

        def _builtin_set_interval(callback, interval_ms):
            if not isinstance(callback, (EHXFunction, EHXBuiltin)):
                raise RuntimeError("EHX Error: set_interval() first argument must be a function")
            if not self.is_number(interval_ms) or interval_ms <= 0:
                raise RuntimeError("EHX Error: set_interval() interval must be a positive number")

            interval_sec = float(interval_ms) / 1000.0

            def _interval_worker():
                while True:
                    time.sleep(interval_sec)
                    try:
                        timer_interp = Interpreter()
                        timer_interp.global_env = self.global_env
                        timer_interp.call_callable(callback, [])
                    except Exception:
                        break

            th = threading.Thread(target=_interval_worker, daemon=True)
            th.start()
            return None

        builtins = [
            EHXBuiltin("len", _builtin_len, 1, 1),
            EHXBuiltin("push", _builtin_push, 2, 2),
            EHXBuiltin("pop", _builtin_pop, 1, 1),
            EHXBuiltin("keys", _builtin_keys, 1, 1),
            EHXBuiltin("values", _builtin_values, 1, 1),
            EHXBuiltin("kind", _builtin_type, 1, 1),
            EHXBuiltin("type", _builtin_type, 1, 1),
            EHXBuiltin("str", _builtin_str, 1, 1),
            EHXBuiltin("int", _builtin_int, 1, 1),
            EHXBuiltin("float", _builtin_float, 1, 1),
            EHXBuiltin("bool", _builtin_bool, 1, 1),
            EHXBuiltin("parse_int", _builtin_int, 1, 1),
            EHXBuiltin("parse_float", _builtin_float, 1, 1),
            EHXBuiltin("is_nan", _builtin_is_nan, 1, 1),
            EHXBuiltin("show_err", _builtin_show_err, 0, -1),
            # General Ergonomics & Automation
            EHXBuiltin("range", _builtin_range, 1, 3),
            EHXBuiltin("ask", _builtin_ask, 0, 1),
            EHXBuiltin("args", _builtin_args, 0, 0),
            EHXBuiltin("format", _builtin_format, 1, -1),
            EHXBuiltin("set_timeout", _builtin_set_timeout, 2, 2),
            EHXBuiltin("set_interval", _builtin_set_interval, 2, 2),
            # System, File & Automation (Plain English primary + aliases)
            EHXBuiltin("save", _builtin_file_write, 2, 2),
            EHXBuiltin("read", _builtin_file_read, 1, 1),
            EHXBuiltin("add_to", _builtin_file_append, 2, 2),
            EHXBuiltin("has_file", _builtin_file_exists, 1, 1),
            EHXBuiltin("lines", _builtin_file_lines, 1, 1),
            EHXBuiltin("pause", _builtin_sleep, 1, 1),
            EHXBuiltin("wait", _builtin_sleep, 1, 1),
            EHXBuiltin("file_read", _builtin_file_read, 1, 1),
            EHXBuiltin("file_write", _builtin_file_write, 2, 2),
            EHXBuiltin("file_append", _builtin_file_append, 2, 2),
            EHXBuiltin("file_exists", _builtin_file_exists, 1, 1),
            EHXBuiltin("file_lines", _builtin_file_lines, 1, 1),
            EHXBuiltin("exec", _builtin_exec, 1, 1),
            EHXBuiltin("sleep", _builtin_sleep, 1, 1),
            EHXBuiltin("timestamp", _builtin_timestamp, 0, 0),
            EHXBuiltin("time_now", _builtin_time_now, 0, 0),
            EHXBuiltin("env", _builtin_env, 1, 2),
            EHXBuiltin("regex_match", _builtin_regex_match, 2, 2),
            EHXBuiltin("regex_find", _builtin_regex_find, 2, 2),
            EHXBuiltin("regex_replace", _builtin_regex_replace, 3, 3),
            # Phase 5: Universal Standard Library
            # Networking
            EHXBuiltin("tcp_connect", _builtin_tcp_connect, 2, 3),
            EHXBuiltin("http_get", _builtin_http_get, 1, 2),
            EHXBuiltin("http_post", _builtin_http_post, 1, 4),
            # Crypto, Security & Encoding
            EHXBuiltin("md5", _builtin_md5, 1, 1),
            EHXBuiltin("sha1", _builtin_sha1, 1, 1),
            EHXBuiltin("sha256", _builtin_sha256, 1, 1),
            EHXBuiltin("sha512", _builtin_sha512, 1, 1),
            EHXBuiltin("base64_encode", _builtin_base64_encode, 1, 1),
            EHXBuiltin("base64_decode", _builtin_base64_decode, 1, 1),
            EHXBuiltin("to_json", _builtin_to_json, 1, 2),
            EHXBuiltin("from_json", _builtin_from_json, 1, 1),
            EHXBuiltin("zip_pack", _builtin_zip_pack, 2, 2),
            EHXBuiltin("zip_unpack", _builtin_zip_unpack, 2, 2),
            # Math
            EHXBuiltin("math_sqrt", _builtin_math_sqrt, 1, 1),
            EHXBuiltin("math_pow", _builtin_math_pow, 2, 2),
            EHXBuiltin("math_floor", _builtin_math_floor, 1, 1),
            EHXBuiltin("math_ceil", _builtin_math_ceil, 1, 1),
            EHXBuiltin("math_round", _builtin_math_round, 1, 1),
            EHXBuiltin("math_abs", _builtin_math_abs, 1, 1),
            EHXBuiltin("lowest", _builtin_min, 1, -1),
            EHXBuiltin("highest", _builtin_max, 1, -1),
            EHXBuiltin("low", _builtin_min, 1, -1),
            EHXBuiltin("high", _builtin_max, 1, -1),
            EHXBuiltin("min", _builtin_min, 1, -1),
            EHXBuiltin("max", _builtin_max, 1, -1),
            EHXBuiltin("math_random", _builtin_math_random, 0, 2),
            EHXBuiltin("math_randint", _builtin_math_randint, 2, 2),
            # Phase 6: Concurrency & Error Raising
            EHXBuiltin("spawn", _builtin_spawn, 1, -1),
            EHXBuiltin("panic", _builtin_panic, 1, 1),
        ]
        for b in builtins:
            self.global_env.define(b.name, b)

    @property
    def variables(self):
        return self.global_env.values

    def run(self, program):
        try:
            for statement in program["statements"]:
                self.execute(statement)
        except ReturnSignal:
            raise RuntimeError("EHX Error: 'return' outside of a function")
        except BreakSignal:
            raise RuntimeError("EHX Error: 'break' outside of a loop")
        except ContinueSignal:
            raise RuntimeError("EHX Error: 'continue' outside of a loop")

    # -------------------------
    # Statements
    # -------------------------

    def execute(self, statement):

        statement_type = statement["type"]

        if statement_type == "let":
            value = self.evaluate(
                statement["value"]
            )

            self.current_env.define(
                statement["name"],
                value,
            )

        elif statement_type == "assign":
            value = self.evaluate(statement["value"])
            self.current_env.assign(statement["name"], value)

        elif statement_type == "index_assign":
            target = self.evaluate(statement["target"])
            index = self.evaluate(statement["index"])
            value = self.evaluate(statement["value"])

            if isinstance(target, list):
                if not isinstance(index, int) or isinstance(index, bool):
                    raise RuntimeError("EHX Error: list index must be an integer")
                if index < -len(target) or index >= len(target):
                    raise RuntimeError(f"EHX Error: list index out of range: {index}")
                target[index] = value
            elif isinstance(target, dict):
                target[index] = value
            else:
                raise RuntimeError(
                    f"EHX Error: indexing assignment not supported for type '{type(target).__name__}'"
                )

        elif statement_type == "show":
            values = [
                self.to_string(self.evaluate(arg))
                for arg in statement["arguments"]
            ]
            print(" ".join(values))

        elif statement_type == "when":
            self.execute_when(statement)

        elif statement_type == "while":
            self.execute_while(statement)

        elif statement_type in ("for", "for_range"):
            self.execute_for_range(statement)

        elif statement_type == "for_in":
            self.execute_for_in(statement)

        elif statement_type == "fn":
            fn_obj = EHXFunction(
                name=statement["name"],
                parameters=statement["parameters"],
                body=statement["body"],
                closure_env=self.current_env,
            )
            self.current_env.define(
                statement["name"],
                fn_obj,
            )

        elif statement_type == "return":
            val = None
            if statement["value"] is not None:
                val = self.evaluate(statement["value"])
            raise ReturnSignal(val)

        elif statement_type == "import":
            self.execute_import(statement)

        elif statement_type == "try":
            self.execute_try(statement)

        elif statement_type == "break":
            raise BreakSignal()

        elif statement_type == "continue":
            raise ContinueSignal()

        elif statement_type == "expression_statement":
            self.evaluate(statement["expression"])

        else:
            raise RuntimeError(
                f"EHX Error: unknown statement "
                f"'{statement_type}'"
            )

    def execute_import(self, statement):
        rel_path = statement["path"]
        if not rel_path.endswith(".ehx"):
            rel_path += ".ehx"

        # Resolve path
        abs_path = os.path.abspath(rel_path)
        if not os.path.isfile(abs_path):
            raise RuntimeError(f"EHX Error: cannot import '{statement['path']}': file not found")

        # Avoid redundant execution of identical module
        if abs_path in self.imported_modules:
            return
        self.imported_modules.add(abs_path)

        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                module_source = f.read()
        except Exception as e:
            raise RuntimeError(f"EHX Error: failed to read imported file '{abs_path}': {e}")

        # Local import inside interpreter to avoid circular dependencies
        from lexer import Lexer
        from parser import Parser

        tokens = Lexer(module_source).tokenize()
        program = Parser(tokens).parse()

        # Execute imported code into the global environment
        prev_env = self.current_env
        self.current_env = self.global_env
        try:
            for stmt in program["statements"]:
                self.execute(stmt)
        finally:
            self.current_env = prev_env

    def execute_try(self, statement):
        try:
            self.execute_block(statement["try_body"])
        except (ReturnSignal, BreakSignal, ContinueSignal):
            # Control flow signals must propagate through try/catch blocks
            raise
        except Exception as e:
            # Clean error message if starts with EHX Error
            err_msg = str(e)
            if err_msg.startswith("EHX Error: "):
                err_msg = err_msg[len("EHX Error: "):]

            # Bind error variable if specified in catch
            if statement["error_var"]:
                self.current_env.define(statement["error_var"], err_msg)

            self.execute_block(statement["catch_body"])

    def execute_block(self, statements):
        for statement in statements:
            self.execute(statement)

    def execute_when(self, statement):

        for branch in statement["branches"]:

            condition = self.evaluate(
                branch["condition"]
            )

            self.require_boolean(
                condition,
                "when condition"
            )

            if condition:
                self.execute_block(
                    branch["body"]
                )

                return

        if statement["otherwise"] is not None:
            self.execute_block(
                statement["otherwise"]
            )

    def execute_while(self, statement):

        while True:

            condition = self.evaluate(
                statement["condition"]
            )

            self.require_boolean(
                condition,
                "while condition"
            )

            if not condition:
                break

            try:
                self.execute_block(
                    statement["body"]
                )
            except BreakSignal:
                break
            except ContinueSignal:
                continue

    def execute_for_range(self, statement):

        start = self.evaluate(
            statement["start"]
        )

        end = self.evaluate(
            statement["end"]
        )

        if not isinstance(start, int) or isinstance(start, bool):
            raise RuntimeError(
                "EHX Error: for range start "
                "must be an integer"
            )

        if not isinstance(end, int) or isinstance(end, bool):
            raise RuntimeError(
                "EHX Error: for range end "
                "must be an integer"
            )

        step = 1 if end >= start else -1

        current = start

        while (
            current <= end
            if step == 1
            else current >= end
        ):
            self.current_env.define(
                statement["variable"],
                current,
            )

            try:
                self.execute_block(
                    statement["body"]
                )
            except BreakSignal:
                break
            except ContinueSignal:
                pass

            current += step

    def execute_for_in(self, statement):
        iterable = self.evaluate(statement["iterable"])

        if isinstance(iterable, list):
            items = iterable
        elif isinstance(iterable, str):
            items = list(iterable)
        elif isinstance(iterable, dict):
            items = list(iterable.keys())
        else:
            raise RuntimeError(
                f"EHX Error: cannot iterate over type '{type(iterable).__name__}'"
            )

        var_name = statement["variable"]
        for item in items:
            self.current_env.define(var_name, item)
            try:
                self.execute_block(statement["body"])
            except BreakSignal:
                break
            except ContinueSignal:
                continue

    # -------------------------
    # Expressions
    # -------------------------

    def evaluate(self, expression):

        expression_type = expression["type"]

        if expression_type == "literal":
            return expression["value"]

        if expression_type == "fstring":
            result_chunks = []
            for part in expression["parts"]:
                if part["type"] == "literal":
                    result_chunks.append(part["value"])
                else:
                    val = self.evaluate(part["expression"])
                    result_chunks.append(self.to_string(val))
            return "".join(result_chunks)

        if expression_type == "variable":
            return self.current_env.get(expression["name"])

        if expression_type == "list":
            return [self.evaluate(item) for item in expression["items"]]

        if expression_type == "dict":
            d = {}
            for entry in expression["entries"]:
                k = self.evaluate(entry["key"])
                v = self.evaluate(entry["value"])
                try:
                    hash(k)
                except TypeError:
                    raise RuntimeError(f"EHX Error: unhashable dictionary key of type '{type(k).__name__}'")
                d[k] = v
            return d

        if expression_type == "index":
            target = self.evaluate(expression["target"])
            index = self.evaluate(expression["index"])
            return self.evaluate_index(target, index)

        if expression_type == "method_call":
            return self.evaluate_method_call(expression)

        if expression_type == "member":
            target = self.evaluate(expression["target"])
            name = expression["name"]
            if isinstance(target, dict) and name in target:
                return target[name]
            raise RuntimeError(f"EHX Error: member '{name}' does not exist on {type(target).__name__}")

        if expression_type == "call":
            return self.evaluate_call_named(expression["name"], expression["arguments"])

        if expression_type == "call_expr":
            callee = self.evaluate(expression["callee"])
            return self.invoke_callable(callee, expression["arguments"], "<anonymous>")

        if expression_type == "unary":
            value = self.evaluate(
                expression["value"]
            )

            operator = expression["operator"]

            if operator == "-":

                if not self.is_number(value):
                    raise RuntimeError(
                        "EHX Error: '-' requires "
                        "a number"
                    )

                return -value

            if operator == "not":

                self.require_boolean(
                    value,
                    "'not'"
                )

                return not value

        if expression_type == "binary":

            left = self.evaluate(
                expression["left"]
            )

            operator = expression["operator"]

            # short circuit and / or
            if operator == "and":
                self.require_boolean(
                    left,
                    "'and'"
                )

                if not left:
                    return False

                right = self.evaluate(
                    expression["right"]
                )

                self.require_boolean(
                    right,
                    "'and'"
                )

                return right

            if operator == "or":
                self.require_boolean(
                    left,
                    "'or'"
                )

                if left:
                    return True

                right = self.evaluate(
                    expression["right"]
                )

                self.require_boolean(
                    right,
                    "'or'"
                )

                return right

            right = self.evaluate(
                expression["right"]
            )

            if operator == "==":
                return left == right

            if operator == "!=":
                return left != right

            if operator in (
                "<",
                "<=",
                ">",
                ">=",
            ):

                if not (
                    self.is_number(left)
                    and self.is_number(right)
                ):
                    raise RuntimeError(
                        f"EHX Error: '{operator}' "
                        f"requires numbers"
                    )

                if operator == "<":
                    return left < right

                if operator == "<=":
                    return left <= right

                if operator == ">":
                    return left > right

                if operator == ">=":
                    return left >= right

            if operator == "+":
                if (
                    self.is_number(left)
                    and self.is_number(right)
                ):
                    return left + right

                if isinstance(left, str) or isinstance(right, str):
                    return self.to_string(left) + self.to_string(right)

                if isinstance(left, list) and isinstance(right, list):
                    return left + right

                raise RuntimeError(
                    "EHX Error: '+' requires "
                    "numbers, strings, or lists"
                )

            if not (
                self.is_number(left)
                and self.is_number(right)
            ):
                raise RuntimeError(
                    f"EHX Error: '{operator}' "
                    f"requires numbers"
                )

            if operator == "-":
                return left - right

            if operator == "*":
                return left * right

            if operator == "**":
                return left ** right

            if operator == "/":

                if right == 0:
                    raise RuntimeError(
                        "EHX Error: division by zero"
                    )

                return left / right

            if operator == "//":
                if right == 0:
                    raise RuntimeError(
                        "EHX Error: integer division by zero"
                    )
                return left // right

            if operator == "%":
                if right == 0:
                    raise RuntimeError(
                        "EHX Error: modulo by zero"
                    )
                return left % right

        raise RuntimeError(
            f"EHX Error: unknown expression type '{expression_type}'"
        )

    def evaluate_index(self, target, index):
        if isinstance(target, list):
            if not isinstance(index, int) or isinstance(index, bool):
                raise RuntimeError("EHX Error: list index must be an integer")
            if index < -len(target) or index >= len(target):
                raise RuntimeError(f"EHX Error: list index out of range: {index}")
            return target[index]

        if isinstance(target, str):
            if not isinstance(index, int) or isinstance(index, bool):
                raise RuntimeError("EHX Error: string index must be an integer")
            if index < -len(target) or index >= len(target):
                raise RuntimeError(f"EHX Error: string index out of range: {index}")
            return target[index]

        if isinstance(target, dict):
            if index not in target:
                raise RuntimeError(f"EHX Error: key '{self.to_string(index)}' not found in dictionary")
            return target[index]

        raise RuntimeError(f"EHX Error: indexing not supported for type '{type(target).__name__}'")

    def evaluate_method_call(self, expression):
        target = self.evaluate(expression["target"])
        method_name = expression["method"]
        args = [self.evaluate(a) for a in expression["arguments"]]

        # List methods
        if isinstance(target, list):
            if method_name == "add":
                if len(args) != 1:
                    raise RuntimeError(f"EHX Error: list.add() takes 1 argument, got {len(args)}")
                target.append(args[0])
                return target

            if method_name == "rm":
                if len(args) != 0:
                    raise RuntimeError(f"EHX Error: list.rm() takes 0 arguments, got {len(args)}")
                if len(target) == 0:
                    raise RuntimeError("EHX Error: rm() from empty list")
                return target.pop()

            if method_name == "len":
                if len(args) != 0:
                    raise RuntimeError(f"EHX Error: list.len() takes 0 arguments, got {len(args)}")
                return len(target)

            if method_name == "clear":
                if len(args) != 0:
                    raise RuntimeError(f"EHX Error: list.clear() takes 0 arguments, got {len(args)}")
                target.clear()
                return None

            if method_name == "contains":
                if len(args) != 1:
                    raise RuntimeError(f"EHX Error: list.contains() takes 1 argument, got {len(args)}")
                return args[0] in target

            if method_name == "reverse":
                if len(args) != 0:
                    raise RuntimeError(f"EHX Error: list.reverse() takes 0 arguments, got {len(args)}")
                target.reverse()
                return target

            if method_name == "map":
                if len(args) != 1:
                    raise RuntimeError(f"EHX Error: list.map() takes 1 argument (callback), got {len(args)}")
                callback = args[0]
                if not isinstance(callback, (EHXFunction, EHXBuiltin)):
                    raise RuntimeError("EHX Error: list.map() argument must be a function")
                return [self.call_callable(callback, [item]) for item in target]

            if method_name == "filter":
                if len(args) != 1:
                    raise RuntimeError(f"EHX Error: list.filter() takes 1 argument (predicate), got {len(args)}")
                predicate = args[0]
                if not isinstance(predicate, (EHXFunction, EHXBuiltin)):
                    raise RuntimeError("EHX Error: list.filter() argument must be a function")
                result = []
                for item in target:
                    cond = self.call_callable(predicate, [item])
                    if not isinstance(cond, bool):
                        raise RuntimeError("EHX Error: list.filter() callback must return a boolean")
                    if cond:
                        result.append(item)
                return result

            if method_name == "for_each":
                if len(args) != 1:
                    raise RuntimeError(f"EHX Error: list.for_each() takes 1 argument (callback), got {len(args)}")
                callback = args[0]
                if not isinstance(callback, (EHXFunction, EHXBuiltin)):
                    raise RuntimeError("EHX Error: list.for_each() argument must be a function")
                for item in target:
                    self.call_callable(callback, [item])
                return None

            if method_name == "fuse":
                sep = ""
                if len(args) == 1:
                    sep = self.to_string(args[0])
                elif len(args) > 1:
                    raise RuntimeError(f"EHX Error: list.fuse() takes at most 1 argument, got {len(args)}")
                return sep.join(self.to_string(x) for x in target)

            if method_name == "order":
                if len(args) != 0:
                    raise RuntimeError(f"EHX Error: list.order() takes 0 arguments, got {len(args)}")
                try:
                    target.sort()
                except TypeError:
                    # In case of mixed types, sort by string representation
                    target.sort(key=self.to_string)
                return target

            if method_name == "slice":
                if len(args) == 1:
                    return target[args[0]:]
                elif len(args) == 2:
                    return target[args[0]:args[1]]
                elif len(args) == 3:
                    return target[args[0]:args[1]:args[2]]
                raise RuntimeError(f"EHX Error: list.slice() takes 1 to 3 arguments, got {len(args)}")

            raise RuntimeError(f"EHX Error: list has no method '{method_name}'")

        # Dict methods
        if isinstance(target, dict):
            if method_name == "keys":
                if len(args) != 0:
                    raise RuntimeError(f"EHX Error: dict.keys() takes 0 arguments, got {len(args)}")
                return list(target.keys())

            if method_name == "values":
                if len(args) != 0:
                    raise RuntimeError(f"EHX Error: dict.values() takes 0 arguments, got {len(args)}")
                return list(target.values())

            if method_name == "len":
                if len(args) != 0:
                    raise RuntimeError(f"EHX Error: dict.len() takes 0 arguments, got {len(args)}")
                return len(target)

            if method_name == "has":
                if len(args) != 1:
                    raise RuntimeError(f"EHX Error: dict.has() takes 1 argument, got {len(args)}")
                return args[0] in target

            if method_name == "clear":
                if len(args) != 0:
                    raise RuntimeError(f"EHX Error: dict.clear() takes 0 arguments, got {len(args)}")
                target.clear()
                return None

            raise RuntimeError(f"EHX Error: dict has no method '{method_name}'")

        # String methods
        if isinstance(target, str):
            if method_name == "len":
                if len(args) != 0:
                    raise RuntimeError(f"EHX Error: string.len() takes 0 arguments, got {len(args)}")
                return len(target)

            if method_name == "upper":
                if len(args) != 0:
                    raise RuntimeError(f"EHX Error: string.upper() takes 0 arguments, got {len(args)}")
                return target.upper()

            if method_name == "lower":
                if len(args) != 0:
                    raise RuntimeError(f"EHX Error: string.lower() takes 0 arguments, got {len(args)}")
                return target.lower()

            if method_name == "trim":
                if len(args) != 0:
                    raise RuntimeError(f"EHX Error: string.trim() takes 0 arguments, got {len(args)}")
                return target.strip()

            if method_name == "split":
                sep = " "
                if len(args) == 1:
                    sep = args[0]
                    if not isinstance(sep, str):
                        raise RuntimeError("EHX Error: split separator must be a string")
                elif len(args) > 1:
                    raise RuntimeError(f"EHX Error: string.split() takes at most 1 argument, got {len(args)}")
                return target.split(sep)

            if method_name == "contains":
                if len(args) != 1:
                    raise RuntimeError(f"EHX Error: string.contains() takes 1 argument, got {len(args)}")
                if not isinstance(args[0], str):
                    raise RuntimeError("EHX Error: string.contains() argument must be a string")
                return args[0] in target

            if method_name == "replace":
                if len(args) != 2:
                    raise RuntimeError(f"EHX Error: string.replace() takes 2 arguments, got {len(args)}")
                if not isinstance(args[0], str) or not isinstance(args[1], str):
                    raise RuntimeError("EHX Error: string.replace() arguments must be strings")
                return target.replace(args[0], args[1])

            if method_name == "starts_with":
                if len(args) != 1:
                    raise RuntimeError(f"EHX Error: string.starts_with() takes 1 argument, got {len(args)}")
                if not isinstance(args[0], str):
                    raise RuntimeError("EHX Error: string.starts_with() argument must be a string")
                return target.startswith(args[0])

            if method_name == "ends_with":
                if len(args) != 1:
                    raise RuntimeError(f"EHX Error: string.ends_with() takes 1 argument, got {len(args)}")
                if not isinstance(args[0], str):
                    raise RuntimeError("EHX Error: string.ends_with() argument must be a string")
                return target.endswith(args[0])

            if method_name == "find":
                if len(args) != 1:
                    raise RuntimeError(f"EHX Error: string.find() takes 1 argument, got {len(args)}")
                if not isinstance(args[0], str):
                    raise RuntimeError("EHX Error: string.find() argument must be a string")
                return target.find(args[0])

            if method_name == "count":
                if len(args) != 1:
                    raise RuntimeError(f"EHX Error: string.count() takes 1 argument, got {len(args)}")
                if not isinstance(args[0], str):
                    raise RuntimeError("EHX Error: string.count() argument must be a string")
                return target.count(args[0])

            if method_name == "slice":
                if len(args) == 1:
                    return target[args[0]:]
                elif len(args) == 2:
                    return target[args[0]:args[1]]
                elif len(args) == 3:
                    return target[args[0]:args[1]:args[2]]
                raise RuntimeError(f"EHX Error: string.slice() takes 1 to 3 arguments, got {len(args)}")

            raise RuntimeError(f"EHX Error: string has no method '{method_name}'")

        # Socket methods
        if isinstance(target, EHXSocket):
            if method_name == "send":
                if len(args) != 1:
                    raise RuntimeError(f"EHX Error: socket.send() takes 1 argument, got {len(args)}")
                return target.send(args[0])

            if method_name == "recv":
                if len(args) == 0:
                    return target.recv()
                elif len(args) == 1:
                    return target.recv(args[0])
                else:
                    raise RuntimeError(f"EHX Error: socket.recv() takes at most 1 argument, got {len(args)}")

            if method_name == "close":
                if len(args) != 0:
                    raise RuntimeError(f"EHX Error: socket.close() takes 0 arguments, got {len(args)}")
                target.close()
                return None

            raise RuntimeError(f"EHX Error: socket has no method '{method_name}'")

        # Task concurrency methods
        if isinstance(target, EHXTask):
            if method_name == "join":
                timeout = None
                if len(args) == 1:
                    if not self.is_number(args[0]):
                        raise RuntimeError("EHX Error: task.join() timeout must be a number")
                    timeout = float(args[0])
                elif len(args) > 1:
                    raise RuntimeError(f"EHX Error: task.join() takes at most 1 argument, got {len(args)}")
                return target.join(timeout=timeout)

            if method_name == "is_done":
                if len(args) != 0:
                    raise RuntimeError(f"EHX Error: task.is_done() takes 0 arguments, got {len(args)}")
                return target.is_done()

            raise RuntimeError(f"EHX Error: task has no method '{method_name}'")

        raise RuntimeError(f"EHX Error: method calls not supported on type '{type(target).__name__}'")

    def evaluate_call_named(self, name, arg_exprs):
        callee = self.current_env.get(name)
        return self.invoke_callable(callee, arg_exprs, name)

    def invoke_callable(self, callee, arg_exprs, name="<function>"):
        if isinstance(callee, EHXBuiltin):
            args = [self.evaluate(arg) for arg in arg_exprs]
            return callee.call(args)

        if not isinstance(callee, EHXFunction):
            raise RuntimeError(f"EHX Error: '{name}' is not a function")

        expected_count = len(callee.parameters)
        received_count = len(arg_exprs)

        if received_count != expected_count:
            raise RuntimeError(
                f"EHX Error: function '{callee.name}' expects {expected_count} "
                f"argument(s), got {received_count}"
            )

        args = [
            self.evaluate(arg)
            for arg in arg_exprs
        ]

        local_env = Environment(parent=callee.closure_env)

        for param_name, arg_val in zip(callee.parameters, args):
            local_env.define(param_name, arg_val)

        previous_env = self.current_env
        self.current_env = local_env

        try:
            self.execute_block(callee.body)
            return None

        except ReturnSignal as ret:
            return ret.value

        finally:
            self.current_env = previous_env

    def call_callable(self, callee, arg_values, name="<function>"):
        if isinstance(callee, EHXBuiltin):
            return callee.call(arg_values)

        if not isinstance(callee, EHXFunction):
            raise RuntimeError(f"EHX Error: '{name}' is not a function")

        expected_count = len(callee.parameters)
        received_count = len(arg_values)

        if received_count != expected_count:
            raise RuntimeError(
                f"EHX Error: function '{callee.name}' expects {expected_count} "
                f"argument(s), got {received_count}"
            )

        local_env = Environment(parent=callee.closure_env)
        for param_name, arg_val in zip(callee.parameters, arg_values):
            local_env.define(param_name, arg_val)

        previous_env = self.current_env
        self.current_env = local_env

        try:
            self.execute_block(callee.body)
            return None
        except ReturnSignal as ret:
            return ret.value
        finally:
            self.current_env = previous_env

    # -------------------------
    # Helpers
    # -------------------------

    def to_representation(self, value):
        if isinstance(value, str):
            escaped = value.replace('"', '\\"')
            return f'"{escaped}"'
        return self.to_string(value)

    def to_string(self, value):
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "none"
        if isinstance(value, (EHXFunction, EHXBuiltin, EHXSocket, EHXTask)):
            return repr(value)
        if isinstance(value, list):
            items_str = ", ".join(self.to_representation(x) for x in value)
            return f"[{items_str}]"
        if isinstance(value, dict):
            entries_str = ", ".join(
                f"{self.to_representation(k)}: {self.to_representation(v)}"
                for k, v in value.items()
            )
            return f"{{{entries_str}}}"
        return str(value)

    @staticmethod
    def is_number(value):
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
        )

    @staticmethod
    def require_boolean(value, context):

        if not isinstance(value, bool):
            raise RuntimeError(
                f"EHX Error: {context} "
                f"must be a boolean"
            )