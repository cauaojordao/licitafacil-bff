import time

import google.generativeai as genai

from src.load.mongodb_loader import MongoDBLoader

SEGMENTOS_MEI = [
    "Alimentação e Bebidas",
    "Construção Civil e Reformas",
    "Tecnologia da Informação e Comunicação",
    "Limpeza e Conservação",
    "Manutenção e Reparos",
    "Transporte e Logística",
    "Educação e Treinamento",
    "Saúde e Bem-estar",
    "Comércio em Geral",
    "Artesanato e Manufatura",
    "Serviços Administrativos",
    "Outros",
]

_PROMPT_TEMPLATE = """\
Você é especialista em licitações públicas para Microempreendedores Individuais (MEIs) no Brasil.

Classifique o objeto da licitação abaixo em exatamente um dos segmentos listados.
Responda SOMENTE com o nome exato do segmento, sem pontuação ou explicação adicional.

Segmentos disponíveis:
{segmentos}

Objeto da licitação: {objeto}

Segmento:"""


class MEICategorizationPipeline:
    """
    Usa o Gemini para categorizar licitações pelo segmento de atuação do MEI.
    Processa registros no MongoDB que ainda não possuem o campo `segmento_mei`.
    """

    def __init__(self, loader: MongoDBLoader, gemini_api_key: str) -> None:
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY não configurada.")
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.loader = loader

    def _categorizar(self, objeto_compra: str) -> str:
        segmentos_fmt = "\n".join(f"- {s}" for s in SEGMENTOS_MEI)
        prompt = _PROMPT_TEMPLATE.format(segmentos=segmentos_fmt, objeto=objeto_compra)
        resposta = self.model.generate_content(prompt).text.strip()

        for segmento in SEGMENTOS_MEI:
            if segmento.lower() in resposta.lower():
                return segmento

        return "Outros"

    def run(self, limit: int = 50) -> dict:
        pendentes = list(
            self.loader.collection.find(
                {"segmento_mei": {"$exists": False}, "objeto_compra": {"$ne": None}},
                {"_id": 1, "numero_controle_pncp": 1, "objeto_compra": 1},
            ).limit(limit)
        )

        separador = "=" * 60
        print(f"\n{separador}")
        print(f"CATEGORIZAÇÃO MEI (Gemini) — {len(pendentes)} registros pendentes")
        print(separador)

        categorizados = 0
        erros = 0

        for doc in pendentes:
            try:
                segmento = self._categorizar(doc["objeto_compra"])
                self.loader.collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"segmento_mei": segmento}},
                )
                print(f"  ✓ {doc.get('numero_controle_pncp', '?')} → {segmento}")
                categorizados += 1
                time.sleep(0.4)  # evita throttling da API Gemini
            except Exception as exc:
                print(f"  ✗ {doc.get('numero_controle_pncp', '?')} — erro: {exc}")
                erros += 1

        print(f"\n  Resultado: {categorizados} categorizados, {erros} erros.")

        return {
            "total_processados": len(pendentes),
            "categorizados": categorizados,
            "erros": erros,
        }
