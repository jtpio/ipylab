from __future__ import annotations

import typing
from typing import Literal

import ipylab
from ipylab._compat.enum import StrEnum
from ipylab._compat.typing import NotRequired, TypedDict

__all__ = ["Area", "InsertMode", "Transform", "TransformType", "JavascriptType"]


class Area(StrEnum):
    # https://github.com/jupyterlab/jupyterlab/blob/da8e7bda5eebd22319f59e5abbaaa9917872a7e8/packages/application/src/shell.ts#L500
    main = "main"
    left = "left"
    right = "right"
    header = "header"
    top = "top"
    bottom = "bottom"
    down = "down"
    menu = "menu"


class InsertMode(StrEnum):
    # ref https://lumino.readthedocs.io/en/latest/api/types/widgets.DockLayout.InsertMode.html
    split_top = "split-top"
    split_left = "split-left"
    split_right = "split-right"
    split_bottom = "split-bottom"
    merge_top = "merge-top"
    merge_left = "merge-left"
    merge_right = "merge-right"
    merge_bottom = "merge-bottom"
    tab_before = "tab-before"
    tab_after = "tab-after"


class Transform(StrEnum):
    """An eumeration of transformations than can be applied to serialized data.

    Data sent between the kernel and Frontend is serialized using JSON. The transform is used
    to specify how that data should be transformed either prior to sending and/or once received.

    Transformations that require parameters should be specified in a dict with the the key 'transform' specifying
    the transform, and other keys providing the parameters accordingly.

    - done: [default] A string '--DONE--'
    - raw: No conversion. Note: data is serialized when sending, some object serialization will fail.
    - function: Use a function to calculate the return value. ['code'] = 'function...'
    - connection: Return a connection to a disposable object in the frontend.
        Use `auto_dispose=True` to dispose of the object when the kernel is dead or restarted.
    - advanced: A mapping of keys to transformations to apply sequentially on the object.

    `function`
    --------
    JS code defining a function and the data to return.

    The function must accept two args: obj, options.

    ```
    transform = {
        "transform": Transform.function,
        "code": "function (obj, options) { return obj.id; }",
    }

    transform = {
        "transform": Transform.connection,
        "cid": "ID TO USE FOR CONNECTION",
        "auto_dispose": True,  # Optional Default is False.
        "info": {} # Optional Dict of info.
    }

    `advanced`
    ---------
    ```
    transform = {
    "transform": Transform.advanced,
    "mappings":  {path: TransformType, ...}
    }
    ```
    """

    raw = "raw"
    done = "done"
    function = "function"
    connection = "connection"
    advanced = "advanced"

    @classmethod
    def validate(cls, transform: TransformType):
        """Return a valid copy of the transform."""
        if isinstance(transform, dict):
            match cls(transform["transform"]):
                case cls.function:
                    code = transform.get("code")
                    if not isinstance(code, str) or not code.startswith("function"):
                        raise TypeError
                    return TransformDictFunction(transform=Transform.function, code=code)
                case cls.connection:
                    cid = transform.get("cid")
                    if not isinstance(cid, str):
                        raise TypeError
                    transform_ = TransformDictConnection(transform=Transform.connection, cid=cid)
                    if info := transform.get("info"):
                        transform_["info"] = dict(info)
                    if auto_dispose := transform.get("auto_dispose"):
                        transform_["auto_dispose"] = bool(auto_dispose)
                    return transform_
                case cls.advanced:
                    mappings = {}
                    transform_ = TransformDictAdvanced(transform=Transform.advanced, mappings=mappings)
                    mappings_ = transform.get("mappings")
                    if not isinstance(mappings_, dict):
                        raise TypeError
                    for pth, tfm in mappings_.items():
                        mappings[pth] = cls.validate(tfm)
                    return transform_
                case _:
                    raise NotImplementedError
        transform_ = Transform(transform)
        if transform_ in [Transform.function, Transform.advanced]:
            msg = "This type of transform should be passed as a dict to provide the additional arguments"
            raise ValueError(msg)
        return transform_

    @classmethod
    def transform_payload(cls, transform: TransformType, payload: dict):
        """Transform the payload according to the transform."""
        transform_ = transform["transform"] if isinstance(transform, dict) else transform
        match transform_:
            case Transform.advanced:
                mappings = typing.cast(TransformDictAdvanced, transform)["mappings"]
                return {key: cls.transform_payload(mappings[key], payload[key]) for key in mappings}
            case Transform.connection:
                return ipylab.Connection(**payload)
        return payload


class TransformDictFunction(TypedDict):
    transform: Literal[Transform.function]
    code: NotRequired[str]


class TransformDictAdvanced(TypedDict):
    transform: Literal[Transform.advanced]
    mappings: dict[str, TransformType]


class TransformDictConnection(TypedDict):
    transform: Literal[Transform.connection]
    cid: str
    auto_dispose: NotRequired[bool]
    info: NotRequired[dict]


TransformType = Transform | TransformDictAdvanced | TransformDictFunction | TransformDictConnection


class JavascriptType(StrEnum):
    string = "string"
    number = "number"
    boolean = "boolean"
    object = "object"
    function = "function"
