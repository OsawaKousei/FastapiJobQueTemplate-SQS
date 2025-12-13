from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.dependencies import get_mock_mgmt_service
from src.domain.mocks.exceptions import MockAlreadyExistsError, MockNotFoundError
from src.domain.mocks.schemas import MockCreate, MockEndpoint
from src.domain.mocks.services import MockManagementService
from src.shared.result import Failure, Success

router = APIRouter(prefix="/api/mocks", tags=["mocks"])


@router.post(
    "",
    response_model=MockEndpoint,
    status_code=status.HTTP_201_CREATED,
    description="Register a new mock endpoint.",
)
async def create_mock(
    schema: MockCreate,
    service: Annotated[MockManagementService, Depends(get_mock_mgmt_service)],
) -> MockEndpoint:
    result = await service.register(schema)
    match result:
        case Success(mock):
            return mock
        case Failure(MockAlreadyExistsError() as e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        case Failure(e):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )


@router.delete(
    "/{mock_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete a mock endpoint by ID.",
)
async def delete_mock(
    mock_id: str,
    service: Annotated[MockManagementService, Depends(get_mock_mgmt_service)],
) -> None:
    result = await service.delete(mock_id)
    match result:
        case Success(True):
            return
        case Failure(MockNotFoundError() as e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        case Failure(e):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )
