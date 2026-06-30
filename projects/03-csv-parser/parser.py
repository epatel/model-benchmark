def parse_csv(text):
    """Parse CSV text into a list of rows, where each row is a list of fields.

    Blank lines are skipped. Fields are separated by commas.
    """
    rows = []
    for line in text.splitlines():
        if line == "":
            continue
        rows.append(line.split(","))
    return rows
