"""Utilitários para validação e formatação de CNPJ."""


def clean_cnpj(cnpj: str) -> str:
    """Remove formatação do CNPJ e valida que possui 14 caracteres.

    Aceita CNPJ com ou sem pontuação (ex: "12.345.678/0001-90" ou "12345678000190").
    Converte letras para maiúsculo (CNPJs alfanuméricos).

    Raises:
        ValueError: Se o CNPJ não tiver 14 caracteres após limpeza
    """
    cleaned = cnpj.replace(".", "").replace("/", "").replace("-", "").strip().upper()
    if len(cleaned) != 14:
        raise ValueError("CNPJ deve conter exatamente 14 caracteres")
    return cleaned


def format_cnpj(cnpj: str) -> str:
    """Formata CNPJ alfanumérico para exibição (XX.XXX.XXX/XXXX-XX).

    Expects a clean 14-character CNPJ (call clean_cnpj first).
    """
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
