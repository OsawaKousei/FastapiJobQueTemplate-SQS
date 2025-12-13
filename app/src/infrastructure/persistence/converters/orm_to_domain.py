from src.domain.mocks.schemas import HttpMethod, MockEndpoint
from src.infrastructure.persistence.postgres.models import MockEndpointModel


def to_domain(orm_model: MockEndpointModel) -> MockEndpoint:
    """
    SQLAlchemyモデルをドメインモデルに変換する
    """
    return MockEndpoint(
        id=orm_model.id,
        path=orm_model.path,
        method=HttpMethod(orm_model.method),
        status_code=orm_model.status_code,
        response_body=orm_model.response_body,
        headers=orm_model.headers,
        latency_ms=orm_model.latency_ms,
    )


def to_orm(domain_model: MockEndpoint) -> MockEndpointModel:
    """
    ドメインモデルをSQLAlchemyモデルに変換する
    """
    return MockEndpointModel(
        id=domain_model.id,
        path=domain_model.path,
        method=domain_model.method.value,
        status_code=domain_model.status_code,
        response_body=domain_model.response_body,
        headers=domain_model.headers,
        latency_ms=domain_model.latency_ms,
    )
