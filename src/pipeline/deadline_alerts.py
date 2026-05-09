from datetime import datetime, timedelta, timezone

from src.load.mongodb_loader import MongoDBLoader


class DeadlineAlertsPipeline:
    """
    Identifica licitações com prazo de encerramento de propostas próximo ao vencimento.
    Consulta o MongoDB e exibe alertas para contratos que fecham dentro de `dias_alerta` dias.
    """

    def __init__(self, loader: MongoDBLoader, dias_alerta: int = 7) -> None:
        self.loader = loader
        self.dias_alerta = dias_alerta

    def run(self) -> dict:
        now = datetime.now(tz=timezone.utc)
        limit_date = now + timedelta(days=self.dias_alerta)

        # ISO 8601 strings comparam lexicograficamente — safe para datas no formato YYYY-MM-DD...
        now_str = now.strftime("%Y-%m-%dT%H:%M:%S")
        limit_str = limit_date.strftime("%Y-%m-%dT%H:%M:%S")

        pipeline_agg = [
            {
                "$match": {
                    "data_encerramento_proposta": {
                        "$gte": now_str,
                        "$lte": limit_str,
                    }
                }
            },
            {
                "$project": {
                    "numero_controle_pncp": 1,
                    "objeto_compra": 1,
                    "data_encerramento_proposta": 1,
                    "valor_total_estimado": 1,
                    "modalidade_nome": 1,
                    "unidade_orgao.municipio_nome": 1,
                    "unidade_orgao.uf_sigla": 1,
                }
            },
            {"$sort": {"data_encerramento_proposta": 1}},
        ]

        alertas = list(self.loader.collection.aggregate(pipeline_agg))

        separador = "=" * 60
        print(f"\n{separador}")
        print(f"ALERTAS DE PRAZO — próximos {self.dias_alerta} dias")
        print(separador)

        if not alertas:
            print("Nenhuma licitação com prazo próximo encontrada.")
        else:
            for alerta in alertas:
                uf = alerta.get("unidade_orgao", {}).get("uf_sigla", "??")
                objeto = (alerta.get("objeto_compra") or "N/A")[:70]
                encerra = alerta.get("data_encerramento_proposta", "N/A")
                valor = alerta.get("valor_total_estimado") or 0
                print(f"  [{uf}] {objeto}")
                print(f"        Encerra: {encerra}  |  Valor est.: R$ {valor:,.2f}")

        return {"total_alertas": len(alertas), "alertas": alertas}
