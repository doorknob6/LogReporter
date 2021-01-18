import os
import numpy as np
import plotly.graph_objects as go
import webbrowser
from datetime import datetime
from app.report import Report
from tqdm import tqdm
from plotly.subplots import make_subplots
from plotly.express import colors
from itertools import cycle



class HealingSaves(Report):

    def __init__(self, report, api, stored_figures_path=None):
        Report.__init__(self, report, api, stored_figures_path=stored_figures_path)

        print("\n\tRetrieving and sorting data ...")

        print()
        bar = tqdm(total=8)

        self.fight_names = self.get_fight_names(self.fights)

        bar.update(1)

        self.friendly_names = self.get_friendly_names(self.fights)

        bar.update(1)

        self.healing_resp = self.api.get_report_events('healing', self.id, end_time = self.end - self.start)

        bar.update(1)

        self.healing_events = self.healing_resp['events']

        bar.update(1)

        self.damage_resp = self.api.get_report_events('damage-taken', self.id, end_time = self.end - self.start)

        bar.update(1)

        self.damage_events = self.damage_resp['events']

        bar.update(1)

        self.death_resp = self.api.get_report_events('deaths', self.id, end_time = self.end - self.start)

        bar.update(1)

        self.death_events = self.death_resp['events']

        bar.update(1)

        bar.close()

        print("\n\tData retrieved")

        self.near_death_percentage = self.get_input("near death percentage", 15, unit='%')
        self.death_timeout = self.get_input("death timeout", 8000, 'ms')
        self.heal_timeout = self.get_input("heal timeout", 3000, 'ms')
        self.heal_treshold = self.get_input("heal treshold", 800, 'hp')

        self.plot_path = os.path.join(self.stored_figures_path, self.saves_plot_name()) if self.saves_plot_name() is not None else None

        self.healing_saves()
        self.saves_plot(self.near_deaths, self.save_healers, save_path=self.plot_path)

        print()

    def healing_saves(self):
        self.near_deaths = []
        self.save_healers = {}

        for damage in self.damage_events:
            if 'hitPoints' in damage:
                if damage['hitPoints'] < self.near_death_percentage:
                    prev_damage = [d for d in self.near_deaths if self.get_target_id(d) == self.get_target_id(damage) and
                                    damage['timestamp'] - self.heal_timeout <= d['timestamp'] <= damage['timestamp']]
                    if not prev_damage:
                        death = [d for d in self.death_events if self.get_target_id(d) == self.get_target_id(damage) and
                                    damage['timestamp'] <= d['timestamp'] <= damage['timestamp'] + self.death_timeout]
                        if not death:

                            saves = [h for h in self.healing_events if self.get_target_id(h) == self.get_target_id(damage) and
                                        damage['timestamp'] <= h['timestamp'] <= damage['timestamp'] + self.heal_timeout and
                                        not 'overheal' in h and
                                        h['amount'] > self.heal_treshold]

                            if saves:

                                damage.update({'saves' : saves})
                                damage.update({'timeStamp' : datetime.fromtimestamp((self.start + damage['timestamp'])/1000)})
                                damage.update({'timeString' : damage['timeStamp'].strftime(r'%H:%M:%S')})
                                self.near_deaths.append(damage)

                                target_name = self.friendly_names[damage['targetID']]
                                damage.update({'targetName' : target_name})
                                fight_name = self.get_fight_name(damage)

                                damage.update({'fightName' : fight_name})

                                fight_str = f"During {fight_name} - "
                                save_amount = 0

                                for save in saves:
                                    save_amount += save['amount']
                                    save.update({'saveDamage' : damage})
                                    save.update({'fightName' : fight_name})
                                    healer = self.friendly_names[save['sourceID']]
                                    save.update({'healerName' : healer})
                                    save.update({'targetName' : target_name})
                                    save.update({'dateTime' : datetime.fromtimestamp((self.start + save['timestamp'])/1000)})
                                    save.update({'timeString' : save['dateTime'].strftime(r'%H:%M:%S')})
                                    save.update({'eventString' : f"{save['timeString']} {healer} saved {target_name} at {damage['hitPoints']}% hp using {save['ability']['name']} for {save['amount']} during {fight_name}"})
                                    if healer in self.save_healers:
                                        self.save_healers[healer].update({'healing amount' : self.save_healers[healer]['healing amount'] + save['amount']})
                                        self.save_healers[healer]['saves'].append(save)
                                        self.save_healers[healer].update({'completeString' : f"{healer} : saved people {len(self.save_healers[healer]['saves'])} times for {self.save_healers[healer]['healing amount']} healing total"})
                                    else:
                                        self.save_healers.update({healer : {'healing amount' : save['amount'], 'saves' : [save]}})
                                        self.save_healers[healer].update({'completeString' : f"{healer} : saved people {len(self.save_healers[healer]['saves'])} times for {self.save_healers[healer]['healing amount']} healing total"})

                                saves_str = ', '.join([f"{s['healerName']} : {s['amount']}" for s in saves])
                                damage_string = f"{damage['timeString']}: {fight_str}Near death of {target_name} with {damage['hitPoints']}% hp saved by {saves_str}"
                                damage.update({'eventString' : damage_string})

                                damage.update({'amount' : save_amount})
                                print(damage_string)

        print()

        self.save_healers = {h : v for h, v in sorted(self.save_healers.items(), key=lambda item: len(item[1]['saves']), reverse=True)}

        for healer in self.save_healers:
            print(self.save_healers[healer]['completeString'])

    def saves_plot(self, events, healers, save_path=None):

        if save_path is not None:
            if os.path.isfile(save_path):
                if os.path.splitext(save_path)[-1] == '.html':
                    webbrowser.open(f'file://{save_path}', new=2)
                    return

        try:
            report_title = f"{datetime.fromtimestamp(self.start/1000).strftime(r'%a %d %b %Y')} {self.title} Healing Saves<br><br><br>"
            report_title = f'{report_title}<span style="font-size: 12px;align=right">Near death counted at {self.near_death_percentage} %</span><br>'
            report_title = f'{report_title}<span style="font-size: 12px;align=right">Death Timeout {self.death_timeout / 1000} s</span><br>'
            report_title = f'{report_title}<span style="font-size: 12px;align=right">Heal Timeout  {self.heal_timeout / 1000} s</span><br>'
            report_title = f'{report_title}<span style="font-size: 12px;align=right">Heal Treshold {self.heal_treshold} hp</span>'
        except AttributeError:
            report_title = ''

        try:
            if not self.start:
                self.start = 0
        except AttributeError:
            self.start = 0

        try:
            if not self.end:
                self.end = events[-1] + 3e5
            else:
                self.end += 3e5
        except AttributeError:
            self.end = events[-1] + 3e5

        fig = make_subplots(rows=1, cols=2,
                            subplot_titles=('Near Death Saves', "Saves per Healer"),
                            column_widths=[0.7, 0.3],
                            horizontal_spacing=0.05)

        palette = cycle(colors.qualitative.Plotly)

        for healer in healers:
            timestamps = np.array([s['saveDamage']['timeStamp'] for s in healers[healer]['saves']])
            event_vals = [s['amount'] for s in healers[healer]['saves']]
            event_strings = [s['eventString'] for s in healers[healer]['saves']]
            healers[healer].update({'markerColor' : next(palette)})
            fig.add_trace(go.Bar(name=healer,
                                    x=timestamps,
                                    y=event_vals,
                                    hovertext=event_strings,
                                    width=(self.end - self.start)/600,
                                    legendgroup=healer,
                                    marker_color=healers[healer]['markerColor']),
                                    row=1, col=1)
        for healer in reversed(healers):
            fig.add_trace(go.Bar(name=healer,
                                    y=[healer],
                                    x=[len(healers[healer]['saves'])],
                                    orientation='h',
                                    legendgroup=healer,
                                    showlegend=False,
                                    marker_color=healers[healer]['markerColor']),
                                    row=1, col=2)

        fig.update_xaxes(range=[self.start, self.end], row=1, col=1)
        fig.update_yaxes(ticksuffix='  ', row=1, col=2)


        fig.update_layout(barmode='stack',
                          plot_bgcolor='#fcfcfc',
                          title=report_title)

        if save_path is not None:
            fig.write_html(save_path, include_plotlyjs='cdn')

        fig.show()

    def saves_plot_name(self):
        try:
            plot_name = f'healing_saves_{self.id}_'
            plot_name += f'{self.near_death_percentage}percent_dt{self.death_timeout}ms_ht{self.heal_timeout}ms_{self.heal_treshold}hp.html'
            return plot_name
        except AttributeError:
            return None

if __name__ == '__main__':
    try:
        pass
    except:
        import sys
        print(sys.exc_info()[0])
        import traceback
        print(traceback.format_exc())
    finally:
        print()
        input("Press enter to exit")