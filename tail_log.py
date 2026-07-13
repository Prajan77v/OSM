with open("logs/app.log", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

print(f"Total lines in app.log: {len(lines)}")
print("Last 150 lines:")
for line in lines[-150:]:
    print(line.strip())
