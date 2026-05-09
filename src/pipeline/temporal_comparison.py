from datetime import date, timedelta

from src.load.mongodb_loader import MongoDBLoader


class TemporalComparisonPipeline:
    """
    Compara os contratos publicados hoje com os de ontem no MongoDB para
    identificar novas oportunidades de licitação para MEIs.

    Depende de que o ETLPipeline já tenha carregado os dados de ambos os dias.
    """

    def __init__(self, loader: MongoDBLoader) -> None:
        self.loader = loader

    def _ids_por_data(self, data_prefix: str) -> set[str]:
        docs = self.loader.collection.find(
            {"data_publicacao_pncp": {"$regex": f"^{data_prefix}"}},
            {"numero_controle_pncp": 1},
        )
        return {doc["numero_controle_pncp"] for doc in docs if doc.get("numero_controle_pncp")}

    def run(self) -> dict:
        hoje = date.today()
        ontem = hoje - timedelta(days=1)

        hoje_prefix = hoje.strftime("%Y-%m-%d")
        ontem_prefix = ontem.strftime("%Y-%m-%d")

        ids_hoje = self._ids_por_data(hoje_prefix)
        ids_ontem = self._ids_por_data(ontem_prefix)

        novos_ids = ids_hoje - ids_ontem
        encerrados_ids = ids_ontem - ids_hoje  # publicados ontem, ausentes hoje

        separador = "=" * 60
        print(f"\n{separador}")
        print(f"COMPARAÇÃO TEMPORAL: {ontem_prefix} → {hoje_prefix}")
        print(separador)
        print(f"  Contratos ontem : {len(ids_ontem)}")
        print(f"  Contratos hoje  : {len(ids_hoje)}")
        print(f"  Novas oportunidades hoje       : {len(novos_ids)}")
        print(f"  Saíram do período (encerradas) : {len(encerrados_ids)}")

        novas_oportunidades = []
        if novos_ids:
            docs = list(
                self.loader.collection.find(
                    {"numero_controle_pncp": {"$in": list(novos_ids)}},
                    {
                        "numero_controle_pncp": 1,
                        "objeto_compra": 1,
                        "valor_total_estimado": 1,
                        "modalidade_nome": 1,
                        "unidade_orgao.uf_sigla": 1,
                        "data_encerramento_proposta": 1,
                    },
                ).limit(10)
            )
            novas_oportunidades = docs
            print(f"\n  Amostra de novas oportunidades (até 10):")
            for doc in docs:
                uf = doc.get("unidade_orgao", {}).get("uf_sigla", "??")
                objeto = (doc.get("objeto_compra") or "N/A")[:65]
                valor = doc.get("valor_total_estimado") or 0
                print(f"    [{uf}] {objeto}  |  R$ {valor:,.2f}")

        return {
            "total_ontem": len(ids_ontem),
            "total_hoje": len(ids_hoje),
            "novas_oportunidades": len(novos_ids),
            "encerradas": len(encerrados_ids),
            "amostra_novas": novas_oportunidades,
        }
