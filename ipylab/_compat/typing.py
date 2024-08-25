from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, Optional, TypeAlias, TypedDict

if sys.version_info < (3, 11):
    from typing import Optional

    from typing_extensions import Self, Unpack
else:
    from typing import Optional, Self, Unpack

__all__ = ["Optional", "TYPE_CHECKING", "Any", "TypeAlias", "TypedDict", "Self", "Unpack"]


def __dir__() -> list[str]:
    return __all__
