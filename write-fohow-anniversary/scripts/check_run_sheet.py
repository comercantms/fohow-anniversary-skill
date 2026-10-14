#!/usr/bin/env python3
"""Validate a sequential event schedule; never read or write external systems."""
import argparse
import json
from pathlib import Path


def validate(data):
    errors = []
    if not isinstance(data, dict):
        return {'status': 'FAIL', 'errors': ['Root must be an object']}
    target = data.get('target_seconds')
    if type(target) is not int or target <= 0:
        errors.append('target_seconds must be a positive integer')
    blocks = data.get('blocks')
    if not isinstance(blocks, list) or not blocks:
        return {'status': 'FAIL', 'errors': errors + ['blocks must be a nonempty list']}
    cursor = reserve = 0
    seen = set()
    for n, b in enumerate(blocks, 1):
        if not isinstance(b, dict):
            errors.append(f'Block {n} must be an object')
            continue
        id_ = b.get('id')
        if not isinstance(id_, str) or not id_.strip() or id_ in seen:
            errors.append(f'Block {n}: missing or duplicate id')
        if isinstance(id_, str):
            seen.add(id_)
        owner = b.get('owner')
        if not isinstance(owner, str) or not owner.strip():
            errors.append(f'Block {n}: owner is missing')
        start, duration = b.get('start_seconds'), b.get('duration_seconds')
        if type(start) is not int or start < 0:
            errors.append(f'Block {n}: start_seconds must be a nonnegative integer')
        if type(duration) is not int or duration <= 0:
            errors.append(f'Block {n}: duration_seconds must be a positive integer')
        if type(start) is int and type(duration) is int and start >= 0 and duration > 0:
            if start != cursor:
                errors.append(f'Block {n}: expected start {cursor}, got {start} (gap/overlap/order)')
            cursor = start + duration
            if b.get('kind') == 'reserve':
                reserve += duration
    if type(target) is int and cursor != target:
        errors.append(f'Schedule ends at {cursor}; target is {target}')
    if reserve == 0:
        errors.append('No explicit reserve block included inside target time')
    return {'status': 'FAIL' if errors else 'PASS', 'errors': errors,
            'target_seconds': target, 'end_seconds': cursor, 'reserve_seconds': reserve,
            'block_count': len(blocks), 'scope': 'Planned schedule only; not a measured live event'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('schedule', type=Path)
    args = parser.parse_args()
    try:
        result = validate(json.loads(args.schedule.read_text(encoding='utf-8')))
    except (OSError, ValueError) as e:
        result = {'status': 'FAIL', 'errors': [str(e)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
