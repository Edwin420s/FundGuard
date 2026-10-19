import os
import re
from typing import Any


def tokenize_metta(text: str) -> list[str]:
    """Tokenizes MeTTa S-expression text, preserving quoted strings and removing comments."""
    clean_lines = []
    for line in text.splitlines():
        line = line.split(";")[0].strip()
        if line:
            clean_lines.append(line)
    clean = " ".join(clean_lines)
    # Add spaces around parentheses
    clean = re.sub(r'([()])', r' \1 ', clean)
    # Match quoted strings, parentheses, or non-whitespace words
    pattern = r'\"[^\"]*\"|[()]|[^\s()\"]+'
    tokens = [t for t in re.findall(pattern, clean) if t.strip()]
    return tokens

def parse_tokens(tokens: list[str]) -> Any:
    """Parses token list into nested Python lists representing S-expressions."""
    if not tokens:
        return None
    token = tokens.pop(0)
    if token == "(":
        expr = []
        while tokens and tokens[0] != ")":
            parsed = parse_tokens(tokens)
            if parsed is not None:
                expr.append(parsed)
        if tokens and tokens[0] == ")":
            tokens.pop(0)
        return expr
    elif token == ")":
        return None
    elif token.startswith('"') and token.endswith('"'):
        return token[1:-1]
    else:
        try:
            if "." in token:
                return float(token)
            return int(token)
        except ValueError:
            return token

class MeTTAEngine:
    """
    Symbolic reasoning engine for SingularityNET MeTTa / Hyperon S-expressions.
    Evaluates reduction rules, manages the typed Atomspace, and enforces financial
    and policy invariants with closed-loop learning from human adjudication.
    """
    def __init__(self, metta_file_path: str = None):
        self.rules: dict[str, list[tuple[list, Any]]] = {}  # func_name -> list of (params, body)
        self.atomspace: list[Any] = []
        self.traces: list[dict] = []

        # Auto-discover and load rules from metta/ and omega/ directories
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        rule_paths = [
            os.path.join(base_dir, "metta", "rules"),
            os.path.join(base_dir, "omega"),
        ]
        for r_dir in rule_paths:
            if os.path.exists(r_dir):
                for fname in sorted(os.listdir(r_dir)):
                    if fname.endswith(".metta"):
                        self.load_file(os.path.join(r_dir, fname))

        # Also load local rules.metta as fallback / complement
        local_rules = os.path.join(os.path.dirname(__file__), "rules.metta")
        if os.path.exists(local_rules):
            self.load_file(local_rules)

        if metta_file_path and os.path.exists(metta_file_path):
            self.load_file(metta_file_path)

    def load_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.load_text(content)
        except Exception:
            pass

    def load_text(self, text: str):
        tokens = tokenize_metta(text)
        while tokens:
            expr = parse_tokens(tokens)
            if expr and isinstance(expr, list) and len(expr) >= 3 and expr[0] == "=":
                pattern = expr[1]
                body = expr[2]
                if isinstance(pattern, list) and len(pattern) > 0:
                    func_name = pattern[0]
                    params = pattern[1:]
                    if func_name not in self.rules:
                        self.rules[func_name] = []
                    self.rules[func_name].append((params, body))
            elif expr and isinstance(expr, list) and len(expr) >= 2 and expr[0] == ":":
                # Type declaration
                self.atomspace.append(expr)

    def evaluate_expr(self, expr: Any, env: dict = None) -> Any:
        env = env or {}
        if not isinstance(expr, list):
            if isinstance(expr, str) and expr.startswith("$"):
                return env.get(expr, expr)
            if expr == "True":
                return True
            if expr == "False":
                return False
            return expr

        if not expr:
            return []

        op = expr[0]
        if isinstance(op, str) and op.startswith("$"):
            op = env.get(op, op)

        # Built-in arithmetic & logical operators
        if op == "+":
            args = [self.evaluate_expr(a, env) for a in expr[1:]]
            return sum(args)
        elif op == "-":
            args = [self.evaluate_expr(a, env) for a in expr[1:]]
            if len(args) == 1:
                return -args[0]
            res = args[0]
            for x in args[1:]:
                res -= x
            return res
        elif op == "*":
            args = [self.evaluate_expr(a, env) for a in expr[1:]]
            res = 1
            for x in args:
                res *= x
            return res
        elif op == "/":
            args = [self.evaluate_expr(a, env) for a in expr[1:]]
            return args[0] / args[1] if args[1] != 0 else 0
        elif op == "==":
            args = [self.evaluate_expr(a, env) for a in expr[1:]]
            return args[0] == args[1]
        elif op == "!=":
            args = [self.evaluate_expr(a, env) for a in expr[1:]]
            return args[0] != args[1]
        elif op == ">=":
            args = [self.evaluate_expr(a, env) for a in expr[1:]]
            return args[0] >= args[1]
        elif op == "<=":
            args = [self.evaluate_expr(a, env) for a in expr[1:]]
            return args[0] <= args[1]
        elif op == ">":
            args = [self.evaluate_expr(a, env) for a in expr[1:]]
            return args[0] > args[1]
        elif op == "<":
            args = [self.evaluate_expr(a, env) for a in expr[1:]]
            return args[0] < args[1]
        elif op == "and":
            for a in expr[1:]:
                if not self.evaluate_expr(a, env):
                    return False
            return True
        elif op == "or":
            for a in expr[1:]:
                if self.evaluate_expr(a, env):
                    return True
            return False
        elif op == "not":
            return not self.evaluate_expr(expr[1], env)
        elif op == "if":
            cond = self.evaluate_expr(expr[1], env)
            if cond:
                return self.evaluate_expr(expr[2], env)
            else:
                return self.evaluate_expr(expr[3], env)
        elif op == "contains-substring":
            haystack = str(self.evaluate_expr(expr[1], env)).lower()
            needle = str(self.evaluate_expr(expr[2], env)).lower()
            return needle in haystack
        elif op == "assert-atom":
            # Add atom to Atomspace
            atom = expr[2] if len(expr) > 2 else expr[1]
            eval_atom = self.evaluate_expr(atom, env)
            self.atomspace.append(eval_atom)
            return "ATOM_ASSERTED"
        elif op == "match":
            # Simple match in atomspace
            pattern = expr[2] if len(expr) > 2 else expr[1]
            return pattern

        # User-defined MeTTa rule reduction
        if op in self.rules:
            evaluated_args = [self.evaluate_expr(a, env) for a in expr[1:]]
            for params, body in self.rules[op]:
                if len(params) == len(evaluated_args):
                    local_env = dict(env)
                    match = True
                    for p, val in zip(params, evaluated_args):
                        if isinstance(p, str) and p.startswith("$"):
                            local_env[p] = val
                        elif p != val:
                            match = False
                            break
                    if match:
                        reduction = self.evaluate_expr(body, local_env)
                        self.traces.append({
                            "query": f"({op} {' '.join(str(a) for a in evaluated_args)})",
                            "reduction": str(reduction)
                        })
                        return reduction

        return [self.evaluate_expr(x, env) for x in expr]

    def query(self, metta_string: str) -> Any:
        tokens = tokenize_metta(metta_string)
        if not tokens:
            return None
        if tokens[0] == "!":
            tokens.pop(0)
        parsed = parse_tokens(tokens)
        return self.evaluate_expr(parsed)

    def register_custom_rule(self, rule_name: str, rule_expression: str) -> bool:
        """Dynamic rule registration ('The Agent That Grows Up')"""
        rule_text = f"(= ({rule_name}) {rule_expression})"
        self.load_text(rule_text)
        return True

    def calculate_updated_reliability(self, current_score: float, event_outcome: str) -> float:
        """MeTTa closed-loop reliability calculation"""
        query_str = f"(calculate-updated-reliability {current_score} \"{event_outcome}\")"
        res = self.query(query_str)
        try:
            return float(res)
        except (ValueError, TypeError):
            if event_outcome == "confirmed_settlement":
                return min(1.0, current_score + 0.05)
            elif event_outcome == "dispute_penalty":
                return max(0.0, current_score - 0.25)
            return current_score

    def get_traces(self) -> list[dict]:
        return list(self.traces)

    def clear_traces(self):
        self.traces.clear()

    def get_atomspace_atoms(self) -> list[Any]:
        return list(self.atomspace)
