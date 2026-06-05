"""
Publisher Kafka da camada Bronze.
Publica dados transformados para o tópico Kafka.
"""

import json
from typing import Any

from kafka import KafkaProducer


class KafkaPublisher:
    """
    Publisher para enviar mensagens ao Kafka.
    """

    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        """
        Inicializa o publisher Kafka.

        Args:
            bootstrap_servers: Endereço do broker Kafka.
            topic: Nome do tópico.
        """
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

    def publish(self, message: dict[str, Any]) -> bool:
        """
        Publica uma mensagem no Kafka.

        Args:
            message: Mensagem a ser publicada.

        Returns:
            True se a publicação foi bem-sucedida.
        """
        try:
            self.producer.send(self.topic, value=message)
            self.producer.flush()
            return True
        except Exception as e:
            print(f"Erro ao publicar mensagem: {e}")
            return False

    def publish_batch(self, messages: list[dict[str, Any]]) -> int:
        """
        Publica múltiplas mensagens em lote.

        Args:
            messages: Lista de mensagens.

        Returns:
            Quantidade de mensagens publicadas com sucesso.
        """
        published = 0
        for msg in messages:
            if self.publish(msg):
                published += 1
        return published

    def close(self) -> None:
        """
        Fecha a conexão com o Kafka.
        """
        self.producer.close()
