"""
Publisher Kafka da camada Bronze.
Responsável por publicar registros brutos no tópico Kafka.
"""

import json
from typing import Any

from kafka import KafkaProducer as KafkaClient


class BronzeKafkaPublisher:
    """
    Responsável por publicar os registros brutos da camada Bronze no Kafka.
    """

    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        """
        Inicializa o publisher.

        Args:
            bootstrap_servers: Endereço do broker Kafka. Ex: 'localhost:9092'
            topic: Nome do tópico Kafka onde os dados serão publicados.
        """
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self._producer = KafkaClient(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

    def publish(self, records: list[dict[str, Any]]) -> int:
        """
        Publica a lista de registros no tópico Kafka.

        Args:
            records: Lista de documentos a publicar.

        Returns:
            Quantidade de mensagens publicadas.
        """
        if not records:
            return 0

        count = 0
        for record in records:
            try:
                self._producer.send(self.topic, value=record)
                count += 1
            except Exception as e:
                print(f"❌ Erro ao publicar mensagem: {e}")

        self._producer.flush()
        return count

    def close(self) -> None:
        """Fecha a conexão com Kafka."""
        self._producer.close()
