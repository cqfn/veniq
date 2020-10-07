from pathlib import Path

current_directory = Path(__file__).absolute().parent
with open(current_directory / "rank_extraction_opportunities.py") as python_code:
    exec(python_code.read())
