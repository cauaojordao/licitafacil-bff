"""
Serviço para publicação de mensagens no Kafka.
"""

import json
from typing import Any, List

from libs.common.kafka_producer import KafkaProducer

class KafkaService:
    """
    Serviço para publicação de dados no Kafka.
    """

    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        """
        Inicializa o serviço Kafka.

        Args:
            bootstrap_servers: Servidores do Kafka.
            topic: Tópico para publicação.
        """
        self.producer = KafkaProducer(bootstrap_servers)
        self.topic = topic

    def publish_batch(self, data: List[dict]) -> int:
        """
        Publica um lote de dados no Kafka.

        Args:
            data: Lista de dados para publicar.

        Returns:
            Número de mensagens publicadas com sucesso.
        """
        try:
            # Usa o método publish_many que já faz flush internamente
            published_count = self.producer.publish_many(self.topic, data)
            print(f"📤 Publicados no Kafka: {published_count} mensagens")
            return published_count

        except Exception as e:
            print(f"❌ Erro ao publicar lote no Kafka: {e}")
            # Fallback: tenta um por um
            published_count = 0
            for record in data:
                try:
                    self.producer.publish(self.topic, record)
                    published_count += 1
                except Exception as individual_error:
                    print(f"❌ Erro ao publicar registro individual no Kafka: {individual_error}")
                    continue
            return published_count

    def close(self) -> None:
        """
        Fecha o produtor Kafka.
        """
        self.producer.close()
