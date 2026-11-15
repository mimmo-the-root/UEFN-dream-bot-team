#!/usr/bin/env python3
"""
Tests for the device wiring simulator.

Tests:
- A chain of device connections
- A loop in the wiring
- A broken wire (event wired to non-existent function)
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add the hooks directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'project-template', 'Claude', 'hooks'))

from device_sim import (
    load_signals,
    parse_wiring_from_devices_md,
    load_wiring_json,
    get_wiring,
    build_reverse_wiring,
    get_device_signals,
    simulate_chain,
    check_wiring,
    print_simulation,
    print_check_results
)


class TestDeviceSignals(unittest.TestCase):
    """Test loading and accessing device signals."""

    def setUp(self):
        self.test_signals = {
            "Button": {
                "events_emitted": ["InteractedWith", "Disabled"],
                "functions_received": ["Enable", "Disable", "Reset"]
            },
            "Trigger": {
                "events_emitted": ["Triggered", "Disabled"],
                "functions_received": ["Enable", "Disable", "Reset"]
            },
            "ItemGranter": {
                "events_emitted": ["ItemGranted", "Disabled"],
                "functions_received": ["GrantItem", "Enable", "Disable"]
            }
        }

    def test_load_signals(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"devices": self.test_signals}, f)
            temp_path = f.name

        try:
            loaded = load_signals(temp_path)
            self.assertEqual(loaded, self.test_signals)
        finally:
            os.unlink(temp_path)

    def test_get_device_signals_exact_match(self):
        signals = get_device_signals("Button", self.test_signals)
        self.assertEqual(signals, self.test_signals["Button"])

    def test_get_device_signals_with_suffix(self):
        signals = get_device_signals("Button_1", self.test_signals)
        self.assertEqual(signals, self.test_signals["Button"])

    def test_get_device_signals_unknown(self):
        signals = get_device_signals("UnknownDevice", self.test_signals)
        self.assertIsNone(signals)


class TestWiringParsing(unittest.TestCase):
    """Test parsing wiring from DEVICES.md and JSON."""

    def test_parse_wiring_from_devices_md(self):
        content = """# Devices

WIRING-READ: yes

- Button_1.InteractedWith -> Trigger_1.Enable
- Trigger_1.Triggered -> ItemGranter_1.GrantItem
- ItemGranter_1.ItemGranted -> HUDMessage_1.Show
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            wiring = parse_wiring_from_devices_md(temp_path)
            self.assertEqual(len(wiring), 3)
            self.assertIn("Button_1", wiring)
            self.assertEqual(wiring["Button_1"][0]["event"], "InteractedWith")
            self.assertEqual(wiring["Button_1"][0]["target_device"], "Trigger_1")
            self.assertEqual(wiring["Button_1"][0]["target_function"], "Enable")
        finally:
            os.unlink(temp_path)

    def test_load_wiring_json(self):
        wiring_data = {
            "Button_1": [{"event": "InteractedWith", "target_device": "Trigger_1", "target_function": "Enable"}],
            "Trigger_1": [{"event": "Triggered", "target_device": "ItemGranter_1", "target_function": "GrantItem"}]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(wiring_data, f)
            temp_path = f.name

        try:
            wiring = load_wiring_json(temp_path)
            self.assertEqual(wiring, wiring_data)
        finally:
            os.unlink(temp_path)


class TestSimulation(unittest.TestCase):
    """Test the simulation logic."""

    def setUp(self):
        self.signals = {
            "Button": {
                "events_emitted": ["InteractedWith", "Disabled"],
                "functions_received": ["Enable", "Disable", "Reset"]
            },
            "Trigger": {
                "events_emitted": ["Triggered", "Disabled"],
                "functions_received": ["Enable", "Disable", "Reset"]
            },
            "ItemGranter": {
                "events_emitted": ["ItemGranted", "Disabled"],
                "functions_received": ["GrantItem", "Enable", "Disable"]
            },
            "HUDMessage": {
                "events_emitted": ["MessageShown", "Disabled"],
                "functions_received": ["Show", "Hide", "Enable", "Disable"]
            }
        }

        self.wiring = {
            "Button_1": [
                {"event": "InteractedWith", "target_device": "Trigger_1", "target_function": "Enable"}
            ],
            "Trigger_1": [
                {"event": "Triggered", "target_device": "ItemGranter_1", "target_function": "GrantItem"}
            ],
            "ItemGranter_1": [
                {"event": "ItemGranted", "target_device": "HUDMessage_1", "target_function": "Show"}
            ]
        }

    def test_simple_chain(self):
        """Test a simple chain: Button -> Trigger -> ItemGranter -> HUDMessage"""
        steps = simulate_chain("Button_1", "InteractedWith", self.wiring, self.signals)

        # Should have 3 wire steps + the final dead ends for emitted events
        wire_steps = [s for s in steps if s['type'] == 'wire']
        self.assertEqual(len(wire_steps), 3)

        # Check the chain
        self.assertEqual(wire_steps[0]['source_device'], "Button_1")
        self.assertEqual(wire_steps[0]['target_device'], "Trigger_1")
        self.assertEqual(wire_steps[1]['source_device'], "Trigger_1")
        self.assertEqual(wire_steps[1]['target_device'], "ItemGranter_1")
        self.assertEqual(wire_steps[2]['source_device'], "ItemGranter_1")
        self.assertEqual(wire_steps[2]['target_device'], "HUDMessage_1")

    def test_dead_end(self):
        """Test event with no wiring"""
        steps = simulate_chain("Button_1", "Disabled", self.wiring, self.signals)
        self.assertEqual(steps[0]['type'], 'dead_end')

    def test_unknown_device(self):
        """Test unknown source device"""
        steps = simulate_chain("Unknown_1", "InteractedWith", self.wiring, self.signals)
        self.assertEqual(steps[0]['type'], 'unknown_device')

    def test_invalid_function(self):
        """Test wire to function that doesn't exist"""
        wiring = {
            "Button_1": [
                {"event": "InteractedWith", "target_device": "Trigger_1", "target_function": "NonExistentFunc"}
            ]
        }
        steps = simulate_chain("Button_1", "InteractedWith", wiring, self.signals)
        # First step is the wire, second should be invalid_function
        self.assertEqual(steps[0]['type'], 'wire')
        self.assertEqual(steps[1]['type'], 'invalid_function')

    def test_unknown_target_device(self):
        """Test wire to unknown device type"""
        wiring = {
            "Button_1": [
                {"event": "InteractedWith", "target_device": "UnknownDevice_1", "target_function": "Enable"}
            ]
        }
        steps = simulate_chain("Button_1", "InteractedWith", wiring, self.signals)
        self.assertEqual(steps[0]['type'], 'wire')
        self.assertEqual(steps[1]['type'], 'unknown_target')


class TestLoopDetection(unittest.TestCase):
    """Test loop detection in simulation."""

    def setUp(self):
        self.signals = {
            "Trigger": {
                "events_emitted": ["Triggered", "Disabled"],
                "functions_received": ["Enable", "Disable", "Reset"]
            }
        }

    def test_loop_detection(self):
        """Test that loops are detected and cut"""
        # Trigger_1 triggers Trigger_2, which triggers Trigger_1
        wiring = {
            "Trigger_1": [
                {"event": "Triggered", "target_device": "Trigger_2", "target_function": "Enable"}
            ],
            "Trigger_2": [
                {"event": "Triggered", "target_device": "Trigger_1", "target_function": "Enable"}
            ]
        }

        steps = simulate_chain("Trigger_1", "Triggered", wiring, self.signals, max_depth=10)

        # Should have wire steps and then a loop detection
        loop_steps = [s for s in steps if s['type'] == 'loop']
        self.assertEqual(len(loop_steps), 1)
        self.assertIn("Loop detected", loop_steps[0]['message'])


class TestCheckWiring(unittest.TestCase):
    """Test the check_wiring function."""

    def setUp(self):
        self.signals = {
            "Button": {
                "events_emitted": ["InteractedWith", "Disabled"],
                "functions_received": ["Enable", "Disable", "Reset"]
            },
            "Trigger": {
                "events_emitted": ["Triggered", "Disabled"],
                "functions_received": ["Enable", "Disable", "Reset"]
            },
            "ItemGranter": {
                "events_emitted": ["ItemGranted", "Disabled"],
                "functions_received": ["GrantItem", "Enable", "Disable"]
            }
        }

    def test_events_wired_to_nothing(self):
        """Test detection of events that source device doesn't emit"""
        wiring = {
            "Button_1": [
                {"event": "NonExistentEvent", "target_device": "Trigger_1", "target_function": "Enable"}
            ]
        }
        issues = check_wiring(wiring, self.signals)
        self.assertIn("Button_1.NonExistentEvent", str(issues['events_wired_to_nothing']))

    def test_functions_nobody_calls(self):
        """Test detection of functions that no wire calls"""
        wiring = {
            "Button_1": [
                {"event": "InteractedWith", "target_device": "Trigger_1", "target_function": "Enable"}
            ]
            # Trigger_1 has Disable and Reset but nobody calls them
        }
        issues = check_wiring(wiring, self.signals)
        # Should detect Trigger_1.Disable and Trigger_1.Reset as uncalled
        self.assertTrue(any("Trigger_1.Disable" in f for f in issues['functions_nobody_calls']))
        self.assertTrue(any("Trigger_1.Reset" in f for f in issues['functions_nobody_calls']))

    def test_wires_to_missing_function(self):
        """Test detection of wires to non-existent functions"""
        wiring = {
            "Button_1": [
                {"event": "InteractedWith", "target_device": "Trigger_1", "target_function": "NonExistentFunc"}
            ]
        }
        issues = check_wiring(wiring, self.signals)
        self.assertTrue(any("Trigger_1.NonExistentFunc" in w for w in issues['wires_to_missing_function']))

    def test_unknown_devices(self):
        """Test detection of unknown device types"""
        wiring = {
            "Unknown_1": [
                {"event": "SomeEvent", "target_device": "Trigger_1", "target_function": "Enable"}
            ],
            "Button_1": [
                {"event": "InteractedWith", "target_device": "UnknownTarget_1", "target_function": "Enable"}
            ]
        }
        issues = check_wiring(wiring, self.signals)
        self.assertIn("Unknown_1", issues['unknown_source_devices'])
        self.assertTrue(any("UnknownTarget_1" in d for d in issues['unknown_target_devices']))


class TestIntegration(unittest.TestCase):
    """Integration test with a fake wiring file."""

    def setUp(self):
        self.signals = {
            "Button": {
                "events_emitted": ["InteractedWith", "Disabled"],
                "functions_received": ["Enable", "Disable", "Reset"]
            },
            "Trigger": {
                "events_emitted": ["Triggered", "Disabled"],
                "functions_received": ["Enable", "Disable", "Reset"]
            },
            "ItemGranter": {
                "events_emitted": ["ItemGranted", "Disabled"],
                "functions_received": ["GrantItem", "Enable", "Disable"]
            }
        }

    def test_full_integration_with_temp_files(self):
        """Test the full flow with temporary files"""
        # Create temp signals file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"devices": self.signals}, f)
            signals_file = f.name

        # Create temp wiring file (JSON)
        wiring_data = {
            "Button_1": [
                {"event": "InteractedWith", "target_device": "Trigger_1", "target_function": "Enable"}
            ],
            "Trigger_1": [
                {"event": "Triggered", "target_device": "ItemGranter_1", "target_function": "GrantItem"}
            ],
            "ItemGranter_1": [
                {"event": "ItemGranted", "target_device": "Trigger_1", "target_function": "Enable"}  # Creates a loop
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(wiring_data, f)
            wiring_file = f.name

        try:
            # Load
            signals = load_signals(signals_file)
            wiring = load_wiring_json(wiring_file)

            # Simulate
            steps = simulate_chain("Button_1", "InteractedWith", wiring, signals, max_depth=5)
            wire_steps = [s for s in steps if s['type'] == 'wire']
            loop_steps = [s for s in steps if s['type'] == 'loop']

            # Should have 3 wires before loop detection
            self.assertEqual(len(wire_steps), 3)
            self.assertEqual(len(loop_steps), 1)

            # Check
            issues = check_wiring(wiring, signals)
            # Trigger_1.Disable and Trigger_1.Reset are uncalled
            # ItemGranter_1.Disable is uncalled
            self.assertTrue(len(issues['functions_nobody_calls']) >= 2)

        finally:
            os.unlink(signals_file)
            os.unlink(wiring_file)


def run_tests():
    """Run all tests and return result."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDeviceSignals))
    suite.addTests(loader.loadTestsFromTestCase(TestWiringParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestSimulation))
    suite.addTests(loader.loadTestsFromTestCase(TestLoopDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestCheckWiring))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)