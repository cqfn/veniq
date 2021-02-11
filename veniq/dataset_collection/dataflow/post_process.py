from pathlib import Path
from typing import Dict, Any


def post_process_data(dct: Dict[str, Any]):
    original_filename = dct['original_filename']
    dct['original_filename'] = Path(dct['original_filename']).name
    dct['output_filename'] = Path(dct['original_filename']).name
    dataset_dir = Path(dct['dataset_dir'])
    dct['project_id'] = '/'.join(original_filename.relative_to(dataset_dir).parts[:2])
    yield dct
