import sys
with open("repodoctor/report.py", "r", encoding="utf-8") as f:
    rep = f.read()

target = "def print_terminal_report(data: ReportData, use_color: bool = True, large_file_threshold: int = 500, deltas: Optional[Dict[str, int]] = None) -> None:"
replacement = "def print_terminal_report(data: ReportData, use_color: bool = True, large_file_threshold: int = 500, deltas: Optional[Dict[str, int]] = None, exec_time: float = None, show_tree: bool = False) -> None:"

rep = rep.replace(target, replacement)

# We also need to fix `exec_time` being printed inside report.py
if "exec_time" not in rep[rep.find("def print_terminal_report"):]:
    # find the end of the report
    end_idx = rep.rfind('print("────────────────────────────────────────────────────────────")')
    if end_idx != -1:
        # Actually it's probably around the scan completed print
        pass

with open("repodoctor/report.py", "w", encoding="utf-8") as f:
    f.write(rep)
print("Patched report.py signature!")
