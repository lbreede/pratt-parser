import Foundation

enum S {
    case atom(Character)
    case cons(Character, [S])
}

extension S: CustomStringConvertible {
    var description: String {
        switch self {
        case .atom(let character):
            return "\(character)"
        case .cons(let head, let rest):
            let restDescription = rest.map { " \($0)" }.joined()
            return "(\(head)\(restDescription))"
        }
    }
}

enum Token: Equatable {
    case atom(Character)
    case op(Character)
    case eof
}

class Lexer {
    private var tokens: [Token]

    init(input: String) {
        self.tokens = input
            .filter { !$0.isWhitespace }
            .map { char in
                if char.isNumber || char.isLetter {
                    return Token.atom(char)
                } else {
                    return Token.op(char)
                }
            }
        self.tokens.reverse()
    }

    func next() -> Token {
        return tokens.popLast() ?? .eof
    }

    func peek() -> Token {
        return tokens.last ?? .eof
    }
}

func expr(_ input: String) -> S {
    let lexer = Lexer(input: input)
    return exprBp(lexer: lexer, minBp: 0)
}

func exprBp(lexer: Lexer, minBp: UInt8) -> S {
    var lhs: S

    let t = lexer.next()
    switch t {
    case .atom(let char):
        lhs = .atom(char)
    case .op("("):
        lhs = exprBp(lexer: lexer, minBp: 0)
        assert(lexer.next() == .op(")"))
    case .op(let op):
        let (_, rBp) = prefixBindingPower(op)
        let rhs = exprBp(lexer: lexer, minBp: rBp)
        lhs = .cons(op, [rhs])
    default:
        fatalError("bad token: \(t)")
    }

    while true {
        var op: Character
        
        let t = lexer.peek()
        switch t {
        case .eof:
            break
        case .op(let op_):
            op = op_
        default:
            fatalError("bad token \(t)")
        }

        if let (lBp, rBp) = infixBindingPower(op) {
            if lBp < minBp {
                return lhs
            }
            lexer.next()
            if op == "?" {
                let mhs = exprBp(lexer: lexer, minBp: 0)
                assert(lexer.next() == .op(":"))
                let rhs = exprBp(lexer: lexer, minBp: rBp)
                lhs = .cons(op, [lhs, mhs, rhs])
            } else {
                let rhs = exprBp(lexer: lexer, minBp: rBp)
                lhs = .cons(op, [lhs, rhs])
            }
        }
    }
}

func prefixBindingPower(_ op: Character) -> ((), UInt8) {
    switch op {
    case "+", "-":
        return ((), 9)
    default:
        fatalError("bad op: \(op)")
    }
}

func postfixBindingPower(_ op: Character) -> (UInt8, ())? {
    switch op {
    case "!":
        return (11, ())
    case "[":
        return (11, ())
    default:
        return nil
    }
}

func infixBindingPower(_ op: Character) -> (UInt8, UInt8)? {
    switch op {
    case "=":
        return (2, 1)
    case "?":
        return (4, 3)
    case "+", "-":
        return (5, 6)
    case "*", "/":
        return (7, 8)
    case ".":
        return (14, 13)
    default:
        return nil
    }
}

func tests() {
    let s1 = expr("1")
    assert(s1.description == "1")

    let s2 = expr("1 + 2 * 3")
    assert(s2.description == "(+ 1 (* 2 3))")

    let s3 = expr("a + b * c * d + e")
    assert(s3.description == "(+ (+ a (* (* b c) d)) e)")

    let s4 = expr("f . g . h")
    assert(s4.description == "(. f (. g h))")

    let s5 = expr(" 1 + 2 + f . g . h * 3 * 4")
    assert(s5.description == "(+ (+ 1 2) (* (* (. f (. g h)) 3) 4))")

    let s6 = expr("--1 * 2")
    assert(s6.description == "(* (- (- 1)) 2)")

    let s7 = expr("--f . g")
    assert(s7.description == "(- (- (. f g)))")

    let s8 = expr("-9!")
    assert(s8.description == "(- (! 9))")

    let s9 = expr("f . g !")
    assert(s9.description == "(! (. f g))")

    let s10 = expr("(((0)))")
    assert(s10.description == "0")

    let s11 = expr("x[0][1]")
    assert(s11.description == "([ ([ x 0) 1)")

    let s12 = expr("a ? b : c ? d : e")
    assert(s12.description == "(? a b (? c d e))")

    let s13 = expr("a = 0 ? b : c = d")
    assert(s13.description == "(= a (= (? 0 b c) d))")
}

tests()
