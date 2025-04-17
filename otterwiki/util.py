#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import datetime
import mimetypes
import os.path
import pathlib
import random
import re
import regex
import string
import time
import unicodedata
from functools import lru_cache
import unicodedata
from typing import List, Tuple, Literal, Optional


def ttl_lru_cache(ttl: int = 60, maxsize: int = 128):
    """
    Time aware lru caching thx to https://stackoverflow.com/a/73026174/212768
    """

    def wrapper(func):

        @lru_cache(maxsize)
        def inner(__ttl, *args, **kwargs):
            # Note that __ttl is not passed down to func,
            # as it's only used to trigger cache miss after some time
            return func(*args, **kwargs)

        return lambda *args, **kwargs: inner(
            time.time() // ttl, *args, **kwargs
        )

    return wrapper


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Yi", suffix)


# from https://github.com/Python-Markdown/markdown/blob/master/markdown/extensions/toc.py
def slugify(value, separator="-"):
    """Slugify a string, to make it URL friendly."""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore")
    value = re.sub(r"[^\w\s-]", "", value.decode("ascii")).strip().lower()
    return re.sub(r"[%s\s]+" % separator, separator, value)


def clean_slashes(value):
    '''This will insure that any path separated by slashes only has one
    slash between each dir and does not end in slash'''

    _split_path = value.split("/")

    # This will remove empty strings
    _path = [p for p in _split_path if p]

    value = "/".join(_path)
    return value


def sanitize_pagename(value, allow_unicode=True):
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    # remove slashes, question marks ...
    value = re.sub(r"[?|$|.|!|#|\\]", r"", value)

    # remove leading -/
    value = value.lstrip("-/")
    # remove leading and trailing whitespaces
    value = value.strip()

    # remove trailing slash and double slashes
    value = clean_slashes(value)

    return value


def split_path(path: str) -> List[str]:
    if path == "":
        return []
    head = os.path.dirname(path)
    tail = os.path.basename(path)
    if head == os.path.dirname(head):
        return [tail]
    return split_path(head) + [tail]


def titleSs(s):
    """
    This function is a workaround for str.title() not knowing upercase 'ß'.
    """
    if 'ß' not in s:
        return s.title()
    magicword = 'M🙉A🙈G🙊I🐤C🐣W🐥O🦆R🐔D'
    while magicword in s:
        magicword = 2 * magicword
    s = s.replace('ß', magicword)
    s = s.title()
    return s.replace(magicword, 'ß')


def get_pagepath(pagename):
    return pagename


def get_page_directoryname(pagepath: str) -> str:
    parts = split_path(pagepath)
    return join_path(parts[:-1])


def join_path(path_arr: List[str]) -> str:
    if len(path_arr) < 1:
        return ""
    return os.path.join(*path_arr)


def is_valid_email(email):
    if not type(email) == str:
        return False
    mail_regexp = re.compile(
        r"([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\"([]!#-[^-~ \t]|(\\[\t -~]))+\")@([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\[[\t -Z^-~]*])"
    )
    return mail_regexp.fullmatch(email) is not None


def random_password(len=8):
    return "".join(
        random.choice(string.ascii_lowercase + string.digits)
        for _ in range(len)
    )


def empty(what):
    if what is None:
        return True
    if isinstance(what, str) and what.strip() == "":
        return True
    return False


def guess_mimetype(path):
    mimetype, encoding = mimetypes.guess_type(path)
    return mimetype


def mkdir(path):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def patchset2filedict(patchset):
    _line_type_style = {
        " ": "",
        "+": "added",
        "-": "removed",
        "\\": "",  # line.line_type='\\' line.value=' No newline at end of file\n'
    }
    files = {}
    for file in patchset:
        line_data = []
        for hunk in file:
            line_data.append(
                {
                    "source": "",
                    "target": "",
                    "value": f"@@ {hunk.source_start},{hunk.source_length} {hunk.target_start},{hunk.target_length} @@",
                    "style": "hunk",
                }
            )
            for line in hunk:
                line_data.append(
                    {
                        "source": line.source_line_no or "",
                        "target": line.target_line_no or "",
                        "type": line.line_type,
                        "style": _line_type_style[line.line_type],
                        "value": line.value,
                        "hunk": False,
                    }
                )
        files[file.path] = line_data

    return files


def get_local_timezone():
    """get the timezone the server is running on"""
    return datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo


AXT_HEADING = re.compile(
    r' {0,3}(#{1,6})(?!#+)(?: *\n+|' r'\s+([^\n]*?)(?:\n+|\s+?#+\s*\n+))'
)
SETEX_HEADING = re.compile(r'([^\n]+)\n *(=|-){2,}[ \t]*\n+')


def get_header(content):
    filehead = content[:512]
    # find first markdown header in filehead
    heading = [line for (_, line) in AXT_HEADING.findall(filehead)]
    heading += [line for (line, _) in SETEX_HEADING.findall(filehead)]
    if len(heading):
        return heading[0]
    return None


def strfdelta_round(tdelta, round_period='second'):
    """timedelta to string,    use for measure running time
    attend period from days downto smaller period, round to minimum period
    omit zero value period

    thanks to https://stackoverflow.com/a/64257852/212768
    """
    period_names = ('week', 'day', 'hour', 'minute', 'second', 'millisecond')
    if round_period not in period_names:
        raise Exception(
            f'round_period "{round_period}" invalid, should be one of {",".join(period_names)}'
        )
    period_seconds = (604800, 86400, 3600, 60, 1, 1 / pow(10, 3))
    period_desc = ('weeks', 'days', 'hours', 'mins', 'secs', 'msecs')
    round_i = period_names.index(round_period)

    s = ''
    remainder = tdelta.total_seconds()
    for i in range(len(period_names)):
        q, remainder = divmod(remainder, period_seconds[i])
        if int(q) > 0:
            if not len(s) == 0:
                s += ' '
            if q > 1:
                s += f'{q:.0f} {period_desc[i]}'
            else:
                s += f'{q:.0f} {period_desc[i][:-1]}'
        if i == round_i:
            break
        if i == round_i + 1:
            if remainder > 1:
                s += f'{remainder} {period_desc[round_i]}'
            else:
                s += f'{remainder} {period_desc[round_i][:-1]}'
            break

    return s


def is_valid_name(
    name: str,
    min_length: int = 1,
    max_length: int = 50,
) -> Tuple[bool, str]:
    """
    Validates if a name meets security and usability requirements,
    supporting international characters.

    Args:
        name: The name to validate
        min_length: Minimum acceptable length
        max_length: Maximum acceptable length

    Returns:
        A tuple containing (is_valid, reason_if_invalid)
    """

    # Check if name is None or empty
    if not name or name.strip() == "":
        return False, "name cannot be empty"

    # Trim whitespace
    name = name.strip()

    # Check length
    if len(name) < min_length:
        return (
            False,
            f"name must be at least {min_length} character(s) long",
        )
    if len(name) > max_length:
        return False, f"name cannot exceed {max_length} characters"

    # Normalize unicode characters
    name = unicodedata.normalize('NFC', name)

    # Check for invisible/control characters
    if any(unicodedata.category(char).startswith('C') for char in name):
        return (
            False,
            f"name contains invisible or control characters",
        )

    # Allow letters from any language, spaces, hyphens, apostrophes
    # Common in names across cultures: spaces, hyphens, apostrophes, periods
    valid_chars: str = r'^[\p{L}\s\'\-\.]+$'

    if not regex.match(valid_chars, name, regex.UNICODE):
        return (
            False,
            f"name can only contain letters, spaces, hyphens, apostrophes, and periods",
        )

    # Check for reasonable spacing (no double spaces, etc.)
    if '  ' in name:
        return False, f"name cannot contain consecutive spaces"

    # Check for reasonable use of special characters
    if re.search(r'[\'\-\.]{2,}', name):
        return (
            False,
            f"name cannot contain consecutive special characters",
        )

    # Check for names that are just special characters
    if regex.match(r'^[\s\'\-\.]+$', name):
        return False, f"name must contain at least one letter"

    # Check for names that are suspiciously repetitive
    if re.search(r'(.)\1{4,}', name):
        return (
            False,
            f"name contains too many consecutive repeated characters",
        )

    # Check for common placeholder names
    placeholder_names: list[str] = [
        "test",
        "user",
        "name",
        "firstname",
        "lastname",
        "first",
        "last",
        "none",
        "nil",
        "null",
        "undefined",
        "anonymous",
        "unknown",
    ]
    if name.lower() in placeholder_names:
        return False, f"name appears to be a placeholder"

    # Check for names with excessive capitalization
    if name.isupper() and len(name) > 2:
        return False, f"name should not be all uppercase"

    return True, f"name is valid"
