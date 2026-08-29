import sys
import re

with open("repodoctor/report.py", "r", encoding="utf-8") as f:
    content = f.read()

# I want to delete the whole function definition down to `print(f"\\nRepository: {data.name}")`
# and replace it with just the definition and `print(f"\\nRepository: {data.name}")`
match = re.search(r'def print_terminal_report.*?print\("\\nRepository:', content, re.DOTALL)
if match:
    old_start = match.group(0)
    
    new_start = """def print_terminal_report(data: ReportData, use_color: bool = True, large_file_threshold: int = 500, deltas=None, exec_time: float = None, show_tree: bool = False) -> None:
    import time, sys
    
    # Helper to print colored text
    def c(text, code):
        return f"\\033[{code}m{text}\\033[0m" if use_color else text

    print(f"\\nRepository:"""
    
    content = content.replace(old_start, new_start)
    with open("repodoctor/report.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched banner completely out of report.py!")
else:
    print("Could not find print_terminal_report start")
