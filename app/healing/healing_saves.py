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

        self.inputs()

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

                                for s in saves:
                                    healer = self.friendly_names[s['sourceID']]
                                    if healer in self.save_healers:
                                        self.save_healers.update({healer : [self.save_healers[healer][0] + s['amount'], self.save_healers[healer][1] + 1]})
                                    else:
                                        self.save_healers.update({healer : [s['amount'], 1]})

                                saves_str = ', '.join([f"{self.friendly_names[s['sourceID']]} : {s['amount']}" for s in saves])
                                fight_str = ""
                                if 'fight' in damage:
                                    fight_str = f"During {self.fight_names[damage['fight']]} - "
                                else:
                                    for fight in self.fights['fights']:
                                        if fight['start_time'] <= damage['timestamp'] <= fight['end_time']:
                                            fight_str = f"During {fight['name']} - "
                                            break
                                print(f"{t_stamp}: {fight_str}Near death of {self.friendly_names[damage['targetID']]} with {damage['hitPoints']}% hp saved by {saves_str}")

        print()

        self.save_healers = {h : v for h, v in sorted(self.save_healers.items(), key=lambda item: item[1][1], reverse=True)}

        for healer, value in self.save_healers.items():
            print(f"{healer} : saved people {value[1]} times for {value[0]} healing total")

    def inputs(self):
        print()
        while True:
            i = input("Input near death percentage [Enter to Accept]: 15%   : ")
            if i:
                i = int(i.strip('%'))
                if 0 < i < 100:
                    self.near_death_percentage = i
                    break
            else:
                self.near_death_percentage = 15
                break
        while True:
            i = input("Input death timeout         [Enter to Accept]: 8s    : ")
            if i:
                i = int(i.strip('s'))
                if i > 0:
                    self.death_timeout = int(i*1000)
                    break
            else:
                self.death_timeout = 8000
                break
        while True:
            i = input("Input heal timeout          [Enter to Accept]: 3s    : ")
            if i:
                i = int(i.strip('s'))
                if i > 0:
                    self.heal_timeout = int(i*1000)
                    break
            else:
                self.heal_timeout = 3000
                break
        while True:
            i = input("Input heal treshold         [Enter to Accept]: 900hp : ")
            if i:
                i = int(i.strip('hp'))
                if i > 0:
                    self.heal_treshold = i
                    break
            else:
                self.heal_treshold = 900
                break

#TODO: centralize
def get_fight_names(fights):
    fight_names = {}
    for fight in fights['fights']:
        fight_names.update({fight['id'] : fight['name']})
    return fight_names

#TODO: centralize
def get_friendly_names(fights):
    friendlies = fights["friendlies"] + fights['friendlyPets']
    friendly_names = {}

    for f in friendlies:
        friendly_names.update({f["id"] : f["name"]})
    return friendly_names

def get_target_id(event):
    if 'targetID' in event:
        return event['targetID']
    if 'target' in event:
        if 'id' in event['target']:
            return event['target']['id']

if __name__ == '__main__':
    try:
        #TODO: input variables
        near_death_percentage = 15
        death_timeout = 8000
        heal_timeout = 3000
        heal_treshold = 900

        #TODO: Remove the server // move to stored configs
        server = 'Nethergarde Keep'
        #TODO: Remove the region // move to stored configs
        region = 'EU'
        #TODO: Remove the guild // move to stored configs
        guild = 'Nerf Inc'
        #TODO: Remove the api_key // move to stored configs
        api_key = "4819a49d98df207962535387d1b699a1"

        #TODO: report retrieval
        Api = WCLApi(api_key)
        reports = Api.get_guild_reports(server, region, guild)

        report = reports[0]

        report.update({'start_datetime' : datetime.fromtimestamp(report['start']/1000).strftime(r'%Y %a %d %b %H:%M:%S')})
        report.update({'end_datetime' : datetime.fromtimestamp(report['end']/1000).strftime(r'%Y %a %d %b %H:%M:%S')})

        print(f"Reports found for {guild}, {server} ({region})")
        print(f"First report: {report['title']}, uploaded by {report['owner']}")
        print(f"    Start: {report['start_datetime']}")
        print(f"    End:   {report['end_datetime']}")

        fights = Api.get_report_fights(report['id'])

        fight_names = get_fight_names(fights)

        friendly_names = get_friendly_names(fights)

        healing_resp = Api.get_report_events('healing', report['id'], end_time = report['end'] - report['start'])

        healing_events = healing_resp['events']

        damage_resp = Api.get_report_events('damage-taken', report['id'], end_time = report['end'] - report['start'])

        damage_events = damage_resp['events']

        death_resp = Api.get_report_events('deaths', report['id'], end_time = report['end'] - report['start'])

        death_events = death_resp['events']

        near_deaths = []
        saves = []
        save_healers = {}

        for damage in damage_events:
            if 'hitPoints' in damage:
                if damage['hitPoints'] < near_death_percentage:
                    prev_damage = [d for d in near_deaths if get_target_id(d) == get_target_id(damage) and
                                                            damage['timestamp'] - heal_timeout <= d['timestamp'] <= damage['timestamp']]
                    if not prev_damage:
                        death = [d for d in death_events if get_target_id(d) == get_target_id(damage) and
                                                            damage['timestamp'] <= d['timestamp'] <= damage['timestamp'] + death_timeout]
                        if not death:
                            t_stamp = datetime.fromtimestamp((report['start'] + damage['timestamp'])/1000).strftime(r'%H:%M:%S')
                            saves = [h for h in healing_events if get_target_id(h) == get_target_id(damage) and
                                                                    damage['timestamp'] <= h['timestamp'] <= damage['timestamp'] + heal_timeout and
                                                                    not 'overheal' in h and
                                                                    h['amount'] > heal_treshold]
                            if saves:
                                damage.update({'saves' : saves})
                                near_deaths.append(damage)

                                for s in saves:
                                    healer = friendly_names[s['sourceID']]
                                    if healer in save_healers:
                                        save_healers.update({healer : [save_healers[healer][0] + s['amount'], save_healers[healer][1] + 1]})
                                    else:
                                        save_healers.update({healer : [s['amount'], 1]})

                                saves_str = ', '.join([f"{friendly_names[s['sourceID']]} : {s['amount']}" for s in saves])
                                fight_str = ""
                                if 'fight' in damage:
                                    fight_str = f"During {fight_names[damage['fight']]} - "
                                else:
                                    for fight in fights['fights']:
                                        if fight['start_time'] <= damage['timestamp'] <= fight['end_time']:
                                            fight_str = f"During {fight['name']} - "
                                            break
                                print(f"{t_stamp}: {fight_str}Near death of {friendly_names[damage['targetID']]} with {damage['hitPoints']}% hp saved by {saves_str}")

        print()

        save_healers = {h : v for h, v in sorted(save_healers.items(), key=lambda item: item[1][1], reverse=True)}

        for healer, value in save_healers.items():
            print(f"{healer} : saved people {value[1]} times for {value[0]} healing total")

    except:
        import sys
        print(sys.exc_info()[0])
        import traceback
        print(traceback.format_exc())
    finally:
        print()
        input("Press enter to exit")