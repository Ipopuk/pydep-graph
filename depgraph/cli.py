from __future__ import annotations

import argparse
import sys

from .config import AppConfig
from .errors import ConfigError, RepositoryError
from .sources import PyPIDependencySource


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="depgraph",
        description="Анализ и визуализация графа зависимостей Python-пакетов."
    )

    parser.add_argument(
        "-p", "--package",
        help="Имя анализируемого Python-пакета (например, 'requests').",
        required=True,
    )
    parser.add_argument(
        "-r", "--repo",
        help="URL репозитория (PyPI-страница) или путь к файлу тестового репозитория.",
        required=True,
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["pypi", "test"],
        default="pypi",
        help="Режим работы: 'pypi' (по умолчанию) или 'test' (работа с тестовым файлом-графом).",
    )
    parser.add_argument(
        "-o", "--output-image",
        default="graph.png",
        help="Имя файла PNG с изображением графа зависимостей (по умолчанию graph.png).",
    )
    parser.add_argument(
        "-f", "--filter",
        default="",
        help="Подстрока для фильтрации пакетов по имени (игнорируются, если содержат её).",
    )
    parser.add_argument(
        "--show-direct-deps",
        action="store_true",
        help="(этап 2) Вывести на экран все прямые зависимости заданного пакета.",
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

    if config.mode.value == "pypi" and args.show_direct_deps:
        source = PyPIDependencySource(config.repo)
        try:
            deps = source.get_direct_dependencies(config.package_name)
        except RepositoryError as exc:
            print(f"[REPOSITORY ERROR] {exc}", file=sys.stderr)
            return 3

        print("\n=== Direct dependencies (PyPI) ===")
        if not deps:
            print("(нет прямых зависимостей)")
        else:
            for d in deps:
                print(f"- {d}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
