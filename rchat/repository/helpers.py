from pydantic import BaseModel


class SQLBuild(BaseModel):
    field_names: str
    placeholders: str
    values: list


def build_model(model: BaseModel, exclude_none: bool = False) -> SQLBuild:
    """
    Создаёт модель с данными для заполнения БД.
    """
    model_dump = model.model_dump(exclude_none=exclude_none)

    field_names = []
    placeholders = []
    values = []
    for i, field_name, field_value in enumerate(model_dump.items()):
        field_names.append(field_name)
        placeholders.append(f"${i}")
        values.append(field_value)

    return SQLBuild(
        field_names=", ".join(field_names),
        placeholders=", ".join(placeholders),
        values=values,
    )
