import plotly.graph_objects as go
from plotly.express import colors
from itertools import cycle


class Report():

    def __init__(self, report, api, fig_dir=None,
                 paper_bgcolor='#0E0E0E', plot_bgcolor='#141414', plot_palette='Plotly',
                 plot_axiscolor='#555555', plot_textcolor='#ffffff', plot_time_barwidth_divisor=1200,
                 plot_time_end_buffer=0):

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
        self.plot_time_barwidth_divisor = plot_time_barwidth_divisor
        self.plot_time_end_buffer = plot_time_end_buffer

    def get_fight_names(self, fights):
        fight_names = {}
        for fight in fights['fights']:
            fight_names.update({fight['id'] : fight['name']})
        return fight_names

    def get_friendly_names(self, fights):
        friendlies = fights['friendlies'] + fights['friendlyPets']
        friendly_names = {}

        for f in friendlies:
            friendly_names.update({f['id'] : f['name']})
        return friendly_names

    def get_enemy_names(self, fights):
        enemies = fights['enemies'] + fights['enemyPets']
        enemy_names = {}

        for e in enemies:
            enemy_names.update({e['id'] : e['name']})
        return enemy_names

    def get_target_id(self, event):
        if 'targetID' in event:
            return event['targetID']
        if 'target' in event:
            if 'id' in event['target']:
                return event['target']['id']

    def get_input(self, input_variable, standard_val, unit=''):
        while True:
            i = input(f'Input {input_variable} [Enter to Accept]: {standard_val:>5}{unit} : ')
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

    def spell_ids(self, healing_spells):
        spells = {}
        for spell in healing_spells:
            spells.update({spell.spell_id : spell})
        return spells

    def find_time_index(self, base_timestamp, event_list):
        n = 0
        while self.is_undershot(base_timestamp, event_list[n]['timestamp']):
            n = n_1 if (n_1:=n+1000) < len(event_list) else len(event_list) - 1
            if n == len(event_list) - 1:
                if self.is_overshot(event_list[n]['timestamp'], base_timestamp, 0):
                    return n
        while not self.is_undershot(base_timestamp, event_list[n]['timestamp']):
            n = n_1 if (n_1:=n-100) > 0 else 0
        while self.is_undershot(base_timestamp, event_list[n]['timestamp']):
            n = n_1 if (n_1:=n+10) < len(event_list) else len(event_list) - 1
        while not self.is_undershot(base_timestamp, event_list[n]['timestamp']):
            n = n_1 if (n_1:=n-10) > 0 else 0
        return n - 1

    def is_undershot(self, base_timestamp, check_timestamp):
        if check_timestamp <= base_timestamp:
            return True
        return False

    def is_overshot(self, base_timestamp, check_timestamp, timeout):
        if check_timestamp > base_timestamp + timeout:
            return True
        return False

    def sort_dict(self, sort_dict, by_value, reverse=True):
        if isinstance(list(sort_dict.values())[0][by_value], (int, float)):
            return {h : v for h, v in sorted(sort_dict.items(), key=lambda item: item[1][by_value], reverse=reverse)}
        elif isinstance(list(sort_dict.values())[0][by_value], list):
            return {h : v for h, v in sorted(sort_dict.items(), key=lambda item: len(item[1][by_value]), reverse=reverse)}
        else:
            return {h : v for h, v in sorted(sort_dict.items(), key=lambda item: item[1][by_value], reverse=reverse)}

    def make_time_plot(self, fig, data_dict, events_key, event_val_key, row, col, palette=None, t_stamp_event_key=None, marker_data_dict=None, showlegend=True):

        if palette is not None:
            palette = cycle(getattr(colors.qualitative, self.plot_palette))

        for item in data_dict:
            if t_stamp_event_key:
                timestamps = [d[t_stamp_event_key]['timeStamp'] for d in data_dict[item][events_key]]
            else:
                timestamps = [d['timeStamp'] for d in data_dict[item][events_key]]
            event_vals = [d[event_val_key] for d in data_dict[item][events_key]]
            event_strings = [d['eventString'] for d in data_dict[item][events_key]]

            if marker_data_dict is not None:
                if item in marker_data_dict:
                    data_dict[item].update({'markerColor' : marker_data_dict[item]['markerColor']})
                else:
                    if palette is not None:
                        data_dict[item].update({'markerColor' : next(palette)})
            else:
                if palette is not None:
                    data_dict[item].update({'markerColor' : next(palette)})

            try:
                fig.add_trace(go.Bar(name=item,
                                        x=timestamps,
                                        y=event_vals,
                                        hovertext=event_strings,
                                        width=(self.end - self.start)/self.plot_time_barwidth_divisor,
                                        legendgroup=item,
                                        showlegend=showlegend,
                                        marker_color=data_dict[item]['markerColor'],
                                        marker=dict(line=dict(width=0))),
                                        row=row, col=col)
            except:
                print()

        fig.update_xaxes(range=[self.start, self.end], mirror=True,
                            zeroline=False,
                            linecolor=self.plot_axiscolor, showline=True, linewidth=1,
                            row=row, col=col)
        fig.update_yaxes(mirror=True,
                            zeroline=False,
                            showgrid=True, gridcolor=self.plot_axiscolor, gridwidth=1,
                            linecolor=self.plot_axiscolor, showline=True, linewidth=1,
                            row=row, col=col)

    def make_horizontal_plot(self, fig, data_dict, value_key, hovertext_key, row, col):
        for key in reversed(data_dict):

            value = 0
            if isinstance(data_dict[key][value_key], (int, float)):
                value = data_dict[key][value_key]
            elif isinstance(data_dict[key][value_key], list):
                value = len(data_dict[key][value_key])

            if value > 0:
                fig.add_trace(go.Bar(name=key,
                                        y=[key],
                                        x=[value],
                                        hovertext=[data_dict[key][hovertext_key]],
                                        orientation='h',
                                        legendgroup=key,
                                        showlegend=False,
                                        marker_color=data_dict[key]['markerColor'],
                                        marker=dict(line=dict(width=0))),
                                        row=row, col=col)

        fig.update_yaxes(ticksuffix='  ',
                            mirror=True,
                            zeroline=False,
                            linecolor=self.plot_axiscolor, showline=True, linewidth=1,
                            row=row, col=col)

        fig.update_xaxes(mirror=True,
                            zeroline=False,
                            showgrid=True, gridcolor=self.plot_axiscolor, gridwidth=1,
                            linecolor=self.plot_axiscolor, showline=True, linewidth=1,
                            row=row, col=col)