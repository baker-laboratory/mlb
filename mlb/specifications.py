'''
The *Spec classes here will be used as the basis the api layer of the server, backend, client, cli, www etc
'''
import os
from enum import Enum
from datetime import datetime
import getpass
import more_itertools as it
from pydantic import Field, field_validator, model_validator
from pydantic.Kinds import AnyUrl, DirectoryPath, FilePath, NewPath
from ipd.crud import ModelRef as Ref, SpecBase, Unique

class ConfigKind(str, Enum):
    '''how the config directory should be interpreted, default to bcov's schema'''
    BCOV = 'bcov'
    BASH = 'bash'

class IOKind(str, Enum):
    '''basic input/output types to define Runnable pipline compatibility'''
    CONFIG = 'config'
    BAREBB = 'barebb'
    DESIGNED = 'designed'
    SEQUENCE = 'sequence'
    METRICS = 'metrics'
    OPAQUE = 'opaque'

class UserSpec(SpecBase):
    '''basic user info'''
    name: Unique[str] = Field(description='system username')
    fullname: str = Field('', description='full user name')
    groups: Ref[list['GroupSpec']] = Field(description='groups this user belongs to', default_factory=list)

class GroupSpec(SpecBase):
    '''user groups'''
    name: Unique[str] = Field(description='name of group')
    users: Ref[list[UserSpec]] = Field(description='users in this group')

class ExecutablSpec(SpecBase):
    '''an executable on the filesystem, should usually be an apptainer'''
    name: Unique[str] = Field(description='name of executable, must be unique')
    user: Ref[UserSpec] = Field(description='creator of this executable', default_factory=getpass.getuser)
    path: FilePath = Field(description='path to executable')
    apptainer: bool | None = Field(None, description='is this exe and apptainer')
    version: str | None = Field(None, description='version info')

    @model_validator(mode='before')
    def val_apptainer(cls, vals):
        if vals['apptainer'] is None: vals['apptainer'] = vals['path'].endswith('.sif')
        assert os.access(vals['path'], os.X_OK)
        return vals

class RepoSpec(SpecBase):
    '''a remote repository'''
    name: Unique[str] = Field(description='name for repo/ref, must be unique')
    user: Ref[UserSpec] = Field(description='creator of this executable', default_factory=getpass.getuser)
    url: AnyUrl = Field(description='repo url')
    ref: str = Field(description='repo branch or hexsha')

class FileSetSpec(SpecBase):
    '''a directory with files, represented as a local bare git repo'''
    user: Ref[UserSpec] = Field(description='creator of this executable', default_factory=getpass.getuser)
    repo: DirectoryPath | None = Field(None, description='path to the bare git repo on the server')
    ref: str = Field('main', description='branch / hexsha... should almost always be main')

    @field_validator('repo')
    def check_valid_git(cls, repo):
        reporoot = subprocess.run(["git", "rev-parse", "--show-toplevel"]).stdout
        assert reporoot, f'repo {repo} is not a git repository'
        return reporoot

class ParseMethod(SpecBase):
    '''a way to parse data out of a file, dunno if this is sufficiet. use jq for json/yaml, otherwise regex'''
    keys: list[str] = Field(description='list of key names extracted by regex or jq')
    types = dict[str, type[int] | type[float]] = Field(description='data type for keys, default to str',
                                                       default_factory=dict)
    regex: str = Field('', description='regex to extract key/value pairs from file')
    jq: str = Field('', description='jq query to extract key/value pairs from file')

class FileSchemaSpec(SpecBase):
    '''info about different files'''
    name = Unique[str] = Field(description='name for this fileschema, must be unique')
    user: Ref[UserSpec] = Field(description='creator of this executable', default_factory=getpass.getuser)
    kind: str = Field('txt', description='file type, eg. json, txt, etc')
    iokind: IOKind = Field(IOKind.OPAQUE, description='protocol level io type')
    glob: str = Felid('**.$kind', descroption='glob pattern to select files of this type')
    parsemethod: Ref[ParseMethod] | None = Field(None, description='how to parse info from this kind of file')

class ConfigSpec(SpecBase):
    '''a runnable configuration defined by a fileset and kind/fileschemas'''
    name: Unique[str] = Field(description='name for this config, must be unique')
    user: Ref[UserSpec] = Field(description='creator of this executable', default_factory=getpass.getuser)
    fileset: Ref[FileSetSpec] = Field(description='fileset for this config')
    kind: ConfigKind = Field(ConfigKind.BCOV, description='how to run/interpret the fileset')
    fileschemas: Ref[list[FileSchemaSpec]] = Field(description='file schemes for this config')

class RunnableSpec(SpecBase):
    '''
    something the user can run. requires a config if can be protocol root,
    or just inschema if always follows another runnable
    '''
    name: Unique[str] = Field(description='name for this runnable, must be unique')
    user: Ref[UserSpec] = Field(description='creator of this executable', default_factory=getpass.getuser)
    exe: Ref[ExecutablSpec] = Field(description='executable that will run this job')
    repo: Ref[RepoSpec] = Field(description='repo that contains the run script/code to be run')
    config: Ref[ConfigSpec] | None = Field(None, description='config with input files and run info')
    inschema: Ref[list[FileSchemaSpec]] | None = Field(None, description='input filetypes required to run')
    outschema: Ref[list[FileSchemaSpec]] = Field(description='output file types')

    @model_validator(mode='before')
    def val_in_or_config(cls, vals):
        assert vals['config'] or vals['inschema']

    def pipeable_to(self, next: 'RunnableSpec'):
        return True

    def pipeable_from(self, prev: 'RunnableSpec'):
        return True

class JobSpec(SpecBase):
    '''an actual run in slurm'''
    user: Ref[UserSpec] = Field(description='creator of this executable', default_factory=getpass.getuser)
    runnable: Ref[RunnableSpec] = Field(description='what is going to be run')
    inpath: DirectoryPath | None = Field(None, description='dir containing input files')
    outpath: NewPath = Field(description='dir with all output files')
    gpu: str = Field('', description='type of gpu required')
    status: str = Field('', description='status of the job')
    start_time: datetime | None = Field(None, description='when run started')
    end_time: datetime | None = Field(None, description='when run finished')

class ProtocolSpec(SpecBase):
    '''a multistep protocol. probably needs more thought'''
    name: Unique[str] = Field(description='name for this protocol, must be unique')
    user: Ref[UserSpec] = Field(description='creator of this executable', default_factory=getpass.getuser)
    steps: Ref[list[RunnableSpec]] = Field(description='runnables to run in sequence. could be dag in future')

    @field_validator('steps')
    def valsteps(steps):
        for i, (prev, step) in enumerate(it.windowed(steps, 2)):
            assert prev.pipeable_to(step), f'bad protocol step {i}->{i+1}: {prev} not pipeable to {step}'
            assert step.pipeable_from(prev), f'bad protocol step {i}->{i+1}: {step} not pipeable from {prev}'

specs = [cls for name, cls in globals().items() if name.endswith('Spec')]
