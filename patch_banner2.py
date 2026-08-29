import sys
import re

with open("repodoctor/report.py", "r", encoding="utf-8") as f:
    content = f.read()

# I want to replace everything from "def print_terminal_report" down to "print()\n    print(f"Repository"
match = re.search(r'def print_terminal_report.*?(?=    print\("\\nRepository:)', content, re.DOTALL)
if match:
    old_banner = match.group(0)
    
    new_banner = """def print_terminal_report(data, use_color=True, large_file_threshold=500, deltas=None, exec_time=None, show_tree=False):
    import time, sys
    
    # Helper to print colored text
    def c(text, code):
        return f"\\033[{code}m{text}\\033[0m" if use_color else text

    print(c("╔════════════════════════════════════════════════════════════╗", "94;1"))
    print(c("║                        ", "94;1"), end="")
    for char in "REPO DOCTOR":
        print(c(char, "96;1"), end="")
        sys.stdout.flush()
        time.sleep(0.05)
    print(c("                         ║", "94;1"))
    print(c("╚════════════════════════════════════════════════════════════╝", "94;1"))"""
    
    content = content.replace(old_banner, new_banner)
    with open("repodoctor/report.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched banner!")
else:
    print("Failed to find banner section")
