from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HttpMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class ContentType(StrEnum):
    JSON = "application/json"
    TEXT = "text/plain"
    HTML = "text/html"


class MockEndpoint(BaseModel):
    """
    1つのモックエンドポイント定義。
    不変オブジェクトとして扱う。
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="UUID")
    path: str = Field(..., description="/users/123 などのパス")
    method: HttpMethod
    status_code: int = Field(200, ge=100, le=599)
    response_body: dict[str, Any] | str = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    latency_ms: int = Field(0, ge=0, description="シミュレートする遅延時間(ms)")

    @property
    def key(self) -> str:
        """ユニークキー: メソッドとパスの組み合わせ"""
        return f"{self.method}:{self.path}"


class MockTemplateContext(BaseModel):
    """レスポンス生成時の動的置換用コンテキスト"""

    model_config = ConfigDict(frozen=True)
    request_id: str
    timestamp: str


class MockCreate(BaseModel):
    """モック作成用データ"""

    model_config = ConfigDict(frozen=True)

    path: str = Field(..., description="/users/123 などのパス")
    method: HttpMethod
    status_code: int = Field(200, ge=100, le=599)
    response_body: dict[str, Any] | str = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    latency_ms: int = Field(0, ge=0, description="シミュレートする遅延時間(ms)")


class SimulationResult(BaseModel):
    """シミュレーション結果"""

    model_config = ConfigDict(frozen=True)

    status_code: int
    body: dict[str, Any] | str
    headers: dict[str, str]
