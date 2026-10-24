#!/usr/bin/env python3
"""
Verify that zero unicode emojis are present across all source and documentation files.
Enforces the professional enterprise styling requirement.
"""
import os
import sys

EMOJI_RANGES = [
    (0x1F600, 0x1F64F), # Emoticons
    (0x1F300, 0x1F5FF), # Misc Symbols and Pictographs
    (0x1F680, 0x1F6FF), # Transport and Map
    (0x1F1E6, 0x1F1FF), # Flags
    (0x2600, 0x26FF),   # Misc symbols
    (0x2700, 0x27BF),   # Dingbats
    (0xFE00, 0xFE0F),   # Variation Selectors
    (0x1F900, 0x1F9FF), # Supplemental Symbols and Pictographs
    (0x1FA70, 0x1FAFF), # Symbols and Pictographs Extended-A
]

IGNORE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    ".gemini",
    ".system_generated",
}

EXTENSIONS = (
    ".py",
    ".jsx",
    ".js",
    ".ts",
    ".tsx",
    ".html",
    ".css",
    ".sh",
    ".md",
    ".json",
    ".yaml",
    ".yml",
)


def has_emoji(text: str):
    for char in text:
        cp = ord(char)
        for start, end in EMOJI_RANGES:
            if start <= cp <= end:
                return True, char, hex(cp)
    return False, None, None


def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    violations = []

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            if f == "package-lock.json":
                continue
            if f.endswith(EXTENSIONS):
                path = os.path.join(root, f)
                rel_path = os.path.relpath(path, root_dir)
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        for line_no, line in enumerate(fh, 1):
                            found, char, code = has_emoji(line)
                            if found:
                                violations.append(
                                    (rel_path, line_no, char, code, line.strip()[:60])
                                )
                except Exception:
                    pass

    if violations:
        print(f"[FAIL] Found {len(violations)} unicode emoji occurrences:")
        for rel_path, line_no, char, code, preview in violations:
            print(f"  {rel_path}:{line_no} char={char} ({code}) -> {preview}")
        sys.exit(1)
    else:
        print("[OK] Zero unicode emojis found across all files. Clean enterprise styling confirmed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
