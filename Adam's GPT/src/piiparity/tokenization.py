"""Offset-preserving split: retain combining marks, expose Han characters as units."""
def split_words(text):
    import regex
    # V1 set subtraction excludes Han from word runs. Original text is never rewritten.
    pattern=r'(?V1)\p{Han}|[\p{L}\p{M}\p{N}_--\p{Han}]+(?:[-_][\p{L}\p{M}\p{N}_--\p{Han}]+)*|\S'
    for match in regex.finditer(pattern,text):
        yield match.group(),match.start(),match.end()
