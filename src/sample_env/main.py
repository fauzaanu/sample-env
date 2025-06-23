# !/usr/bin/env python3
"""
Find all env-var references in Python code and emit a .env.sample file.
Detects references such as:
  - os.getenv("VAR")
  - os.environ.get("VAR", ...)
  - from os import environ; environ.get("VAR", ...)
  - os.environ["VAR"]
  - from os import environ; environ["VAR"]
"""

import os
import ast
import argparse
from pathlib import Path


def find_env_vars_in_file(path):
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    found = set()

    for node in ast.walk(tree):
        # match os.getenv("VAR")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            func = node.func
            if (
                isinstance(func.value, ast.Name)
                and func.value.id == "os"
                and func.attr == "getenv"
            ):
                if (
                    node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                ):
                    found.add(node.args[0].value)

            # match os.environ.get("VAR", ...) and environ.get("VAR", ...)
            if func.attr == "get":
                # os.environ.get(...)
                if (
                    isinstance(func.value, ast.Attribute)
                    and isinstance(func.value.value, ast.Name)
                    and func.value.value.id == "os"
                    and func.value.attr == "environ"
                ):
                    if (
                        node.args
                        and isinstance(node.args[0], ast.Constant)
                        and isinstance(node.args[0].value, str)
                    ):
                        found.add(node.args[0].value)
                # from os import environ; environ.get(...)
                if isinstance(func.value, ast.Name) and func.value.id == "environ":
                    if (
                        node.args
                        and isinstance(node.args[0], ast.Constant)
                        and isinstance(node.args[0].value, str)
                    ):
                        found.add(node.args[0].value)

        # match os.environ["VAR"] and environ["VAR"]
        if isinstance(node, ast.Subscript):
            target = node.value
            key = node.slice
            if isinstance(key, ast.Index):
                key = key.value

            name = None
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                if target.value.id == "os" and target.attr == "environ":
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        name = key.value
            elif isinstance(target, ast.Name) and target.id == "environ":
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    name = key.value

            if name:
                found.add(name)

    return found


def find_all_env_vars(root):
    envs = set()
    gitignore_path = Path(root) / ".gitignore"
    ignored_dirs = set()
    ignored_files = set()

    if gitignore_path.exists():
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if line.endswith("/"):
                        ignored_dirs.add(Path(line.rstrip("/")))
                    else:
                        ignored_files.add(line)

    for path in Path(root).rglob("*.py"):
        rel = path.relative_to(root)
        if any(rel == d or rel.is_relative_to(d) for d in ignored_dirs):
            continue
        if any(rel.match(f) or rel.name == f for f in ignored_files):
            continue
        envs.update(find_env_vars_in_file(path))
    return envs


def write_sample(env_vars, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        for var in sorted(env_vars):
            f.write(f"{var}=\n")
    print(f"[✓] Wrote {len(env_vars)} entries to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate .env.sample from code")
    parser.add_argument(
        "project_dir", nargs="?", default=".", help="Root of your Python project"
    )
    parser.add_argument(
        "-o",
        "--output",
        default=".env.sample",
        help="Output file (default .env.sample)",
    )
    args = parser.parse_args()

    env_vars = find_all_env_vars(args.project_dir)
    if not env_vars:
        print("[!] No environment variables found.")
    else:
        write_sample(env_vars, args.output)


if __name__ == "__main__":
    main()
