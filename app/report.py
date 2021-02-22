import plotly.graph_objects as go
from plotly.express import colors
from itertools import cycle
from bs4 import BeautifulSoup
from datetime import datetime


class Report():

    def __init__(self, report, api, fig_dir=None, fights=None, tanks=None,
                 paper_bgcolor='#0E0E0E', plot_bgcolor='#141414', plot_palette='Plotly',
                 plot_axiscolor='#555555', plot_textcolor='#ffffff', plot_time_barwidth_divisor=1200,
                 plot_time_end_buffer=0):

        for key, item in report.items():
            self.__setattr__(key, item)
        self.api = api
        self.fig_dir = fig_dir
        self.fights = self.api.get_report_fights(self.id) if fights is None else fights
        self.tanks = {'fights' : []} if tanks is None else tanks

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

    def is_tank(self, event):

        tank = False

        if event['fight'] in self.tanks['fights']:
            if event['targetID'] in self.tanks:
                if event['fight'] in self.tanks[event['targetID']]:
                    tank = True
        else:
            # Additional check for Defensive Stance '71', Dire Bear Form '9634' or Holy Shield '20928'
            if 'buffs' in event:
                if any(b in event['buffs'].split('.') for b in ['71', '9634', '20928']):
                    tank = True
                    if event['targetID'] in self.tanks:
                        if event['fight'] not in self.tanks[event['targetID']]:
                            self.tanks[event['targetID']].append(event['fight'])

            if fight:=[f for f in self.fights['fights'] if f['id']==event['fight']]:
                fight = fight[0]

                fight_summary = self.api.get_report_tables(view='summary',
                                                            report_code=self.id,
                                                            start_time=fight['start_time'],
                                                            end_time=fight['end_time'])

                fight.update({'summary' : fight_summary})

                for player in fight_summary['composition']:
                    for spec in player['specs']:
                        if spec['role'] == 'tank':
                            if player['id'] in self.tanks:
                                if fight['id'] not in self.tanks[player['id']]:
                                    self.tanks[player['id']].append(fight['id'])
                            else:
                                self.tanks.update({player['id'] : [fight['id']]})
                            if player['id'] == event['targetID']:
                                tank = True

                self.tanks['fights'].append(fight['id'])

        return tank

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
        if check_timestamp >= base_timestamp + timeout:
            return True
        return False

    def sort_dict(self, sort_dict, by_value, reverse=True):
        if isinstance(list(sort_dict.values())[0][by_value], (int, float)):
            return {h : v for h, v in sorted(sort_dict.items(), key=lambda item: item[1][by_value], reverse=reverse)}
        elif isinstance(list(sort_dict.values())[0][by_value], list):
            return {h : v for h, v in sorted(sort_dict.items(), key=lambda item: len(item[1][by_value]), reverse=reverse)}
        else:
            return {h : v for h, v in sorted(sort_dict.items(), key=lambda item: item[1][by_value], reverse=reverse)}

    def make_time_plot(self, fig, data_dict, events_key, event_val_key, row, col, palette, t_stamp_event_key=None):

        palette = cycle(getattr(colors.qualitative, self.plot_palette))

        for item in data_dict:
            if t_stamp_event_key:
                timestamps = [d[t_stamp_event_key]['timeStamp'] for d in data_dict[item][events_key]]
            else:
                timestamps = [d['timeStamp'] for d in data_dict[item][events_key]]
            event_vals = [d[event_val_key] for d in data_dict[item][events_key]]
            event_strings = [d['eventString'] for d in data_dict[item][events_key]]

            marker_color = None
            marker = None
            showlegend=True

            for data in fig._data:
                if 'legendgroup' in data:
                    if item==data['legendgroup']:
                        marker_color=data['marker']['color']
                        marker=data['marker']
                        if data['x'] and data['y']:
                            showlegend=False
                            break

            if marker_color is None:
                marker_color = next(palette)
            if marker is None:
                marker = dict(line=dict(width=0))

            fig.add_trace(go.Bar(name=item,
                                    x=timestamps,
                                    y=event_vals,
                                    hovertext=event_strings,
                                    width=(self.end - self.start)/self.plot_time_barwidth_divisor,
                                    legendgroup=item,
                                    showlegend=showlegend,
                                    marker_color=marker_color,
                                    marker=marker),
                                    row=row, col=col)

        fig.update_xaxes(range=[datetime.fromtimestamp((self.start)/1000).replace(microsecond=0),
                                datetime.fromtimestamp((self.end)/1000).replace(microsecond=0)],
                            mirror=True,
                            zeroline=False,
                            linecolor=self.plot_axiscolor, showline=True, linewidth=1,
                            row=row, col=col)
        fig.update_yaxes(mirror=True,
                            zeroline=False,
                            showgrid=True, gridcolor=self.plot_axiscolor, gridwidth=1,
                            linecolor=self.plot_axiscolor, showline=True, linewidth=1,
                            row=row, col=col)

    def make_horizontal_plot(self, fig, data_dict, value_key, hovertext_key, row, col, palette):

        palette = cycle(getattr(colors.qualitative, self.plot_palette))

        for key in reversed(data_dict):

            value = 0
            if isinstance(data_dict[key][value_key], (int, float)):
                value = data_dict[key][value_key]
            elif isinstance(data_dict[key][value_key], list):
                value = len(data_dict[key][value_key])

            if value > 0:

                marker_color = None
                marker = None
                showlegend=True

                for data in fig._data:
                    if 'legendgroup' in data:
                        if key==data['legendgroup']:
                            marker_color=data['marker']['color']
                            marker=data['marker']
                            if data['x'] and data['y']:
                                showlegend=False
                                break

                if marker_color is None:
                    marker_color = next(palette)
                if marker is None:
                    marker = dict(line=dict(width=0))

                fig.add_trace(go.Bar(name=key,
                                        y=[key],
                                        x=[value],
                                        hovertext=[data_dict[key][hovertext_key]],
                                        orientation='h',
                                        legendgroup=key,
                                        showlegend=showlegend,
                                        marker_color=marker_color,
                                        marker=marker),
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

    def insert_tab_button(self, report):
        assert all(k for k in [self.tab_title, self.tab_id]), "Please provide arguments for the report tab_title and tab_id."
        tab_button = report.new_tag('button', id=f'{self.tab_id}-button')
        tab_button['class'] = 'tablinks'
        tab_button['onclick'] = f"openReport(event, '{self.tab_id}')"
        tab_button.string = self.tab_title
        tab_bar = report.find('div', 'tabbar')
        tab_bar.append(tab_button)

    def insert_tab_content(self, report):
        assert all(k for k in [self.tab_title, self.tab_id, self.plot]), "Please create the report plot."
        tab_content = report.new_tag('div', id=self.tab_id)
        tab_content['class'] = 'tabcontent'
        plot = BeautifulSoup(self.plot.to_html(full_html=False, include_plotlyjs='cdn'), 'html.parser')
        plotly_graph_div = plot.find('div', 'plotly-graph-div')
        del plotly_graph_div['style']
        plot.div['class'] = 'plotly-container'
        tab_content.append(plot)
        tab_bar = report.find('div', 'tabbar')
        tab_bar.insert_after(tab_content)

    def insert_report(self, report):
        self.insert_tab_button(report)
        self.insert_tab_content(report)
