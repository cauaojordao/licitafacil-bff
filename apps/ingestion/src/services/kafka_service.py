"""
Serviço para publicação de mensagens no Kafka.
"""

import logging

from libs.common.kafka_producer import KafkaProducer

logger = logging.getLogger(__name__)


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

    def publish_batch(self, data: list[dict]) -> int:
        """
        Publica um lote de dados no Kafka.

        Args:
            data: Lista de dados para publicar.

        Returns:
            Número de mensagens publicadas com sucesso.
        """
        try:
            published_count = self.producer.publish_many(self.topic, data)
            logger.info("Publicados no Kafka: %s mensagens", published_count)
            return published_count

        except Exception as e:
            logger.error("Erro ao publicar lote no Kafka: %s", e)
            # Fallback: tenta um por um
            published_count = 0
            for record in data:
                try:
                    self.producer.publish(self.topic, record)
                    published_count += 1
                except Exception as individual_error:
                    logger.error(
                        "Erro ao publicar registro individual no Kafka: %s",
                        individual_error,
                    )
                    continue
            return published_count

    def close(self) -> None:
        """
        Fecha o produtor Kafka.
        """
        self.producer.close()
