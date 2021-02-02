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
from copy import copy


class HealingSnipes(Report):

    def __init__(self, report, api, fig_dir=None, healing_spells=None, full_report=False):
        Report.__init__(self, report, api, fig_dir=fig_dir)

        assert healing_spells is not None, "Please provide a list with healing_spell dataclasses."

        print("\nHealing Snipes")
        print("\n\tRetrieving and sorting data ...\n")

        bar = tqdm(total=3)

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

        bar.close()

        print("\n\tData retrieved.\n")

        self.snipe_timeout = self.get_input(f"{'snipe timeout':<25}", 400, unit='ms')
        self.snipe_threshold = self.get_input(f"{'snipe threshold':<25}", 700, unit='hp')
        self.overhealing_treshold = self.get_input(f"{'overhealing treshold':<25}", 500, 'hp')

        print()

        self.plot_path = os.path.join(self.fig_dir, n) if (n:=self.snipes_plot_name()) is not None else None

        self.healing_snipes()

        self.plot = self.snipes_plot(self.sniped_heals, self.max_snipers, self.max_sniped, save_path=self.plot_path, full_report=full_report)

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

        self.max_snipers = self.sort_dict(self.max_snipers, 'snipes', reverse=True)
        self.max_sniped = self.sort_dict(self.max_sniped, 'snipes', reverse=True)

        print()
        for sniper in self.max_snipers:
            print(self.max_snipers[sniper]['completeString'])

        print()
        for sniped in self.max_sniped:
            print(self.max_sniped[sniped]['completeString'])

    def process_snipes(self, snipes, base_heal):

        self.assert_instantiated()

        base_heal.update({'snipes' : snipes})
        base_heal.update({'timeStamp' : datetime.fromtimestamp((self.start + base_heal['timestamp'])/1000).replace(microsecond=0)})
        base_heal.update({'timeString' : base_heal['timeStamp'].strftime(r'%H:%M:%S')})
        base_heal.update({'fightName' : self.get_fight_name(base_heal)})
        base_heal.update({'healer' : self.friendly_names[base_heal['sourceID']]})

        self.sniped_heals.append(base_heal)

        for snipe in snipes:

            if 'snipedHeal' in snipe:
                snipe = copy(snipe)

            snipe.update({'snipedHeal' : base_heal})
            snipe.update({'fightName' : base_heal['fightName']})
            snipe.update({'healer' : self.friendly_names[snipe['sourceID']]})
            snipe.update({'dateTime' : datetime.fromtimestamp((self.start + snipe['timestamp'])/1000).replace(microsecond=0)})
            snipe.update({'timeString' : snipe['dateTime'].strftime(r'%H:%M:%S')})
            snipe.update({'eventString' : f"{snipe['timeString']} {base_heal['healer']}'s {base_heal['ability']['name']} " \
                                            f"sniped by {snipe['healer']} for {snipe['amount']} using {snipe['ability']['name']} " \
                                            f"during {snipe['fightName']}"})

            print(snipe['eventString'])

            if snipe['healer'] in self.max_snipers:
                self.max_snipers[snipe['healer']]['amount'] += snipe['amount']
                self.max_snipers[snipe['healer']]['snipes'].append(snipe)
            else:
                self.max_snipers.update({snipe['healer'] : {'amount' : snipe['amount'], 'snipes' : [snipe]}})

            self.max_snipers[snipe['healer']].update({'completeString' : f"{snipe['healer']} : sniped people " \
                                                                            f"{len(self.max_snipers[snipe['healer']]['snipes'])} " \
                                                                            f"times for {self.max_snipers[snipe['healer']]['amount']}" \
                                                                            " healing total"})

            if base_heal['healer'] in self.max_sniped:
                self.max_sniped[base_heal['healer']]['amount'] += snipe['amount']
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

    def is_snipe(self, base_heal, snipe_heal, snipe_timeout):
        snipe_min = base_heal['timestamp'] - base_heal['spell'].duration + snipe_timeout
        snipe_max = base_heal['timestamp'] - snipe_heal['spell'].duration
        snipe_t = snipe_heal['timestamp'] - snipe_heal['spell'].duration
        return True if snipe_min <= snipe_t <= snipe_max else False

    def trunc_list(self, n, delta, list_to_trunc):
        n_0 = n - delta if n - delta > 0 else 0
        return list_to_trunc[n_0:n]

    def assert_instantiated(self):
        assert all(t is not None for t in [self.spells,
                                            self.fight_names,
                                            self.snipe_threshold,
                                            self.snipe_timeout,
                                            self.snipe_timeout,
                                            self.start,
                                            self.end]), "Please instantiate the class."

    def snipes_plot(self, events, snipers, snipeds, save_path=None, full_report=False):

        if not full_report:
            if save_path is not None:
                if os.path.isfile(save_path):
                    if os.path.splitext(save_path)[-1] == '.html':
                        webbrowser.open(f'file://{save_path}', new=2)
                        return

        try:
            report_title = '<span style="font-size: 28px">Sniper Elite &nbsp;&nbsp;&nbsp;&nbsp;</span>' \
                            f'<span style="font-size: 22px"><i>Healing Snipes</i></span><br>' \
                            f'<span style="font-size: 12px">{self.title} - ' \
                            f"{datetime.fromtimestamp(self.start/1000).strftime(r'%a %d %b %Y')}</span><br><br>"
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
                self.end = events[-1] + self.plot_time_end_buffer
            else:
                self.end += self.plot_time_end_buffer
        except AttributeError:
            self.end = events[-1] + self.plot_time_end_buffer

        fig = make_subplots(rows=2, cols=2,
                            subplot_titles=('Snipes', "Snipes per Healer", "Got Sniped", "Got Sniped per Healer"),
                            column_widths=[0.7, 0.3],
                            horizontal_spacing=0.065,
                            vertical_spacing=0.075)

        palette = cycle(getattr(colors.qualitative, self.plot_palette))

        for sniper in snipers:
            timestamps = np.array([s['snipedHeal']['timeStamp'] for s in snipers[sniper]['snipes']])
            event_vals = [s['amount'] for s in snipers[sniper]['snipes']]
            event_strings = [s['eventString'] for s in snipers[sniper]['snipes']]
            snipers[sniper].update({'markerColor' : next(palette)})
            fig.add_trace(go.Bar(name=sniper,
                                    x=timestamps,
                                    y=event_vals,
                                    hovertext=event_strings,
                                    width=(self.end - self.start)/self.plot_time_barwidth_divisor,
                                    legendgroup=sniper,
                                    marker_color=snipers[sniper]['markerColor'],
                                    marker=dict(line=dict(width=0))),
                                    row=1, col=1)
        for sniper in reversed(snipers):
            fig.add_trace(go.Bar(name=sniper,
                                    y=[sniper],
                                    x=[len(snipers[sniper]['snipes'])],
                                    hovertext=[snipers[sniper]['completeString']],
                                    orientation='h',
                                    legendgroup=sniper,
                                    showlegend=False,
                                    marker_color=snipers[sniper]['markerColor'],
                                    marker=dict(line=dict(width=0))),
                                    row=1, col=2)

        fig.update_xaxes(range=[self.start, self.end], mirror=True,
                            zeroline=False,
                            linecolor=self.plot_axiscolor, showline=True, linewidth=1,
                            row=1, col=1)
        fig.update_yaxes(mirror=True,
                            zeroline=False,
                            showgrid=True, gridcolor=self.plot_axiscolor, gridwidth=1,
                            linecolor=self.plot_axiscolor, showline=True, linewidth=1,
                            row=1, col=1)

        fig.update_yaxes(ticksuffix='  ', mirror=True,
                            zeroline=False,
                            linecolor=self.plot_axiscolor, showline=True, linewidth=1,
                            row=1, col=2)
        fig.update_xaxes(mirror=True,
                            zeroline=False,
                            showgrid=True, gridcolor=self.plot_axiscolor, gridwidth=1,
                            linecolor=self.plot_axiscolor, showline=True, linewidth=1,
                            row=1, col=2)

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
                                    width=(self.end - self.start)/self.plot_time_barwidth_divisor,
                                    legendgroup=sniped,
                                    showlegend=False,
                                    marker_color=snipeds[sniped]['markerColor'],
                                    marker=dict(line=dict(width=0))),
                                    row=2, col=1)
        for sniped in reversed(snipeds):
            fig.add_trace(go.Bar(name=sniped,
                                    y=[sniped],
                                    x=[len(snipeds[sniped]['snipes'])],
                                    hovertext=[snipeds[sniped]['completeString']],
                                    orientation='h',
                                    legendgroup=sniped,
                                    showlegend=False,
                                    marker_color=snipeds[sniped]['markerColor'],
                                    marker=dict(line=dict(width=0))),
                                    row=2, col=2)

        fig.update_xaxes(range=[self.start, self.end], mirror=True,
                            zeroline=False,
                            linecolor=self.plot_axiscolor, showline=True, linewidth=1,
                            row=2, col=1)
        fig.update_yaxes(mirror=True,
                            zeroline=False,
                            showgrid=True, gridcolor=self.plot_axiscolor, gridwidth=1,
                            linecolor=self.plot_axiscolor, showline=True, linewidth=1,
                            row=2, col=1)

        fig.update_yaxes(ticksuffix='  ', mirror=True,
                            zeroline=False,
                            linecolor=self.plot_axiscolor, showline=True, linewidth=1,
                            row=2, col=2)
        fig.update_xaxes(mirror=True,
                            zeroline=False,
                            showgrid=True, gridcolor=self.plot_axiscolor, gridwidth=1,
                            linecolor=self.plot_axiscolor, showline=True, linewidth=1,
                            row=2, col=2)

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