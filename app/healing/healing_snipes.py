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


class HealingSnipes(Report):

    def __init__(self, report, api, fig_dir=None, healing_spells=None):
        Report.__init__(self, report, api, fig_dir=fig_dir)

        assert healing_spells is not None, "Please provide a dict with valid healing spells."

        print("\n\tRetrieving and sorting data ...")

        print()
        bar = tqdm(total=5)

        self.fight_names = self.get_fight_names(self.fights)

        bar.update(1)

        self.friendly_names = self.get_friendly_names(self.fights)

        bar.update(1)

        self.healing_resp = self.api.get_report_events('healing', self.id, end_time = self.end - self.start)

        bar.update(1)

        self.healing_events = self.healing_resp['events']

        bar.update(1)

        self.spells = self.spell_ids(healing_spells)

        bar.update(1)

        print("\n\tData retrieved")

        self.snipe_timeout = self.get_input(f"{'snipe timeout':<20}", 400, unit='ms')
        self.snipe_threshold = self.get_input(f"{'snipe threshold':<20}", 700, unit='hp')
        self.overhealing_treshold = self.get_input(f"{'overhealing treshold':<20}", 500, 'hp')

        print()

        self.plot_path = os.path.join(self.fig_dir, self.snipes_plot_name()) if self.snipes_plot_name() is not None else None

        self.healing_snipes()

        self.snipes_plot(self.sniped_heals, self.max_snipers, self.max_sniped, save_path=self.plot_path)

        print()

    def healing_snipes(self):

        self.assert_instantiated()

        self.max_snipers = {}
        self.max_sniped = {}

        self.sniped_heals = []

        for base_heal, n in zip(self.healing_events, range(len(self.healing_events))):
            if not 'tick' in base_heal:
                if 'overheal' in base_heal:
                    if base_heal['ability']['guid'] in self.spells:
                        if base_heal['overheal'] > self.overhealing_treshold:
                            snipes = self.get_snipes(base_heal, n, 50, self.healing_events)

                            if snipes:
                                self.process_snipes(snipes, base_heal)

        self.max_snipers = {h : v for h, v in sorted(self.max_snipers.items(), key=lambda item: len(item[1]['snipes']), reverse=True)}
        self.max_sniped = {h : v for h, v in sorted(self.max_sniped.items(), key=lambda item: len(item[1]['snipes']), reverse=True)}

        print()
        for sniper in self.max_snipers:
            print(self.max_snipers[sniper]['completeString'])

        print()
        for sniped in self.max_sniped:
            print(self.max_sniped[sniped]['completeString'])

    def process_snipes(self, snipes, base_heal):

        self.assert_instantiated()

        base_heal.update({'snipes' : snipes})
        base_heal.update({'timeStamp' : datetime.fromtimestamp((self.start + base_heal['timestamp'])/1000)})
        base_heal.update({'timeString' : base_heal['timeStamp'].strftime(r'%H:%M:%S')})
        base_heal.update({'fightName' : self.get_fight_name(base_heal)})
        base_heal.update({'healer' : self.friendly_names[base_heal['sourceID']]})

        self.sniped_heals.append(base_heal)

        for snipe in snipes:

            snipe.update({'snipedHeal' : base_heal})
            snipe.update({'fightName' : base_heal['fightName']})
            snipe.update({'healer' : self.friendly_names[snipe['sourceID']]})
            snipe.update({'dateTime' : datetime.fromtimestamp((self.start + snipe['timestamp'])/1000)})
            snipe.update({'timeString' : snipe['dateTime'].strftime(r'%H:%M:%S')})
            snipe.update({'eventString' : f"{snipe['timeString']} {base_heal['healer']}'s {base_heal['ability']['name']} " \
                                            f"sniped by {snipe['healer']} for {snipe['amount']} using {snipe['ability']['name']} " \
                                            f"during {snipe['fightName']}"})

            print(snipe['eventString'])

            if snipe['healer'] in self.max_snipers:
                self.max_snipers[snipe['healer']].update({'amount' : self.max_snipers[snipe['healer']]['amount'] + snipe['amount']})
                self.max_snipers[snipe['healer']]['snipes'].append(snipe)
            else:
                self.max_snipers.update({snipe['healer'] : {'amount' : snipe['amount'], 'snipes' : [snipe]}})

            self.max_snipers[snipe['healer']].update({'completeString' : f"{snipe['healer']} : sniped people " \
                                                                            f"{len(self.max_snipers[snipe['healer']]['snipes'])} " \
                                                                            f"times for {self.max_snipers[snipe['healer']]['amount']}" \
                                                                            " healing total"})

            if base_heal['healer'] in self.max_sniped:
                self.max_sniped[base_heal['healer']].update({'amount' : self.max_sniped[base_heal['healer']]['amount'] + snipe['amount']})
                self.max_sniped[base_heal['healer']]['snipes'].append(snipe)
            else:
                self.max_sniped.update({base_heal['healer'] : {'amount' : snipe['amount'], 'snipes' : [snipe]}})

            self.max_sniped[base_heal['healer']].update({'completeString' : f"{base_heal['healer']} : got sniped by people " \
                                                                                f"{len(self.max_sniped[base_heal['healer']]['snipes'])} " \
                                                                                f"times for " \
                                                                                f"{self.max_sniped[base_heal['healer']]['amount']}" \
                                                                                " healing total"})

    def get_snipes(self, base_heal, n, delta, healing_events):

        self.assert_instantiated()

        healing_events = self.trunc_list(n, delta, healing_events)
        snipes = []

        for h in healing_events:
            if h['ability']['guid'] in self.spells:
                if self.get_target_id(h) == self.get_target_id(base_heal):
                    if h['amount'] > self.snipe_threshold:
                        if not base_heal['sourceID'] == h['sourceID']:
                            base_heal['spell'] = self.spells[base_heal['ability']['guid']]
                            h['spell'] = self.spells[h['ability']['guid']]
                            if self.is_snipe(base_heal, h, self.snipe_timeout):
                                    snipes.append(h)
        return snipes

    def is_snipe(self, base_heal, snipe_heal, snipe_timeout,):
        snipe_min = base_heal['timestamp'] - base_heal['spell'].duration + snipe_timeout
        snipe_max = base_heal['timestamp'] - snipe_heal['spell'].duration
        snipe_t = snipe_heal['timestamp'] - snipe_heal['spell'].duration
        return True if snipe_min <= snipe_t <= snipe_max else False

    def trunc_list(self, n, delta, list_to_trunc):
        n_0 = n - delta if n - delta > 0 else 0
        n_1 = n_0 + delta if n_0 + delta < len(list_to_trunc) else len(list_to_trunc)
        return list_to_trunc[n_0:n_1]

    def spell_ids(self, healing_spells):
        spells = {}
        for spell in healing_spells:
            spells.update({spell.spell_id : spell})
        return spells

    def assert_instantiated(self):
        assert all(t is not None for t in [self.spells,
                                            self.fight_names,
                                            self.snipe_threshold,
                                            self.snipe_timeout,
                                            self.snipe_timeout,
                                            self.start,
                                            self.end]), "Please instantiate the class."

    def snipes_plot(self, events, snipers, snipeds, save_path=None):

        if save_path is not None:
            if os.path.isfile(save_path):
                if os.path.splitext(save_path)[-1] == '.html':
                    webbrowser.open(f'file://{save_path}', new=2)
                    return

        try:
            report_title = f"{datetime.fromtimestamp(self.start/1000).strftime(r'%a %d %b %Y')} {self.title}" \
                            " Healing Snipes<br><br><br>"
            report_title = f'{report_title}<span style="font-size: 12px;align=right">' \
                            f'Snipe Timeout {self.snipe_timeout / 1000} s</span><br>' \
                            f'<span style="font-size: 12px;align=right">' \
                            f'Snipe Treshold {self.snipe_threshold} hp</span><br>' \
                            f'<span style="font-size: 12px;align=right">' \
                            f'Overhealing Treshold  {self.overhealing_treshold} hp</span><br>'
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

        fig = make_subplots(rows=2, cols=2,
                            subplot_titles=('Snipes', "Snipes per Healer", "Got Sniped", "Got Sniped per Healer"),
                            column_widths=[0.7, 0.3],
                            horizontal_spacing=0.05,
                            vertical_spacing=0.05)

        palette = cycle(colors.qualitative.Plotly)

        for sniper in snipers:
            timestamps = np.array([s['snipedHeal']['timeStamp'] for s in snipers[sniper]['snipes']])
            event_vals = [s['amount'] for s in snipers[sniper]['snipes']]
            event_strings = [s['eventString'] for s in snipers[sniper]['snipes']]
            snipers[sniper].update({'markerColor' : next(palette)})
            fig.add_trace(go.Bar(name=sniper,
                                    x=timestamps,
                                    y=event_vals,
                                    hovertext=event_strings,
                                    width=(self.end - self.start)/600,
                                    legendgroup=sniper,
                                    marker_color=snipers[sniper]['markerColor']),
                                    row=1, col=1)
        for sniper in reversed(snipers):
            fig.add_trace(go.Bar(name=sniper,
                                    y=[sniper],
                                    x=[len(snipers[sniper]['snipes'])],
                                    hovertext=[snipers[sniper]['completeString']],
                                    orientation='h',
                                    legendgroup=sniper,
                                    showlegend=False,
                                    marker_color=snipers[sniper]['markerColor']),
                                    row=1, col=2)

        fig.update_xaxes(range=[self.start, self.end], row=1, col=1)
        fig.update_yaxes(ticksuffix='  ', row=1, col=2)

        for sniped in snipeds:
            timestamps = np.array([s['snipedHeal']['timeStamp'] for s in snipeds[sniped]['snipes']])
            event_vals = [s['amount'] for s in snipeds[sniped]['snipes']]
            event_strings = [s['eventString'] for s in snipeds[sniped]['snipes']]
            if sniped in snipers:
                snipeds[sniped].update({'markerColor' : snipers[sniped]['markerColor']})
            else:
                snipeds[sniped].update({'markerColor' : next(palette)})
            fig.add_trace(go.Bar(name=sniped,
                                    x=timestamps,
                                    y=event_vals,
                                    hovertext=event_strings,
                                    width=(self.end - self.start)/600,
                                    legendgroup=sniped,
                                    showlegend=False,
                                    marker_color=snipeds[sniped]['markerColor']),
                                    row=2, col=1)
        for sniped in reversed(snipeds):
            fig.add_trace(go.Bar(name=sniped,
                                    y=[sniped],
                                    x=[len(snipeds[sniped]['snipes'])],
                                    hovertext=[snipeds[sniped]['completeString']],
                                    orientation='h',
                                    legendgroup=sniped,
                                    showlegend=False,
                                    marker_color=snipeds[sniped]['markerColor']),
                                    row=2, col=2)

        fig.update_xaxes(range=[self.start, self.end], row=2, col=1)
        fig.update_yaxes(ticksuffix='  ', row=2, col=2)

        fig.update_layout(barmode='stack',
                          plot_bgcolor='#fcfcfc',
                          title=report_title)

        if save_path is not None:
            fig.write_html(save_path, include_plotlyjs='cdn')

        fig.show()

    def snipes_plot_name(self):
        try:
            plot_name = f'healing_snipes_{self.id}_' \
                        f'st{self.snipe_timeout}ms_st{self.snipe_threshold}hp_ot{self.overhealing_treshold}hp.html'
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