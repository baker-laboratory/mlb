'''
The *Spec classes here will be used as the basis the api layer of the server, backend, client, cli, www etc
'''
import getpass
import os
import subprocess
from datetime import datetime
from enum import Enum
from token import CIRCUMFLEX

import more_itertools as it
from pydantic import (AnyUrl, DirectoryPath, Field, FilePath, NewPath, field_validator, model_validator)

from ipd.crud import ModelRef as Ref, SpecBase, Unique, client_method, backend_method

def F(description: str, default=Field().default, **kw):
    assert isinstance(description, str)
    if callable(default):
        return Field(description=description, default_factory=default, **kw)
    else:
        return Field(description=description, default=default, **kw)

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

class ParseKind(str, Enum):
    '''different ways to parse a file, proccedural or'''
    PDB = 'pdb'
    CIF = 'cif'
    JQ = 'jq'
    REGEX = 'regex'

class UserSpec(SpecBase):
    '''basic user info'''
    name: Unique[str] = F('system username')
    fullname: str = F('full user name', '')
    groups: list['GroupSpec'] = F('groups this user belongs to', list)

class GroupSpec(SpecBase):
    '''user groups'''
    name: Unique[str] = F('name of group')
    users: list[UserSpec] = F('users in this group', list)

class ExecutableSpec(SpecBase):
    '''an executable on the filesystem, should usually be an apptainer'''
    name: Unique[str] = F('name of executable, must be unique')
    user: Ref[UserSpec] = F('creator of this executable', getpass.getuser)
    path: FilePath = F('path to executable')
    apptainer: bool | None = F('is this exe and apptainer', None)
    version: str | None = F('version info', None)

    @classmethod
    @model_validator(mode='before')
    def val_apptainer(cls, vals):
        print(vals)
        if vals['apptainer'] is None: vals['apptainer'] = vals['path'].endswith('.sif')
        assert os.access(vals['path'], os.X_OK)
        return vals

class RepoSpec(SpecBase):
    '''a remote repository'''
    name: Unique[str] = F('name for repo/ref, must be unique')
    user: Ref[UserSpec] = F('creator of this executable', getpass.getuser)
    url: AnyUrl = F('repo url')
    ref: str = F('repo branch or hexsha')

class FileSetSpec(SpecBase):
    '''a directory with files, represented as a local bare git repo'''
    user: Ref[UserSpec] = F('creator of this executable', getpass.getuser)
    repo: DirectoryPath | None = F('path to the bare git repo on the server', None)
    ref: str = F('branch / hexsha... should almost always be main', 'main')

    @field_validator('repo')
    def check_valid_git(cls, repo):
        reporoot = subprocess.run(["git", "rev-parse", "--show-toplevel"]).stdout
        assert reporoot, f'repo {repo} is not a git repository'
        return reporoot

    @client_method
    def creat_fileset(self, foo):
        print(foo)

class ParseMethodSpec(SpecBase):
    '''a way to parse data out of a file. use jq for json/yaml, otherwise regex'''
    kind: ParseKind = F('basic way to parse a file', ParseKind.REGEX)
    keys: list[str] = F('list of key names extracted by regex or jq')
    types: dict[str, int | float | str] = F('data type for keys, default to str', dict)
    query: str = F('regex to extract key/value pairs from file', '')

class FileSchemaSpec(SpecBase):
    '''info about different files'''
    name: Unique[str] = F('name for this fileschema, must be unique')
    user: Ref[UserSpec] = F('creator of this executable', getpass.getuser)
    kind: str = F('file type, eg. json, txt, etc')
    iokind: IOKind = F('protocol level io type', IOKind.OPAQUE)
    glob: str = F('glob pattern to select files of this type', '**.$kind')
    parsemethod: Ref[ParseMethodSpec] = F('how to parse info from this kind of file', None)

class ConfigSpec(SpecBase):
    '''a runnable configuration defined by a fileset and kind/fileschemas'''
    name: Unique[str] = F('name for this config, must be unique')
    user: Ref[UserSpec] = F('creator of this executable', getpass.getuser)
    fileset: Ref[FileSetSpec] = F('fileset for this config')
    kind: ConfigKind = F('how to run/interpret the fileset', ConfigKind.BCOV)
    fileschemas: list[FileSchemaSpec] = F('file schemes for this config')

class RunnableSpec(SpecBase):
    '''
    something the user can run. requires a config if can be protocol root,
    or just inschema if always follows another runnable
    '''
    name: Unique[str] = F('name for this runnable, must be unique')
    user: Ref[UserSpec] = F('creator of this executable', getpass.getuser)
    exe: Ref[ExecutableSpec] = F('executable that will run this job')
    repo: Ref[RepoSpec] = F('repo that contains the run script/code to be run')
    config: Ref[ConfigSpec] = F('config with input files and run info', None)
    inschema: Ref[list[FileSchemaSpec], 'in'] = F('input filetypes required to run')
    outschema: Ref[list[FileSchemaSpec], 'out'] = F('output file types')

    @model_validator(mode='before')
    def val_in_or_config(cls, vals):
        # assert vals['config'] or vals['inschema']
        return vals

    def pipeable_to(self, next: 'RunnableSpec'):
        return True

    def pipeable_from(self, prev: 'RunnableSpec'):
        return True

class JobSpec(SpecBase):
    '''an actual run in slurm'''
    user: Ref[UserSpec] = F('creator of this executable', getpass.getuser)
    runnable: Ref[RunnableSpec] = F('what is going to be run')
    inpath: DirectoryPath = F('dir containing input files', None)
    outpath: NewPath = F('dir with all output files')
    gpu: str = F('type of gpu required', '')
    status: str = F('status of the job', '')
    start_time: datetime = F('when run started', None)
    end_time: datetime = F('when run finished', None)

class ProtocolSpec(SpecBase):
    '''a multistep protocol. probably needs more thought'''
    name: Unique[str] = F('name for this protocol, must be unique')
    user: Ref[UserSpec] = F('creator of this executable', getpass.getuser)
    steps: list[RunnableSpec] = F('runnables to run in sequence. could be dag in future')

    @field_validator('steps')
    def valsteps(steps):
        for i, (prev, step) in enumerate(it.windowed(steps, 2)):
            assert prev.pipeable_to(step), f'bad protocol step {i}->{i+1}: {prev} not pipeable to {step}'
            assert step.pipeable_from(prev), f'bad protocol step {i}->{i+1}: {step} not pipeable from {prev}'

specs = [cls for name, cls in globals().items() if name.endswith('Spec')]
