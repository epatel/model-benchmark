import unittest

from bus import EventBus


class TestEventBus(unittest.TestCase):
    def test_publish_calls_in_order(self):
        bus = EventBus()
        seen = []
        bus.subscribe("e", lambda x: seen.append(("a", x)))
        bus.subscribe("e", lambda x: seen.append(("b", x)))
        bus.publish("e", 1)
        self.assertEqual(seen, [("a", 1), ("b", 1)])

    def test_unsubscribe_stops_calls(self):
        bus = EventBus()
        seen = []

        def h(x):
            seen.append(x)

        bus.subscribe("e", h)
        bus.unsubscribe("e", h)
        bus.publish("e", 1)
        self.assertEqual(seen, [])

    def test_subscribe_once_fires_once(self):
        bus = EventBus()
        seen = []
        bus.subscribe_once("e", lambda x: seen.append(x))
        bus.publish("e", 1)
        bus.publish("e", 2)
        self.assertEqual(seen, [1])


if __name__ == "__main__":
    unittest.main()
