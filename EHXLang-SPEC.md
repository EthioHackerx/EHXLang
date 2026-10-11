# EHXLang Specification

EHXLang is an indent-scoped, Python-inspired programming language designed for **automation, cybersecurity tooling, and systems scripting**, created by **Ethio Hacker X**.

## Version
Current Core: **0.3.0** (Targeting **1.0.0**)

## Syntax Overview

### 1. Variables
Variables are declared using the `let` keyword:
```ehx
let target = "192.168.1.1"
let port = 80
let timeout = 2.5
let is_active = true
```

### 2. Output (`show`)
Print expressions using `show(...)` with mandatory parentheses:
```ehx
show("Scanning:", target)
show("Port times 2:", port * 2)
show("Multiple", "arguments", "auto-spaced")
```

### 3. Strings
Both single `'...'` and double `"..."` quotes are supported:
```ehx
let host = '127.0.0.1'
let msg = "Connecting to 'SSH' service"
```

### 4. Arithmetic & Logic
- **Arithmetic:** `+`, `-`, `*`, `/` (string `+` automatically stringifies numbers & booleans)
- **Comparisons:** `==`, `!=`, `<`, `>`, `<=`, `>=`
- **Logical:** `and`, `or`, `not`

```ehx
let secure = port == 443 or port == 22
show(not secure)
show("Port: " + port)
```

### 5. Control Flow
EHXLang uses Python-style significant whitespace indentation (4 spaces recommended; tabs are forbidden).

#### Conditionals (`when` / `or when` / `otherwise`)
```ehx
when port == 80:
    show("HTTP service")
or when port == 443:
    show("HTTPS service")
otherwise:
    show("Custom service")
```

#### While Loop
```ehx
let count = 1
while count <= 5:
    show(count)
    let count = count + 1
```

#### For Loop (Range)
```ehx
for port in 1..1024:
    show("Scanning port:", port)
```

### 6. Functions (`fn`) & Scopes
Functions are declared using `fn` with parameter lists and significant whitespace indentation:
```ehx
# Function definition
fn calculate_hash(data, salt):
    let combined = data + ":" + salt
    return combined

# Function call
let result = calculate_hash("admin", "s3cr3t")
show("Result:", result)

# Recursion is fully supported
fn factorial(n):
    when n <= 1:
        return 1
    return n * factorial(n - 1)

show("5! =", factorial(5))
```

- **Scope Rules:** Variables defined inside a function with `let` are scoped locally and do not leak into the enclosing or global scope. Functions can read variables from enclosing/global scopes.
- **Return Values:** Returns the evaluated expression via `return <expr>`. Functions without a `return` statement return `none`.
- **First-Class Functions:** Functions can be stored in variables and passed around as first-class objects.