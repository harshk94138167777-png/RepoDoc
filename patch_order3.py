import sys

with open("repodoctor/report.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if 'print(c("╔' in line:
        skip = True
    if skip:
        if 'print(c("╚' in line:
            skip = False
        continue
    new_lines.append(line)

with open("repodoctor/report.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)
print("Done!")
