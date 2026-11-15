#!/usr/bin/env python3
"""
Offline simulator of device wiring.

Reads the wiring the kit learned (Claude/docs/map/DEVICES.md WIRING-READ lines, or a JSON snapshot),
and:
- `sim <device> <event>` prints the chain of what happens (device -> event -> device.function -> its events ...),
  with loops cut and unknown devices marked.
- `check` lists: events wired to nothing, functions nobody calls, wires to a function the target does not have.

Usage:
  python device_sim.py sim <device> <event> [--wiring-file <path>] [--signals-file <path>] [--max-depth <n>]
  python device_sim.py check [--wiring-file <path>] [--signals-file <path>]
"""

import json
import os
import re
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple


def load_signals(signals_file: str) -> Dict[str, Any]:
    """Load device signals from JSON file."""
    with open(signals_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('devices', {})


def parse_wiring_from_devices_md(wiring_file: str) -> Dict[str, List[Dict]]:
    """
    Parse wiring from DEVICES.md file.
    Expected format: WIRING-READ: yes and then lines like:
    - Button_1.InteractedWith -> Trigger_1.Enable
    """
    wiring = defaultdict(list)

    if not os.path.isfile(wiring_file):
        return dict(wiring)

    with open(wiring_file, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Look for wiring lines: SourceDevice.Event -> TargetDevice.Function
    # Pattern handles device names with underscores, numbers, etc.
    pattern = r'([A-Za-z_][A-Za-z0-9_]*)\.(\w+)\s*->\s*([A-Za-z_][A-Za-z0-9_]*)\.(\w+)'

    for match in re.finditer(pattern, content):
        src_device, src_event, tgt_device, tgt_func = match.groups()
        wiring[src_device].append({
            'event': src_event,
            'target_device': tgt_device,
            'target_function': tgt_func
        })

    return dict(wiring)


def load_wiring_json(wiring_file: str) -> Dict[str, List[Dict]]:
    """Load wiring from JSON snapshot file."""
    with open(wiring_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Expected format: { "device_name": [{"event": "...", "target_device": "...", "target_function": "..."}, ...] }
    if isinstance(data, dict):
        return data
    return {}


def get_wiring(wiring_file: str) -> Dict[str, List[Dict]]:
    """Load wiring from either DEVICES.md or JSON file."""
    if wiring_file.endswith('.json'):
        return load_wiring_json(wiring_file)
    else:
        return parse_wiring_from_devices_md(wiring_file)


def build_reverse_wiring(wiring: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """Build reverse wiring: target_device.function -> list of (source_device, event)."""
    reverse = defaultdict(list)
    for src_device, connections in wiring.items():
        for conn in connections:
            key = f"{conn['target_device']}.{conn['target_function']}"
            reverse[key].append({
                'source_device': src_device,
                'event': conn['event']
            })
    return dict(reverse)


def get_device_signals(device_name: str, signals: Dict) -> Optional[Dict]:
    """Get signals for a device, matching by base name (without number suffix)."""
    # Try exact match first
    if device_name in signals:
        return signals[device_name]

    # Try base name (strip trailing _N or _NN)
    base = re.sub(r'_\d+$', '', device_name)
    if base in signals:
        return signals[base]

    return None


def simulate_chain(
    start_device: str,
    start_event: str,
    wiring: Dict[str, List[Dict]],
    signals: Dict,
    max_depth: int = 20,
    visited: Optional[Set[str]] = None,
    depth: int = 0
) -> List[Dict]:
    """
    Simulate the chain of events from a starting device/event.
    Returns a list of steps in the chain.
    """
    if visited is None:
        visited = set()

    if depth >= max_depth:
        return [{'type': 'max_depth', 'device': start_device, 'event': start_event, 'message': f'Max depth ({max_depth}) reached'}]

    # Check for loops
    step_key = f"{start_device}.{start_event}"
    if step_key in visited:
        return [{'type': 'loop', 'device': start_device, 'event': start_event, 'message': f'Loop detected: {step_key}'}]

    visited.add(step_key)

    # Check if device exists in wiring
    if start_device not in wiring:
        return [{
            'type': 'unknown_device',
            'device': start_device,
            'event': start_event,
            'message': f'Device {start_device} not found in wiring'
        }]

    # Find connections for this event
    connections = [c for c in wiring[start_device] if c['event'] == start_event]

    if not connections:
        return [{
            'type': 'dead_end',
            'device': start_device,
            'event': start_event,
            'message': f'No wiring found for {start_device}.{start_event}'
        }]

    steps = []
    for conn in connections:
        tgt_device = conn['target_device']
        tgt_func = conn['target_function']

        step = {
            'type': 'wire',
            'source_device': start_device,
            'source_event': start_event,
            'target_device': tgt_device,
            'target_function': tgt_func,
            'message': f'{start_device}.{start_event} -> {tgt_device}.{tgt_func}'
        }
        steps.append(step)

        # Check if target device has this function
        tgt_signals = get_device_signals(tgt_device, signals)
        if not tgt_signals:
            steps.append({
                'type': 'unknown_target',
                'device': tgt_device,
                'function': tgt_func,
                'message': f'Unknown device type: {tgt_device} (cannot verify function {tgt_func})'
            })
            continue

        if tgt_func not in tgt_signals.get('functions_received', []):
            steps.append({
                'type': 'invalid_function',
                'device': tgt_device,
                'function': tgt_func,
                'message': f'{tgt_device} does not have function {tgt_func}'
            })
            continue

        # Get events emitted by the target device when this function is called
        # For simulation, we assume calling a function may trigger the device's emitted events
        # This is a simplification - in reality, only specific functions trigger specific events
        emitted_events = tgt_signals.get('events_emitted', [])

        for emitted in emitted_events:
            # Recursively simulate
            sub_steps = simulate_chain(
                tgt_device, emitted, wiring, signals, max_depth, visited.copy(), depth + 1
            )
            steps.extend(sub_steps)

    return steps


def check_wiring(wiring: Dict[str, List[Dict]], signals: Dict) -> Dict[str, List[str]]:
    """
    Check wiring for issues:
    - events wired to nothing
    - functions nobody calls
    - wires to a function the target does not have
    """
    issues = {
        'events_wired_to_nothing': [],
        'functions_nobody_calls': [],
        'wires_to_missing_function': [],
        'unknown_source_devices': [],
        'unknown_target_devices': []
    }

    # Track all devices mentioned in wiring
    all_source_devices = set(wiring.keys())
    all_target_devices = set()
    all_target_functions = defaultdict(set)

    for src_device, connections in wiring.items():
        src_signals = get_device_signals(src_device, signals)
        if not src_signals:
            issues['unknown_source_devices'].append(src_device)

        for conn in connections:
            tgt_device = conn['target_device']
            tgt_func = conn['target_function']
            all_target_devices.add(tgt_device)
            all_target_functions[tgt_device].add(tgt_func)

            # Check if target device has this function
            tgt_signals = get_device_signals(tgt_device, signals)
            if not tgt_signals:
                issues['unknown_target_devices'].append(f"{tgt_device}.{tgt_func} (device unknown)")
            elif tgt_func not in tgt_signals.get('functions_received', []):
                issues['wires_to_missing_function'].append(f"{tgt_device}.{tgt_func} (not in functions_received)")

            # Check if source device emits this event
            if src_signals and conn['event'] not in src_signals.get('events_emitted', []):
                issues['events_wired_to_nothing'].append(f"{src_device}.{conn['event']} (not in events_emitted)")

    # Check for functions nobody calls
    for device, funcs in all_target_functions.items():
        device_signals = get_device_signals(device, signals)
        if device_signals:
            for func in device_signals.get('functions_received', []):
                if func not in funcs:
                    issues['functions_nobody_calls'].append(f"{device}.{func}")

    # Deduplicate
    for key in issues:
        issues[key] = sorted(set(issues[key]))

    return issues


def print_simulation(steps: List[Dict], indent: int = 0):
    """Print simulation steps with indentation."""
    prefix = "  " * indent
    for step in steps:
        stype = step.get('type', 'unknown')
        msg = step.get('message', '')

        if stype == 'wire':
            print(f"{prefix}-> {msg}")
        elif stype == 'loop':
            print(f"{prefix}[LOOP] {msg}")
        elif stype == 'dead_end':
            print(f"{prefix}[DEAD END] {msg}")
        elif stype == 'unknown_device':
            print(f"{prefix}[UNKNOWN DEVICE] {msg}")
        elif stype == 'unknown_target':
            print(f"{prefix}[UNKNOWN TARGET] {msg}")
        elif stype == 'invalid_function':
            print(f"{prefix}[INVALID FUNCTION] {msg}")
        elif stype == 'max_depth':
            print(f"{prefix}[MAX DEPTH] {msg}")
        else:
            print(f"{prefix}{msg}")


def print_check_results(issues: Dict[str, List[str]]):
    """Print check results."""
    total = sum(len(v) for v in issues.values())
    if total == 0:
        print("✓ No wiring issues found")
        return

    print(f"Found {total} wiring issue(s):\n")

    if issues['events_wired_to_nothing']:
        print("Events wired to nothing (source device doesn't emit them):")
        for e in issues['events_wired_to_nothing']:
            print(f"  - {e}")
        print()

    if issues['functions_nobody_calls']:
        print("Functions nobody calls:")
        for f in issues['functions_nobody_calls']:
            print(f"  - {f}")
        print()

    if issues['wires_to_missing_function']:
        print("Wires to functions the target device does not have:")
        for w in issues['wires_to_missing_function']:
            print(f"  - {w}")
        print()

    if issues['unknown_source_devices']:
        print("Unknown source devices (not in device-signals.json):")
        for d in issues['unknown_source_devices']:
            print(f"  - {d}")
        print()

    if issues['unknown_target_devices']:
        print("Unknown target devices (not in device-signals.json):")
        for d in issues['unknown_target_devices']:
            print(f"  - {d}")
        print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Offline simulator of device wiring')
    parser.add_argument('command', choices=['sim', 'check'], help='Command to run')
    parser.add_argument('device', nargs='?', help='Device name (for sim command)')
    parser.add_argument('event', nargs='?', help='Event name (for sim command)')
    parser.add_argument('--wiring-file', default='Claude/docs/map/DEVICES.md', help='Path to wiring file (DEVICES.md or JSON)')
    parser.add_argument('--signals-file', default='Claude/reference/device-signals.json', help='Path to device signals JSON')
    parser.add_argument('--max-depth', type=int, default=20, help='Maximum simulation depth')

    args = parser.parse_args()

    # Resolve paths relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    wiring_file = os.path.join(project_root, args.wiring_file)
    signals_file = os.path.join(project_root, args.signals_file)

    # Load data
    signals = load_signals(signals_file)
    wiring = get_wiring(wiring_file)

    if args.command == 'sim':
        if not args.device or not args.event:
            parser.error('sim command requires device and event arguments')

        print(f"Simulating: {args.device}.{args.event}")
        print("=" * 60)

        steps = simulate_chain(args.device, args.event, wiring, signals, args.max_depth)
        print_simulation(steps)

    elif args.command == 'check':
        print("Checking wiring...")
        print("=" * 60)

        issues = check_wiring(wiring, signals)
        print_check_results(issues)


if __name__ == '__main__':
    main()