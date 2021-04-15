from enum import Enum, auto
from typing import Any, Optional

import prison
from fastapi import Body, FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field, ValidationError

app = FastAPI()


class StrEnum(str, Enum):
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[Any]
    ) -> str:
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


class Filters(BaseModel):
    options: list[Filter] = Field([], title="optionsのフィルタ")


class Item(BaseModel):
    id: int = Field(title="ID")
    name: str = Field(title="名前")
    options: dict[str, Any] = Field(title="options")


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


items = [
    Item(id=1, name="名前1", options={}),
    Item(
        id=2,
        name="名前2",
        options={"int": 1, "float": 1.1, "date": "2021-01-01", "str": "foobazbar"},
    ),
]


@app.post("/items/search", response_model=list[Item])
def search_items(
    name: str = Query("", title="name", description="nameの部分一致"),
    filters: Filters = Body(Filters(), title="filter", description="options filter"),
) -> Any:
    results = items

    if name:
        results = list(filter(lambda x: name in x.name, results))

    for o in filters.options:
        results = list(filter(lambda x: options_filter(o, x), results))

    return results


@app.get("/items", response_model=list[Item])
def read_items(
    name: str = Query("", title="name", description="nameの部分一致"),
    filters: Optional[str] = Query(None, title="filter", description="options filter"),
) -> Any:
    if filters:
        try:
            decoded_filters = prison.loads(filters)
            validated_filters = Filters(**decoded_filters)
        except prison.decoder.ParserException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.errors(),
            )

    results = items

    if name:
        results = list(filter(lambda x: name in x.name, results))

    for o in validated_filters.options:
        results = list(filter(lambda x: options_filter(o, x), results))

    return results
