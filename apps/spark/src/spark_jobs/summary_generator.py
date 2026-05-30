"""
Gerador de resumos simplificados de editais usando Gemini API.
"""

from typing import Any

import google.generativeai as genai


class SummaryGenerator:
    """
    Gera resumos simplificados de editais de licitação.
    """

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        """
        Inicializa o gerador.

        Args:
            api_key: Chave da API Gemini.
            model: Modelo Gemini a ser usado.
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def generate(
        self,
        objeto_compra: str,
        valor_estimado: float | None = None,
        modalidade: str | None = None,
        orgao: str | None = None,
    ) -> str:
        """
        Gera um resumo simplificado do edital.

        Args:
            objeto_compra: Descrição do objeto da licitação.
            valor_estimado: Valor estimado do edital.
            modalidade: Modalidade da licitação.
            orgao: Nome do órgão responsável.

        Returns:
            Resumo simplificado em até 200 caracteres.
        """
        prompt = f"""
Crie um resumo MUITO BREVE (máximo 150 caracteres) deste edital de licitação.
Foque no que está sendo comprado/contratado.

OBJETO: {objeto_compra}
VALOR: R$ {valor_estimado or 0:,.2f}
MODALIDADE: {modalidade or "N/A"}
ÓRGÃO: {orgao or "N/A"}

Retorne APENAS o resumo, sem explicações adicionais.
"""

        try:
            response = self.model.generate_content(prompt)
            summary = response.text.strip()

            # Garante que não ultrapasse 200 caracteres
            return summary[:200] if len(summary) > 200 else summary
        except Exception as e:
            print(f"❌ Erro ao gerar resumo: {e}")
            # Fallback: pega primeiras palavras do objeto
            return objeto_compra[:150] + "..." if len(objeto_compra) > 150 else objeto_compra
