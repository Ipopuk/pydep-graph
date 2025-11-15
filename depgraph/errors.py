class ConfigError(Exception):
    """Ошибки, связанные с конфигурацией/аргументами CLI."""


class RepositoryError(Exception):
    """Ошибки, связанные с получением зависимостей из репозитория."""


class GraphError(Exception):
    """Ошибки при построении или обработке графа зависимостей."""


class VisualizationError(Exception):
    """Ошибки при визуализации графа."""
