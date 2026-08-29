import re
import ast

def run_micro_linters(file_info, content):
    smells = []
    lines = content.splitlines()
    
    if not lines:
    
    # 14. Empty File Check
    if not content.strip():
        smells.append("Completely empty file")
        
    # 15. Banned words (Profanity / Slurs / etc.)
    if re.search(r'\b(fuck|shit|crap|bitch)\b', content, re.IGNORECASE):
        smells.append("Profanity found in code")
        
    # 16. TODO without owner
    if re.search(r'//\s*TODO(?![(\[])', content) or re.search(r'#\s*TODO(?![(\[])', content):
        smells.append("TODO without owner/ticket")
        
    # Language Specific Extensions
    if file_info.language in ("JavaScript", "TypeScript"):
        # 17. eval() usage
        if re.search(r'\beval\s*\(', content):
            smells.append("Dangerous eval() usage")
        # 18. Missing strict mode (for pure JS)
        if file_info.language == "JavaScript" and not re.search(r'["\']use strict["\']', content):
            smells.append("Missing \"use strict\" in JS")
        # 19. console.error/warn
        if re.search(r'\bconsole\.(error|warn)\s*\(', content):
            smells.append("console.error/warn left in code")
            
    elif file_info.language == "Python":
        # 20. eval() / exec()
        if re.search(r'\b(eval|exec)\s*\(', content):
            smells.append("Dangerous eval()/exec() usage")
        try:
            tree = ast.parse(content)
            for n in ast.walk(tree):
                # 21. Wildcard imports
                if isinstance(n, ast.ImportFrom) and any(alias.name == '*' for alias in n.names):
                    if "Wildcard import (import *)" not in smells: smells.append("Wildcard import (import *)")
                # 22. Bare exceptions
                if isinstance(n, ast.ExceptHandler) and n.type is None:
                    if "Bare except: block" not in smells: smells.append("Bare except: block")
                # 23. Mutable default arguments
                if isinstance(n, ast.arguments):
                    for d in n.defaults:
                        if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                            if "Mutable default argument ([] or {})" not in smells: smells.append("Mutable default argument ([] or {})")
                # 24. sys.exit()
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                    if isinstance(n.func.value, ast.Name) and n.func.value.id == "sys" and n.func.attr == "exit":
                        if "Hard sys.exit() found" not in smells: smells.append("Hard sys.exit() found")
        except:
            pass
            
    elif file_info.language == "CSS":
        # 25. Empty rulesets
        if re.search(r'\{[^}]*\}', content) and not re.search(r'\{[^a-zA-Z]*[a-zA-Z-]+\s*:[^}]*\}', content):
            smells.append("Empty CSS ruleset")
        # 26. Deep nesting (heuristic for uncompiled CSS/SCSS)
        if content.count('>') > (len(lines) // 10): 
            smells.append("High CSS child combinator density")
            
    elif file_info.language == "HTML":
        # 27. Inline CSS (style="...")
        if re.search(r'\bstyle\s*=\s*["\']', content):
            smells.append("Inline CSS (style=...) used")
        # 28. Inline JS (onclick="...")
        if re.search(r'\bon(click|load|submit|mouseover|change)\s*=\s*["\']', content):
            smells.append("Inline JavaScript (onclick=...) used")
            
    elif file_info.language == "JSON":
        # 29. Giant JSON files
        if len(lines) > 2000:
            smells.append("Massive JSON configuration (>2000 lines)")
            
    elif file_info.language == "Markdown":
        # 30. Missing H1 title at start
        if lines and not lines[0].startswith('# '):
            smells.append("Markdown missing # H1 Title at start")

    return smells

    # 1. Trailing whitespace
    if any(l.rstrip('\n\r').endswith((' ', '\t')) for l in lines):
        smells.append("Trailing whitespace")
        
    # 2. Missing EOF Newline
    if content and not content.endswith('\n'):
        smells.append("Missing EOF newline")
        
    # 3. Line Length > 120
    if any(len(l) > 120 for l in lines):
        smells.append("Lines > 120 chars")
        
    # 4. Mixed Tabs & Spaces
    has_tabs = any('\t' in l for l in lines)
    has_spaces = any(l.startswith(' ') for l in lines)
    if has_tabs and has_spaces:
        smells.append("Mixed tabs and spaces")
        
    # 5. Localhost Hardcoding
    if re.search(r'http://localhost|http://127\.0\.0\.1', content):
        smells.append("Hardcoded localhost URL")
        
    # Language Specific
    if file_info.language in ("JavaScript", "TypeScript"):
        # 6. console.log
        if re.search(r'\bconsole\.log\s*\(', content):
            smells.append("console.log() found")
        # 7. debugger
        if re.search(r'\bdebugger\s*;?', content):
            smells.append("debugger statement found")
            
    elif file_info.language == "Python":
        # 8. print statements
        if re.search(r'\bprint\s*\(', content):
            smells.append("print() statement found")
        try:
            tree = ast.parse(content)
            for n in ast.walk(tree):
                # 9. Too many args
                if isinstance(n, ast.FunctionDef):
                    if len(n.args.args) > 6:
                        if "Function with > 6 args" not in smells: smells.append("Function with > 6 args")
                    # 10. Missing docstring
                    if not ast.get_docstring(n):
                        if "Missing docstring" not in smells: smells.append("Missing docstring")
                # 11. Swallowed errors
                if isinstance(n, ast.ExceptHandler):
                    if not n.body or (len(n.body) == 1 and isinstance(n.body[0], ast.Pass)):
                        if "Empty except block" not in smells: smells.append("Empty except block")
        except:
            pass
            
    elif file_info.language == "CSS":
        # 12. CSS !important
        if "!important" in content:
            smells.append("CSS !important used")
            
    elif file_info.language == "HTML":
        # 13. Missing alt text
        if re.search(r'<img\b(?![^>]*\balt=)[^>]*>', content):
            smells.append("<img> missing alt attribute")
            

    # 14. Empty File Check
    if not content.strip():
        smells.append("Completely empty file")
        
    # 15. Banned words (Profanity / Slurs / etc.)
    if re.search(r'\b(fuck|shit|crap|bitch)\b', content, re.IGNORECASE):
        smells.append("Profanity found in code")
        
    # 16. TODO without owner
    if re.search(r'//\s*TODO(?![(\[])', content) or re.search(r'#\s*TODO(?![(\[])', content):
        smells.append("TODO without owner/ticket")
        
    # Language Specific Extensions
    if file_info.language in ("JavaScript", "TypeScript"):
        # 17. eval() usage
        if re.search(r'\beval\s*\(', content):
            smells.append("Dangerous eval() usage")
        # 18. Missing strict mode (for pure JS)
        if file_info.language == "JavaScript" and not re.search(r'["\']use strict["\']', content):
            smells.append("Missing \"use strict\" in JS")
        # 19. console.error/warn
        if re.search(r'\bconsole\.(error|warn)\s*\(', content):
            smells.append("console.error/warn left in code")
            
    elif file_info.language == "Python":
        # 20. eval() / exec()
        if re.search(r'\b(eval|exec)\s*\(', content):
            smells.append("Dangerous eval()/exec() usage")
        try:
            tree = ast.parse(content)
            for n in ast.walk(tree):
                # 21. Wildcard imports
                if isinstance(n, ast.ImportFrom) and any(alias.name == '*' for alias in n.names):
                    if "Wildcard import (import *)" not in smells: smells.append("Wildcard import (import *)")
                # 22. Bare exceptions
                if isinstance(n, ast.ExceptHandler) and n.type is None:
                    if "Bare except: block" not in smells: smells.append("Bare except: block")
                # 23. Mutable default arguments
                if isinstance(n, ast.arguments):
                    for d in n.defaults:
                        if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                            if "Mutable default argument ([] or {})" not in smells: smells.append("Mutable default argument ([] or {})")
                # 24. sys.exit()
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                    if isinstance(n.func.value, ast.Name) and n.func.value.id == "sys" and n.func.attr == "exit":
                        if "Hard sys.exit() found" not in smells: smells.append("Hard sys.exit() found")
        except:
            pass
            
    elif file_info.language == "CSS":
        # 25. Empty rulesets
        if re.search(r'\{[^}]*\}', content) and not re.search(r'\{[^a-zA-Z]*[a-zA-Z-]+\s*:[^}]*\}', content):
            smells.append("Empty CSS ruleset")
        # 26. Deep nesting (heuristic for uncompiled CSS/SCSS)
        if content.count('>') > (len(lines) // 10): 
            smells.append("High CSS child combinator density")
            
    elif file_info.language == "HTML":
        # 27. Inline CSS (style="...")
        if re.search(r'\bstyle\s*=\s*["\']', content):
            smells.append("Inline CSS (style=...) used")
        # 28. Inline JS (onclick="...")
        if re.search(r'\bon(click|load|submit|mouseover|change)\s*=\s*["\']', content):
            smells.append("Inline JavaScript (onclick=...) used")
            
    elif file_info.language == "JSON":
        # 29. Giant JSON files
        if len(lines) > 2000:
            smells.append("Massive JSON configuration (>2000 lines)")
            
    elif file_info.language == "Markdown":
        # 30. Missing H1 title at start
        if lines and not lines[0].startswith('# '):
            smells.append("Markdown missing # H1 Title at start")

    return smells
