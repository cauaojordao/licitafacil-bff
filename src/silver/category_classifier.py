"""
Classificador de editais por categorias CNAE usando Gemini API.
"""

import json
from typing import Any

import google.generativeai as genai


class CategoryClassifier:
    """
    Classifica editais em categorias MEI baseadas em CNAEs usando Gemini.
    """

    # Lista de CNAEs MEI mais comuns
    CNAES_MEI = [
        {"codigo": "5611-2/01", "descricao": "Restaurantes e similares"},
        {
            "codigo": "4744-0/01",
            "descricao": "Comércio varejista de ferragens e ferramentas",
        },
        {
            "codigo": "4753-9/00",
            "descricao": "Comércio varejista especializado de eletrodomésticos",
        },
        {
            "codigo": "4789-0/05",
            "descricao": "Comércio varejista de produtos saneantes domissanitários",
        },
        {"codigo": "8121-4/00", "descricao": "Limpeza em prédios e em domicílios"},
        {"codigo": "4330-4/05", "descricao": "Aplicação de revestimentos e de resinas"},
        {"codigo": "4313-4/00", "descricao": "Obras de terraplenagem"},
        {
            "codigo": "4322-3/02",
            "descricao": (
                "Instalação e manutenção de sistemas centrais de ar condicionado"
            ),
        },
        {"codigo": "7490-1/04", "descricao": "Consultoria em tecnologia da informação"},
        {
            "codigo": "6201-5/00",
            "descricao": "Desenvolvimento de programas de computador sob encomenda",
        },
    ]

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        """
        Inicializa o classificador.

        Args:
            api_key: Chave da API Gemini.
            model: Modelo Gemini a ser usado.
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def classify(self, objeto_compra: str) -> dict[str, Any]:
        """
        Classifica o edital em categorias CNAE.

        Args:
            objeto_compra: Descrição do objeto da licitação.

        Returns:
            Dicionário com categorias identificadas e confiança.
        """
        prompt = f"""
Você é um especialista em classificação de licitações públicas para MEI
(Microempreendedor Individual).

Analise o seguinte objeto de licitação e identifique até
3 categorias CNAE MEI mais adequadas:

OBJETO: {objeto_compra}

CNAES DISPONÍVEIS:
{json.dumps(self.CNAES_MEI, ensure_ascii=False, indent=2)}

Retorne APENAS um JSON válido no formato:
{{
  "categorias": [
    {{"codigo": "XXXX-X/XX", "descricao": "...", "confianca": 0.95}}
  ],
  "justificativa": "explicação breve"
}}
"""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Remove markdown code blocks se existirem
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            result = json.loads(result_text)
            return {
                "categorias": result.get("categorias", []),
                "justificativa": result.get("justificativa", ""),
                "status": "success",
            }
        except Exception as e:
            return {
                "categorias": [],
                "justificativa": "",
                "status": "error",
                "error_message": str(e),
            }
