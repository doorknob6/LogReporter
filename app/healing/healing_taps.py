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


class HealingTaps(Report):

    def __init__(self, report, api, fig_dir=None, healing_spells=None, full_report=False):
        Report.__init__(self, report, api, fig_dir=fig_dir)

        assert healing_spells is not None, "Please provide a list with healing_spell dataclasses."

        print("\nHealing Taps")
        print("\n\tRetrieving and sorting data ...\n")

        bar = tqdm(total=5)

        self.fight_names = self.get_fight_names(self.fights)

        bar.update(1)

        self.friendly_names = self.get_friendly_names(self.fights)

        bar.update(1)

        self.healing_resp = self.api.get_report_events('healing', self.id, end_time = self.end - self.start)
        self.healing_events = self.healing_resp['events']

        bar.update(1)

        self.tap_resp = self.api.get_report_events('casts', self.id, end_time = self.end - self.start, abilityid=11689)
        self.tap_events = self.tap_resp['events']

        bar.update(1)

        self.spells = self.spell_ids(healing_spells)

        bar.update(1)

        bar.close()

        print("\n\tData retrieved.\n")

        self.grace_timeout = self.get_input(f"{'grace period timeout':<25}", 400, unit='ms')
        self.tap_heal_timeout = self.get_input(f"{'tap heal timeout':<25}", 1200, unit='ms')

        self.plot_path = os.path.join(self.fig_dir, n) if (n:= self.taps_plot_name()) is not None else None

        print()

        self.healing_taps()
        self.plot = self.taps_plot(self.tap_events, self.tap_healers, save_path=self.plot_path, full_report=full_report)

        print()

    def healing_taps(self):

        self.assert_instantiated()

        self.tap_heals = []
        self.tap_healers = {}

        for tap in self.tap_events:

            tap_heals = self.get_tap_heals(tap, self.healing_events, self.grace_timeout, self.tap_heal_timeout)

            if tap_heals:

                self.process_tap_heals(tap, tap_heals)

        print()

        self.tap_healers = self.sort_dict(self.tap_healers, 'tapHeals', reverse=True)

        for healer, value in self.tap_healers.items():
            print(f"{healer} : healed taps {len(value['tapHeals'])} times for {value['amount']} healing")

    def process_tap_heals(self, tap, tap_heals):

        tap.update({'tapHeals' : tap_heals})
        tap.update({'timeStamp' : datetime.fromtimestamp((self.start + tap['timestamp'])/1000).replace(microsecond=0)})
        tap.update({'timeString' : tap['timeStamp'].strftime(r'%H:%M:%S')})

        warlock_name = self.friendly_names[tap['sourceID']]
        tap.update({'warlockName' : warlock_name})
        fight_name = self.get_fight_name(tap)

        tap.update({'fightName' : fight_name})

        heal_amount = 0

        for heal in tap_heals:

            heal_amount += heal['amount']
            heal.update({'Tap' : tap})
            heal.update({'fightName' : fight_name})

            healer = self.friendly_names[heal['sourceID']]

            heal.update({'healerName' : healer})
            heal.update({'targetName' : warlock_name})
            heal.update({'dateTime' : datetime.fromtimestamp((self.start + heal['timestamp'])/1000).replace(microsecond=0)})
            heal.update({'timeString' : heal['dateTime'].strftime(r'%H:%M:%S')})
            heal.update({'healSpeed' : (heal['timestamp'] - heal['spell'].duration - tap['timestamp']) / 1000})
            heal.update({'eventString' : f"{heal['timeString']} {healer} healed {heal['targetName']}'s tap at {tap['hitPoints']}% hp " \
                                            f"within {heal['healSpeed']:.2f}s " \
                                            f"using {heal['ability']['name']} for {heal['amount']} " \
                                            f"with {heal['overheal'] if 'overheal' in heal else '0'} overheal during {fight_name}"})

            print(heal['eventString'])

            if healer in self.tap_healers:

                self.tap_healers[healer]['amount'] += heal['amount']
                self.tap_healers[healer]['tapHeals'].append(heal)
                self.tap_healers[healer].update({'completeString' : f"{healer} : healed taps {len(self.tap_healers[healer]['tapHeals'])} " \
                                                                    f"times for {self.tap_healers[healer]['amount']} healing total"})

            else:

                self.tap_healers.update({healer : {'amount' : heal['amount'], 'tapHeals' : [heal]}})
                self.tap_healers[healer].update({'completeString' : f"{healer} : healed taps {len(self.tap_healers[healer]['tapHeals'])} " \
                                                                    f"times for {self.tap_healers[healer]['amount']} healing total"})

        heals_str = ', '.join([f"{h['healerName']} : {h['amount']}" for h in tap_heals])
        tap_string = f"{tap['timeString']}: During {fight_name} - {tap['warlockName']}'s lifetap with {tap['hitPoints']}% hp healed by {heals_str}"
        tap.update({'eventString' : tap_string})
        tap.update({'amount' : heal_amount})

    def get_tap_heals(self, tap, healing_events, grace_timeout, tap_heal_timeout, max_heal_duration=3000):

        tap_heals = []

        n = self.find_time_index(tap['timestamp'], healing_events)

        for heal in healing_events[n-15:]:

            if self.is_tap_heal(tap, heal, grace_timeout, tap_heal_timeout):

                tap_heals.append(heal)

            if self.is_overshot(tap['timestamp'], heal['timestamp'], tap_heal_timeout + max_heal_duration):
                break

        return tap_heals

    def is_tap_heal(self, tap, tap_heal, grace_timeout, tap_heal_timeout):
        if not 'tick' in tap_heal:
            if tap_heal['ability']['guid'] in self.spells:
                if 'sourceID' in tap:
                    if tap['sourceID'] == self.get_target_id(tap_heal):
                        tap_heal['spell'] = self.spells[tap_heal['ability']['guid']]
                        tap_heal_min = tap['timestamp'] + grace_timeout
                        tap_heal_max = tap['timestamp'] + tap_heal_timeout
                        tap_heal_t = tap_heal['timestamp'] - tap_heal['spell'].duration
                        if tap_heal_min <= tap_heal_t <= tap_heal_max:
                            return True
        return False

    def taps_plot(self, events, healers, save_path=None, full_report=False):

        if not full_report:
            if save_path is not None:
                if os.path.isfile(save_path):
                    if os.path.splitext(save_path)[-1] == '.html':
                        webbrowser.open(f'file://{save_path}', new=2)
                        return

        try:
            self.tab_title = "Parses on Tap"
            self.tab_id = "parses-on-tap"
            report_title = '<span style="font-size: 28px">Parses on Tap &nbsp;&nbsp;&nbsp;&nbsp;</span>' \
                            f'<span style="font-size: 22px"><i>Warlock Life Taps Healed</i></span><br>' \
                            f'<span style="font-size: 12px">{self.title} - ' \
                            f"{datetime.fromtimestamp(self.start/1000).strftime(r'%a %d %b %Y')}</span><br><br>"
            report_title = f'{report_title}<span style="font-size: 12px;align=right">' \
                            f'After Lifetap grace period is {self.grace_timeout / 1000} s</span><br>'
            report_title = f'{report_title}<span style="font-size: 12px;align=right">' \
                            f'After Lifetap tap heal timeout is {self.tap_heal_timeout / 1000} s</span><br>'
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

        fig = make_subplots(rows=1, cols=2,
                            subplot_titles=('Life Taps Healed', "Tap Heals per Healer"),
                            column_widths=[0.7, 0.3],
                            horizontal_spacing=0.065)

        palette = cycle(getattr(colors.qualitative, self.plot_palette))

        self.make_time_plot(fig, healers, 'tapHeals', 'amount', row=1, col=1, palette=palette, t_stamp_event_key='Tap')
        self.make_horizontal_plot(fig, healers, 'tapHeals', 'completeString', row=1, col=2)

        # for healer in healers:
        #     timestamps = np.array([s['Tap']['timeStamp'] for s in healers[healer]['tapHeals']])
        #     event_vals = [h['amount'] for h in healers[healer]['tapHeals']]
        #     event_strings = [h['eventString'] for h in healers[healer]['tapHeals']]
        #     healers[healer].update({'markerColor' : next(palette)})
        #     fig.add_trace(go.Bar(name=healer,
        #                             x=timestamps,
        #                             y=event_vals,
        #                             hovertext=event_strings,
        #                             width=(self.end - self.start)/self.plot_time_barwidth_divisor,
        #                             legendgroup=healer,
        #                             marker_color=healers[healer]['markerColor'],
        #                             marker=dict(line=dict(width=0))),
        #                             row=1, col=1)
        # for healer in reversed(healers):
        #     fig.add_trace(go.Bar(name=healer,
        #                             y=[healer],
        #                             x=[len(healers[healer]['tapHeals'])],
        #                             hovertext=[healers[healer]['completeString']],
        #                             orientation='h',
        #                             legendgroup=healer,
        #                             showlegend=False,
        #                             marker_color=healers[healer]['markerColor'],
        #                             marker=dict(line=dict(width=0))),
        #                             row=1, col=2)

        # fig.update_xaxes(range=[self.start, self.end], mirror=True,
        #                     zeroline=False,
        #                     linecolor=self.plot_axiscolor, showline=True, linewidth=1,
        #                     row=1, col=1)
        # fig.update_yaxes(mirror=True,
        #                     zeroline=False,
        #                     showgrid=True, gridcolor=self.plot_axiscolor, gridwidth=1,
        #                     linecolor=self.plot_axiscolor, showline=True, linewidth=1,
        #                     row=1, col=1)

        # fig.update_yaxes(ticksuffix='  ', mirror=True,
        #                     zeroline=False,
        #                     linecolor=self.plot_axiscolor, showline=True, linewidth=1,
        #                     row=1, col=2)
        # fig.update_xaxes(mirror=True,
        #                     zeroline=False,
        #                     showgrid=True, gridcolor=self.plot_axiscolor, gridwidth=1,
        #                     linecolor=self.plot_axiscolor, showline=True, linewidth=1,
        #                     row=1, col=2)

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

    def taps_plot_name(self):
        try:
            plot_name = f'healing_taps_{self.id}'
            plot_name += f'_gt{self.grace_timeout}'
            plot_name += f'_tht{self.tap_heal_timeout}ms.html'
            return plot_name
        except AttributeError:
            return None

    def assert_instantiated(self):
        assert all(t is not None for t in [self.fight_names,
                                            self.grace_timeout,
                                            self.tap_heal_timeout,
                                            self.tap_events,
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