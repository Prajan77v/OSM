with open("surveillance.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for i, line in enumerate(lines):
    if any(x in line for x in ["_format_log_cols", "append_to_pretty_log", "log_event"]):
        output.append(f"Line {i+1}: {line.strip()}")

with open("search_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))
