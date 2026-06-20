"""
Configurações específicas do Cronjob.
"""

from pydantic_settings import BaseSettings


class CronjobSettings(BaseSettings):
    """
    Configurações específicas para o Cronjob de manutenção.
    Herda configurações globais e adiciona configurações específicas.
    """

    # Configurações específicas do maintenance
    MAINTENANCE_HOUR: str = "03:00"
    EXPIRE_SNAPSHOTS_DAYS: int = 7
    COMPACTION_MIN_INPUT_FILES: int = 2

    @classmethod
    def get_maintenance_config(cls) -> dict[str, str]:
        """
        Retorna configurações específicas para manutenção.
        """
        return {
            "iceberg_warehouse": cls.ICEBERG_WAREHOUSE_PATH,
            "iceberg_database": cls.ICEBERG_DATABASE,
            "iceberg_table": cls.ICEBERG_TABLE,
            "maintenance_hour": cls.MAINTENANCE_HOUR,
            "expire_snapshots_days": str(cls.EXPIRE_SNAPSHOTS_DAYS),
        }
