from pathlib import Path

# import pydantic
from hypothesis import given
from hypothesis import strategies as st
from rich import print

import ipd
import mlb

for Spec in mlb.specs:

    # print(Spec)
    strat = mlb.tests.mlbstrats(Spec)

    # sys.ps1 = 'foo'
    # print(strat.example())
    # del sys.ps1

    def make_test_func(_Spec=Spec, _strat=strat):
        @given(data=_strat)
        def test_create(data):
            spec = _Spec(**data)

        return test_create

    create = make_test_func()
    globals()[f'test_{Spec.__name__}_create'] = create

def main():
    for k, v in globals().items():
        if k.startswith('test_') and callable(v):
            v()
            print(k, 'pass')
    print('PASS')

if __name__ == '__main__':
    main()

# from typing import Annotated
# from hypothesis import given, strategies as st
# from pydantic import pydantic.BaseModel, Field, StringConstraints
# from hypothesis_jsonschema import from_schema
# class MyModel(pydantic.BaseModel):
#     # foo: Annotated[str, StringConstraints(max_length=7, pattern=r"^[abc]+$")] = Field(
#     # json_schema_extra={"format": "foo"})
#     foo: str = Field(pattern=r'^[abc]+$', max_length=7)
#
# schema = MyModel.model_json_schema()
#
# # or hack without `json_schema_extra` defined
# # schema["properties"]["foo"]["format"] = "foo"
#
# # MyModel(foo='abcabcabc')
#
# # @given(from_schema(schema, custom_formats={"foo": st.text(
# # alphabet=st.sampled_from('abc'),
# # max_size=7,
# # )}))
# @pytest.mark.skip
# @given(from_schema(schema))
# def test_foo_pass(data):
#     print(data)
#     MyModel(**data)
#
# schema = mlb.specs[0].model_json_schema()
# print(schema)
#
# @pytest.mark.skip
# @given(from_schema(schema))
# def test_user(data):
#     mlb.specs[0](**data)
