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


class HealerFrags(Report):

    def __init__(self, report, api, fig_dir=None, classes=None, meme_spells=None, full_report=False):
        Report.__init__(self, report, api, fig_dir=fig_dir)

        print("\nHealer Frags")
        print("\n\tRetrieving and sorting data ...\n")

        self.classes = classes if classes is not None else ['Priest', 'Druid', 'Paladin']
        self.meme_spells = meme_spells if meme_spells is not None else ['Starfire', 'Maul', 'Shred',
                                                                        'Mindflay',
                                                                        'Seal of Command', 'Holy Shield', 'Seal of Righteousness']

        bar = tqdm(total=3)

        self.fight_names = self.get_fight_names(self.fights)

        bar.update(1)

        self.friendly_names = self.get_friendly_names(self.fights)

        bar.update(1)

        self.enemy_names = self.get_enemy_names(self.fights)

        bar.update(1)

        bar.close()

        self.frag_events = self.get_frag_events(self.classes)

        self.frag_events = self.remove_meme_specs(self.frag_events, self.meme_spells)

        self.plot_path = os.path.join(self.fig_dir, n) if (n:=self.frags_plot_name()) is not None else None

        self.process_frags(self.frag_events)

        self.plot = self.frags_plot(self.frag_events, self.healers, self.loatheb_events, self.skeleton_frags, self.viscidus_events, self.cthun_events,
                                    save_path=self.plot_path, full_report=full_report)

        print()

    def process_frags(self, frag_events):

        self.assert_instantiated()

        self.healers = {}
        self.skeleton_frags = False
        self.loatheb_events = False
        self.viscidus_events = False
        self.cthun_events = False

        for f in frag_events:
            f.update({'timeStamp' : datetime.fromtimestamp((self.start + f['timestamp'])/1000).replace(microsecond=0)})
            f.update({'timeString' : f['timeStamp'].strftime(r'%H:%M:%S')})
            f.update({'healer' : self.friendly_names[f['sourceID']]})
            try:
                f.update({'target' : self.enemy_names[f['targetID']]})
            except:
                print(f"\t{f['timeString']} Could not find targetID {f['targetID']} for damage by {f['healer']}")
                continue
            f.update({'fightName' : self.get_fight_name(f)})

            f.update({'eventString' : f"{f['timeString']} {f['healer']} did {f['amount']} damage to {f['target']} " \
                                            f"during {f['fightName']}"})

            print(f['eventString'])

            if f['healer'] in self.healers:

                self.healers[f['healer']]['damage'] += f['amount']
                self.healers[f['healer']]['damageEvents'].append(f)

            else:

                self.healers.update({f['healer'] : {'damage' : f['amount'],
                                                    'damageEvents' : [f]}})

            if f['target'] == 'Soldier of the Frozen Wastes':

                if 'overkill' in f:
                    if 'skeletonFrags' in self.healers[f['healer']]:
                        self.healers[f['healer']]['skeletonFrags'] += 1
                        self.healers[f['healer']]['skeletonFragEvents'].append(f)
                    else:
                        self.healers[f['healer']].update({'skeletonFrags' : 1, 'skeletonFragEvents' : [f]})
                    self.healers[f['healer']].update({'skeletonString' : f"{f['healer']} : made " \
                                                        f"{self.healers[f['healer']]['skeletonFrags']} killing blows on Kel'Thuzad skeletons"})

                    self.skeleton_frags = True

            elif f['target'] == 'Loatheb':

                if 'loathebDamage' in self.healers[f['healer']]:
                    self.healers[f['healer']]['loathebDamage'] += f['amount']
                else:
                    self.healers[f['healer']].update({'loathebDamage' : f['amount']})
                self.healers[f['healer']].update({'loathebString' : f"{f['healer']} : did " \
                                                    f"{self.healers[f['healer']]['loathebDamage']} damage on Loatheb"})

                self.loatheb_events = True

            elif f['target'] == 'Viscidus':

                if 'viscidusSlaps' in self.healers[f['healer']]:
                    self.healers[f['healer']]['viscidusSlaps'] += 1
                else:
                    self.healers[f['healer']].update({'viscidusSlaps' : 1})
                self.healers[f['healer']].update({'viscidusString' : f"{f['healer']} : slapped Viscidus " \
                                                    f"{self.healers[f['healer']]['viscidusSlaps']} times"})

                self.viscidus_events = True

            elif f['target'] in ["Eye of C'Thun", "C'Thun"]:

                if 'cthunDamage' in self.healers[f['healer']]:
                    self.healers[f['healer']]['cthunDamage'] += f['amount']
                else:
                    self.healers[f['healer']].update({'cthunDamage' : f['amount']})
                self.healers[f['healer']].update({'cthunString' : f"{f['healer']} : did " \
                                                    f"{self.healers[f['healer']]['cthunDamage']} damage on C'Thun"})

                self.cthun_events = True

            self.healers[f['healer']].update({'completeString' : f"{f['healer']} : did " \
                                                                    f"{self.healers[f['healer']]['damage']} damage total"})

        if self.skeleton_frags:
            for healer in self.healers:
                if not 'skeletonFrags' in self.healers[healer]:
                    self.healers[healer].update({'skeletonFrags' : 0})
        if self.loatheb_events:
            for healer in self.healers:
                if not 'loathebDamage' in self.healers[healer]:
                    self.healers[healer].update({'loathebDamage' : 0})
        if self.viscidus_events:
            for healer in self.healers:
                if not 'viscidusSlaps' in self.healers[healer]:
                    self.healers[healer].update({'viscidusSlaps' : 0})
        if self.cthun_events:
            for healer in self.healers:
                if not 'cthunDamage' in self.healers[healer]:
                    self.healers[healer].update({'cthunDamage' : 0})

        self.healers = self.sort_dict(self.healers, 'damage', reverse=True)

    def get_frag_events(self, classes):

        self.assert_instantiated()

        bar = tqdm(desc='\tReading Events from Warcraftlogs', total=len(classes))

        events = []
        for game_class in classes:
            resp = self.api.get_report_events('damage-done',
                                                self.id,
                                                end_time = self.end - self.start,
                                                sourceclass=game_class)
            events += resp['events']
            bar.update(1)

        bar.close()

        events = sorted(events, key=lambda item: item['timestamp'])

        return events

    def remove_meme_specs(self, events, meme_spells=None):

        self.assert_instantiated()

        filtered_events = []
        meme_ids = []

        for event in events:
            if 'ability' in event:
                if 'sourceID' in event:
                    if event['sourceID'] not in meme_ids:
                        if 'name' in event['ability']:
                            if event['ability']['name']:
                                if event['ability']['name'] in meme_spells:
                                    meme_id = event['sourceID']
                                    if meme_id not in meme_ids:
                                        meme_ids.append(meme_id)
                                        filtered_events = [e for e in filtered_events if e['sourceID'] != meme_id]
                                else:
                                    filtered_events.append(event)

        return filtered_events

    def assert_instantiated(self):
        assert all(t is not None for t in [self.classes,
                                            self.fight_names,
                                            self.meme_spells,
                                            self.start,
                                            self.end]), "Please instantiate the class."

    def frags_plot(self, events, healers, loatheb_events=False, skeleton_frags=False, viscidus_events=False, cthun_events=False, save_path=None, full_report=False):

        if not full_report:
            if save_path is not None:
                if os.path.isfile(save_path):
                    if os.path.splitext(save_path)[-1] == '.html':
                        webbrowser.open(f'file://{save_path}', new=2)
                        return
        try:
            self.tab_title = "Respec Applications"
            self.tab_id = "respec-applications"
            report_title = '<span style="font-size: 28px">Respec Applications &nbsp;&nbsp;&nbsp;&nbsp;</span>' \
                            f'<span style="font-size: 22px"><i>"No"</i></span>' \
                            f'<span style="font-size: 12px"><i> - Exit (2019), Healingbeard (2020), Parshathh (2021)</i></span><br>' \
                            f'<span style="font-size: 12px">{self.title} - ' \
                            f"{datetime.fromtimestamp(self.start/1000).strftime(r'%a %d %b %Y')}</span>"
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

        n_lists = sum(l is not False for l in [skeleton_frags, loatheb_events, viscidus_events, cthun_events])

        n_rows = 1 if n_lists < 1 else 2
        n_cols = 12 # divisible by 1, 2, 3 and 4

        specs = [[{"colspan": 8}] + [None] * 7 + [{"colspan": 4}] + [None] * 3, ] if n_lists < 1 else \
                [[{"colspan": 8}] + [None] * 7 + [{"colspan": 4}] + [None] * 3, \
                    ([{"colspan" : int(n_cols / n_lists)}] + [None] * int(n_cols / n_lists - 1)) * n_lists]
        titles = ['Damage Timeline', 'Damage per Healer']

        if skeleton_frags:
            titles.append('Killing Blows on KT Skeletons')
        if loatheb_events:
            titles.append('Damage on Loatheb')
        if viscidus_events:
            titles.append('Hits on Viscidus')
        if cthun_events:
            titles.append("Damage on C'Thun")

        fig = make_subplots(rows=n_rows, cols=n_cols,
                            specs=specs,
                            subplot_titles=titles,
                            horizontal_spacing=0.065,
                            vertical_spacing=0.075)

        palette = cycle(getattr(colors.qualitative, self.plot_palette))

        self.make_time_plot(fig, healers, 'damageEvents', 'amount', row=1, col=1, palette=palette)
        self.make_horizontal_plot(fig, healers, 'damage', 'completeString', row=1, col=9)

        n_col = 0

        if loatheb_events:
            n_col += 1
            healers = self.sort_dict(healers, 'loathebDamage', reverse=True)
            self.make_horizontal_plot(fig, healers, 'loathebDamage', 'loathebString', row=2, col=n_col)

        if skeleton_frags:
            n_col += int(n_cols / n_lists) if n_col > 0 else 1
            healers = self.sort_dict(healers, 'skeletonFrags', reverse=True)
            self.make_horizontal_plot(fig, healers, 'skeletonFrags', 'skeletonString', row=2, col=n_col)

        if viscidus_events:
            n_col += int(n_cols / n_lists) if n_col > 0 else 1
            healers = self.sort_dict(healers, 'viscidusSlaps', reverse=True)
            self.make_horizontal_plot(fig, healers, 'viscidusSlaps', 'viscidusString', row=2, col=n_col)

        if cthun_events:
            n_col += int(n_cols / n_lists) if n_col > 0 else 1
            healers = self.sort_dict(healers, 'cthunDamage', reverse=True)
            self.make_horizontal_plot(fig, healers, 'cthunDamage', 'cthunString', row=2, col=n_col)

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

    def frags_plot_name(self):
        try:
            plot_name = f'healer_frags_{self.id}.html'
            return plot_name
        except AttributeError:
            return None