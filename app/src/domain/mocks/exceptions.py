from dataclasses import dataclass


@dataclass(frozen=True)
class MockNotFoundError:
    method: str
    path: str
    message: str = "Mock endpoint not found"


@dataclass(frozen=True)
class MockAlreadyExistsError:
    method: str
    path: str
    message: str = "Mock endpoint already exists"


@dataclass(frozen=True)
class InvalidMockError:
    reason: str
    message: str = "Invalid mock definition"
