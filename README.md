# EHXLang (v1.0.0)

```
███████╗██╗  ██╗██╗  ██╗██╗      █████╗ ███╗   ██╗ ██████╗ 
██╔════╝██║  ██║╚██╗██╔╝██║     ██╔══██╗████╗  ██║██╔════╝ 
█████╗  ███████║ ╚███╔╝ ██║     ███████║██╔██╗ ██║██║  ███╗
██╔══╝  ██╔══██║ ██╔██╗ ██║     ██╔══██║██║╚██╗██║██║   ██║
███████╗██║  ██║██╔╝ ██╗███████╗██║  ██║██║ ╚████║╚██████╔╝
╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ 
```

> **A Modern, Human-Readable, General-Purpose Programming Language for Everyone.**  
> Designed and Developed by **Yonatan Muluken ( ETHIO HACKER X )**.

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/EthioHackerX)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/EthioHackerX)

The interpreter engine is engineered in Python to parse, analyze, and execute EHXLang code seamlessly across all operating systems.

---

## Official Book & Learning Guide (PDF)

Download the complete official programming tutorial handbook (61-Page Comprehensive Edition):
- **Official PDF Book (61 Pages):** [EHXLang_Complete_Programming_Book.pdf](./EHXLang_Complete_Programming_Book.pdf)

---

## Official Community & Channels

Connect with the author and join the official community:
- **Telegram Community:** [@EthioHackerX](https://t.me/EthioHackerX)
- **TikTok Channel:** [@ethio_hacker_x](https://www.tiktok.com/@ethio_hacker_x)
- **YouTube Tutorials:** [@EthioHackerX](https://www.youtube.com/@EthioHackerX)
- **GitHub Repository:** [https://github.com/EthioHackerX](https://github.com/EthioHackerX)

---

## Core Features & Language Signature

EHXLang replaces complex syntax and academic jargon with clear, active plain-English instructions.

| Operational Task | EHXLang Signature | Benefit |
|:---|:---|:---|
| **Declare Variable** | `set x = 10` | Active instruction keyword |
| **Write to File** | `save("file.txt", "Data")` | 1 clean function call without manual handles |
| **Read from File** | `set content = read("file.txt")` | Clean and direct without file-leak risks |
| **Append to File** | `add_to("file.txt", "Log\n")` | Natural plain English |
| **Check File Exists** | `when has_file("conf.json"):` | Direct condition check |
| **Read File Lines** | `set list = lines("words.txt")` | Directly loads file lines into an array |
| **Display Output** | `show(...)` | Punchy and visual standard output |
| **Ask User Input** | `set user = ask("Name: ")` | Interactive, readable user input |
| **Conditional Branching** | `when ... or when ... otherwise` | Reads like natural spoken English |
| **Import Module** | `load "math_lib.ehx"` | Distinct, clean module loading |
| **Pause Execution** | `pause(2)` | Direct execution delay |
| **Spawn Thread** | `set t = spawn(my_worker)` | Native background concurrency |
| **Type Inspection** | `kind(x)` | Clean type examination (`"string"`, `"int"`, etc.) |
| **Array Append** | `ports.add(8080)` | Minimalist, single-purpose method |
| **Array Remove Last** | `set dropped = ports.rm()` | Dedicated element removal |
| **Array Sort** | `ports.order()` | Clean in-place ordering |
| **Array Join** | `ports.fuse(" \| ")` | Signature string join method |
| **String Interpolation** | `f"Host: {host}:{port}"` | Modern embedded variable and math expressions |

---

## Language Feature Tour

### 1. Variables, F-Strings & Mathematics
```python
set user = "Yonatan"
set target = "192.168.1.50"
set port = 8080

# Clean string interpolation
show(f"Connecting to {target}:{port} for {user}...")

# Math operations: exponentiation, integer floor division, modulo
show(f"2 ** 8 = {2 ** 8}")          # 256
show(f"17 // 5 = {17 // 5}")        # 3
show(f"17 % 5  = {17 % 5}")         # 2

# Finding extremes
show(f"Lowest: {low(10, 5, 20)} | Highest: {high(10, 5, 20)}")
```

### 2. Conditionals & Loops
```python
set status_code = 200

when status_code == 200:
    show("Request Successful!")
or when status_code == 404:
    show("Endpoint Not Found.")
otherwise:
    show("Unknown status code:", status_code)

# Iterate over an array
set active_ports = [21, 22, 80, 443]
for p in active_ports:
    show("Auditing port:", p)

# Iteration using ranges
for i in range(1, 4):
    show("Retry attempt:", i)
```

### 3. Arrays & Data Collections
```python
set ports = [8080, 22, 443]

# Add and remove elements
ports.add(21)
set removed_port = ports.rm()

# Sort and join
ports.order()
show(f"Open ports: {ports.fuse(' | ')}")

# Functional programming: map, filter, for_each
fn double_val(x):
    return x * 2

set doubled_ports = ports.map(double_val)
show("Doubled ports:", doubled_ports)
```

### 4. Reusable Functions & Modules
```python
# In 'math_utils.ehx':
fn calculate_hash_space(bits):
    return 2 ** bits

# In 'main.ehx':
load "math_utils.ehx"

show(f"Keyspace for 16-bit key: {calculate_hash_space(16)}")
```

### 5. Networking, Sockets & Cryptography
```python
# Raw TCP Sockets
try:
    set sock = tcp_connect("127.0.0.1", 80, 3.0)
    sock.send("GET / HTTP/1.1\r\n\r\n")
    set response = sock.recv(1024)
    show("Response received:", response)
    sock.close()
catch err:
    show_err("Connection failed:", err)

# Cryptographic Hashing
set key = "admin_password"
show("SHA-256 Hash:", sha256(key))
show("MD5 Hash:    ", md5(key))

# ZIP Compression & Extraction
zip_pack("logs/", "backup.zip")
zip_unpack("backup.zip", "extracted_logs/")
```

### 6. Concurrency & Asynchronous Tasks
```python
fn heavy_task(target):
    pause(1.0)
    return f"Finished scan on {target}"

# Spawn background worker thread
set background_job = spawn(heavy_task, "192.168.1.1")

show("Doing work in the foreground...")
set job_result = background_job.wait()
show(job_result)
```

---

## Installation & Setup

You can install EHXLang via the pre-built binaries on the [GitHub Releases](https://github.com/EthioHackerX/EHXLang/releases) page or directly from the source repository.

### Option A: Windows Installation (`EHXSetup.exe`)
Download `EHXSetup.exe` from the latest release and run it:
1. **Privilege Mode:** Automatically detects administrative or current user permissions.
2. **Setup Wizard:** Review license terms, select installation folder, and choose components.
3. **Automated Configuration:** Adds `ehx` to system `PATH` and installs the official VS Code Extension.
4. **Instant Access:** Open any Command Prompt or PowerShell and type `ehx`.

### Option B: Linux & macOS Installation (`install.sh`)
Linux and macOS users can install EHXLang with a single command:
```bash
git clone https://github.com/EthioHackerX/EHXLang.git
cd EHXLang
chmod +x install.sh
./install.sh
```
The script automatically:
- Installs the runtime to `~/.local/share/ehxlang`
- Links the `ehx` launcher into `~/.local/bin/ehx`
- Deploys the VS Code Extension to `~/.vscode/extensions/`
- Adds `~/.local/bin` to your `PATH` (in `.bashrc` or `.zshrc`)

---

## Command-Line Usage

Once installed, you can use the `ehx` command directly from any terminal or PowerShell:

### Run an EHXLang script:
```bash
ehx main.ehx
```
or
```bash
ehx run main.ehx
```

### Start the Interactive REPL Shell:
```bash
ehx repl
```

### Display Version & Banner:
```bash
ehx -v
```

---

## VS Code Extension

EHXLang includes an official Visual Studio Code extension:
- **Syntax Highlighting:** Colors keywords (`set`, `when`, `fn`, `load`), built-ins, and f-strings.
- **Smart Indentation:** Automatically applies 4-space indent rules after typing a colon `:`.
- Automatically deployed by `EHXSetup.exe` to `~/.vscode/extensions/ehx-vscode`.

---

## Author & Credits

- **Creator & Lead Architect:** Yonatan Muluken (**ETHIO HACKER X**)
- **Project Repository:** [https://github.com/EthioHackerX](https://github.com/EthioHackerX)

*EHXLang v1.0.0 &copy; 2026. Distributed under the MIT License.*
