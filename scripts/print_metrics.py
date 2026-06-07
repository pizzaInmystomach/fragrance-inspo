#!/usr/bin/env python3
import json
import os
import argparse
from datetime import datetime


def find_file(provided):
    if provided:
        return provided if os.path.exists(provided) else None
    candidates = [
        os.path.join('.venv', 'fragrance_metrics.json'),
        'fragrance_metrics.json',
        os.path.join(os.getcwd(), '.venv', 'fragrance_metrics.json'),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def human_time(ts):
    try:
        return datetime.fromtimestamp(float(ts)).isoformat()
    except Exception:
        return str(ts)


def print_metrics(path):
    print(f"Found metrics file: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, list):
        print('Metrics file does not contain a JSON array.')
        return
    for i, entry in enumerate(data, 1):
        ts = entry.get('timestamp')
        prompt = entry.get('prompt')
        metrics = entry.get('metrics', {})
        print(f"--- Entry {i} ---")
        print(f"timestamp: {ts} ({human_time(ts)})")
        if prompt:
            print(f"prompt: {prompt}")
        if metrics:
            for k, v in metrics.items():
                print(f"{k}: {v}")
        else:
            print('no metrics object present')


def main():
    p = argparse.ArgumentParser(description='Print fragrance metrics JSON')
    p.add_argument('--file', '-f', help='Path to metrics JSON file')
    args = p.parse_args()
    path = find_file(args.file)
    if not path:
        print('No metrics file found. Try --file /path/to/fragrance_metrics.json')
        raise SystemExit(2)
    print_metrics(path)


if __name__ == '__main__':
    main()
