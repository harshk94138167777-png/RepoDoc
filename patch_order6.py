import sys
with open("repodoctor/report.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# delete from def print_terminal_report down to line 75 (before print(f"\nRepository:"))
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if line.startswith("def print_terminal_report"):
        start_idx = i
    if "print(f\"\\nRepository:" in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    sig = lines[start_idx]
    new_lines = lines[:start_idx] + [sig, "    print()\n"] + lines[end_idx:]
    with open("repodoctor/report.py", "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print("Finally deleted the banner logic from report.py!")
else:
    print("Could not find bounds")
