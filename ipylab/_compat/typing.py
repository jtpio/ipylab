from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, TypeAlias, TypedDict

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired, Self, TypedDict, Unpack
else:
    from typing import NotRequired, Self, TypedDict, Unpack

__all__ = ["NotRequired", "TYPE_CHECKING", "Any", "TypeAlias", "TypedDict", "Self", "Unpack"]


def __dir__() -> list[str]:
    return __all__
