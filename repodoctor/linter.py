import re
import ast

def run_micro_linters(file_info, content):
    smells = []
    lines = content.splitlines()
    
    if not lines:
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
            
    return smells
