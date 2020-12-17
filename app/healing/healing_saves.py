from WCLApi import WCLApi
import json
import os
from datetime import datetime, timedelta
from app.report import Report
from tqdm import tqdm

class HealingSaves(Report):

    def __init__(self, report, api):
        Report.__init__(self, report, api)

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
        self.heal_treshold = self.get_input("heal treshold", 900, 'hp')

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
                            t_stamp = datetime.fromtimestamp((self.start + damage['timestamp'])/1000).strftime(r'%H:%M:%S')

                            saves = [h for h in self.healing_events if self.get_target_id(h) == self.get_target_id(damage) and
                                        damage['timestamp'] <= h['timestamp'] <= damage['timestamp'] + self.heal_timeout and
                                        not 'overheal' in h and
                                        h['amount'] > self.heal_treshold]

                            if saves:

                                damage.update({'saves' : saves})
                                self.near_deaths.append(damage)

                                for save in saves:
                                    healer = self.friendly_names[save['sourceID']]
                                    if healer in self.save_healers:
                                        self.save_healers[healer].update({'healing amount' : self.save_healers[healer]['healing amount'] + save['amount']})
                                        self.save_healers[healer]['saves'].append(save)
                                    else:
                                        self.save_healers.update({healer : {'healing amount' : save['amount'],
                                                                            'saves' : [save]}})

                                saves_str = ', '.join([f"{self.friendly_names[s['sourceID']]} : {s['amount']}" for s in saves])
                                fight_str = ""

                                if 'fight' in damage:
                                    fight_str = f"During {self.fight_names[damage['fight']]} - "
                                else:
                                    for fight in self.fights['fights']:
                                        if fight['start_time'] <= damage['timestamp'] <= fight['end_time']:
                                            fight_str = f"During {fight['name']} - "
                                            break

                                damage_string = f"{t_stamp}: {fight_str}Near death of {self.friendly_names[damage['targetID']]} with {damage['hitPoints']}% hp saved by {saves_str}"
                                damage.update({'eventString' : damage_string})
                                damage.update({'timeString' : t_stamp})
                                print(damage_string)

        print()

        self.save_healers = {h : v for h, v in sorted(self.save_healers.items(), key=lambda item: len(item[1]['saves']), reverse=True)}

        for healer, value in self.save_healers.items():
            print(f"{healer} : saved people {len(value['saves'])} times for {value['healing amount']} healing total")

        print('done')

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