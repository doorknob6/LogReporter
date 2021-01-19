import os
import json
from app.configs import config_mapping


class Config():

    def __init__(self, file_path):
        self.file_path = self.check_file_path(file_path)
        config = self.load_json(file_path)
        assert config['name'] in config_mapping, f'Unknown config type supplied: {config["name"]}'
        self.name = config['name']
        if isinstance(config['content'], list):
            self.content = [config_mapping[self.name](**k) for k in config['content']]
        else:
            self.content = config_mapping[self.name](**config['content'])

    def check_file_path(self, file_path):
        assert os.path.isfile(file_path), f'Config file path {file_path} is not a valid file path'
        assert '.json' == os.path.splitext(file_path)[-1].lower(), f'Config file path {file_path} is not a json file'
        return file_path

    def load_json(self, file_path):
        file_path = self.check_file_path(file_path)
        with open(file_path) as f:
            return json.load(f)

    def dump_json(self):
        self.file_path = self.check_file_path(self.file_path)
        dump_obj = {'name' : self.name}
        if isinstance(self.content, list):
            dump_obj.update({'content' : [k.__dict__ for k in self.content]})
        else:
            dump_obj.update({'content' : self.content.__dict__})
        with open(self.file_path, 'w') as f:
            return json.dump(dump_obj, f)
