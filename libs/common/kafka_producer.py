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

    def send(self, topic: str, key: bytes = None, value: bytes = None) -> None:
        """
        Interface compatível com kafka-python para envio de mensagem.

        Args:
            topic: Nome do tópico Kafka.
            key: Chave da mensagem (opcional).
            value: Valor da mensagem em bytes.
        """
        # Converte bytes de volta para dict se necessário
        if value:
            try:
                message_dict = json.loads(value.decode("utf-8"))
                self._producer.send(topic, value=message_dict, key=key)
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Se não for JSON válido, manda como string
                self._producer.send(
                    topic,
                    value={
                        "raw_data": value.decode("utf-8", errors="ignore"),
                    },
                    key=key,
                )

    def flush(self) -> None:
        """
        Força o envio de todas as mensagens pendentes.
        """
        self._producer.flush()

    def close(self) -> None:
        """Fecha a conexão com o broker."""
        self._producer.close()
