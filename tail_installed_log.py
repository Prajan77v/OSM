with open("C:/Users/Prajan/OMS_Sentinel/logs/app.log", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
print("Last 100 lines:")
for line in lines[-100:]:
    print(line.strip())
