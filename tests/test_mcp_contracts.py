"""Test that mcp-tool-contracts SKILL.md has the expected contracts and pointers from agents."""
import os, re, sys

root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
skill_path = os.path.join(root, "user-level-skills", "mcp-tool-contracts", "SKILL.md")
device_builder_path = os.path.join(root, "user-level-agents", "device-builder.md")
coder_path = os.path.join(root, "user-level-agents", "coder.md")

def read(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()

skill = read(skill_path)
device_builder = read(device_builder_path)
coder = read(coder_path)

ok = True

# 1. Check the wire-after-build contract exists in SKILL.md
if "## Contract: wire-after-build (retry wiring after Verse build)" not in skill:
    print("FAIL: wire-after-build contract not found in SKILL.md")
    ok = False
else:
    print("PASS: wire-after-build contract exists in SKILL.md")

# 2. Check the contract has the required sections
required_sections = ["**When:**", "**Use:**", "**Don't use:**", "**Procedure:**", '**Known "not built yet" error texts']
for sec in required_sections:
    if sec not in skill:
        print("FAIL: Required section '" + sec + "' missing from wire-after-build contract")
        ok = False
    else:
        print("PASS: Section '" + sec + "' present")

# 3. Check specific error texts are listed (in SKILL.md or its references)
refs_dir = os.path.join(root, "user-level-skills", "mcp-tool-contracts", "references")
wire_after_build_ref = os.path.join(refs_dir, "wire-after-build-errors.md")
ref_content = read(wire_after_build_ref) if os.path.exists(wire_after_build_ref) else ""
combined = skill + "\n" + ref_content

error_texts = [
    "Verse device '<path>' has no resolved Script subobject",
    "Parameter error: <actor> is not valid ScriptDevice",
    "Source device has no bindable event named",
    "class not found",
    "no hash",
    "stale reflection",
    "not compiled",
    "no editable properties",
    "reflection.*pending",
]
for et in error_texts:
    if re.search(et, combined):
        print("PASS: Error text pattern '" + et + "' found")
    else:
        print("FAIL: Error text pattern '" + et + "' NOT found")
        ok = False

# 4. Check device-builder.md has a pointer to the contract
if "wire-after-build" in device_builder and "mcp-tool-contracts/SKILL.md" in device_builder:
    print("PASS: device-builder.md has pointer to wire-after-build contract")
else:
    print("FAIL: device-builder.md missing pointer to wire-after-build contract")
    ok = False

# 5. Check coder.md has a pointer to the contract
if "wire-after-build" in coder and "mcp-tool-contracts/SKILL.md" in coder:
    print("PASS: coder.md has pointer to wire-after-build contract")
else:
    print("FAIL: coder.md missing pointer to wire-after-build contract")
    ok = False

# 6. Check verse_check.py is referenced
if "verse_check.py" in skill:
    print("PASS: verse_check.py referenced in contract")
else:
    print("FAIL: verse_check.py not referenced in contract")
    ok = False

sys.exit(0 if ok else 1)
