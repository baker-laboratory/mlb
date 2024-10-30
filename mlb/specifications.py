'''
The *Spec classes here will be used as the basis the api layer of the server, backend, client, cli, www etc
'''
import getpass
import os
import subprocess
from enum import Enum
import uuid

# from token import CIRCUMFLEX
import requests
from pydantic import AnyUrl, DirectoryPath, Field, FilePath, field_validator, model_validator

import ipd
from ipd.crud import ModelRef as Ref, SpecBase, Unique, client_method

def F(description: str, default=Field().default, **kw):
    assert isinstance(description, str)
    if callable(default):
        return Field(description=description, default_factory=default, **kw)
    else:
        return Field(description=description, default=default, **kw)

class ParseKind(str, Enum):
    '''different ways to parse a file, proccedural or'''
    PDB = 'pdb'
    CIF = 'cif'
    JQ = 'jq'
    REGEX = 'regex'

class VarKind(str, Enum):
    '''different types of parameters'''
    FILES = 'files'
    STR = 'str'
    INT = 'int'
    FLOAT = 'float'
    STR_LIST = 'str_list'
    INT_LIST = 'int_list'
    FLOAT_LIST = 'float_list'

class UserSpec(SpecBase):
    '''basic user info'''
    name: Unique[str] = F('system username', getpass.getuser)
    fullname: str = F('full user name', '')
    groups: list['GroupSpec'] = F('groups this user belongs to', list)

class GroupSpec(SpecBase):
    '''user groups'''
    name: Unique[str] = F('name of group')
    users: list[UserSpec] = F('users in this group', list)

class ExeSpec(SpecBase):
    '''an executable on the filesystem, should usually be an apptainer'''
    name: Unique[str] = F('name of executable, must be unique')
    user: Ref[UserSpec] = F('creator of this executable', getpass.getuser)
    path: FilePath = F('path to executable')
    apptainer: bool | None = F('is this exe and apptainer', None)
    version: str | None = F('version info', None)

    @model_validator(mode='before')
    def validate(cls, vals):
        # if isinstance(vals, uuid.UUID): return dict(id=vals)
        # if isinstance(vals, str):
        # if ipd.dev.touuid(vals): return dict(id=vals)
        # elif ipd.dev.toname(vals): return dict(name=vals)
        # else: assert 0, f'cant make ExeSpec from string "{vals}"'
        if '__test__' not in vals:
            if ipd.dev.keyexists(vals, 'apptainer'): vals['apptainer'] = str(vals['path']).endswith('.sif')
            assert os.access(vals['path'], os.X_OK), f'path {vals["path"]} is not executable'
        return vals

class RepoSpec(SpecBase):
    '''a remote repository from which to clone Method code'''
    name: Unique[str] = F('name for repo/ref, must be unique')
    user: Ref[UserSpec] = F('creator of this executable', getpass.getuser)
    url: AnyUrl = F('repo url')
    ref: str = F('repo branch or hexsha')

    @model_validator(mode='before')
    def valurl(cls, vals):
        url, ref = vals['url'], vals['ref']
        assert str(url).endswith('.git'), f'url {url} is not a git repo'
        if '__test__' not in vals:
            assert requests.get(str(url)).ok, f'url {url} is not reachable'
        assert ipd.dev.ishex(ref) or ref.isidentifier(), f'repo ref {ref} is not valid'
        return vals

class ConfigFilesSpec(SpecBase):
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
        assert 0

class ParseMethodSpec(SpecBase):
    '''a way to parse data out of a file. use jq for json/yaml, otherwise regex'''
    name: str = F('name of this way of parsing a file')
    user: Ref[UserSpec] = F('creator of this ParseMethod', getpass.getuser)
    kind: ParseKind = F('basic way to parse a file', ParseKind.REGEX)
    glob: str = F('glob pattern to select files of this type', '**.$kind')
    queries: dict[str, list[str]] = F('mapping from regex/qeurys to list of keynames extracted', dict)

class FileSchemaSpec(SpecBase):
    '''spec for contents of a file/directory'''
    name: Unique[str] = F('name for this fileschema, must be unique')
    user: Ref[UserSpec] = F('creator of this FileSchema', getpass.getuser)
    parsemethod: list[ParseMethodSpec] = F('how to parse info from this kind of file/directory', None)

class VarSpec(SpecBase):
    '''info about a variable provided by a Config/Method or input to a Method'''
    name: Unique[str] = F('name for this parameter, must be unique')
    kind: VarKind = F('type of this parameter', VarKind.FILES)
    default: str | None = F('default value for this parameter', None)
    files: Ref[FileSchemaSpec] = F('optional fileschema for this parameter', None)

class ParamsSpec(SpecBase):
    '''spec for the inputs to a Method'''
    name: Unique[str] = F('name for this result, must be unique')
    user: Ref[UserSpec] = F('creator of this Param', getpass.getuser)
    required: list[str] = F('required input vars', list)
    invars: list[VarSpec] = F('vars specification for all possible inputs', list)

class ResultSpec(SpecBase):
    '''spec for the output of a Method or contents of a Config'''
    name: Unique[str] = F('name for this result, must be unique')
    user: Ref[UserSpec] = F('creator of this Result', getpass.getuser)
    guaranteed: list[str] = F('guaranteed output vars', list)
    outvars: list[VarSpec] = F('vars specification for all possible outputs', list)

class ConfigSpec(SpecBase):
    '''a configuration fileset providing outvars'''
    name: Unique[str] = F('name for this config, must be unique')
    user: Ref[UserSpec] = F('creator of this Config', getpass.getuser)
    fileset: Ref[ConfigFilesSpec] = F('fileset for this config')
    outvars: Ref[ResultSpec] = F('output labels/types')

class MethodSpec(SpecBase):
    '''
    a basic comuptational unit. requires a config if can be protocol root,
    or just inschema if always follows another runnable. in and out schemas
    have names corresponding to required inputs / provided outputs
    '''
    name: Unique[str] = F('name for this runnable, must be unique')
    user: Ref[UserSpec] = F('creator of this Method', getpass.getuser)
    exe: Ref[ExeSpec] = F('executable that will run this Task')
    repo: Ref[RepoSpec] = F('repo that contains the run script/code to be run', None)
    config: Ref[ConfigSpec] = F('config with input files and run info', None)
    params: Ref[ParamsSpec] = F('input labels/types', None)
    result: Ref[ResultSpec] = F('output labels/types')
    gpus: str = F('does running this method require a gpu', '')

    @model_validator(mode='before')
    def val_in_or_config(cls, vals):
        keys = ipd.dev.keyexists(vals, 'configid config paramsid params'.split())
        assert any(keys), 'Method must have config or params'
        return vals

class ProtocolSpec(SpecBase):
    '''a multistep protocol. probably needs more thought'''
    name: Unique[str] = F('name for this protocol, must be unique')
    user: Ref[UserSpec] = F('creator of this Protocol', getpass.getuser)
    config: Ref[ConfigSpec] = F('config with input files and run info', None)
    params: Ref[ParamsSpec] = F('input labels/types', None)
    result: Ref[ResultSpec] = F('output labels/types')
    methods: list[MethodSpec] = F('runnables to run in sequence. could be dag in future')

    @model_validator(mode='before')
    def val_methods(cls, vals):
        return vals

# handling this via airflow now
# class TaskSpec(SpecBase):
#     '''an actual run in slurm'''
#     user: Ref[UserSpec] = F('creator of this executable', getpass.getuser)
#     runnable: Ref[MethodSpec] = F('what is going to be run')
#     inpath: DirectoryPath = F('dir containing input files', None)
#     outpath: NewPath = F('dir with all output files')
#     gpu: str = F('type of gpu required', '')
#     status: str = F('status of the Task', '')
#     start_time: datetime = F('when run started', None)
#     end_time: datetime = F('when run finished', None)

specs = [cls for name, cls in globals().items() if name.endswith('Spec')]
