import unittest
from app import main

class TestApp(unittest.TestCase):
    def test_main_runs(self):
        # Just check that main() runs without error
        try:
            main()
        except Exception as e:
            self.fail(f"main() raised an exception: {e}")

if __name__ == "__main__":
    unittest.main()
