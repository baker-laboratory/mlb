"""The *Spec classes here will be used as the basis the api layer of the server, backend, client, cli, www etc"""
import getpass
import os
from enum import Enum

import httpx
import pydantic
from pydantic import AnyUrl, DirectoryPath, FilePath, field_validator, model_validator

import ipd
from ipd.crud import ModelRef as Ref
from ipd.crud import SpecBase, Unique, client_method

def Field(description: str, default=pydantic.Field().default, **kw):
    assert isinstance(description, str)
    if callable(default):
        return pydantic.Field(description=description, default_factory=default, **kw)
    else:
        return pydantic.Field(description=description, default=default, **kw)

class ParseKind(str, Enum):
    """different ways to parse a file, proccedural or"""
    PDB = 'pdb'
    CIF = 'cif'
    JQ = 'jq'
    REGEX = 'regex'

class VarKind(str, Enum):
    """different types of parameters"""
    FILES = 'files'
    STR = 'str'
    INT = 'int'
    FLOAT = 'float'
    STR_LIST = 'str_list'
    INT_LIST = 'int_list'
    FLOAT_LIST = 'float_list'

class UserSpec(SpecBase):
    """basic user info"""
    name: Unique[str] = Field('system username', getpass.getuser)
    fullname: str = Field('full user name', '')
    groups: list['GroupSpec'] = Field('groups this user belongs to', list)

class GroupSpec(SpecBase):
    """user groups"""
    name: Unique[str] = Field('name of group')
    users: list[UserSpec] = Field('users in this group', list)

class ExeSpec(SpecBase):
    """an executable on the filesystem, should usually be an apptainer"""
    name: Unique[str] = Field('name of executable, must be unique')
    user: Ref[UserSpec] = Field('creator of this executable', getpass.getuser)
    path: FilePath = Field('path to executable')
    apptainer: bool | None = Field('is this exe and apptainer', None)
    version: str | None = Field('version info', None)

    @model_validator(mode='before')
    def validate(cls, vals):
        # if isinstance(vals, uuid.UUID): return dict(id=vals)
        # if isinstance(vals, str):
        # if ipd.dev.touuid(vals): return dict(id=vals)
        # elif ipd.dev.toname(vals): return dict(name=vals)
        # else: assert 0, f'cant make ExeSpec from string "{vals}"'
        if '__test__' not in vals:
            if ipd.dev.key_exists_true(vals, 'apptainer'):
                vals['apptainer'] = str(vals['path']).endswith('.sif')
            assert os.access(vals['path'], os.X_OK), f'path {vals["path"]} is not executable'
        return vals

class RepoSpec(SpecBase):
    """a remote repository from which to clone Method code"""
    name: Unique[str] = Field('name for repo/ref, must be unique')
    user: Ref[UserSpec] = Field('creator of this executable', getpass.getuser)
    url: AnyUrl = Field('repo url')
    ref: str = Field('repo branch or hexsha')

    @model_validator(mode='before')
    def valurl(cls, vals):
        url, ref = vals['url'], vals['ref']
        assert str(url).endswith('.git'), f'url {url} is not a git repo'
        if '__test__' not in vals:
            assert httpx.get(str(url)).status_code == 200, f'url {url} is not reachable'
        assert ipd.dev.ishex(ref) or ref.isidentifier(), f'repo ref {ref} is not valid'
        return vals

class ConfigFilesSpec(SpecBase):
    """a directory with files, represented as a local bare git repo"""
    user: Ref[UserSpec] = Field('creator of this executable', getpass.getuser)
    repo: DirectoryPath = Field('path to the bare git repo on the server')
    ref: str = Field('branch / hexsha... should almost always be main', 'main')

    @field_validator('repo')
    def check_valid_git(cls, repo):
        reporoot = ipd.dev.run(f'cd {repo} && git rev-parse --show-toplevel')
        assert reporoot, f'repo {reporoot} is not a git repository'
        return reporoot

    @client_method
    def creat_fileset(self, foo):
        assert 0

class ParseMethodSpec(SpecBase):
    """a way to parse data out of a file. use jq for json/yaml, otherwise regex"""
    name: str = Field('name of this way of parsing a file')
    user: Ref[UserSpec] = Field('creator of this ParseMethod', getpass.getuser)
    kind: ParseKind = Field('basic way to parse a file', ParseKind.REGEX)
    glob: str = Field('glob pattern to select files of this type', '**.$kind')
    queries: dict[str, list[str]] = Field('mapping from regex/qeurys to list of keynames extracted', dict)

class FileSchemaSpec(SpecBase):
    """spec for contents of a file/directory"""
    name: Unique[str] = Field('name for this fileschema, must be unique')
    user: Ref[UserSpec] = Field('creator of this FileSchema', getpass.getuser)
    parsemethod: list[ParseMethodSpec] = Field('how to parse info from this kind of file/directory', None)

class VarSpec(SpecBase):
    """info about a variable provided by a Config/Method or input to a Method"""
    name: Unique[str] = Field('name for this parameter, must be unique')
    kind: VarKind = Field('type of this parameter', VarKind.FILES)
    default: str | None = Field('default value for this var', None)
    immutable: bool = Field('is this var immutable?', False)
    files: Ref[FileSchemaSpec] = Field('optional fileschema for this var', None)

class ParamSpec(SpecBase):
    """spec for the inputs to a Method"""
    name: Unique[str] = Field('name for this result, must be unique')
    user: Ref[UserSpec] = Field('creator of this Param', getpass.getuser)
    required: list[str] = Field('required input vars', list)
    invars: list[VarSpec] = Field('vars specification for all possible inputs', list)

class ResultSpec(SpecBase):
    """spec for the output of a Method or contents of a Config"""
    name: Unique[str] = Field('name for this result, must be unique')
    user: Ref[UserSpec] = Field('creator of this Result', getpass.getuser)
    guaranteed: list[str] = Field('guaranteed output vars', list)
    outvars: list[VarSpec] = Field('vars specification for all possible outputs', list)

class ConfigSpec(SpecBase):
    """a configuration fileset providing outvars"""
    name: Unique[str] = Field('name for this config, must be unique')
    user: Ref[UserSpec] = Field('creator of this Config', getpass.getuser)
    fileset: Ref[ConfigFilesSpec] = Field('fileset for this config')
    outvars: Ref[ResultSpec] = Field('output labels/types')

class MethodSpec(SpecBase):
    """a basic comuptational unit. requires a config if can be protoco,
    or just inschema if always follows another runnable. in and out schemas
    have names corresponding to required inputs / provided outputs
    """
    name: Unique[str] = Field('name for this runnable, must be unique')
    user: Ref[UserSpec] = Field('creator of this Method', getpass.getuser)
    exe: Ref[ExeSpec] = Field('executable that will run this Task')
    repo: Ref[RepoSpec] = Field('repo that contains the run script/code to be run', None)
    config: Ref[ConfigSpec] = Field('config with input files and run info', None)
    param: Ref[ParamSpec] = Field('input labels/types', None)
    result: Ref[ResultSpec] = Field('output labels/types')
    gpus: str = Field('does running this method require a gpu', '')

    @model_validator(mode='before')
    def val(cls, vals):
        keys = ipd.dev.key_exists_true(vals, 'configid config paramid param'.split())
        assert any(keys), 'Method must have config or param'
        return vals

class ProtocolSpec(SpecBase):
    """a multistep protocol. probably needs more thought"""
    name: Unique[str] = Field('name for this protocol, must be unique')
    user: Ref[UserSpec] = Field('creator of this Protocol', getpass.getuser)
    config: Ref[ConfigSpec] = Field('config with input files and run info', None)
    param: Ref[ParamSpec] = Field('input labels/types', None)
    result: Ref[ResultSpec] = Field('output labels/types')
    methods: list[MethodSpec] = Field('runnables to run in sequence. could be dag in future', list)

    @model_validator(mode='before')
    def val(cls, vals):
        keys = ipd.dev.key_exists_true(vals, 'configid config paramid param'.split())
        assert any(keys), 'Protocol must have config or param'
        return vals

# handling this via airflow now
# class TaskSpec(SpecBase):
#     """an actual run in slurm"""
#     user: Ref[UserSpec] = Field('creator of this executable', getpass.getuser)
#     runnable: Ref[MethodSpec] = Field('what is going to be run')
#     inpath: DirectoryPath = Field('dir containing input files', None)
#     outpath: NewPath = Field('dir with all output files')
#     gpu: str = Field('type of gpu required', '')
#     status: str = Field('status of the Task', '')
#     start_time: datetime = Field('when run started', None)
#     end_time: datetime = Field('when run finished', None)

specs = [cls for name, cls in globals().items() if name.endswith('Spec')]
