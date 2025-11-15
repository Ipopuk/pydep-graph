from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import List
from urllib.parse import urlparse
from urllib.request import urlopen

from .errors import RepositoryError

from pathlib import Path
from typing import Dict, Set


class DependencySource(ABC):
    """Абстракция источника зависимостей."""

    @abstractmethod
    def get_direct_dependencies(self, package_name: str) -> List[str]:
        """Вернуть список имён пакетов, от которых непосредственно зависит package_name."""
        raise NotImplementedError


class PyPIDependencySource(DependencySource):
    """
    Источник зависимостей для реальных пакетов через PyPI JSON API.
    Запрещён pip, но PyPI API и stdlib можно использовать.
    """

    def __init__(self, repo_url: str):
        self.repo_url = repo_url.rstrip("/")

    def _extract_package_from_repo(self, default_name: str) -> str:
        """
        Пытается вытащить имя пакета из URL вида:
        https://pypi.org/project/requests/...
        Если не получается — возвращает default_name.
        """
        parsed = urlparse(self.repo_url)
        if "pypi.org" in parsed.netloc and parsed.path.startswith("/project/"):
            parts = parsed.path.strip("/").split("/")
            if len(parts) >= 2:
                return parts[1]
        return default_name

    def get_direct_dependencies(self, package_name: str) -> List[str]:
        package = self._extract_package_from_repo(package_name).lower()
        url = f"https://pypi.org/pypi/{package}/json"

        try:
            with urlopen(url) as resp:
                data = json.load(resp)
        except Exception as exc:
            raise RepositoryError(f"Не удалось получить метаданные из {url}: {exc}") from exc

        requires = data.get("info", {}).get("requires_dist") or []
        deps: List[str] = []

        for entry in requires:
            name_part = entry.split(";", 1)[0].strip()
            if not name_part:
                continue

            cutoff = len(name_part)
            for ch in (" ", "(", "["):
                idx = name_part.find(ch)
                if idx != -1:
                    cutoff = min(cutoff, idx)
            dep_name = name_part[:cutoff].strip()
            if dep_name:
                deps.append(dep_name.lower())

        return deps


class TestFileDependencySource(DependencySource):
    """
    Источник зависимостей для тестового репозитория.
    Формат файла:
      A: B C
      B: C
      C:
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._graph: Dict[str, Set[str]] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            raise RepositoryError(f"Файл тестового репозитория не найден: {self.path}")

        graph: Dict[str, Set[str]] = {}

        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" not in line:
                    raise RepositoryError(f"Некорректная строка в тестовом файле: {line!r}")
                name_part, deps_part = line.split(":", 1)
                name = name_part.strip()
                deps = [d.strip() for d in deps_part.split() if d.strip()]
                graph.setdefault(name, set()).update(deps)

                for d in deps:
                    graph.setdefault(d, set())

        self._graph = graph

    def get_direct_dependencies(self, package_name: str) -> List[str]:
        return sorted(self._graph.get(package_name, set()))
