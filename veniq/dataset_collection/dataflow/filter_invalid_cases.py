from typing import Dict, Any


def filter_invalid_cases(dct: Dict[str, Any]):
    no_ignored_cases = dct['NO_IGNORED_CASES']
    print('filtered')
    print(dct)
    if not no_ignored_cases:
        yield dct
