from WCLApi import WCLApi
from NexusApi import NexusApi, Price
from datetime import datetime, timedelta
from app.report import Report
from tqdm import tqdm
import json
import os
import math


class HealingManaConsumes(Report):

    def __init__(self, report, wcl_api, fig_dir=None, classes=None, nexus_api=None, healing_consumes=None, server_name=None):
        Report.__init__(self, report, wcl_api, fig_dir=fig_dir)

        assert healing_consumes is not None, "Please provide a list with healing_consume dataclasses."

        self.consumes = healing_consumes

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

        print()

        self.process_consumes()

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

        bar = tqdm(desc='Reading Event from Warcraftlogs', total=len(consume_list)*len(classes))

        events = []
        for consume in consume_list:
            for game_class in classes:
                resp = self.api.get_report_events('casts', self.id,
                                                    end_time = self.end - self.start,
                                                    abilityid=consume.ability_id,
                                                    sourceclass=game_class)
                events += resp['events']
                bar.update(1)

        events = sorted(events, key=lambda item: item['timestamp'])

        return events

    def process_consumes(self):

        self.assert_instantiated()

        self.healers = {}

        self.total_cost = Price(0)

        for c in self.consume_events:
            c.update({'dateTime' : datetime.fromtimestamp((self.start + c['timestamp'])/1000)})
            c.update({'timeString' : c['dateTime'].strftime(r'%H:%M:%S')})
            c.update({'healer' : self.friendly_names[c['sourceID']]})
            c.update({'fightName' : self.get_fight_name(c)})

            consume = [i for i in self.consumes if i.ability_id == c['ability']['guid']][0]

            c.update({'consume' : consume})
            c.update({'eventString' : f"{c['timeString']} {c['healer']} used a {consume.name} " \
                                            f"during {c['fightName']}"})

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

                self.healers[c['healer']]['amount'] += 1

            else:

                self.healers.update({c['healer'] : {'cost' : consume.cost_price,
                                                    'consumes' : {consume.name : 1},
                                                    'amount' : 1}})

            self.healers[c['healer']].update({'consumeString' :
                                                f"{', '.join([f'{i} x {k}' for k, i in self.healers[c['healer']]['consumes'].items()])}"})

            self.healers[c['healer']].update({'completeString' : f"{c['healer']} : used " \
                                                                    f"{self.healers[c['healer']]['amount']} " \
                                                                    f"consumes for {self.healers[c['healer']]['cost']} " \
                                                                    f"total : " \
                                                                    f"{self.healers[c['healer']]['consumeString']}"})

        self.healers = {h : v for h, v in sorted(self.healers.items(), key=lambda item: item[1]['cost'], reverse=True)}
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
                pass

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