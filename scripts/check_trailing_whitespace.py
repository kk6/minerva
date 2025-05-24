#!/usr/bin/env python3
import sys
import os
import re

EXCLUDE_DIRS = {'.git', '.venv', 'venv', '__pycache__', '.egg-info', 'htmlcov'}
TARGET_EXTS = {'.py', '.md', '.yml', '.yaml'}

trailing_ws = re.compile(r'[ \t]+$')

def should_check(path):
    parts = path.split(os.sep)
    if any(d in EXCLUDE_DIRS for d in parts):
        return False
    _, ext = os.path.splitext(path)
    return ext in TARGET_EXTS

def main():
    failed = False
    for root, dirs, files in os.walk('.'):
        # 除外ディレクトリをwalkから除外
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            path = os.path.join(root, f)
            if not should_check(path):
                continue
            try:
                with open(path, encoding='utf-8', errors='ignore') as fp:
                    for i, line in enumerate(fp, 1):
                        if trailing_ws.search(line):
                            print(f'{path}:{i}:{line.rstrip()}')
                            failed = True
            except Exception as e:
                print(f'Error reading {path}: {e}', file=sys.stderr)
    if failed:
        print('✗ Files with trailing whitespace found')
        sys.exit(1)
    print('✓ No trailing whitespace found')

if __name__ == '__main__':
    main()
