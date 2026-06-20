"""
Serviço de agendamento de tarefas.
"""

import logging
import time
from collections.abc import Callable

import schedule
from core.config import CronjobSettings

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Serviço para agendamento de tarefas periódicas.
    """

    def __init__(self) -> None:
        """
        Inicializa o serviço de agendamento.
        """
        self.settings = CronjobSettings()

    def schedule_maintenance(self, maintenance_function: Callable[[], None]) -> None:
        """
        Agenda a função de manutenção para executar diariamente.

        Args:
            maintenance_function: Função que executa a manutenção.
        """
        schedule.every().day.at(self.settings.MAINTENANCE_HOUR).do(maintenance_function)
        logger.info("Manutenção agendada para %s", self.settings.MAINTENANCE_HOUR)

    def run_scheduler(self) -> None:
        """
        Inicia o loop do scheduler.
        """
        logger.info("Scheduler de cronjobs iniciado")
        logger.info("Próxima execução: %s", schedule.next_run())

        while True:
            schedule.run_pending()
            time.sleep(60)  # Verifica a cada minuto

    def run_once(self, function: Callable[[], None]) -> None:
        """
        Executa uma função imediatamente (útil para testes).

        Args:
            function: Função para executar.
        """
        logger.info("Executando tarefa imediatamente...")
        function()
