from __future__ import annotations

import argparse
import sys

from .config import AppConfig
from .errors import ConfigError, RepositoryError, GraphError
from .graph import build_graph_bfs_recursive, detect_cycles, topological_load_order
from .sources import PyPIDependencySource, TestFileDependencySource


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="depgraph",
        description="Анализ и визуализация графа зависимостей Python-пакетов."
    )

    parser.add_argument(
        "-p", "--package",
        help="Имя анализируемого Python-пакета или узла графа (в тестовом режиме).",
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
        help="Режим работы: 'pypi' или 'test'.",
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
    parser.add_argument(
        "--show-direct-deps",
        action="store_true",
        help="(этап 2/3) Вывести на экран все прямые зависимости заданного пакета.",
    )
    parser.add_argument(
        "--show-load-order",
        action="store_true",
        help="(этап 4) Показать порядок загрузки зависимостей для заданного пакета.",
    )
    parser.add_argument(
        "--no-visualization",
        action="store_true",
        help="Не генерировать Mermaid и PNG-файл (по умолчанию визуализация включена).",
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

    if config.mode.value == "pypi":
        source = PyPIDependencySource(config.repo)
    else:
        source = TestFileDependencySource(config.repo)

    if args.show_direct_deps:
        try:
            deps = source.get_direct_dependencies(config.package_name)
        except RepositoryError as exc:
            print(f"[REPOSITORY ERROR] {exc}", file=sys.stderr)
            return 3

        print("\n=== Direct dependencies ===")
        if not deps:
            print("(нет прямых зависимостей)")
        else:
            for d in deps:
                print(f"- {d}")

    print("\n=== Building dependency graph (BFS + recursion) ===")
    graph = build_graph_bfs_recursive(
        root=config.package_name,
        source=source,
        filter_substring=config.filter_substring,
    )

    print(f"Всего узлов в графе: {len(graph.nodes())}")
    if graph.ignored_packages:
        ignored_str = ", ".join(sorted(graph.ignored_packages))
        print(f"Игнорированы пакеты (по фильтру): {ignored_str}")

    has_cycle = detect_cycles(graph)
    print(f"Циклические зависимости: {'обнаружены' if has_cycle else 'не обнаружены'}")

    if args.show_load_order:
        print("\n=== Load order (topological) ===")
        try:
            order = topological_load_order(graph, config.package_name)
        except GraphError as exc:
            print(f"[GRAPH ERROR] {exc}", file=sys.stderr)
        else:
            for i, name in enumerate(order, start=1):
                print(f"{i}. {name}")

    # Визуализация (если не отключена)
    if not args.no_visualization:
        from .visualization import graph_to_mermaid, save_mermaid, render_mermaid_png
        from .errors import VisualizationError

        print("\n=== Visualization (Mermaid + PNG) ===")
        mermaid_text = graph_to_mermaid(graph)

        mermaid_file = config.output_image.with_suffix(".mmd")
        save_mermaid(mermaid_text, mermaid_file)
        print(f"Mermaid-диаграмма сохранена в: {mermaid_file}")

        try:
            render_mermaid_png(mermaid_file, config.output_image)
        except VisualizationError as exc:
            print(f"[VISUALIZATION WARNING] {exc}", file=sys.stderr)
        else:
            print(f"PNG с графом зависимостей сохранён в: {config.output_image}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
