#!/usr/local/bin/python3
# coding: utf-8
"""
Author       : weaming
Created Time : 2018-07-19 03:24:06

CSV and JSON converter
"""
import sys
import argparse
import json
import io
from . import *


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from .format import pretty_print
from data_process.io_csv import process_row_generator, read_csv

is_py2 = sys.version_info[0] == 2

# https://stackoverflow.com/a/15063941/5281824
import csv

maxInt = sys.maxsize
while True:
    # decrease the maxInt value by factor 10
    # as long as the OverflowError occurs.
    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt / 10)


def filter_keys(data, fields, raise_missing=True, raise_extra=True):
    def check_keys(x):
        missing = list(set(fields) - set(x.keys()))
        if missing and raise_missing:
            raise ValueError(f"missing keys '{missing}' for {x}")
        for k, v in x.items():
            if k in fields:
                yield k, v
            elif raise_extra:
                raise ValueError(f"extra key '{k}' for {x}")

    for x in data:
        xx = dict(check_keys(x))
        if xx:
            yield xx


def _merge_value(v):
    if isinstance(v, (list, tuple, dict)):
        return json.dumps(v, ensure_ascii=False)
    elif not isinstance(v, (int, float)):
        return str(v)
    elif v is None:
        return ''
    return v


def to_csv(
    data,
    fields=None,
    ignore_missing=False,
    ignore_extra=False,
    loose=False,
    sort_keys=False,
):
    if is_py2:
        fuck = lambda x: x.encode("utf8")
    else:
        fuck = lambda x: x
    data = [
        dict(
            (sorted if sort_keys else lambda x: x)(
                {fuck(k): _merge_value(fuck(v)) for k, v in row.items()}.items()
            )
        )
        for row in data
    ]
    f = StringIO()
    if not fields:
        if loose:
            fields = set()
            for r in data:
                for k in r:
                    fields.add(k)
            fields = sorted(fields)
        else:
            fields = sorted(data[0]) if is_py2 else list(data[0])
    process_row_generator(
        fields,
        filter_keys(
            data,
            fields,
            raise_missing=(not ignore_missing) and (not loose),
            raise_extra=not ignore_extra,
        ),
        f,
        keep_open=True,
    )
    return f.getvalue()


def from_csv(text):
    return read_csv(StringIO(text))


def get_target_type_from_text(text):
    text = text.strip()
    if text and text[0] in "{[":
        return "csv"
    return "json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t", "--type", help="type of target output, csv and json are allowed"
    )
    parser.add_argument(
        "-v", "--version", default=False, action="store_true", help="print version"
    )
    parser.add_argument("-f", "--fields", nargs='*', help="specific the fields")
    parser.add_argument("--loose", action='store_true', help="output all fields")
    parser.add_argument(
        "-m",
        "--ignore-missing",
        default=False,
        action="store_true",
        help="ignore the missing fields",
    )
    parser.add_argument(
        "-e",
        "--ignore-extra",
        default=False,
        action="store_true",
        help="ignore the extra fields",
    )
    parser.add_argument(
        "-s", "--sort-keys", default=False, action="store_true", help="sort keys",
    )

    args = parser.parse_args()
    if args.version:
        print(version)
        sys.exit(0)

    text = sys.stdin.read()

    t = args.type or get_target_type_from_text(text)
    if t == "csv":
        try:
            data = json.loads(text)
        except ValueError as e:
            print(e)
            sys.exit(1)

        y = to_csv(
            data,
            args.fields,
            args.ignore_missing,
            args.ignore_extra,
            args.loose,
            sort_keys=args.sort_keys,
        )
        print(y)

    elif t == "json":
        pretty_print(from_csv(text))


if __name__ == "__main__":
    main()
