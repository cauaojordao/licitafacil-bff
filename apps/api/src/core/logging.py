"""Configuração de logging da aplicação."""

import logging
import sys

from src.core.config import settings


def setup_logging() -> None:
    """
    Configura o sistema de logging da aplicação.

    Define formato, nível e handlers para os logs.
    """
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "%(funcName)s:%(lineno)d - %(message)s"
    )

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado com o nome especificado.

    Args:
        name: Nome do módulo/componente

    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


logger = get_logger(settings.APP_NAME)
