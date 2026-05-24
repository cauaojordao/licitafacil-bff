"""
Cliente Kafka Producer genérico para publicação de mensagens.
"""

import json
from typing import Any

from kafka import KafkaProducer as _KafkaProducer


class KafkaProducer:
    """
    Cliente Kafka genérico para publicação de mensagens em tópicos.
    """

    def __init__(self, bootstrap_servers: str) -> None:
        """
        Inicializa o producer Kafka.

        Args:
            bootstrap_servers: Endereço(s) do broker Kafka. Ex: 'localhost:9092'
        """
        self._producer = _KafkaProducer(
            bootstrap_servers=bootstrap_servers.split(","),
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode(
                "utf-8"
            ),
        )

    def publish(self, topic: str, message: dict[str, Any]) -> None:
        """
        Publica uma única mensagem no tópico.

        Args:
            topic: Nome do tópico Kafka.
            message: Mensagem a ser publicada.
        """
        self._producer.send(topic, value=message)

    def publish_many(self, topic: str, messages: list[dict[str, Any]]) -> int:
        """
        Publica uma lista de mensagens no tópico.

        Args:
            topic: Nome do tópico Kafka.
            messages: Lista de mensagens a serem publicadas.

        Returns:
            Quantidade de mensagens publicadas.
        """
        for message in messages:
            self._producer.send(topic, value=message)
        self._producer.flush()
        return len(messages)

    def close(self) -> None:
        """Fecha a conexão com o broker."""
        self._producer.close()
