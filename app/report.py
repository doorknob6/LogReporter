

class Report():

    def __init__(self, report, api, fig_dir=None,
                 paper_bgcolor='#0E0E0E', plot_bgcolor='#141414', plot_palette='Plotly',
                 plot_axiscolor='#555555', plot_textcolor='#FFFFFF'):
        for key, item in report.items():
            self.__setattr__(key, item)
        self.api = api
        self.fig_dir = fig_dir
        self.fights = self.api.get_report_fights(self.id)

        self.paper_bgcolor = paper_bgcolor
        self.plot_bgcolor = plot_bgcolor
        self.plot_palette = plot_palette
        self.plot_axiscolor = plot_axiscolor
        self.plot_textcolor = plot_textcolor

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

    def get_input(self, input_variable, standard_val, unit=''):
        while True:
            i = input(f"Input {input_variable} [Enter to Accept]: {standard_val:>5}{unit} : ")
            if i:
                try:
                    i = int(i.strip(unit))
                except ValueError:
                    try:
                        i = float(i.strip(unit))
                        i = int(i)
                    except ValueError:
                        i = i.strip(unit)
                return i
            else:
                return standard_val

    def get_fight_name(self, event):
        if 'fight' in event:
            if self.fight_names:
                return self.fight_names[event['fight']]
        else:
            if self.fights:
                for fight in self.fights['fights']:
                    if fight['start_time'] <= event['timestamp'] <= fight['end_time']:
                        return fight['name']
        return None