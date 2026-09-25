import copy
import unittest
from solution import render, render_config

VALUES = {"db_host": "example.com", "db_port": 5001}


class RenderTests(unittest.TestCase):
    def test_representative(self):
        self.assertEqual(render("app -> {{db_host}}:{{db_port}}", VALUES), "app -> example.com:5001")

    def test_whitespace_and_repeats(self):
        self.assertEqual(render("{{ db_host }}", VALUES), "example.com")
        self.assertEqual(render("{{a}}-{{a}}", {"a": 1}), "1-1")

    def test_missing_name_is_loud(self):
        with self.assertRaises(KeyError) as ctx:
            render("{{nope}}", {})
        self.assertEqual(ctx.exception.args[0], "nope")

    def test_literal_braces(self):
        self.assertEqual(render("{x} and {{ open", {}), "{x} and {{ open")
        self.assertEqual(render("{{{db_port}}}", VALUES), "{5001}")

    def test_nested_config_without_mutation(self):
        config = {"db": {"url": "{{db_host}}"}, "ports": ["{{db_port}}", 1], "flag": True}
        snapshot = copy.deepcopy(config)
        self.assertEqual(render_config(config, VALUES),
                         {"db": {"url": "example.com"}, "ports": ["5001", 1], "flag": True})
        self.assertEqual(config, snapshot)

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            render(5, {})
        with self.assertRaises(ValueError):
            render("x", [])
        with self.assertRaises(ValueError):
            render_config([], {})


if __name__ == "__main__":
    unittest.main()
