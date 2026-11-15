# Known "not built yet" error texts for wire-after-build contract

These are the exact strings seen in `Claude/logs/verse-errors.jsonl`, MCP tool responses, and `uefn-lessons` entries across projects.

## From ListDeviceProperties / GetDeviceProperties / SetDeviceProperty
- `"Verse device '<path>' has no resolved Script subobject (build Verse first?)"` — a Verse device whose class hasn't been built yet (verse-build area trap 5, level-devices area trap 5)
- `"Parameter error: <actor> is not valid ScriptDevice for property 'Device'"` — same tools on a non-device actor (level-devices area trap 5)

## From AddEventBinding
- `"Source device has no bindable event named 'OnX'."` — the device's event list is not yet populated (level-devices area trap 6)

## Generic error keywords (case-insensitive, substring match)
- `"class not found"` / `"Class not found"` / `"NoClass"` / `"class_not_found"`
- `"no hash"` / `"No hash"` / `"hash not found"` / `"hash_not_found"`
- `"stale reflection"` / `"Stale reflection"` / `"reflection not ready"` / `"reflection_stale"`
- `"not compiled"` / `"Not compiled"` / `"verse not built"` / `"Verse not built"`
- `"no editable properties"` / `"No editable properties"` / `"editable properties not found"` / `"editable_properties_not_found"`
- `"reflection"` + `"pending"` / `"updating"` / `"initializing"`

## Behavioural signal
- Device property list returns empty or missing the expected `@editable` field name

These are checked by the contract's step 1: on failure, the error text is matched against this list (case-insensitive substring match for the generic keywords; exact for the first three).