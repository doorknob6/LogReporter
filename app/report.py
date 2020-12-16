

class Report():

    def __init__(self, report, api):
        for key, item in report.items():
            self.__setattr__(key, item)
        self.api = api
        self.fights = self.api.get_report_fights(self.id)

    def get_fight_names(self, fights):
        fight_names = {}
        for fight in fights['fights']:
            fight_names.update({fight['id'] : fight['name']})
        return fight_names

    def get_friendly_names(self, fights):
        friendlies = fights["friendlies"] + fights['friendlyPets']
        friendly_names = {}

        for f in friendlies:
            friendly_names.update({f["id"] : f["name"]})
        return friendly_names

    def get_target_id(self, event):
        if 'targetID' in event:
            return event['targetID']
        if 'target' in event:
            if 'id' in event['target']:
                return event['target']['id']