import sys
import re
with open("repodoctor/report.py", "r", encoding="utf-8") as f:
    content = f.read()

# Delete EVERYTHING from `def print_terminal_report` to `print(f"\\nRepository:` EXCEPT the signature!
# Actually, I'll just find the exact block and replace it.
content = re.sub(
    r'    print\(c\("╔[^"]*", "94;1"\)\)\n.*?\n    print\(c\("╚[^"]*", "94;1"\)\)\n',
    '',
    content,
    flags=re.DOTALL
)

# Also delete that ghost string if it's there
content = re.sub(
    r'    print\(c\("║[^"]*", "94;1"\)\)\n.*?\n    for char in "REPO DOCTOR":\n.*?\n',
    '',
    content,
    flags=re.DOTALL
)

# And if there's any remaining `║                                                            ║║                        REPO DOCTOR`
content = re.sub(r'print\(c\("║                                                            ║", "94;1"\)\)\n    print\(c\("║                        ", "94;1"\), end=""\)\n    for char in "REPO DOCTOR":\n        print\(c\(char, "96;1"\), end=""\)\n        sys.stdout.flush\(\)\n        time.sleep\(0.05\)\n    print\(c\("                         ║", "94;1"\)\)\n', '', content)

with open("repodoctor/report.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Deleted banner for real!")
