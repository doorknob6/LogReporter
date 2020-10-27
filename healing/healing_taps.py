from WCLApi import WCLApi
import json
import os
from datetime import datetime, timedelta

if __name__ == '__main__':
    try:
        heal_timeout = 3000
        server = 'Nethergarde Keep'
        region = 'EU'
        guild = 'Nerf Inc'
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

        report.update({'start_datetime' : datetime.fromtimestamp(report['start']/1000).strftime('%c')})
        report.update({'end_datetime' : datetime.fromtimestamp(report['end']/1000).strftime('%c')})

        print(f"Reports found for {guild}, {server} ({region})")
        print(f"First report: {report['title']}, uploaded by {report['owner']}")
        print(f"    Start: {report['start_datetime']}")
        print(f"    End:   {report['end_datetime']}")

        fights = Api.get_report_fights(report['id'])

        fight_names = {}
        for fight in fights['fights']:
            fight_names.update({fight['id'] : fight['name']})

        friendlies = fights["friendlies"]
        player_names = {}

        for f in friendlies:
            player_names.update({f["id"] : f["name"]})


        healing_resp = Api.get_report_events('healing', report['id'], end_time = report['end'] - report['start'], targetclass='Warlock')
        healing_events = healing_resp['events']

        tap_resp = Api.get_report_events('casts', report['id'], end_time = report['end'] - report['start'], abilityid=11689)
        tap_events = tap_resp['events']

        tap_heals = []
        for tap in tap_events:
            tap_stamp = tap['timestamp']
            for heal in healing_events:
                if not 'tick' in heal:
                    if tap_stamp <= heal['timestamp'] <= tap_stamp + heal_timeout:
                        tap_heals.append(heal)
                        break

        max_healers = {}
        for heal in tap_heals:
            t_stamp = datetime.fromtimestamp((report['start'] + heal['timestamp'])/1000).strftime(r'%H:%M:%S')
            if 'overheal' in heal:
                heal_amount = heal['amount'] + heal['overheal']
                heal_real = heal['amount']
                heal_over = heal['overheal']
            else:
                heal_amount = heal['amount']
                heal_real = heal_amount
                heal_over = 0

            fight_str = ""
            if 'fight' in heal:
                fight_str = f"During {fight_names[heal['fight']]} - "
            else:
                for fight in fights['fights']:
                    if fight['start_time'] <= heal['timestamp'] <= fight['end_time']:
                        fight_str = f"During {fight['name']} - "
                        break

            print(f"{t_stamp}: {fight_str}{player_names[heal['targetID']]}'s' tap healed for {heal_real}, total heal {heal_amount} and {heal_over} overheal using {heal['ability']['name']} by source: {player_names[heal['sourceID']]} ")

            healer = player_names[heal['sourceID']]
            if healer in max_healers:
                max_healers.update({healer : max_healers[healer] + heal_real})
            else:
                max_healers.update({healer : heal_real})

        print()

        max_healers = {h : v for h, v in sorted(max_healers.items(), key=lambda item: item[1], reverse=True)}

        for healer, value in max_healers.items():
            print(f"{healer} : healed {value} tap damage")

    except:
        import sys
        print(sys.exc_info()[0])
        import traceback
        print(traceback.format_exc())
    finally:
        print()
        input("Press enter to exit")