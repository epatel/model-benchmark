def dedupe(items):
    """Return the items with duplicates removed, preserving first-seen order.

    Example: dedupe([3, 1, 3, 2, 1]) == [3, 1, 2]
    """
    result = []
    for x in items:
        if x not in result:
            result.append(x)
    return result
