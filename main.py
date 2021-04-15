import json
from enum import Enum, auto
from fastapi import FastAPI, Query, Body
from pydantic import BaseModel, Field, Json
from typing import Any, Optional

app = FastAPI()


class StrEnum(str, Enum):
    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[Any]) -> str:
        return name.lower()


class Condition(StrEnum):
    EQ = auto()  # equal ==
    NEQ = auto()  # not equal !=
    GT = auto()  # greater than <
    GE = auto()  # greater equal <=
    LT = auto()  # less than >
    LE = auto()  # less equal >=


class Filter(BaseModel):
    key: str = Field(title="key")
    val: Any = Field(title="value")
    cond: Condition = Field(title="condition")


class Item(BaseModel):
    name: str = Field(title="名前")
    options: dict[str, Any] = Field(title="options")

items = [
    Item(name="名前1", options={}),
    Item(name="名前2", options={"int": 1, "float": 1.1, "date": "2021-01-01", "str": "foobazbar"}),
]

@app.get("/items", response_model=list[Item])
def read_root(
    name: str = Query("", title="name", description="nameの部分一致"),
    options: list[Filter] = Body([], title="options", description="optionsのフィルタ"),
) -> list[Item]:
    results = items

    if name:
        results = list(filter(lambda x: name in x.name, results))

    def options_filter(f: Filter, item: Item) -> bool:
        if f.key not in item.options:
            return False

        val = item.options[f.key]

        if type(f.val) != type(val):
            return False

        if f.cond == Condition.EQ:
            return val == f.val
        if f.cond == Condition.NEQ:
            return val != f.val
        if f.cond == Condition.GT:
            return val > f.val
        if f.cond == Condition.GE:
            return val >= f.val
        if f.cond == Condition.LT:
            return val < f.val
        if f.cond == Condition.LE:
            return val <= f.val

        return False  # pragma: no cover

    for o in options:
        results = list(filter(lambda x: options_filter(o, x), results))

    return results
