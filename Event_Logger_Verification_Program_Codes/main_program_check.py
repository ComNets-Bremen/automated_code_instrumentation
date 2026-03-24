import difflib
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

def compare_files(file1_path, file2_path):
    with open(file1_path, 'r', encoding='utf-8') as f1, open(file2_path, 'r', encoding='utf-8') as f2:
        code1_lines = f1.readlines()
        code2_lines = f2.readlines()

    differ = difflib.Differ()
    diff = list(differ.compare(code1_lines, code2_lines))

    removed_lines = [line for line in diff if line.startswith('- ')]
    added_lines = [line for line in diff if line.startswith('+ ')]

    total_lines = max(len(code1_lines), len(code2_lines))
    removed_percentage = (len(removed_lines) / total_lines) * 100 if total_lines > 0 else 0

    return removed_lines, added_lines, len(removed_lines), total_lines, removed_percentage


def load_and_compare():
    file1 = filedialog.askopenfilename(
        title="Select First File",
        filetypes=[("Code Files", "*.py *.ino *.txt"), ("All Files", "*.*")]
    )
    if not file1:
        return

    file2 = filedialog.askopenfilename(
        title="Select Second File",
        filetypes=[("Code Files", "*.py *.ino *.txt"), ("All Files", "*.*")]
    )
    if not file2:
        return

    removed_lines, added_lines, diff_count, total, percent = compare_files(file1, file2)

    # Clear output
    result_text.delete('1.0', tk.END)

    # Summary
    result_text.insert(tk.END, f" File 1: {file1}\n File 2: {file2}\n\n", "header")
    result_text.insert(tk.END, f" Lines removed (from File 1 only): {len(removed_lines)}\n", "header")
    result_text.insert(tk.END, f" Lines added (from File 2 only): {len(added_lines)}\n", "header")
    result_text.insert(tk.END, f" Total lines in larger file: {total}\n", "header")
    result_text.insert(tk.END, f" Percentage difference: {percent:.2f}%\n\n", "header")

    # Removed lines
    result_text.insert(tk.END, " Removed Lines:\n", "header")
    for line in removed_lines:
        result_text.insert(tk.END, line, "removed")

    # Added lines
    result_text.insert(tk.END, "\n Added Lines:\n", "header")
    for line in added_lines:
        result_text.insert(tk.END, line, "added")


# GUI Setup
root = tk.Tk()
root.title("Code Comparator (Python + Arduino INO)")
root.geometry("900x650")

btn = tk.Button(root, text="Select and Compare Files", command=load_and_compare,
                font=("Arial", 12), bg="skyblue")
btn.pack(pady=10)

result_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Courier", 10))
result_text.pack(expand=True, fill='both', padx=10, pady=10)

# Tag configs for colors
result_text.tag_config("header", foreground="blue", font=("Courier", 10, "bold"))
result_text.tag_config("removed", foreground="red")
result_text.tag_config("added", foreground="green")

root.mainloop()
