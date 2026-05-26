"""Rotas para consulta de localidades (estados e municípios)."""

from fastapi import APIRouter, HTTPException, status

from src.domain.schemas.user import StateResponse
from src.integrations.ibge import ibge_client

router = APIRouter()


@router.get(
    "/states",
    response_model=list[StateResponse],
    summary="Listar estados brasileiros",
    description="Retorna lista de todos os estados do Brasil via API do IBGE.",
)
async def list_states() -> list[StateResponse]:
    """
    Lista todos os estados brasileiros.

    Returns:
        Lista de estados ordenados por nome

    Raises:
        HTTPException 500: Se erro na consulta ao IBGE
    """
    try:
        estados = await ibge_client.get_states()
        return [StateResponse(**estado) for estado in estados]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar lista de estados",
        ) from e


@router.get(
    "/states/{state_id}",
    response_model=StateResponse,
    summary="Buscar estado por ID",
    description="Retorna dados de um estado específico via API do IBGE.",
)
async def get_state(state_id: str) -> StateResponse:
    """
    Busca dados de um estado específico.

    Args:
        state_id: ID do estado no IBGE (ex: "35" para SP)

    Returns:
        Dados do estado

    Raises:
        HTTPException 404: Se estado não encontrado
        HTTPException 500: Se erro na consulta ao IBGE
    """
    try:
        estado = await ibge_client.get_state_by_id(state_id)

        if not estado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Estado não encontrado",
            )

        return StateResponse(**estado)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar dados do estado",
        ) from e
