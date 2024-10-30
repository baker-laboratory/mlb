import datetime
import os
import sys
import types
import uuid
from pathlib import Path
from typing import Any, Optional, Type, Union, _AnnotatedAlias, get_args

import pydantic
import pydantic_core
from hypothesis import given
from hypothesis import strategies as st
from rich import print

import mlb
from mlb.specifications import ConfigFilesSpec

class PydanticStrats:
    def __init__(self, overrides=None):
        self.overrides = overrides or {}
        # self.urls_strat = st.text().filter(str.isidentifier).map(lambda s: f'https://example.com/{s}.git').map(
        # pydantic.AnyUrl)
        self.files_strat = st.sampled_from(['pyproject.toml', '.gitignore']).map(Path)
        self.urlstrat = st.just('https://github.com/baker-laboratory/ipd.git')

        self.type_mapping = {
            str: st.text(),
            int: st.integers(),
            float: st.floats(),
            bool: st.booleans(),
            list[int]: st.lists(st.integers()),
            list[str]: st.lists(st.text()),
            dict[str, int]: st.dictionaries(st.text(), st.integers()),
            dict[str, list[str]]: st.dictionaries(st.text(), st.lists(st.text())),
            uuid.UUID: st.uuids(),
            datetime.datetime: st.datetimes(),
            pydantic_core._pydantic_core.Url: self.urlstrat,
            Path: self.files_strat,
            mlb.ParseKind: st.sampled_from(mlb.ParseKind),
            mlb.VarKind: st.sampled_from(mlb.VarKind),
            # pydantic_core._pydantic_core.Url: provisional.urls,
            # pydantic_core._pydantic_core.Url: urls_strat,
            # Path: st.text().map(Path),
        }

    def __call__(self, Model: Type[pydantic.BaseModel]) -> st.SearchStrategy[dict[str, Any]]:
        strategy_dict = {'__test__': st.just(True)}
        for attr, field in Model.model_fields.items():
            field_type = field.annotation
            if (strategy := self.get_strategy(Model, attr, field_type)) is not None:
                strategy = self.postprocess_field_strategy(Model, attr, field, strategy)
                assert isinstance(strategy, st.SearchStrategy)
                if field.default is not pydantic_core.PydanticUndefined:
                    strategy = st.one_of(st.just(field.default), strategy)
                strategy_dict[attr] = strategy
        modelstrat = st.fixed_dictionaries(strategy_dict)
        modelstrat = self.postprocess_moodel_strategy(Model, modelstrat)
        assert isinstance(modelstrat, st.SearchStrategy)
        return modelstrat

    def pick_from_union_types(self, Ts):
        Ts = [T for T in Ts if T is not type(None)]
        if len(Ts) == 1: return Ts[0]
        if Ts == [uuid.UUID, str]: return uuid.UUID

    def get_strategy(self, Model, attr, T):
        if None is not (strat := self.overrides.get(f'*.{attr}')): return strat
        if None is not (strat := self.overrides.get(f'{Model.__name__}.{attr}')): return strat
        orig, args = getattr(T, '__origin__', None), get_args(T)
        if orig is Optional: T = args[0]
        if orig is Union: T = self.pick_from_union_types(args)
        if orig is list and issubclass(args[0], pydantic.BaseModel): return None
        if isinstance(T, types.UnionType): T = self.pick_from_union_types(T.__args__)
        if isinstance(T, _AnnotatedAlias): T = get_args(args[0])[0]
        if (strat := self.type_mapping.get(T, None)) is not None: return strat
        raise Valuerror(f'cant make hypothesis strat for {T} {type(T)} {orig} {args}')

    def postprocess_moodel_strategy(self, Model, strat):
        return strat

    def postprocess_field_strategy(self, Model, attr, field, strat):
        return strat

class MLBStrats(PydanticStrats):
    def __init__(self):
        super().__init__(
            overrides={
                '*.name': st.text().filter(str.isidentifier),
                '*.ref': st.integers().map(hex).map(lambda s: s[2:]),
                'ConfigFilesSpec.repo': st.sampled_from(['mlb', 'ide']).map(Path),
            })

    def postprocess_moodel_strategy(self, Model, strat):
        if Model.modelkind() == 'method':
            return strat.filter(lambda d: d['config'] or d['params'])
        return strat

mlbstrats = MLBStrats()

for Spec in mlb.specs:

    # print(Spec)
    strat = mlbstrats(Spec)

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
