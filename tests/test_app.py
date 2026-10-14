"""GUI behavior tests without a real display or USB keyboard."""
import sys
import types
import unittest
from unittest import mock

# Tests must also run on machines without HIDAPI installed.
sys.modules.setdefault("hid", types.SimpleNamespace())
import app
from blade_protocol import effect_packet


class FakeVar:
    def __init__(self, value=None):
        self.value = value
        self.callbacks = []

    def get(self):
        return self.value

    def set(self, value):
        self.value = value
        for callback in self.callbacks:
            callback("fake", "fake", "write")

    def trace_add(self, mode, callback):
        assert mode == "write"
        self.callbacks.append(callback)


class FakeRoot:
    def __init__(self):
        self.now_ms = 0
        self.jobs = {}
        self._next_job = 0
        self.destroyed = False

    def after(self, delay, callback):
        self._next_job += 1
        job = self._next_job
        self.jobs[job] = (self.now_ms + delay, callback)
        return job

    def after_cancel(self, job):
        del self.jobs[job]

    def advance(self, milliseconds):
        deadline = self.now_ms + milliseconds
        while True:
            ready = sorted((when, job) for job, (when, _) in self.jobs.items() if when <= deadline)
            if not ready:
                break
            when, job = ready[0]
            self.now_ms = when
            _, callback = self.jobs.pop(job)
            callback()
        self.now_ms = deadline

    def title(self, *_):
        pass

    def geometry(self, *_):
        pass

    def minsize(self, *_):
        pass

    def configure(self, **_):
        pass

    def protocol(self, *_):
        pass

    def destroy(self):
        self.destroyed = True


class FakeDevice:
    def __init__(self):
        self.dev = None
        self.available = True
        self.fail_send = False
        self.connect_attempts = 0
        self.writes = []

    def connect(self):
        self.connect_attempts += 1
        if not self.available:
            raise RuntimeError("Not connected")
        self.dev = object()

    def send(self, packets):
        self.writes.append(packets)
        if self.fail_send:
            raise OSError("HID disconnected")

    def close(self):
        self.dev = None


class AutomaticEffectTests(unittest.TestCase):
    def setUp(self):
        self.root = FakeRoot()
        self.device = FakeDevice()
        self.device_patcher = mock.patch.object(app, "BladeDevice", return_value=self.device)
        self.ui_patcher = mock.patch.object(app.App, "_ui")
        self.vars_patcher = mock.patch.multiple(app.tk, StringVar=FakeVar, BooleanVar=FakeVar, IntVar=FakeVar)
        self.time_patcher = mock.patch.object(app.time, "monotonic", new=lambda: self.root.now_ms / 1000)
        for patcher in (self.device_patcher, self.ui_patcher, self.vars_patcher, self.time_patcher):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.gui = app.App(self.root)

    def test_autoconnect_does_not_write_default_effect(self):
        self.assertEqual(self.device.connect_attempts, 0)
        self.root.advance(100)
        self.assertEqual(self.device.connect_attempts, 1)
        self.assertIsNotNone(self.device.dev)
        self.assertEqual(self.device.writes, [])

    def test_settings_auto_apply_and_coalesce_slider_changes(self):
        self.root.advance(100)
        self.gui.brightness.set(1)
        self.root.advance(200)
        self.gui.brightness.set(2)
        self.root.advance(349)
        self.assertEqual(len(self.device.writes), 0)
        self.root.advance(1)
        self.assertEqual(self.device.writes, [[effect_packet("Static", "Blue", 2, 2)]])

    def test_rapid_changes_are_rate_limited_and_duplicates_skipped(self):
        self.root.advance(100)
        self.gui.mode.set("Breathing")
        self.root.advance(350)
        self.assertEqual(len(self.device.writes), 1)
        self.gui.speed.set(3)
        self.root.advance(999)
        self.assertEqual(len(self.device.writes), 1)
        self.root.advance(1)
        self.assertEqual(self.device.writes[-1], [effect_packet("Breathing", "Blue", 3, 4)])
        self.gui.speed.set(3)
        self.root.advance(1000)
        self.assertEqual(len(self.device.writes), 2)

    def test_missing_keyboard_retries_and_applies_queued_changes(self):
        self.device.available = False
        self.root.advance(100)
        self.assertIsNone(self.device.dev)
        self.gui.palette.set("Red")
        self.assertEqual(self.device.writes, [])
        self.device.available = True
        self.root.advance(3000)
        self.assertIsNotNone(self.device.dev)
        self.root.advance(350)
        self.assertEqual(self.device.writes, [[effect_packet("Static", "Red", 2, 4)]])

    def test_failed_write_does_not_auto_retry_to_protect_flash(self):
        self.root.advance(100)
        self.device.fail_send = True
        self.gui.mode.set("Breathing")
        self.root.advance(350)
        self.assertEqual(len(self.device.writes), 1)
        self.assertIsNone(self.device.dev)
        self.device.fail_send = False
        self.root.advance(3000)
        self.assertEqual(len(self.device.writes), 1)
        self.assertIsNotNone(self.device.dev)
        self.gui.mode.set("Static")
        self.root.advance(350)
        self.assertEqual(len(self.device.writes), 2)

    def test_custom_rgb_still_requires_manual_apply(self):
        self.root.advance(100)
        self.gui.colors = ["#123456"] * 104
        self.root.advance(5000)
        self.assertEqual(self.device.writes, [])
        self.gui.apply_custom()
        self.assertEqual(len(self.device.writes), 1)
        self.assertEqual(len(self.device.writes[0]), 9)

    def test_close_cancels_reconnection_and_effect_jobs(self):
        self.root.advance(100)
        self.gui.palette.set("Green")
        self.gui.close()
        self.assertTrue(self.root.destroyed)
        self.assertEqual(self.root.jobs, {})
        self.root.advance(5000)
        self.assertEqual(self.device.writes, [])


if __name__ == "__main__":
    unittest.main()
