import hashlib
from pathlib import Path
from typing import Dict, Tuple


def save_text_to_new_file(input_dir: Path, text: str, dct: Dict[Tuple, Tuple], output_dir=None):
    print(dct)
    filename = dct.key()
    # need to avoid situation when filenames are the same
    hash_path = hashlib.sha256(str(filename.parent).encode('utf-8')).hexdigest()
    dst_filename = input_dir / f'{filename.stem}_{hash_path}.java'
    if not dst_filename.parent.exists():
        dst_filename.parent.mkdir(parents=True)
    if not dst_filename.exists():
        with open(dst_filename, 'w', encoding='utf-8') as w:
            w.write(text)
    yield {}