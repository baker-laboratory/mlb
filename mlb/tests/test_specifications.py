from rich import print
from typing import Annotated

from hypothesis import given, strategies as st
from hypothesis_jsonschema import from_schema
from pydantic import BaseModel, Field, StringConstraints

class MyModel(BaseModel):
    # foo: Annotated[str, StringConstraints(max_length=7, pattern=r"^[abc]+$")] = Field(
    # json_schema_extra={"format": "foo"})
    foo: str = Field(pattern=r'^[abc]+$', max_length=7)

schema = MyModel.model_json_schema()

# or hack without `json_schema_extra` defined
# schema["properties"]["foo"]["format"] = "foo"

# MyModel(foo='abcabcabc')

# @given(from_schema(schema, custom_formats={"foo": st.text(
# alphabet=st.sampled_from('abc'),
# max_size=7,
# )}))
@given(from_schema(schema))
def test_foo_pass(data):
    print(data)
    MyModel(**data)

import mlb

schema = mlb.specs[0].model_json_schema()
print(schema)

@given(from_schema(schema))
def test_user(data):
    mlb.specs[0](**data)
