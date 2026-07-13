with open("main.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

with open("web_search.txt", "w", encoding="utf-8") as out:
    for idx, line in enumerate(lines):
        if any(w in line.lower() for w in ["web_server", "web_integration", "alarm", "export_csv", "telegram", "shutdown", "init_web", "control_handlers", "register_control"]):
            out.write(f"Line {idx+1}: {line.rstrip()}\n")
print("Done")
