from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from .errors import ConfigError


class RepositoryMode(str, Enum):
    PYPI = "pypi"
    TEST = "test"


@dataclass
class AppConfig:
    package_name: str
    repo: str               # URL
    mode: RepositoryMode
    output_image: Path
    filter_substring: str

    @classmethod
    def from_args(cls, args: "argparse.Namespace") -> "AppConfig":
        package_name = (args.package or "").strip()
        if not package_name:
            raise ConfigError("Имя анализируемого пакета (--package) не задано или пусто.")
        try:
            mode = RepositoryMode(args.mode)
        except ValueError:
            raise ConfigError(
                f"Некорректный режим '--mode={args.mode}'. Допустимо: {', '.join(m.value for m in RepositoryMode)}."
            )

        repo = (args.repo or "").strip()
        if not repo:
            raise ConfigError("Не указан URL репозитория / путь к тестовому репозиторию (--repo).")

        if mode is RepositoryMode.TEST:
            path = Path(repo)
            if not path.exists():
                raise ConfigError(f"Файл тестового репозитория не найден: {path}")
            if not path.is_file():
                raise ConfigError(f"Ожидался путь к файлу тестового репозитория, но это не файл: {path}")

        image_path = Path(args.output_image or "graph.png")
        if image_path.is_dir():
            raise ConfigError(
                f"Путь к файлу изображения указывает на директорию: {image_path}"
            )
        if not image_path.suffix:
            image_path = image_path.with_suffix(".png")

        filter_substring = args.filter or ""

        return cls(
            package_name=package_name,
            repo=repo,
            mode=mode,
            output_image=image_path,
            filter_substring=filter_substring,
        )

    def as_dict(self) -> dict[str, str]:
        """Вывод 'ключ = значение'."""
        return {
            "package_name": self.package_name,
            "repo": self.repo,
            "mode": self.mode.value,
            "output_image": str(self.output_image),
            "filter_substring": self.filter_substring,
        }
