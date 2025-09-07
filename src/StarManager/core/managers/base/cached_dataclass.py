from dataclasses import dataclass, fields, asdict, is_dataclass
from typing import Type, TypeVar, Any

T = TypeVar("T", bound="BaseCachedModel")

@dataclass
class BaseCachedModel:
    dict = asdict

    @classmethod
    def from_model(cls: Type[T], model: Any) -> T:
        if not is_dataclass(cls):
            raise TypeError(f"{cls.__name__} must be a dataclass")
        field_names = {f.name for f in fields(cls)}
        init_kwargs = {}
        for name in field_names:
            value = getattr(model, name)
            if isinstance(value, list):
                value = list(value)
            init_kwargs[name] = value
        return cls(**init_kwargs)
