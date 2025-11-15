from __future__ import annotations

import argparse
import sys

from .config import AppConfig
from .errors import ConfigError


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="depgraph",
        description="Анализ и визуализация графа зависимостей Python-пакетов."
    )

    parser.add_argument(
        "-p", "--package",
        help="Имя анализируемого Python-пакета.",
        required=True,
    )
    parser.add_argument(
        "-r", "--repo",
        help="URL репозитория (PyPI-страница).",
        required=True,
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["pypi", "test"],
        default="pypi",
        help="Режим работы: 'pypi' (по умолчанию) или 'test'.",
    )
    parser.add_argument(
        "-o", "--output-image",
        default="graph.png",
        help="Имя файла PNG с изображением графа зависимостей.",
    )
    parser.add_argument(
        "-f", "--filter",
        default="",
        help="Подстрока для фильтрации пакетов по имени.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        config = AppConfig.from_args(args)
    except ConfigError as exc:
        print(f"[CONFIG ERROR] {exc}", file=sys.stderr)
        return 2

    print("=== depgraph configuration ===")
    for key, value in config.as_dict().items():
        print(f"{key} = {value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
