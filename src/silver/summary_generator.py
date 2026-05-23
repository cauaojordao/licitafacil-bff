"""
Gerador de resumos simplificados de editais usando Gemini API.
"""
import google.generativeai as genai


class SummaryGenerator:
    """
    Gera resumos simplificados de editais para MEIs.
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
        valor_estimado: float | None,
        modalidade: str | None,
        orgao: str | None,
    ) -> str:
        """
        Gera um resumo simplificado do edital.

        Args:
            objeto_compra: Descrição do objeto.
            valor_estimado: Valor estimado da licitação.
            modalidade: Modalidade de contratação.
            orgao: Órgão responsável.

        Returns:
            Resumo em linguagem simples.
        """
        valor_texto = f"R$ {valor_estimado:,.2f}" if valor_estimado else "Não informado"

        prompt = f"""
Você é um assistente que ajuda MEIs a entenderem editais de licitação.

Crie um resumo SIMPLES e DIRETO (máximo 3 frases) do edital abaixo:

OBJETO: {objeto_compra}
VALOR: {valor_texto}
MODALIDADE: {modalidade or 'Não informada'}
ÓRGÃO: {orgao or 'Não informado'}

Use linguagem clara e destaque o que o MEI precisa fornecer.
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Erro ao gerar resumo: {str(e)}"
