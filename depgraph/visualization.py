from __future__ import annotations

from pathlib import Path
from typing import Iterable

import subprocess

from .errors import VisualizationError
from .graph import DependencyGraph


def graph_to_mermaid(graph: DependencyGraph) -> str:
    """
    Формирует текстовое представление графа зависимостей в формате Mermaid.
    Пример:
      graph TD
        A --> B
        A --> C
        B --> D
    """
    lines: list[str] = ["graph TD"]

    if not graph.adjacency:
        return "\n".join(lines)

    for src, targets in sorted(graph.adjacency.items()):
        if not targets:
            # Обособленная вершина
            lines.append(f'    "{src}"')
        else:
            for dst in sorted(targets):
                lines.append(f'    "{src}" --> "{dst}"')

    return "\n".join(lines)


def save_mermaid(mermaid_text: str, path: str | Path) -> Path:
    path = Path(path)
    path.write_text(mermaid_text, encoding="utf-8")
    return path


def render_mermaid_png(mermaid_file: str | Path, png_file: str | Path) -> None:
    """
    Вызывает внешнюю утилиту mmdc (Mermaid CLI) для рендеринга PNG.
    Требуется предварительная установка:
      npm install -g @mermaid-js/mermaid-cli
    """
    mermaid_file = Path(mermaid_file)
    png_file = Path(png_file)

    try:
        subprocess.run(
            ["mmdc", "-i", str(mermaid_file), "-o", str(png_file)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise VisualizationError(
            "Не найдена утилита 'mmdc'. Установите Mermaid CLI: "
            "npm install -g @mermaid-js/mermaid-cli"
        ) from exc
    except subprocess.CalledProcessError as exc:  # noqa: BLE001
        raise VisualizationError(
            f"Ошибка при рендеринге диаграммы Mermaid: {exc.stderr.decode(errors='ignore')}"
        ) from exc
