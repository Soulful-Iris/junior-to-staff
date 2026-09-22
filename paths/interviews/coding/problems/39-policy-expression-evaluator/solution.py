"""A small explicit policy language; never use Python eval on policy input."""
from collections.abc import Mapping
from dataclasses import dataclass
import json
import re

MAX_CHARS = 65536
MAX_TOKENS = 4096
MAX_DEPTH = 100


@dataclass(frozen=True)
class Token:
    kind: str
    value: object
    position: int


_TOKEN = re.compile(
    r'(?P<SPACE>\s+)|(?P<STRING>"(?:\\.|[^"\\\x00-\x1f])*")'
    r'|(?P<NUMBER>-?(?:0|[1-9][0-9]*))|(?P<EQ>==)|(?P<NE>!=)'
    r'|(?P<LPAREN>\()|(?P<RPAREN>\))|(?P<ID>[A-Za-z_][A-Za-z0-9_.]*)'
)


def lex(expression):
    if not isinstance(expression, str) or len(expression) > MAX_CHARS:
        raise ValueError("policy must be a string of at most 65536 characters")
    tokens, position = [], 0
    while position < len(expression):
        match = _TOKEN.match(expression, position)
        if match is None:
            raise ValueError(f"invalid token at position {position}")
        kind, value = match.lastgroup, match.group()
        if kind != 'SPACE':
            if kind == 'ID' and value in ('AND', 'OR', 'TRUE', 'FALSE'):
                kind = value
            if kind == 'STRING':
                try:
                    value = json.loads(value)
                except ValueError as exc:
                    raise ValueError(f"invalid string at position {position}") from exc
            elif kind == 'NUMBER':
                value = int(value)
            elif kind in ('TRUE', 'FALSE'):
                value = kind == 'TRUE'
            tokens.append(Token(kind, value, position))
            if len(tokens) > MAX_TOKENS:
                raise ValueError("policy exceeds 4096 tokens")
        position = match.end()
    tokens.append(Token('EOF', None, position))
    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens, self.position = tokens, 0

    def take(self, kind):
        token = self.tokens[self.position]
        if token.kind != kind:
            raise ValueError(f"expected {kind} at position {token.position}")
        self.position += 1
        return token.value

    def parse(self):
        node = self.expression(0)
        self.take('EOF')
        return node

    def expression(self, depth):
        node = self.conjunction(depth)
        while self.tokens[self.position].kind == 'OR':
            self.take('OR')
            node = ('OR', node, self.conjunction(depth))
        return node

    def conjunction(self, depth):
        node = self.factor(depth)
        while self.tokens[self.position].kind == 'AND':
            self.take('AND')
            node = ('AND', node, self.factor(depth))
        return node

    def factor(self, depth):
        if self.tokens[self.position].kind == 'LPAREN':
            if depth >= MAX_DEPTH:
                raise ValueError("policy exceeds 100 nested parentheses")
            self.take('LPAREN')
            node = self.expression(depth + 1)
            self.take('RPAREN')
            return node
        field = self.take('ID')
        kind = self.tokens[self.position].kind
        if kind not in ('EQ', 'NE'):
            raise ValueError(f"expected comparison at position {self.tokens[self.position].position}")
        self.take(kind)
        literal_kind = self.tokens[self.position].kind
        if literal_kind not in ('STRING', 'NUMBER', 'TRUE', 'FALSE'):
            raise ValueError(f"expected literal at position {self.tokens[self.position].position}")
        return ('PRED', field, kind, self.take(literal_kind))


def evaluate(expression, record):
    if not isinstance(record, Mapping):
        raise ValueError("record must be a mapping")
    tree = Parser(lex(expression)).parse()
    # Explicit traversal avoids recursion on long left-associated AND/OR chains.
    pending, results = [(tree, False)], []
    while pending:
        node, left_done = pending.pop()
        if node[0] == 'PRED':
            _, field, operator, expected = node
            if field not in record:
                results.append(False)
            else:
                actual = record[field]
                equal = type(actual) is type(expected) and actual == expected
                # A mismatched type fails both comparison operators.
                results.append(equal if operator == 'EQ' else
                               type(actual) is type(expected) and not equal)
        elif not left_done:
            pending.append((node, True))
            pending.append((node[1], False))
        else:
            left = results.pop()
            if (node[0] == 'AND' and not left) or (node[0] == 'OR' and left):
                results.append(left)
            else:
                pending.append((node[2], False))
    return results[0]
