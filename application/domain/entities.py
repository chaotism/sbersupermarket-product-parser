from datetime import datetime, date, time, timedelta
from decimal import Decimal
from enum import Enum
from types import GeneratorType
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from common.utils import utc_now
from domain.types import IntId


class EncodedModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        allow_population_by_field_name = True
        orm_mode = True
        json_encoders = (
            {  # possible to remove and use jsonable_encoder from fastapi.encoders
                UUID: str,
                datetime: lambda dt: dt.isoformat(),
                date: lambda d: d.isoformat(),
                time: lambda t: t.isoformat(),
                timedelta: lambda td: td.total_seconds(),
                bytes: lambda o: o.decode(),
                set: list,
                frozenset: list,
                GeneratorType: list,
                Decimal: float,
                Enum: lambda v: v.value,
            }
        )


class Entity(EncodedModel):
    id: Optional[IntId] = Field(description='local storage Id')
    created_at: Optional[datetime] = Field(default_factory=utc_now)
    modified_at: Optional[datetime] = Field(default_factory=utc_now)

    def get_id(self):
        return self.id

    def set_id(self, id_: IntId):
        self.id = id_

    def set_modified_at(self):
        self.modified_at = utc_now()

    def update(self, instance: BaseModel):
        self_data = self.dict()
        self_data.update(instance.dict(exclude_none=True))
        self.__init__(**self_data)  # type: ignore[misc]
        self.set_modified_at()

    def dict(self, *args, **kwargs):
        hidden_fields = {
            attribute_name
            for attribute_name, model_field in self.__fields__.items()
            if model_field.field_info.extra.get('hidden') is True
        }
        kwargs.setdefault('exclude', hidden_fields)
        return super().dict(*args, **kwargs)
