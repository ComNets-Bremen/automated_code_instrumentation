import difflib
import tkinter as tk
from tkinter import filedialog, scrolledtext

def compare_files(file1_path, file2_path):
    def should_ignore(line):
        return (
            line.strip().startswith('_fun_name') or
            line.strip().startswith('_cls_name') or
            line.strip().startswith('_thread_id') or
            line.strip().startswith('vl.log') or
            line.strip().startswith('VarLogger::log')   # <-- new filter for Arduino/C++
        )

    with open(file1_path, 'r', encoding='utf-8') as f1, open(file2_path, 'r', encoding='utf-8') as f2:
        code1_lines = [line.rstrip() for line in f1 if not should_ignore(line)]
        code2_lines = [line.rstrip() for line in f2 if not should_ignore(line)]

    differ = difflib.Differ()
    diff = list(differ.compare(code1_lines, code2_lines))

    removed_lines = [line for line in diff if line.startswith('- ')]
    added_lines = [line for line in diff if line.startswith('+ ')]

    total_lines = max(len(code1_lines), len(code2_lines))
    total_changes = len(removed_lines) + len(added_lines)
    removed_percentage = (total_changes / total_lines) * 100 if total_lines > 0 else 0

    return removed_lines, added_lines, len(removed_lines), len(added_lines), total_lines, removed_percentage


def load_and_compare():
    file1 = filedialog.askopenfilename(title="Select First File",
                                       filetypes=[("Code Files", "*.py *.ino *.txt *.cpp *.h"), ("All Files", "*.*")])
    if not file1:
        return

    file2 = filedialog.askopenfilename(title="Select Second File",
                                       filetypes=[("Code Files", "*.py *.ino *.txt *.cpp *.h"), ("All Files", "*.*")])
    if not file2:
        return

    removed_lines, added_lines, removed_count, added_count, total, percent = compare_files(file1, file2)

    result_text.delete('1.0', tk.END)
    result_text.insert(tk.END, f" File 1: {file1}\n File 2: {file2}\n\n")
    result_text.insert(tk.END, f" Lines removed: {removed_count}\n")
    result_text.insert(tk.END, f" Lines added: {added_count}\n")
    result_text.insert(tk.END, f" Total changes: {removed_count + added_count}\n")
    result_text.insert(tk.END, f" Total lines in larger file: {total}\n")
    result_text.insert(tk.END, f" Percentage difference: {percent:.2f}%\n\n")

    # Show removed lines
    result_text.insert(tk.END, "  Red Lines (from File 1 only):\n")
    for line in removed_lines:
        result_text.insert(tk.END, line + "\n", 'removed')

    # Show added lines
    result_text.insert(tk.END, "\n  Green Lines (from File 2 only):\n")
    for line in added_lines:
        result_text.insert(tk.END, line + "\n", 'added')

    # Tag colors
    result_text.tag_config('removed', foreground='red')
    result_text.tag_config('added', foreground='green')


# GUI Setup
root = tk.Tk()
root.title("Code Comparator (Python + Arduino INO + C++)")
root.geometry("850x650")

btn = tk.Button(root, text="Select and Compare Files", command=load_and_compare,
                font=("Arial", 12), bg="skyblue")
btn.pack(pady=10)

result_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Courier", 10))
result_text.pack(expand=True, fill='both', padx=10, pady=10)

root.mainloop()
