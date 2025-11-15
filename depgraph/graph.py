from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from .errors import GraphError
from .sources import DependencySource


@dataclass
class DependencyGraph:
    adjacency: Dict[str, Set[str]] = field(default_factory=dict)
    ignored_packages: Set[str] = field(default_factory=set)

    def add_edge(self, src: str, dst: str) -> None:
        self.adjacency.setdefault(src, set()).add(dst)
        self.adjacency.setdefault(dst, set())

    def nodes(self) -> Set[str]:
        return set(self.adjacency.keys())


def build_graph_bfs_recursive(
    root: str,
    source: DependencySource,
    filter_substring: str = "",
) -> DependencyGraph:
    """
    Строит граф зависимостей, начиная с root, BFS-ом с рекурсией:
    - BFS реализован как рекурсивный обход по слоям.
    - Учитывается фильтрация по подстроке.
    - Циклы корректно обрабатываются за счёт множества visited.
    """
    graph = DependencyGraph()
    visited: Set[str] = set()
    filter_substring = filter_substring or ""

    def bfs_layer(current_layer: List[str]) -> None:
        next_layer: List[str] = []

        for pkg in current_layer:
            if pkg in visited:
                continue
            visited.add(pkg)

            if filter_substring and filter_substring in pkg:
                graph.ignored_packages.add(pkg)
                continue

            deps = source.get_direct_dependencies(pkg)
            for dep in deps:
                if filter_substring and filter_substring in dep:
                    graph.ignored_packages.add(dep)
                    continue
                graph.add_edge(pkg, dep)
                if dep not in visited:
                    next_layer.append(dep)

        if next_layer:
            bfs_layer(next_layer)

    bfs_layer([root])
    return graph


def detect_cycles(graph: DependencyGraph) -> bool:
    """
    Простейшая проверка наличия цикла через DFS с цветами (white/gray/black).
    Возвращает True, если цикл обнаружен.
    """
    color: Dict[str, str] = {node: "white" for node in graph.adjacency}

    def dfs(node: str) -> bool:
        color[node] = "gray"
        for neighbor in graph.adjacency.get(node, set()):
            if color[neighbor] == "gray":
                return True  # цикл
            if color[neighbor] == "white" and dfs(neighbor):
                return True
        color[node] = "black"
        return False

    for node in graph.adjacency:
        if color[node] == "white" and dfs(node):
            return True
    return False
