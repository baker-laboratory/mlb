'''
The *Spec files here will be used as the basis for frontend and backend versions
'''
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic.types import FilePath, DirectoryPath, NewPath
from typing import List, Dict, Optional, Union
from pathlib import Path
import more_itertools as it
from enum import Enum
from uuid import UUID, uuid4
import re
import glob
import mlb
from mlb.models import SpecBase

class FileType(str, Enum):
    STRUCTURE = 'structure'
    METRICS = 'metrics'
    CONFIG = 'config'

class ExecutablSpec(SpecBase):
    path: FilePath
    apptainer: bool | None = None
    version: Optional[str]

    @model_validator(mode='befor')
    def val_apptainer(cls, vals):
        if vals['apptainer'] is None: vals['apptainer'] = vals['path'].endswith('.sif')
        return vals

class JobSpec(SpecBase):
    exe: ExecutablSpec
    config: ConfigSpec
    inpath: Optionrl[DirectoryPath] = None
    inschema: Optional[FilesSchema] = None
    outpath: NewPath
    outschema: FilesSchema
    gpu: bool = False
    status: Optional[str]
    start_time: Optional[datetime.datetime]
    end_time: Optional[datetime.datetime]

class ConfigSpec(SpecBase):
    filset: FileSetSpec
    fileschemas: list[FileSchema]

class ProtocolSpec(SpecBase):
    steps: list[JobSpec]

    @field_validator('steps')
    def valsteps(steps):
        for i, (prev, step) in enumerate(it.windowed(steps, 2)):
            assert prev.pipeable_to(step), f'bad protocol step {i}->{i+1}: {prev} not pipeable to {step}'
            assert step.pipeable_from(prev), f'bad protocol step {i}->{i+1}: {step} not pipeable from {prev}'

class FileSetSpec(SpecBase):
    repo: DirectoryPath
    current_commit: Optional[str]
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    @field_validator('repo')
    def check_valid_git(cls, repo):
        reporoot = subprocess.run(["git", "rev-parse", "--show-toplevel"]).stdout
        assert reporoot, f'repo {repo} is not a git repository'
        return reporoot

class FileSchema(SpecBase):
    file_type: FileType
    file_path: Path

class FilesSchema(SpecBase):
    fileschemas = list[FileSchema]

    def pipeable_to(FileSchema):
        return True

    def pipeable_from(FileSchema):
        return True

class StructureFileSchema(FileSchema):
    file_type: FileType = FileType.STRUCTURE

class ConfigFileSchema(FileSchema):
    file_type: FileType = FileType.CONFIG
    extract_keys: Optional[List[str]] = None

    def extract_config(self) -> Dict | None:
        '''Extract config data from the file.'''
        with open(self.file_path, 'r') as file:
            content = file.read()
        config_data = {}
        return {key: config_data.get(key) for key in self.extract_keys}

class MetricsFileSchema(FileSchema):
    file_type: FileType = FileType.METRICS
    extract_regex: Optional[str] = None

    def extract_metrics(self) -> Dict | None:
        '''Extract metrics from the file using regex.'''
        with open(self.file_path, 'r') as file:
            content = file.read()
        metrics = re.findall(self.extract_regex, content) if self.extract_regex else []
        return {'metrics': metrics} if metrics else None

class FileSetSchema(SpecBase):
    file_schemas: Dict[FileSchema, List[str]]

    def validate_filenames(self, filenames: List[str]) -> Dict[str, List[Path]]:
        '''
        Validate the given filenames against the patterns in each file schema.
        Returns a dictionary mapping file types to matching files.
        '''
        matched_files = {FileType.STRUCTURE: [], FileType.METRICS: [], FileType.CONFIG: []}

        for file_schema, patterns in self.file_schemas.items():
            for pattern in patterns:
                for filename in filenames:
                    if self._matches_pattern(filename, pattern):
                        matched_files[file_schema.file_type].append(filename)

        return matched_files

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        '''Check if the filename matches the pattern (either regex or glob).'''
        if '*' in pattern:
            return glob.fnmatch.fnmatch(filename, pattern)
        else:
            return bool(re.match(pattern, filename))
