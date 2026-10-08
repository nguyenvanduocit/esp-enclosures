"""printkit command line: new, cad, build."""

import argparse
import sys

from printkit import bundle


def main(argv=None):
    parser = argparse.ArgumentParser(prog="printkit")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "build",
        help="validate every model, version viewer assets, package offline ZIPs",
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            bundle.build_all()
    except ValueError as error:
        print(f"printkit: {error}", file=sys.stderr)
        return 1
    return 0
