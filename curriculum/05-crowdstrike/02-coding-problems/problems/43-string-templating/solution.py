import re

PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")


def render(template, values):
    if not isinstance(template, str) or not isinstance(values, dict):
        raise ValueError("template must be a string and values a dict")

    def lookup(match):
        name = match.group(1)
        if name not in values:
            raise KeyError(name)
        return str(values[name])

    return PLACEHOLDER.sub(lookup, template)


def render_config(config, values):
    if not isinstance(config, dict) or not isinstance(values, dict):
        raise ValueError("config and values must be dicts")

    def walk(node):
        if isinstance(node, dict):
            return {key: walk(child) for key, child in node.items()}
        if isinstance(node, list):
            return [walk(child) for child in node]
        if isinstance(node, str):
            return render(node, values)
        return node

    return walk(config)
