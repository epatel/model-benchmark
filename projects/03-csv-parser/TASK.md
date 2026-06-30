# Task: Support quoted fields in the CSV parser

`parser.py` has a `parse_csv(text)` function that splits each line on commas.
That naive approach is wrong for real CSV: a field wrapped in double quotes may
itself contain commas, and a quoted field may contain escaped quotes written as
two double quotes (`""`).

Extend `parse_csv` so it follows these rules:

- Fields are comma-separated.
- A field may be wrapped in double quotes. The surrounding quotes are **not**
  part of the value.
- A comma inside a quoted field is part of the value, not a separator.
- Inside a quoted field, two double quotes (`""`) represent one literal `"`.
- Unquoted fields are taken verbatim.
- Blank lines are skipped.

Examples:

| Input              | Expected output            |
|--------------------|----------------------------|
| `a,b,c`            | `[["a", "b", "c"]]`        |
| `"a,b",c`          | `[["a,b", "c"]]`          |
| `"she said ""hi"""`| `[['she said "hi"']]`      |

Keep the signature `parse_csv(text) -> list[list[str]]`.

Run `python3 -m unittest test_parser.py` to check your work.
