import os
from WCLApi import WCLApi
from app.config import Config
from app.reportpicker import Reportpicker
from app.report import Report
from app.healing.healing_saves import HealingSaves

class Main():

    def __init__(self, config_dir='stored_configs', figures_dir='stored_figures'):
        self.app_dir = os.path.dirname(os.path.realpath(__file__))
        self.config_dir = os.path.join(self.app_dir, config_dir)
        self.figures_dir = os.path.join(self.app_dir, figures_dir)
        self.read_configs(self.config_dir)
        self.query_dir = q_d if os.path.isdir(q_d:= os.path.join(self.app_dir, self.wcl_config.content.query_dir)) else None
        self.api = WCLApi(self.wcl_config.content.api_key, query_dir=self.query_dir)
        self.report = Reportpicker(self.wcl_config, api=self.api).pick_loop()
        #self.report = Report(self.report, self.api)
        self.healing_saves = HealingSaves(self.report, self.api, stored_figures_path=self.figures_dir)

    def read_configs(self, config_dir):
        assert os.path.isdir(config_dir), f'The given config folder path is not a directory: {config_dir}'
        self.config_paths = [os.path.join(config_dir, c) for c in os.listdir(config_dir)]
        for c in self.config_paths:
            config = Config(c)
            self.__setattr__(config.name, config)