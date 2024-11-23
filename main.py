from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    ATOM = auto()
    OP = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    char: str

    @staticmethod
    def Atom(char: str) -> Token:
        return Token(TokenType.ATOM, char)

    @staticmethod
    def Op(char: str) -> Token:
        return Token(TokenType.OP, char)

    @staticmethod
    def Eof() -> Token:
        return Token(TokenType.EOF, "\0")

    def __str__(self) -> str:
        return f"{self.type.name.title()}({self.char!r})"


class BadTokenError(Exception):
    def __init__(self, token: Token) -> None:
        super().__init__(f"bad token: {token}")


class BadOpError(Exception):
    def __init__(self, op: str) -> None:
        super().__init__(f"bad op: {op!r}")


class Lexer:
    def __init__(self, input_string: str) -> None:
        self.tokens = []
        for char in input_string.replace(" ", ""):
            if char.isalnum():
                self.tokens.append(Token.Atom(char))
            else:
                self.tokens.append(Token.Op(char))
        self.tokens.reverse()

    def next(self) -> Token:
        if self.tokens:
            return self.tokens.pop()
        return Token.Eof()

    def peek(self) -> Token:
        if self.tokens:
            return self.tokens[-1]
        return Token.Eof()


class SType(Enum):
    ATOM = auto()
    CONS = auto()


@dataclass
class S:
    type: SType
    char: str
    vec: list[S]

    @staticmethod
    def Atom(char: str) -> S:
        return S(SType.ATOM, char, [])

    @staticmethod
    def Cons(char: str, vec: list[S]) -> S:
        return S(SType.CONS, char, vec)

    def __repr__(self) -> str:
        return f"S({self.type}, {self.char}, {self.vec})"

    def __str__(self) -> str:
        if self.type == SType.ATOM:
            return self.char

        # NOTE: enum SType only has two variants, therefore we do not need an
        #       else path here.
        string = f"({self.char}"
        for s in self.vec:
            string += f" {s}"
        string += ")"
        return string


def expr(input_string: str) -> S:
    lexer = Lexer(input_string)
    return expr_bp(lexer, 0)


def expr_bp(lexer: Lexer, min_bp: int) -> S:
    match lexer.next():
        case Token(TokenType.ATOM, it):
            lhs = S.Atom(it)
        case Token(TokenType.OP, "("):
            lhs = expr_bp(lexer, 0)
            assert lexer.next(), Token.Op(")")
        case Token(TokenType.OP, op):
            _, r_bp = prefix_binding_power(op)
            rhs = expr_bp(lexer, r_bp)
            lhs = S.Cons(op, [rhs])
        case t:
            raise BadTokenError(t)

    while True:
        match lexer.peek():
            case Token(TokenType.EOF, _):
                break
            case Token(TokenType.OP, op):
                pass
            case t:
                raise BadTokenError(t)

        if bp := postfix_binding_power(op):
            l_bp, _ = bp
            if l_bp < min_bp:
                break
            lexer.next()

            if op == "[":
                rhs = expr_bp(lexer, 0)
                assert lexer.next() == Token.Op("]")
                lhs = S.Cons(op, [lhs, rhs])
            else:
                lhs = S.Cons(op, [lhs])
            continue

        if bp := infix_binding_power(op):
            l_bp, r_bp = bp
            if l_bp < min_bp:
                break
            lexer.next()

            if op == "?":
                mhs = expr_bp(lexer, 0)
                assert lexer.next() == Token.Op(":")
                rhs = expr_bp(lexer, r_bp)
                lhs = S.Cons(op, [lhs, mhs, rhs])
            else:
                rhs = expr_bp(lexer, r_bp)
                lhs = S.Cons(op, [lhs, rhs])

            continue

        break

    return lhs


def prefix_binding_power(op: str) -> tuple[None, int]:
    match op:
        case "+" | "-":
            return (None, 9)
        case _:
            raise BadOpError(op)


def postfix_binding_power(op: str) -> tuple[int, None] | None:
    match op:
        case "!":
            return (11, None)
        case "[":
            return (11, None)
        case _:
            return None


def infix_binding_power(op: str) -> tuple[int, int] | None:
    match op:
        case "=":
            return (2, 1)
        case "?":
            return (4, 3)
        case "+" | "-":
            return (5, 6)
        case "*" | "/":
            return (7, 8)
        case ".":
            return (14, 13)
        case op:
            return None


def test_parser() -> None:
    s = expr("1")
    assert str(s) == "1"

    s = expr("1 + 2 * 3")
    assert str(s) == "(+ 1 (* 2 3))"

    s = expr("a + b * c * d + e")
    assert str(s) == "(+ (+ a (* (* b c) d)) e)"

    s = expr("f . g . h")
    assert str(s) == "(. f (. g h))"

    s = expr(" 1 + 2 + f . g . h * 3 * 4")
    assert str(s) == "(+ (+ 1 2) (* (* (. f (. g h)) 3) 4))"

    s = expr("--1 * 2")
    assert str(s) == "(* (- (- 1)) 2)"

    s = expr("--f . g")
    assert str(s) == "(- (- (. f g)))"

    s = expr("-9!")
    assert str(s) == "(- (! 9))"

    s = expr("f . g !")
    assert str(s) == "(! (. f g))"

    s = expr("(((0)))")
    assert str(s) == "0"

    s = expr("x[0][1]")
    assert str(s) == "([ ([ x 0) 1)"

    s = expr("a ? b : c ? d : e")
    assert str(s) == "(? a b (? c d e))"

    s = expr("a = 0 ? b : c = d")
    assert str(s) == "(= a (= (? 0 b c) d))"


def main():
    # while True:
    # input_string = input("> ")
    # if input_string.startswith("exit"):
    # break
    input_string = "1 + x[0]"
    s = expr(input_string)
    print(s)


if __name__ == "__main__":
    main()
