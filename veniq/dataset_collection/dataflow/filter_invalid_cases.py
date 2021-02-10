def filter_invalid_cases(dct):
    no_ignored_cases = dct['NO_IGNORED_CASES']
    if not no_ignored_cases:
        yield dct
