import sys
import re

# 1. Remove banner from report.py
with open("repodoctor/report.py", "r", encoding="utf-8") as f:
    rep_lines = f.readlines()

new_rep_lines = []
skip = False
for line in rep_lines:
    if 'print(c("╔' in line:
        skip = True
    if skip:
        if 'print(c("╚' in line:
            skip = False
        continue
    new_rep_lines.append(line)

with open("repodoctor/report.py", "w", encoding="utf-8") as f:
    f.writelines(new_rep_lines)

# 2. Add banner to __main__.py
with open("repodoctor/__main__.py", "r", encoding="utf-8") as f:
    main_content = f.read()

banner_code = """
    # 1. Print Banner & Greeting
    use_color = not args.no_color and sys.stdout.isatty()
    def c(text, code):
        return f"\\033[{code}m{text}\\033[0m" if use_color else text

    if not args.json:
        print()
        print(c("╔════════════════════════════════════════════════════════════╗", "94;1"))
        print(c("║                        ", "94;1"), end="")
        for char in "REPO DOCTOR":
            print(c(char, "96;1"), end="")
            sys.stdout.flush()
            time.sleep(0.05)
        print(c("                         ║", "94;1"))
        print(c("╚════════════════════════════════════════════════════════════╝", "94;1"))
        print(c("Welcome to RepoDoctor! 🩺", "92;1"))
        print(c("Initializing zero-dependency static analysis engine...", "90;1"))
        print()
        time.sleep(0.5)
"""

main_content = main_content.replace(
    "def main():\n    start_time = time.time()\n    args = parse_args()\n",
    "def main():\n    start_time = time.time()\n    args = parse_args()\n" + banner_code
)

with open("repodoctor/__main__.py", "w", encoding="utf-8") as f:
    f.write(main_content)

print("Order patched!")
