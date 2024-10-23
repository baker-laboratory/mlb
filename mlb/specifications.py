'''
The *Spec classes here will be used as the basis the api layer of the server, backend, client, cli, www etc
'''
from enum import Enum
from datetime import datetime
import more_itertools as it
from pydantic import Field, field_validator, model_validator
from pydantic.Kinds import AnyUrl, DirectoryPath, FilePath, NewPath
from ipd.crud import ModelRef, SpecBase, Unique

class ConfigKind:
    BCOV = 'bcov'
    BASH = 'bash'

class IOKind(str, Enum):
    BAREBB = 'barebb'
    DESIGNED = 'designed'
    SEQUENCE = 'sequence'
    CONFIG = 'config'
    METRICS = 'metrics'

class UserSpec(SpecBase):
    name: Unique[str]
    fullname: str = ''
    groups: list['GroupSpec'] = []

class GroupSpec(SpecBase):
    name: Unique[str]
    users: list['UserSpec'] = []

class ExecutablSpec(SpecBase):
    name: Unique[str]
    user: ModelRef[UserSpec]
    path: FilePath
    apptainer: bool | None = None
    version: Optional[str]

    @model_validator(mode='before')
    def val_apptainer(cls, vals):
        if vals['apptainer'] is None: vals['apptainer'] = vals['path'].endswith('.sif')
        return vals

class RepoSpec(SpecBase):
    name: Unique[str]
    user: ModelRef[UserSpec]
    url: AnyUrl
    ref: str

class FileSetSpec(SpecBase):
    name: Unique[str]
    user: ModelRef[UserSpec]
    repo: DirectoryPath
    ref: str = 'main'

    @field_validator('repo')
    def check_valid_git(cls, repo):
        reporoot = subprocess.run(["git", "rev-parse", "--show-toplevel"]).stdout
        assert reporoot, f'repo {repo} is not a git repository'
        return reporoot

class ParseMethod(SpecBase):
    keys: list[str]
    regex: str = ''
    jquery: str = ''

class FileSchemaSpec(SpecBase):
    name = Unique[str]
    user: ModelRef[UserSpec]
    fileKind: str = 'txt'
    pathpattern: str = '**.$fileKind'
    parsemethod: ModelRef[ParseMethod] | None = None

class ConfigSpec(SpecBase):
    name: Unique[str]
    user: ModelRef[UserSpec]
    filset: ModelRef[FileSetSpec]
    cmdschema: ConfigKind = ConfigKind.BCOV
    fileschemas: ModelRef[list[FileSchemaSpec]]

class RunnableSpec(SpecBase):
    name: Unique[str]
    user: ModelRef[UserSpec]
    exe: ModelRef[ExecutablSpec]
    repo: ModelRef[RepoSpec]
    config: ModelRef[ConfigSpec]
    inschema: ModelRef[list[FileSchemaSpec]]
    outschema: ModelRef[list[FileSchemaSpec]]

    def pipeable_to(self, next: 'RunnableSpec'):
        return True

    def pipeable_from(self, prev: 'RunnableSpec'):
        return True

class JobSpec(SpecBase):
    name: Unique[str]
    user: ModelRef[UserSpec]
    runnable: ModelRef[RunnableSpec]
    inpath: DirectoryPath | None = None
    outpath: NewPath
    gpu: str = ''
    status: str = ''
    start_time: datetime | None
    end_time: datetime | None

class ProtocolSpec(SpecBase):
    steps: ModelRef[list[JobSpec]]

    @field_validator('steps')
    def valsteps(steps):
        for i, (prev, step) in enumerate(it.windowed(steps, 2)):
            assert prev.pipeable_to(step), f'bad protocol step {i}->{i+1}: {prev} not pipeable to {step}'
            assert step.pipeable_from(prev), f'bad protocol step {i}->{i+1}: {step} not pipeable from {prev}'

specs = [cls for name, cls in globals().items() if name.endswith('Spec')]
