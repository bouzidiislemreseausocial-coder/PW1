import re
import sys
from collections import Counter
from typing import List, NamedTuple, Tuple
KEYWORDS = {"if", "else", "while", "int", "float"}
TOKEN_SPECIFICATION = [
    ("COMMENT", r"//[^\n]*"),
    ("NEWLINE", r"\n"),
    ("WHITESPACE", r"[ \t\r]+"),
    ("BAD_ID", r"\d+(?:\.\d+)?[A-Za-z_]\w*"),
    ("REAL", r"\d+\.\d+"),
    ("BAD_NUMBER", r"\d+\."),
    ("INTEGER", r"\d+"),
    ("IDENTIFIER", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("RELATIONAL_OPERATOR", r"==|!=|<=|>=|<|>"),
    ("ASSIGNMENT_OPERATOR", r"="),
    ("ARITHMETIC_OPERATOR", r"[+\-*/]"),
    ("SEPARATOR", r"[;,(){}]"),
    ("INVALID", r"."),
]
MASTER = re.compile("|".join(f"(?P<{n}>{r})" for n, r in TOKEN_SPECIFICATION))
ERROR_MESSAGES = {
    "BAD_ID": "malformed identifier",
    "BAD_NUMBER": "malformed number",
    "INVALID": "invalid character",
}
class Token(NamedTuple):
    type: str
    lexeme: str
    line: int
    column: int
class LexError(NamedTuple):
    message: str
    lexeme: str
    line: int
    column: int
def lexical_analysis(source: str) -> Tuple[List[Token], List[LexError]]:
    tokens, errors = [], []
    line, line_start = 1, 0
    for m in MASTER.finditer(source):
        kind, text = m.lastgroup, m.group()
        column = m.start() - line_start + 1
        if kind == "NEWLINE":
            line += 1
            line_start = m.end()
        elif kind in ("WHITESPACE", "COMMENT"):
            continue
        elif kind in ERROR_MESSAGES:
            errors.append(LexError(ERROR_MESSAGES[kind], text, line, column))
        else:
            if kind == "IDENTIFIER" and text in KEYWORDS:
                kind = "KEYWORD"
            tokens.append(Token(kind, text, line, column))
    return tokens, errors
def report(source: str) -> bool:
    tokens, errors = lexical_analysis(source)

    print(f"  {'TYPE':<20} {'LEXEME':<10} LINE  COL")
    for t in tokens:
        print(f"  {t.type:<20} {t.lexeme:<10} {t.line:<5} {t.column}")

    for e in errors:
        print(f"  LEXICAL ERROR: {e.message} '{e.lexeme}' at line {e.line}, column {e.column}")

    print(f"  -- Total tokens: {len(tokens)} | lexical errors: {len(errors)}")
    for kind, n in sorted(Counter(t.type for t in tokens).items()):
        print(f"     {kind:<20}: {n}")
    per_line = Counter(t.line for t in tokens)
    if per_line:
        print("     per line: " + ", ".join(f"L{ln}={n}" for ln, n in sorted(per_line.items())))
    return not errors
def self_test() -> None:
    types = lambda s: [t.type for t in lexical_analysis(s)[0]]
    lexemes = lambda s: [t.lexeme for t in lexical_analysis(s)[0]]
    errs = lambda s: [(e.lexeme, e.line, e.column) for e in lexical_analysis(s)[1]]

    tests = [
        "int x = 12;",
        "float result = 3.14 + value;",
        "if (x >= 10) {\n    x = x - 1;\n}",
        "int 2x = 10;",
        "int x = 10 @ 2;;",
        "int x = 10; // initialize x\nfloat y = 2.5;",
        "a = b >= 10;\nc == d;",
    ]
    for i, src in enumerate(tests, 1):
        label = f"Test {i}" if i <= 5 else ("Comment example" if i == 6 else "Maximal munch")
        print(f"\n{label}: {src!r}")
        report(src)
    assert types("int x = 12;") == ["KEYWORD", "IDENTIFIER", "ASSIGNMENT_OPERATOR", "INTEGER", "SEPARATOR"]
    assert "REAL" in types("float result = 3.14 + value;")
    assert ">=" in lexemes("if (x >= 10) {") and ">" not in lexemes("if (x >= 10) {")
    assert errs("int 2x = 10;") == [("2x", 1, 5)]
    assert errs("int x = 10 @ 2;;") == [("@", 1, 12)]
    assert lexemes("int x = 10; // initialize x\nfloat y = 2.5;").count("initialize") == 0
    assert len(lexical_analysis("int x = 10; // initialize x\nfloat y = 2.5;")[0]) == 10
    assert lexemes("a = b >= 10;\nc == d;") == ["a", "=", "b", ">=", "10", ";", "c", "==", "d", ";"]
    assert errs("x = 3.;") == [("3.", 1, 5)]
    print("\nAll automatic checks passed.")
if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        self_test()
    elif args[0] == "-c" and len(args) > 1:
        sys.exit(0 if report(args[1]) else 1)
    else:
        with open(args[0], encoding="utf-8") as f:
            sys.exit(0 if report(f.read()) else 1)