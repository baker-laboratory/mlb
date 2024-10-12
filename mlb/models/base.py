from datetime import datetime
import os
import uuid
import pydantic as pd

STRUCTURE_FILE_SUFFIX = tuple('.pdb .pdb.gz .cif .bcif'.split())
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

class SpecBase(pydantic.BaseModel):
    name: str
    desc: str
    uuid: uuid.UUID = pd.Field(default_factory=uuid.uuid4)
    datecreated: datetime = pydantic.Field(default_factory=datetime.now)
    attrs: dict[str, pd.types.JsonValue] = {}
    ghost: bool = False
    _errors: list[str] = ''

    @pydantic.validator('attrs')
    def valattrs(cls, attrs):
        if isinstance(attrs, dict): return attrs
        try:
            attrs = ipd.dev.safe_eval(attrs)
        except (NameError, SyntaxError):
            if isinstance(attrs, str):
                if not attrs.strip(): return {}
                attrs = {
                    x.split('=').split(':')[0].strip(): x.split('=').split(':')[1].strip()
                    for x in attrs.strip().split(',')
                }
        return attrs

    def errors(self):
        return self._errors

    def __getitem__(self, k):
        return getattr(self, k)

    def spec(self):
        return self

class StrictFields:
    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)
        init_cls = cls.__init__.__qualname__.split('.')[-2]
        # if cls has explicit __init__, don't everride
        if init_cls == cls.__name__: return

        def new_init(self, pppclient=None, id=None, **data):
            for name in data:
                if name not in cls.__fields__:
                    raise TypeError(f"{cls} Invalid field name: {name}")
            data |= dict(pppclient=pppclient, id=id)
            super(cls, self).__init__(**data)

        cls.__init__ = new_init
