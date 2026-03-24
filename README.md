Automated Event Logger Tool (Python + Arduino)

This project provides a GUI-based automated logging tool that injects structured logging statements into source code. It supports both Python and Arduino/C/C++ files, making debugging, tracing, and monitoring easier and more consistent.

**Features:** 

**Python Logging (AST-Based)**
- Uses Python's AST (Abstract Syntax Tree) for accurate code transformation

**Automatically:**
- Adds _thread_id, _fun_name, _cls_name at the start of functions
- Logs every variable assignment using vl.log()
- Format: `vl.log(var="x", fun=_fun_name, clas=_cls_name, th=_thread_id)`

**Handles:**
- Functions and class methods
- Nested blocks (if, for, while, try)
- Tuple assignments, object attributes, array indexing
- Adds default logging if no variables are present in a function

**Arduino/C/C++ Logging (Regex-Based)**

**Injects logging using:**
`VarLogger::log("var", "function", "class", "thread");`

**Detects:**
- Variable assignments (=, +=, etc.)
- Increment/decrement (++, --)
- Works inside functions only
- Adds default logging if no variables are found


**GUI Interface**

**Simple and user-friendly interface:**
- Select input file
- Choose output file
- Run logging injection
- Displays success/error messages

**Supported File Types**

- **Python:** .py
- **Arduino/C/C++:** .ino, .cpp, .c, .h

**How the Program Works**

- Load the input file
- Detect file type
- Apply:
1. AST transformation (Python)
2. Regex-based parsing (Arduino/C/C++)
- Save modified file with logging injected
