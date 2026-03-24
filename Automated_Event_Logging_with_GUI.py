import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import ast
import astor
import _thread
import re

# ---------------- PYTHON LOGGING ---------------- #
class PythonLoggingTransformer(ast.NodeTransformer):
    def __init__(self):
        self.has_function = False
        self.current_class = None
        super().__init__()

    def visit_ClassDef(self, node):
        previous_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = previous_class
        return node

    def visit_FunctionDef(self, node):
        self.has_function = True
        init_statements = [
            self.create_assign("_thread_id", self.get_thread_id_call()),
            self.create_assign("_fun_name", ast.Constant(value=node.name)),
            self.create_assign("_cls_name", ast.Constant(value=self.current_class if self.current_class else "0")),
        ]
        new_body = self.process_statements_in_block(node.body)

        # If function has no variable assignments, log default '0'
        has_variable = any(isinstance(stmt, ast.Assign) for stmt in node.body)
        if not has_variable:
            new_body.insert(0, self.create_log_node('0'))

        node.body = init_statements + new_body
        return node

    def visit_Module(self, node):
        self.generic_visit(node)
        new_body = []
        if not self.has_function:
            new_body.extend([
                self.create_assign("_thread_id", self.get_thread_id_call()),
                self.create_assign("_fun_name", ast.Constant(value="0")),
                self.create_assign("_cls_name", ast.Constant(value="0")),
            ])
        new_body.extend(self.process_statements_in_block(node.body))
        node.body = new_body
        return node

    def process_statements_in_block(self, block):
        new_block = []
        for stmt in block:
            if isinstance(stmt, (ast.If, ast.For, ast.While, ast.Try)):
                stmt.body = self.process_statements_in_block(stmt.body)
                if hasattr(stmt, 'orelse') and stmt.orelse:
                    stmt.orelse = self.process_statements_in_block(stmt.orelse)
                if isinstance(stmt, ast.Try):
                    for handler in stmt.handlers:
                        handler.body = self.process_statements_in_block(handler.body)
                    if stmt.finalbody:
                        stmt.finalbody = self.process_statements_in_block(stmt.finalbody)
                new_block.append(stmt)
            elif isinstance(stmt, ast.Assign):
                new_block.append(stmt)
                for target in stmt.targets:
                    var_names = self.extract_names(target)
                    for name in var_names:
                        new_block.append(self.create_log_node(name))
            else:
                new_block.append(stmt)
        return new_block

    def extract_names(self, target):
        if isinstance(target, ast.Name):
            return [target.id]
        elif isinstance(target, ast.Tuple):
            names = []
            for elt in target.elts:
                names.extend(self.extract_names(elt))
            return names
        elif isinstance(target, ast.Subscript):
            return [astor.to_source(target).strip()]
        elif isinstance(target, ast.Attribute):
            return [astor.to_source(target).strip()]
        else:
            return []

    def create_log_node(self, var_name):
        return ast.Expr(
            value=ast.Call(
                func=ast.Attribute(value=ast.Name(id="vl", ctx=ast.Load()), attr="log", ctx=ast.Load()),
                args=[],
                keywords=[
                    ast.keyword(arg="var", value=ast.Constant(value=var_name)),
                    ast.keyword(arg="fun", value=ast.Name(id="_fun_name", ctx=ast.Load())),
                    ast.keyword(arg="clas", value=ast.Name(id="_cls_name", ctx=ast.Load())),
                    ast.keyword(arg="th", value=ast.Name(id="_thread_id", ctx=ast.Load())),
                ],
            )
        )

    def create_assign(self, varname, value):
        return ast.Assign(targets=[ast.Name(id=varname, ctx=ast.Store())], value=value)

    def get_thread_id_call(self):
        return ast.Call(
            func=ast.Attribute(value=ast.Name(id="_thread", ctx=ast.Load()), attr="get_ident", ctx=ast.Load()),
            args=[], keywords=[]
        )

# ---------------- ARDUINO LOGGING ---------------- #
def add_arduino_logging(source_code):
    lines = source_code.splitlines()
    output_lines = []
    current_function = None
    current_class = "main"
    in_function = False
    waiting_for_brace = False
    function_has_var = False

    assign_pattern = re.compile(r'([a-zA-Z_][a-zA-Z0-9_\.\[\]]*)\s*([\+\-\*/]?=)')
    incdec_pattern = re.compile(r'([a-zA-Z_][a-zA-Z0-9_\.\[\]]*)\s*(\+\+|--)')
    control_keywords = ("if", "else", "while", "for", "switch", "case")

    for line in lines:
        stripped = line.strip()

        # Detect function definitions
        func_match = re.match(r'\s*(?:[\w:<>\*\s]+)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(.*\)\s*\{?', stripped)
        if func_match:
            current_function = func_match.group(1)
            function_has_var = False
            if '{' in stripped:
                in_function = True
            else:
                waiting_for_brace = True

        if waiting_for_brace and stripped == "{":
            in_function = True
            waiting_for_brace = False

        # Detect end of function
        if in_function and stripped == "}":
            if not function_has_var and current_function:
                indent = len(line) - len(line.lstrip())
                default_log = f'{" " * indent}VarLogger::log("0", "{current_function}", "{current_class}", "thread1");'
                output_lines.append(default_log)
            in_function = False
            current_function = None

        output_lines.append(line)

        if not stripped or stripped in ["{", "}"]:
            continue

        # Only log assignments inside functions and skip control statements
        if current_function and not any(stripped.startswith(kw) for kw in control_keywords):
            assign_matches = assign_pattern.findall(stripped)
            incdec_matches = incdec_pattern.findall(stripped)
            all_vars = [var for var, op in assign_matches] + [var for var, op in incdec_matches]

            if all_vars:
                function_has_var = True

            current_indent = len(line) - len(line.lstrip())
            for var in all_vars:
                log_line = f'{" " * current_indent}VarLogger::log("{var}", "{current_function}", "{current_class}", "thread1");'
                output_lines.append(log_line)

    return "\n".join(output_lines)

# ---------------- GUI ---------------- #
def generate_logged_code():
    code = code_text.get("1.0", tk.END)
    code_type = code_type_var.get()
    try:
        if code_type == "Python":
            tree = ast.parse(code)
            transformer = PythonLoggingTransformer()
            tree = transformer.visit(tree)

            # Initial setup
            initial_setup = [
                ast.Assign(targets=[ast.Name(id="_thread_id", ctx=ast.Store())],
                           value=ast.Call(func=ast.Attribute(value=ast.Name(id="_thread", ctx=ast.Load()),
                                                             attr="get_ident", ctx=ast.Load()), args=[], keywords=[])),
                ast.Assign(targets=[ast.Name(id="_fun_name", ctx=ast.Store())], value=ast.Constant(value='0')),
                ast.Assign(targets=[ast.Name(id="_cls_name", ctx=ast.Store())], value=ast.Constant(value='0')),
            ]

            insert_index = 0
            for idx, node in enumerate(tree.body):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    insert_index = idx + 1
                else:
                    break
            tree.body = tree.body[:insert_index] + initial_setup + tree.body[insert_index:]

            logged_code = astor.to_source(tree)

        else:  # Arduino/C++
            logged_code = add_arduino_logging(code)

        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, logged_code)

    except Exception as e:
        messagebox.showerror("Error", f"Error processing code:\n{e}")

def save_logged_code():
    logged_code = output_text.get("1.0", tk.END)
    if not logged_code.strip():
        messagebox.showerror("Error", "No logged code to save!")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".py",
                                             filetypes=[("All Files", "*.*")])
    if file_path:
        with open(file_path, "w") as f:
            f.write(logged_code)
        messagebox.showinfo("Saved", f"Logged code saved to {file_path}")

# ---------------- GUI Layout ---------------- #
root = tk.Tk()
root.title("Automated Event Logger GUI")
root.geometry("1800x1200")

tk.Label(root, text="Select Code Type:").pack()
code_type_var = tk.StringVar(value="Python")
tk.OptionMenu(root, code_type_var, "Python", "Arduino/C++").pack()

tk.Label(root, text="Write your code below:").pack()
code_text = scrolledtext.ScrolledText(root, height=25, width=180)
code_text.pack(padx=10, pady=10)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)
tk.Button(btn_frame, text="Generate Logged Code", command=generate_logged_code, bg="green", fg="white", width=25).grid(row=0, column=0, padx=5)
tk.Button(btn_frame, text="Save Logged Code", command=save_logged_code, bg="blue", fg="white", width=25).grid(row=0, column=1, padx=5)

tk.Label(root, text="Logged code output:").pack()
output_text = scrolledtext.ScrolledText(root, height=25, width=180)
output_text.pack(padx=10, pady=10)

root.mainloop()
