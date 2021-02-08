import os
import numpy as np
import plotly.graph_objects as go
import webbrowser
from NexusApi import NexusApi, Price
from datetime import datetime
from app.report import Report
from tqdm import tqdm
from plotly.subplots import make_subplots
from plotly.express import colors
from itertools import cycle


class HealingManaConsumes(Report):

    def __init__(self, report, wcl_api, fig_dir=None, classes=None, nexus_api=None, healing_consumes=None, server_name=None, full_report=False):
        Report.__init__(self, report, wcl_api, fig_dir=fig_dir)

        assert healing_consumes is not None, "Please provide a list with healing_consume dataclasses."

        self.consumes = healing_consumes

        print("\nHealing Mana Consumes")
        print("\n\tRetrieving and sorting data ...\n")

        self.classes = classes if classes is not None else ['Priest', 'Druid', 'Paladin']

        self.nexus_api = NexusApi() if not isinstance(nexus_api, NexusApi) else nexus_api

        self.fight_names = self.get_fight_names(self.fights)

        self.friendly_names = self.get_friendly_names(self.fights)

        self.faction = ''
        while self.faction.lower() not in ['horde', 'alliance']:
            self.faction = self.get_input(f"{'Faction? [Alliance/Horde]':<25}", 'Alliance', unit='')

        self.nexus_server_id = f"{server_name.replace(' ', '-')}-{self.faction.lower()}"

        self.consumes = self.get_consume_prices(self.consumes, self.nexus_server_id)

        self.consume_events = self.get_consume_events(self.consumes, self.classes)

        print("\n\tData retrieved.\n")

        self.plot_path = os.path.join(self.fig_dir, n) if (n:=self.consumes_plot_name()) is not None else None

        self.process_consumes()

        self.plot = self.consumes_plot(self.consume_events, self.healers, self.consumes, save_path=self.plot_path, full_report=full_report)

        print()

    def get_consume_prices(self, consume_list, nexus_server_id):

        self.assert_instantiated()

        for consume in consume_list:
            if consume.name == 'Dark Rune':
                cost_data = self.nexus_api.get_items_items(nexus_server_id, consume.item_id)
                consume.cost_price = Price(cost_data['stats']['current']['marketValue'])
                c_2 = [i for i in consume_list if i.name == 'Demonic Rune'][0]
                c_2.cost_price = Price(cost_data['stats']['current']['marketValue'])
            elif consume.name == "Night Dragons Breath":
                consume.cost_price = Price(0)
            elif consume.name == 'Demonic Rune':
                pass
            else:
                cost_data = self.nexus_api.get_items_items(nexus_server_id, consume.item_id)
                if cost_data:
                    consume.cost_price = Price(cost_data['stats']['current']['marketValue'])
                else:
                    raise AssertionError(f"{consume.name} price data not found on {nexus_server_id}")
            consume.total_cost = Price(0)
        return consume_list

    def get_consume_events(self, consume_list, classes):

        self.assert_instantiated()

        bar = tqdm(desc='Reading Events from Warcraftlogs', total=len(consume_list)*len(classes))

        events = []
        for consume in consume_list:
            for game_class in classes:
                resp = self.api.get_report_events('casts', self.id,
                                                    end_time = self.end - self.start,
                                                    abilityid=consume.ability_id,
                                                    sourceclass=game_class)
                events += resp['events']
                bar.update(1)

        bar.close()

        events = sorted(events, key=lambda item: item['timestamp'])

        return events

    def process_consumes(self):

        self.assert_instantiated()

        self.healers = {}

        self.total_cost = Price(0)

        for c in self.consume_events:
            c.update({'timeStamp' : datetime.fromtimestamp((self.start + c['timestamp'])/1000).replace(microsecond=0)})
            c.update({'timeString' : c['timeStamp'].strftime(r'%H:%M:%S')})
            c.update({'healer' : self.friendly_names[c['sourceID']]})
            c.update({'fightName' : self.get_fight_name(c)})

            consume = [i for i in self.consumes if i.ability_id == c['ability']['guid']][0]

            c.update({'consume' : consume})
            c.update({'eventString' : f"{c['timeString']} {c['healer']} used a {consume.name} " \
                                            f"during {c['fightName']}, costing {consume.cost_price}"})

            print(c['eventString'])

            try:
                consume.events.append(c)
            except AttributeError:
                consume.events = [c]

            consume.total_cost = Price(len(consume.events) * consume.cost_price)

            consume.complete_string = f"{consume.name} used {len(consume.events)} times for {consume.total_cost} total"

            self.total_cost = Price(self.total_cost + consume.cost_price)

            if c['healer'] in self.healers:

                self.healers[c['healer']].update({'cost' : Price(self.healers[c['healer']]['cost'] + consume.cost_price)})

                if consume.name in self.healers[c['healer']]['consumes']:
                    self.healers[c['healer']]['consumes'][consume.name] += 1
                else:
                    self.healers[c['healer']]['consumes'].update({consume.name : 1})

                self.healers[c['healer']]['consumeEvents'].append(c)

                self.healers[c['healer']]['amount'] += 1

            else:

                self.healers.update({c['healer'] : {'cost' : consume.cost_price,
                                                    'consumes' : {consume.name : 1},
                                                    'consumeEvents' : [c],
                                                    'amount' : 1}})

            self.healers[c['healer']].update({'consumeString' :
                                                f"{', '.join([f'{i} x {k}' for k, i in self.healers[c['healer']]['consumes'].items()])}"})

            self.healers[c['healer']].update({'completeString' : f"{c['healer']} : used " \
                                                                    f"{self.healers[c['healer']]['amount']} " \
                                                                    f"consumes for {self.healers[c['healer']]['cost']} " \
                                                                    f"total : " \
                                                                    f"{self.healers[c['healer']]['consumeString']}"})

        self.healers = self.sort_dict(self.healers, 'cost', reverse=True)
        self.consumes = sorted(self.consumes, key=lambda item: item.total_cost, reverse=True)

        print()
        print(f"Raid healers used {self.total_cost} in consumes")

        print()
        for healer in self.healers:
            print(self.healers[healer]['completeString'])

        print()
        for consume in self.consumes:
            try:
                print(consume.complete_string)
            except AttributeError:
                print(f'{consume.name} has not been used.')

    def consumes_plot(self, events, healers, consumes, save_path=None, full_report=False):

        if not full_report:
            if save_path is not None:
                if os.path.isfile(save_path):
                    if os.path.splitext(save_path)[-1] == '.html':
                        webbrowser.open(f'file://{save_path}', new=2)
                        return

        try:
            self.tab_title = "Doping Up"
            self.tab_id = "doping-up"
            report_title = '<span style="font-size: 28px">Doping Up &nbsp;&nbsp;&nbsp;&nbsp;</span>' \
                            f'<span style="font-size: 22px"><i>Healing Mana Consumes</i></span><br>' \
                            f'<span style="font-size: 12px">{self.title} - ' \
                            f"{datetime.fromtimestamp(self.start/1000).strftime(r'%a %d %b %Y')}</span><br>"
            report_title = f'{report_title}<span style="font-size: 12px;align=right">' \
                            f'Total Gold Spent on Mana Consumes is <b>{self.total_cost}</b></span><br>'

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
                            specs=[[{"colspan": 2}, None], [{}, {}]],
                            subplot_titles=('Mana Consumes Timeline', "Total Mana Consumes", "Mana Consumes per Healer"),
                            column_widths=[0.5, 0.5],
                            horizontal_spacing=0.065,
                            vertical_spacing=0.075)

        palette = cycle(getattr(colors.qualitative, self.plot_palette))


        for healer in healers:
            timestamps = np.array([c['timeStamp'] for c in healers[healer]['consumeEvents']])
            event_vals = [c['consume'].cost_price.price / 10000 for c in healers[healer]['consumeEvents']]
            event_strings = [c['eventString'] for c in healers[healer]['consumeEvents']]
            healers[healer].update({'markerColor' : next(palette)})
            fig.add_trace(go.Bar(name=healer,
                                    x=timestamps,
                                    y=event_vals,
                                    hovertext=event_strings,
                                    width=(self.end - self.start)/self.plot_time_barwidth_divisor,
                                    legendgroup=healer,
                                    marker_color=healers[healer]['markerColor'],
                                    marker=dict(line=dict(width=0))),
                                    row=1, col=1)

        for consume in reversed(consumes):
            try:
                fig.add_trace(go.Bar(name=consume.name,
                                        y=[consume.name],
                                        x=[consume.total_cost.price/10000],
                                        hovertext=[consume.complete_string],
                                        orientation='h',
                                        legendgroup=consume.name,
                                        marker_color=next(palette),
                                        marker=dict(line=dict(width=0))),
                                        row=2, col=1)
            except AttributeError:
                print(f'{consume.name} has not been used.')

        for healer in reversed(healers):
            fig.add_trace(go.Bar(name=healer,
                                    y=[healer],
                                    x=[healers[healer]['cost'].price / 10000],
                                    hovertext=[healers[healer]['completeString']],
                                    orientation='h',
                                    legendgroup=healer,
                                    showlegend=False,
                                    marker_color=healers[healer]['markerColor'],
                                    marker=dict(line=dict(width=0))),
                                    row=2, col=2)

        fig.update_xaxes(range=[self.start, self.end], mirror=True,
                            zeroline=False,
                            linecolor=self.plot_axiscolor, showline=True, linewidth=1,
                            row=1, col=1)
        fig.update_yaxes(ticksuffix='g', mirror=True,
                            zeroline=False,
                            showgrid=True, gridcolor=self.plot_axiscolor, gridwidth=1,
                            linecolor=self.plot_axiscolor, showline=True, linewidth=1,
                            row=1, col=1)
        fig.update_yaxes(ticksuffix='  ', mirror=True,
                            zeroline=False,
                            linecolor=self.plot_axiscolor, showline=True, linewidth=1,
                            row=2, col=1)
        fig.update_xaxes(ticksuffix='g', mirror=True,
                            zeroline=False,
                            showgrid=True, gridcolor=self.plot_axiscolor, gridwidth=1,
                            linecolor=self.plot_axiscolor, showline=True, linewidth=1,
                            row=2, col=1)
        fig.update_yaxes(ticksuffix='  ', mirror=True,
                            zeroline=False,
                            linecolor=self.plot_axiscolor, showline=True, linewidth=1,
                            row=2, col=2)
        fig.update_xaxes(ticksuffix='g', mirror=True,
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

    def consumes_plot_name(self):
        try:
            plot_name = f'healing_mana_consumes_{self.id}.html'
            return plot_name
        except AttributeError:
            return None

    def assert_instantiated(self):
        assert all(t is not None for t in [self.nexus_api,
                                            self.consumes,
                                            self.classes,
                                            self.fight_names,
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