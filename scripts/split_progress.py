"""Split 项目进度.md into modular phase files."""
import re
import os

with open("d:/enployment_service_agent/docs/项目进度.md", "r", encoding="utf-8") as f:
    content = f.read()

sections = {}

# Phase 0: from start to '### 阶段 1 Phase 1-P0'
phase0_match = re.split(r"(?=### 阶段 1 Phase 1-P0)", content, maxsplit=1)
if len(phase0_match) >= 2:
    sections["phase-0"] = phase0_match[0].rstrip() + "\n"
    remaining = phase0_match[1]
else:
    sections["phase-0"] = content
    remaining = ""

# Phase 1: from '### 阶段 1 Phase 1-P0' to '### 阶段 2 Phase 2'
phase1_match = re.split(r"(?=### 阶段 2 Phase 2)", remaining, maxsplit=1)
if len(phase1_match) >= 2:
    sections["phase-1"] = phase1_match[0].rstrip() + "\n"
    remaining = phase1_match[1]
else:
    sections["phase-1"] = remaining
    remaining = ""

# Phase 2: from '### 阶段 2 Phase 2' to '### 阶段 3 Phase 3'
phase2_match = re.split(r"(?=### 阶段 3 Phase 3)", remaining, maxsplit=1)
if len(phase2_match) >= 2:
    sections["phase-2"] = phase2_match[0].rstrip() + "\n"
    remaining = phase2_match[1]
else:
    sections["phase-2"] = remaining
    remaining = ""

# Phase 3: from '### 阶段 3 Phase 3' to '### 阶段 4 Phase 4'
phase3_match = re.split(r"(?=### 阶段 4 Phase 4)", remaining, maxsplit=1)
if len(phase3_match) >= 2:
    sections["phase-3"] = phase3_match[0].rstrip() + "\n"
    remaining = phase3_match[1]
else:
    sections["phase-3"] = remaining
    remaining = ""

# Phase 4: from '### 阶段 4 Phase 4' to '### 修复 1'
phase4_match = re.split(r"(?=### 修复 1)", remaining, maxsplit=1)
if len(phase4_match) >= 2:
    sections["phase-4"] = phase4_match[0].rstrip() + "\n"
    remaining = phase4_match[1]
else:
    sections["phase-4"] = remaining
    remaining = ""

# Bugfixes: everything from '### 修复 1' onwards
sections["bugfixes"] = remaining.rstrip() + "\n"

os.makedirs("d:/enployment_service_agent/docs/progress", exist_ok=True)

for name, text in sections.items():
    filepath = f"d:/enployment_service_agent/docs/progress/{name}.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)
    lines = len(text.splitlines())
    print(f"{filepath}: {lines} lines")

# Verify total lines
total = sum(len(text.splitlines()) for text in sections.values())
orig_lines = len(content.splitlines())
print(f"Original: {orig_lines} lines, Split total: {total} lines")
