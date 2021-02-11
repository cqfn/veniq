import re
from pathlib import Path

from veniq.utils.encoding_detector import read_text_with_autodetected_encoding


def create_existing_dir(directory: Path):
    if not directory.exists():
        directory.mkdir(parents=True)


def preprocess(file: str):
    def _remove_comments(string: str):
        pattern = r"(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)"
        # first group captures quoted strings (double or single)
        # second group captures comments (//single-line or /* multi-line */)
        regex = re.compile(pattern, re.MULTILINE | re.DOTALL)

        def _replacer(match):
            # if the 2nd group (capturing comments) is not None,
            # it means we have captured a non-quoted (real) comment string.
            if match.group(2) is not None:
                # so we will return empty to remove the comment
                return ""
            else:  # otherwise, we will return the 1st group
                return match.group(1)  # captured quoted-string

        return regex.sub(_replacer, string)

    original_text = read_text_with_autodetected_encoding(str(file))
    # remove comments
    text_without_comments = _remove_comments(original_text)
    # remove whitespaces
    text = "\n".join([ll.rstrip() for ll in text_without_comments.splitlines() if ll.strip()])

    yield {'text': text, 'original_filename': file}
