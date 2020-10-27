from WCLApi import WCLApi
import json
import os
from datetime import datetime, timedelta

def get_target_id(event):
    if 'targetID' in event:
        return event['targetID']
    if 'target' in event:
        if 'id' in event['target']:
            return event['target']['id']

if __name__ == '__main__':
    try:
        near_death_percentage = 15
        death_timeout = 8000
        heal_timeout = 3000
        heal_treshold = 900

        server = 'Nethergarde Keep'
        region = 'EU'
        guild = 'Nerf Inc'
        api_key = ''
        
        dir_name = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(dir_name, 'wcl_clients.json')) as f:
            wcl_clients = json.load(f)
            for client in wcl_clients:
                if client["api_version"] == 1:
                    api_key = client["api_key"]
                    break

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

        fight_names = {}
        for fight in fights['fights']:
            fight_names.update({fight['id'] : fight['name']})

        friendlies = fights["friendlies"] + fights['friendlyPets']

        friendly_names = {}

        for f in friendlies:
            friendly_names.update({f["id"] : f["name"]})

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