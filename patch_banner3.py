import sys
with open("repodoctor/report.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "║                                                            ║" in line:
        continue
    new_lines.append(line)

with open("repodoctor/report.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)
