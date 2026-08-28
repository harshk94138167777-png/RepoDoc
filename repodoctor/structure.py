import os
from typing import Dict, Any

def check_project_structure(root_path: str) -> Dict[str, str]:
    """
    Returns PASS, WARN, FAIL, or NOT APPLICABLE
    """
    results = {
        "README": "WARN",
        ".gitignore": "WARN",
        "Tests": "WARN",
        "LICENSE": "WARN",
        "CI config": "WARN"
    }

    root = os.path.abspath(root_path)

    # Check README
    if any(os.path.exists(os.path.join(root, f)) for f in ["README.md", "README.txt", "README"]):
        results["README"] = "PASS"

    # Check .gitignore
    if os.path.exists(os.path.join(root, ".gitignore")):
        results[".gitignore"] = "PASS"
    elif not os.path.exists(os.path.join(root, ".git")):
        results[".gitignore"] = "NOT APPLICABLE"

    # Check tests
    if os.path.exists(os.path.join(root, "tests")) or os.path.exists(os.path.join(root, "test")):
        results["Tests"] = "PASS"

    # Check LICENSE
    if any(os.path.exists(os.path.join(root, f)) for f in ["LICENSE", "LICENSE.txt", "LICENSE.md"]):
        results["LICENSE"] = "PASS"

    # Check CI config
    if os.path.exists(os.path.join(root, ".github")) or os.path.exists(os.path.join(root, ".gitlab-ci.yml")):
        results["CI config"] = "PASS"
    
    return results
