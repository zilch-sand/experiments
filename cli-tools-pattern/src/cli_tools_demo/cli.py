"""Console entry points for the demo package."""
from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Example CLI tools.")
    parser.add_argument(
        "--name",
        default="world",
        help="Name to greet or bid farewell (default: world).",
    )
    return parser


def hello_world() -> None:
    """Entry point for the hello-world CLI."""
    parser = build_parser()
    args = parser.parse_args()
    print(f"Hello, {args.name}!")


def goodbye_world() -> None:
    """Entry point for the goodbye-world CLI."""
    parser = build_parser()
    args = parser.parse_args()
    print(f"Goodbye, {args.name}!")
