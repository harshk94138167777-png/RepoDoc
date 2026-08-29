import sys
with open("repodoctor/report.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix banner alignment
if "║                       REPO DOCTOR                         ║" in content:
    content = content.replace(
        "║                       REPO DOCTOR                         ║",
        "║                        REPO DOCTOR                         ║"
    )
    with open("repodoctor/report.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed banner alignment!")
else:
    print("Could not find the banner text.")
