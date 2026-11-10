"""Atomically rotate one gzip JSON rollback bundle; never deletes arbitrary files."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile

FORMAT = 'local-account-project-migration.rollback.v1'
NAME = 'rollback.json.gz'
META = 'rollback-info.json'


def validate(data):
    value = json.loads(data)
    if not isinstance(value, dict) or value.get('format') != FORMAT:
        raise ValueError('Unexpected rollback bundle format')
    if not isinstance(value.get('payload'), dict) or not value['payload']:
        raise ValueError('Rollback payload must be a nonempty object')
    return value


def inspect_bundle(path):
    with gzip.open(path, 'rb') as handle:
        data = handle.read()
    validate(data)
    return {'sha256_uncompressed': hashlib.sha256(data).hexdigest(),
            'uncompressed_bytes': len(data), 'compressed_bytes': path.stat().st_size}


def atomic_json(path, value):
    fd, temporary = tempfile.mkstemp(prefix='.info-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def rotate(snapshot, store):
    snapshot, store = snapshot.resolve(strict=True), store.resolve()
    data = snapshot.read_bytes()
    validate(data)  # Invalid input must not touch the previous backup.
    store.mkdir(parents=True, exist_ok=True)
    destination = store/NAME
    if snapshot == destination:
        raise ValueError('Snapshot and destination must differ')
    if destination.is_symlink() or (store/META).is_symlink():
        raise ValueError('Backup targets must not be symbolic links')
    if destination.exists():
        inspect_bundle(destination)  # Do not overwrite an unrelated/broken file silently.
    fd, temporary = tempfile.mkstemp(prefix='.rollback-', suffix='.tmp', dir=store)
    try:
        with os.fdopen(fd, 'wb') as raw:
            with gzip.GzipFile(filename='', mode='wb', fileobj=raw, compresslevel=9, mtime=0) as handle:
                handle.write(data)
            raw.flush()
            os.fsync(raw.fileno())
        candidate = Path(temporary)
        info = inspect_bundle(candidate)
        if info['sha256_uncompressed'] != hashlib.sha256(data).hexdigest():
            raise ValueError('Backup verification failed')
        # Only this replacement removes the previous permanent backup.
        os.replace(candidate, destination)
        info['backup'] = str(destination)
        info['format'] = FORMAT
        atomic_json(store/META, info)
        return info
    finally:
        Path(temporary).unlink(missing_ok=True)


def verify(store):
    store = store.resolve()
    info = inspect_bundle(store/NAME)
    if (store/META).exists():
        saved = json.loads((store/META).read_text(encoding='utf-8'))
        for key in ['sha256_uncompressed', 'uncompressed_bytes', 'compressed_bytes']:
            if saved.get(key) != info[key]:
                raise ValueError('Backup metadata mismatch; verify bundle before continuing')
    info['backup'] = str(store/NAME)
    info['other_compressed_backups'] = [str(p) for p in store.iterdir()
                                        if p.is_file() and p.suffix in {'.gz', '.zip'} and p.name != NAME]
    if info['other_compressed_backups']:
        raise ValueError('Extra compressed backups found; consolidate only after inspecting them')
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    rot = sub.add_parser('rotate')
    rot.add_argument('--snapshot', type=Path, required=True)
    rot.add_argument('--store', type=Path, required=True)
    ver = sub.add_parser('verify')
    ver.add_argument('--store', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(rotate(args.snapshot, args.store) if args.action == 'rotate' else verify(args.store), ensure_ascii=False))


if __name__ == '__main__':
    main()
