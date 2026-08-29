import sys
import re

with open("repodoctor/__main__.py", "r", encoding="utf-8") as f:
    main = f.read()

# We need to wrap the analysis block in a loop
# The analysis block starts around `files = []` or `custom_ignores = ...`
# Actually, it's easier to completely rewrite the core logic of __main__.py from `custom_ignores` down to `if not args.json:`

# Let's write a python script that does exactly what is needed.
