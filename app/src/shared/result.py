from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True)
class Success(Generic[T]):
    """Represents a successful operation result."""

    value: T


@dataclass(frozen=True)
class Failure(Generic[E]):
    """Represents a failed operation result."""

    error: E


# Result type alias for use in type hints
# Example: def my_func() -> Result[int, str]: ...
Result = Success[T] | Failure[E]
