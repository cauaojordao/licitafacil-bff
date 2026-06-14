"""Rotas para consulta de CNPJ e CNAEs."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.dependencies import get_opencnpj_client
from src.domain.schemas.user import CNAEResponse, CNPJCNAEsResponse
from src.integrations.opencnpj import OpenCNPJClient

router = APIRouter()


@router.get(
    "/cnaes",
    response_model=CNPJCNAEsResponse,
    summary="Consultar CNAEs de um CNPJ",
    description="Busca lista de CNAEs de um CNPJ via OpenCNPJ (com ou sem formatação).",
)
async def get_cnpj_cnaes(
    cnpj: str = Query(
        ...,
        description="CNPJ com ou sem formatação",
    ),
    client: OpenCNPJClient = Depends(get_opencnpj_client),
) -> CNPJCNAEsResponse:
    try:
        data = await client.get_cnpj_data(cnpj)

        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CNPJ não encontrado",
            )

        cnpj_limpo = client.clean_cnpj(cnpj)
        cnaes_data = client.parse_cnaes_from_data(data)

        razao_social = (
            data.get("company", {}).get("name") if data.get("company") else None
        )

        primary_cnae = cnaes_data["primary"]
        secondary_cnaes = cnaes_data["secondary"]

        return CNPJCNAEsResponse(
            cnpj=client.format_cnpj(cnpj_limpo),
            razao_social=razao_social,
            primary_cnae=CNAEResponse(**primary_cnae) if primary_cnae else None,
            secondary_cnaes=[CNAEResponse(**cnae) for cnae in secondary_cnaes],
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao consultar CNPJ",
        ) from e
