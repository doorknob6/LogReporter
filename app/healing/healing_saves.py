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

    def __init__(self, report, api, fig_dir=None, healing_spells=None, full_report=False):
        Report.__init__(self, report, api, fig_dir=fig_dir)

        assert healing_spells is not None, "Please provide a list with healing_spell dataclasses."

        print("\nHealing Saves")
        print("\n\tRetrieving and sorting data ...\n")

        bar = tqdm(total=9)

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

        self.spells = self.spell_ids(healing_spells)

        bar.update(1)

        bar.close()

        print("\n\tData retrieved.\n")

        self.near_death_percentage = self.get_input(f"{'near death percentage':<25}", 15, unit='%')
        self.death_timeout = self.get_input(f"{'death timeout':<25}", 8000, 'ms')
        self.no_damage_timeout = self.get_input(f"{'no damage timeout':<25}", 30000, 'ms')
        self.heal_timeout = self.get_input(f"{'heal timeout':<25}", 3000, 'ms')
        self.heal_treshold = self.get_input(f"{'heal treshold':<25}", 800, 'hp')

        self.plot_path = os.path.join(self.fig_dir, n) if (n:=self.saves_plot_name()) is not None else None

        print()

        self.healing_saves()
        self.plot = self.saves_plot(self.near_deaths, self.save_healers, save_path=self.plot_path, full_report=full_report)

        print()

    def healing_saves(self):

        self.assert_instantiated()

        self.near_deaths = []
        self.save_healers = {}

        for damage, i in zip(self.damage_events, range(len(self.damage_events))):
            if 'hitPoints' in damage:
                if damage['hitPoints'] < self.near_death_percentage:
                    prev_damage = [d for d in self.near_deaths if self.get_target_id(d) == self.get_target_id(damage) and
                                    damage['timestamp'] - self.heal_timeout <= d['timestamp'] <= damage['timestamp']]
                    if not prev_damage:
                        death = [d for d in self.death_events if self.get_target_id(d) == self.get_target_id(damage) and
                                    damage['timestamp'] <= d['timestamp'] <= damage['timestamp'] + self.death_timeout]
                        if not death:

                            next_damage = []

                            for d in self.damage_events[i:]:
                                if d['timestamp'] <= damage['timestamp'] + self.no_damage_timeout:
                                    if self.get_target_id(d) == self.get_target_id(damage):
                                        next_damage.append(d)
                                else:
                                    break

                            if next_damage:

                                saves = self.get_saves(damage, self.healing_events, self.heal_timeout, self.heal_treshold)

                                if saves:

                                    self.process_saves(damage, saves)

        print()

        self.save_healers = self.sort_dict(self.save_healers, 'raidSaves', reverse=True)

        for healer in self.save_healers:
            print(self.save_healers[healer]['raidCompleteString'])

    def process_saves(self, damage, saves):

        self.assert_instantiated()

        self.near_deaths.append(damage)

        damage.update({'saves' : saves})
        damage.update({'timeStamp' : datetime.fromtimestamp((self.start + damage['timestamp'])/1000).replace(microsecond=0)})
        damage.update({'timeString' : damage['timeStamp'].strftime(r'%H:%M:%S')})

        target_name = self.friendly_names[damage['targetID']]
        damage.update({'targetName' : target_name})

        fight_name = self.get_fight_name(damage)
        damage.update({'fightName' : fight_name})

        is_tank = self.is_tank(damage)
        damage.update({'tank' : is_tank})

        save_amount = 0

        for save in saves:

            save_amount += save['amount']
            save.update({'saveDamage' : damage})
            save.update({'fightName' : fight_name})

            healer = self.friendly_names[save['sourceID']]

            save.update({'healerName' : healer})
            save.update({'targetName' : target_name})
            save.update({'dateTime' : datetime.fromtimestamp((self.start + save['timestamp'])/1000).replace(microsecond=0)})
            save.update({'timeString' : save['dateTime'].strftime(r'%H:%M:%S')})
            save.update({'eventString' : f"{save['timeString']} {healer} saved {target_name} at {damage['hitPoints']}% hp using " \
                                            f"{save['ability']['name']} for {save['amount']} during {fight_name}"})

            if healer not in self.save_healers:
                self.save_healers.update({healer : {'tankHealingAmount' : 0, 'tankSaves' : []}})
                self.save_healers[healer].update({'tankCompleteString' : ''})
                self.save_healers[healer].update({'raidHealingAmount' : 0, 'raidSaves' : []})
                self.save_healers[healer].update({'raidCompleteString' : ''})

            if is_tank:
                self.save_healers[healer]['tankHealingAmount'] += save['amount']
                self.save_healers[healer]['tankSaves'].append(save)
                self.save_healers[healer].update({'tankCompleteString' : f"{healer} : saved tanks {len(self.save_healers[healer]['tankSaves'])} " \
                                                                        f"times for {self.save_healers[healer]['tankHealingAmount']} healing total"})
            else:
                self.save_healers[healer]['raidHealingAmount'] += save['amount']
                self.save_healers[healer]['raidSaves'].append(save)
                self.save_healers[healer].update({'raidCompleteString' : f"{healer} : saved people {len(self.save_healers[healer]['raidSaves'])} " \
                                                                            f"times for {self.save_healers[healer]['raidHealingAmount']} healing total"})




        saves_str = ', '.join([f"{s['healerName']} : {s['amount']}" for s in saves])
        damage_string = f"{damage['timeString']}: During {fight_name} - Near death of {target_name} with {damage['hitPoints']}% hp saved by {saves_str}"
        damage.update({'eventString' : damage_string})

        damage.update({'amount' : save_amount})

        print(damage_string)

    def get_saves(self, damage, healing_events, heal_timeout, heal_treshold):

        saves = []

        n = self.find_time_index(damage['timestamp'], self.healing_events)

        for heal in healing_events[n-15:]:

            if heal['ability']['guid'] in self.spells:
                if not 'overheal' in heal:
                    if heal['amount'] > heal_treshold:
                        if self.get_target_id(heal) == self.get_target_id(damage):
                            if damage['timestamp'] <= heal['timestamp'] <= damage['timestamp'] + heal_timeout:
                                saves.append(heal)

            if self.is_overshot(damage['timestamp'], heal['timestamp'], heal_timeout):
                break

        return saves

    def saves_plot(self, events, healers, save_path=None, full_report=False):

        if not full_report:
            if save_path is not None:
                if os.path.isfile(save_path):
                    if os.path.splitext(save_path)[-1] == '.html':
                        webbrowser.open(f'file://{save_path}', new=2)
                        return

        try:
            self.tab_title = "Guardian Angels"
            self.tab_id = "guardian-angels"
            report_title = '<span style="font-size: 28px">Guardian Angels &nbsp;&nbsp;&nbsp;&nbsp;</span>' \
                            f'<span style="font-size: 22px"><i>Healing Saves</i></span><br>' \
                            f'<span style="font-size: 12px">{self.title} - ' \
                            f"{datetime.fromtimestamp(self.start/1000).strftime(r'%a %d %b %Y')}</span><br><br>"
            report_title = f'{report_title}<span style="font-size: 12px;align:right">' \
                            f'Near death counted under {self.near_death_percentage} %</span><br>'
            report_title = f'{report_title}<span style="font-size: 12px;align:right">' \
                            f'Death Timeout {self.death_timeout / 1000} s</span><br>'
            report_title = f'{report_title}<span style="font-size: 12px;align:right">' \
                            f'No damage taken timeout {self.no_damage_timeout / 1000} s</span><br>'
            report_title = f'{report_title}<span style="font-size: 12px;align:right">' \
                            f'Heal Timeout  {self.heal_timeout / 1000} s</span><br>'
            report_title = f'{report_title}<span style="font-size: 12px;align:right">' \
                            f'Heal Treshold {self.heal_treshold} hp</span>'
        except AttributeError:
            report_title = ''

        try:
            if not self.start:
                self.start = 0
        except AttributeError:
            self.start = 0

        try:
            if not self.end:
                self.end = events[-1] + self.plot_time_end_buffer
            else:
                self.end += self.plot_time_end_buffer
        except AttributeError:
            self.end = events[-1] + self.plot_time_end_buffer

        fig = make_subplots(rows=2, cols=2,
                            subplot_titles=('Raid Near Death Saves', 'Raid Saves per Healer',
                                            'Tank Near Death Saves', 'Tank Saves per Healer'),
                            column_widths=[0.7, 0.3],
                            horizontal_spacing=0.065,
                            vertical_spacing=0.075)

        palette = cycle(getattr(colors.qualitative, self.plot_palette))

        self.make_time_plot(fig, healers, 'raidSaves', 'amount', row=1, col=1, palette=palette, t_stamp_event_key='saveDamage')
        self.make_horizontal_plot(fig, healers, 'raidSaves', 'raidCompleteString', row=1, col=2, palette=palette)

        healers = self.sort_dict(healers, 'tankSaves', reverse=True)

        self.make_time_plot(fig, healers, 'tankSaves', 'amount', row=2, col=1, palette=palette, t_stamp_event_key='saveDamage')
        self.make_horizontal_plot(fig, healers, 'tankSaves', 'tankCompleteString', row=2, col=2, palette=palette)

        fig.update_layout(barmode='stack',
                          paper_bgcolor=self.paper_bgcolor,
                          plot_bgcolor=self.plot_bgcolor,
                          font=go.layout.Font(family='Arial', color=self.plot_textcolor),
                          title=report_title)

        if save_path is not None:
            fig.write_html(save_path, include_plotlyjs='cdn')

        if full_report:
            return fig
        else:
            fig.show()

    def saves_plot_name(self):
        try:
            plot_name = f'healing_saves_{self.id}_'
            plot_name += f'{self.near_death_percentage}percent_dt{self.death_timeout}ms_ht{self.heal_timeout}ms_{self.heal_treshold}hp.html'
            return plot_name
        except AttributeError:
            return None

    def assert_instantiated(self):
        assert all(t is not None for t in [self.fight_names,
                                            self.near_death_percentage,
                                            self.death_timeout,
                                            self.heal_timeout,
                                            self.heal_treshold,
                                            self.damage_events,
                                            self.healing_events,
                                            self.start,
                                            self.end]), "Please instantiate the class."

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