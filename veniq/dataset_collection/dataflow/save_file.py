import hashlib
from pathlib import Path
from typing import Dict, Any

from veniq.dataset_collection.dataflow.preprocess import create_existing_dir


def save_input_file(dct: Dict[str, Any]):
    input_dir = dct['input_dir']
    filename = dct['original_filename']
    print(dct['original_filename'])
    text = dct['text']
    # need to avoid situation when filenames are the same
    hash_path = hashlib.sha256(str(filename.parent).encode('utf-8')).hexdigest()
    dst_filename = Path(input_dir) / f'{filename.stem}_{hash_path}.java'
    create_existing_dir(dst_filename.parent)
    if not dst_filename.exists():
        with open(dst_filename, 'w', encoding='utf-8') as w:
            w.write(text)
    yield dct


def save_output_file(dct: Dict[str, Any]):
    output_dir = dct['output_dir']
    filename = dct['original_filename']
    target_node = dct['target_node']
    method_invoked = dct['method_invoked']
    text = dct['inlined_text']
    new_full_filename = Path(output_dir, f'{filename.name}_{target_node.name}_{method_invoked.line}.java')
    create_existing_dir(new_full_filename.parent)
    dct['output_filename'] = new_full_filename
    if not new_full_filename.exists():
        with open(new_full_filename, 'w', encoding='utf-8') as w:
            w.write(text)
    yield dct
