"""Rotas para consulta de CNPJ e CNAEs."""

from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.dependencies import get_opencnpj_client
from src.domain.schemas.user import CNAEResponse, CNPJCNAEsResponse
from src.integrations.opencnpj import OpenCNPJClient

router = APIRouter()


@router.get(
    "/{cnpj}/cnaes",
    response_model=CNPJCNAEsResponse,
    summary="Consultar CNAEs de um CNPJ",
    description="Busca lista de CNAEs de um CNPJ via OpenCNPJ.",
)
async def get_cnpj_cnaes(
    cnpj: str,
    client: OpenCNPJClient = Depends(get_opencnpj_client),
) -> CNPJCNAEsResponse:
    cnpj_limpo = client.clean_cnpj(cnpj)

    try:
        data = await client.get_cnpj_data(cnpj_limpo)

        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CNPJ não encontrado",
            )

        cnaes_data = client.parse_cnaes_from_data(data)

        razao_social = (
            data.get("company", {}).get("name") if data.get("company") else None
        )

        primary_cnae_dict = cnaes_data.get("primary")
        secondary_cnaes_data = cast(
            list[dict[str, str]], cnaes_data.get("secondary", [])
        )

        return CNPJCNAEsResponse(
            cnpj=client.format_cnpj(cnpj_limpo),
            razao_social=razao_social,
            primary_cnae=CNAEResponse(
                **cast(dict[str, str], primary_cnae_dict)
            )
            if primary_cnae_dict
            else None,
            secondary_cnaes=[CNAEResponse(**cnae) for cnae in secondary_cnaes_data],
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
