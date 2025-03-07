import ipd
from mlb.frontend import MLBClient

class MLBTool(ipd.dev.cli.CliBase):
    def hello(self, whom: str):
        print(f'hello from {self.__class__.__name__} {whom}')

class APITool(MLBTool, ipd.crud.CrudCli, Client=MLBClient):
    def hello(self, whom: str):
        print(f'hello from {self.__class__.__name__} {whom}')
