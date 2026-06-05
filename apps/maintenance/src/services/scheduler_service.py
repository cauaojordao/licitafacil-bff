"""
Serviço de agendamento de tarefas.
"""

import time
from typing import Callable

import schedule

from core.config import CronjobSettings


class SchedulerService:
    """
    Serviço para agendamento de tarefas periódicas.
    """

    def __init__(self):
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
        print(f"⏰ Manutenção agendada para {self.settings.MAINTENANCE_HOUR}")

    def run_scheduler(self) -> None:
        """
        Inicia o loop do scheduler.
        """
        print("🚀 Scheduler de cronjobs iniciado")
        print(f"⏰ Próxima execução: {schedule.next_run()}")

        while True:
            schedule.run_pending()
            time.sleep(60)  # Verifica a cada minuto

    def run_once(self, function: Callable[[], None]) -> None:
        """
        Executa uma função imediatamente (útil para testes).

        Args:
            function: Função para executar.
        """
        print("🏃‍♂️ Executando tarefa imediatamente...")
        function()
