import json
from typing import Any

from kafka import KafkaProducer as _KafkaProducer


class KafkaProducer:
    """
    Cliente Kafka genérico para publicação de mensagens.
    """

    def __init__(self, bootstrap_servers: str) -> None:
        self._producer = _KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        )
"""
Publisher Kafka da camada Bronze.
Responsável por publicar registros brutos no tópico Kafka.
"""
from typing import Any

from src.messaging.kafka_producer import KafkaProducer


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
        self._producer = KafkaProducer(bootstrap_servers=bootstrap_servers)

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

        count = self._producer.publish_many(topic=self.topic, messages=records)
        self._producer.close()
        return count
    def publish(self, topic: str, message: dict[str, Any]) -> None:
        self._producer.send(topic, value=message)

    def publish_many(self, topic: str, messages: list[dict[str, Any]]) -> int:
        for message in messages:
            self._producer.send(topic, value=message)
        self._producer.flush()
        return len(messages)

    def close(self) -> None:
        self._producer.close()