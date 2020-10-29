from WCLApi import WCLApi
import json
import os
from datetime import datetime, timedelta

#TODO: move to stored_configs only
healing_spells = [
{ "spell_id" : 10917, "name" : "Flash Heal (Rank 7)", "duration" : 1500 },
{ "spell_id" : 10916, "name" : "Flash Heal (Rank 6)", "duration" : 1500 },
{ "spell_id" : 10915, "name" : "Flash Heal (Rank 5)", "duration" : 1500 },
{ "spell_id" : 9474, "name" : "Flash Heal (Rank 4)", "duration" : 1500 },
{ "spell_id" : 9473, "name" : "Flash Heal (Rank 3)", "duration" : 1500 },
{ "spell_id" : 9472, "name" : "Flash Heal (Rank 2)", "duration" : 1500 },
{ "spell_id" : 2061, "name" : "Flash Heal (Rank 1)", "duration" : 1500 },
{ "spell_id" : 2050, "name" : "Lesser Heal (Rank 1)", "duration" : 1500 },
{ "spell_id" : 2052, "name" : "Lesser Heal (Rank 2)", "duration" : 2000 },
{ "spell_id" : 2053, "name" : "Lesser Heal (Rank 3)", "duration" : 2500 },
{ "spell_id" : 25314, "name" : "Greater Heal (Rank 5)", "duration" : 2500 },

{ "spell_id" : 10965, "name" : "Greater Heal (Rank 4)", "duration" : 2500 },
{ "spell_id" : 10964, "name" : "Greater Heal (Rank 3)", "duration" : 2500 },
{ "spell_id" : 10963, "name" : "Greater Heal (Rank 2)", "duration" : 2500 },
{ "spell_id" : 2060, "name" : "Greater Heal (Rank 1)", "duration" : 2500 },
{ "spell_id" : 6064, "name" : "Heal (Rank 4)", "duration" : 2500 },
{ "spell_id" : 6063, "name" : "Heal (Rank 3)", "duration" : 2500 },
{ "spell_id" : 2055, "name" : "Heal (Rank 2)", "duration" : 2500 },
{ "spell_id" : 2054, "name" : "Heal (Rank 1)", "duration" : 2500 },

{ "spell_id" : 5185, "name" : "Healing Touch (Rank 1)", "duration" : 1000 },
{ "spell_id" : 5186, "name" : "Healing Touch (Rank 2)", "duration" : 1500 },
{ "spell_id" : 5187, "name" : "Healing Touch (Rank 3)", "duration" : 2000 },
{ "spell_id" : 5188, "name" : "Healing Touch (Rank 4)", "duration" : 2500 },
{ "spell_id" : 5189, "name" : "Healing Touch (Rank 5)", "duration" : 3000 },
{ "spell_id" : 6778, "name" : "Healing Touch (Rank 6)", "duration" : 3000 },
{ "spell_id" : 8903, "name" : "Healing Touch (Rank 7)", "duration" : 3000 },
{ "spell_id" : 9758, "name" : "Healing Touch (Rank 8)", "duration" : 3000 },
{ "spell_id" : 9888, "name" : "Healing Touch (Rank 9)", "duration" : 3000 },
{ "spell_id" : 9889, "name" : "Healing Touch (Rank 10)", "duration" : 3000 },
{ "spell_id" : 25297, "name" : "Healing Touch (Rank 10)", "duration" : 3000 },
{ "spell_id" : 8936, "name" : "Regrowth (Rank 1)", "duration" : 2000 },
{ "spell_id" : 8938, "name" : "Regrowth (Rank 2)", "duration" : 2000 },
{ "spell_id" : 8939, "name" : "Regrowth (Rank 3)", "duration" : 2000 },
{ "spell_id" : 8940, "name" : "Regrowth (Rank 4)", "duration" : 2000 },
{ "spell_id" : 8941, "name" : "Regrowth (Rank 5)", "duration" : 2000 },
{ "spell_id" : 9750, "name" : "Regrowth (Rank 6)", "duration" : 2000 },
{ "spell_id" : 9856, "name" : "Regrowth (Rank 7)", "duration" : 2000 },
{ "spell_id" : 9857, "name" : "Regrowth (Rank 8)", "duration" : 2000 },
{ "spell_id" : 9858, "name" : "Regrowth (Rank 9)", "duration" : 2000 },

{ "spell_id" : 635, "name" : "Holy Light (Rank 1)", "duration" : 2500 },
{ "spell_id" : 639, "name" : "Holy Light (Rank 2)", "duration" : 2500 },
{ "spell_id" : 647, "name" : "Holy Light (Rank 3)", "duration" : 2500 },
{ "spell_id" : 1026, "name" : "Holy Light (Rank 4)", "duration" : 2500 },
{ "spell_id" : 1042, "name" : "Holy Light (Rank 5)", "duration" : 2500 },
{ "spell_id" : 3472, "name" : "Holy Light (Rank 6)", "duration" : 2500 },
{ "spell_id" : 10328, "name" : "Holy Light (Rank 7)", "duration" : 2500 },
{ "spell_id" : 10329, "name" : "Holy Light (Rank 8)", "duration" : 2500 },
{ "spell_id" : 25292, "name" : "Holy Light (Rank 9)", "duration" : 2500 },
{ "spell_id" : 19968, "name" : "Holy Light (Rank 9)", "duration" : 2500 },
{ "spell_id" : 19750, "name" : "Flash of Light (Rank 1)", "duration" : 1500 },
{ "spell_id" : 19939, "name" : "Flash of Light (Rank 2)", "duration" : 1500 },
{ "spell_id" : 19940, "name" : "Flash of Light (Rank 3)", "duration" : 1500 },
{ "spell_id" : 19941, "name" : "Flash of Light (Rank 4)", "duration" : 1500 },
{ "spell_id" : 19942, "name" : "Flash of Light (Rank 5)", "duration" : 1500 },
{ "spell_id" : 19943, "name" : "Flash of Light (Rank 6)", "duration" : 1500 },
{ "spell_id" : 19993, "name" : "Flash of Light (Rank 6)", "duration" : 1500 },
{ "spell_id" : 20473, "name" : "Holy Shock (Rank 1)", "duration" : 0 },
{ "spell_id" : 25912, "name" : "Holy Shock (Rank 1)", "duration" : 0 },
{ "spell_id" : 25914, "name" : "Holy Shock (Rank 1)", "duration" : 0 },
{ "spell_id" : 20929, "name" : "Holy Shock (Rank 2)", "duration" : 0 },
{ "spell_id" : 25911, "name" : "Holy Shock (Rank 2)", "duration" : 0 },
{ "spell_id" : 25913, "name" : "Holy Shock (Rank 2)", "duration" : 0 },
{ "spell_id" : 20930, "name" : "Holy Shock (Rank 3)", "duration" : 0 },
{ "spell_id" : 25902, "name" : "Holy Shock (Rank 3)", "duration" : 0 },
{ "spell_id" : 25903, "name" : "Holy Shock (Rank 3)", "duration" : 0 }
]

def make_spells(healing_spells):
    spells = {}
    for spell in healing_spells:
        spells.update({spell['spell_id'] : {'name' : spell['name'], 'duration' : spell['duration']}})
    return spells

def get_target_id(event):
    if 'targetID' in event:
        return event['targetID']
    if 'target' in event:
        if 'id' in event['target']:
            return event['target']['id']

if __name__ == '__main__':
    try:
        #TODO: Input parameters
        snipe_timeout = 400
        snipe_threshold = 700
        overhealing_treshold = 500

        #TODO: Remove the server // move to stored configs
        server = 'Nethergarde Keep'
        #TODO: Remove the region // move to stored configs
        region = 'EU'
        #TODO: Remove the guild // move to stored configs
        guild = 'Nerf Inc'
        #TODO: Remove the api_key // move to stored configs
        api_key = "4819a49d98df207962535387d1b699a1"

        #TODO: centralize report retrieval
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


        healing_resp = Api.get_report_events('healing', report['id'], end_time = report['end'] - report['start'])
        healing_events = healing_resp['events']

        spells = make_spells(healing_spells)

        max_snipers = {}
        max_sniped = {}

        snipe_heals = []
        for base_heal, n in zip(healing_events, range(len(healing_events))):

            if n - 50 < 0:
                n_0 = 0
            else:
                n_0 = n - 50
            if n_0 + 50 > len(healing_events):
                n_1 = len(healing_events)
            else:
                n_1 = n_0 + 50

            if not 'tick' in base_heal and 'overheal' in base_heal:
                base_stamp = base_heal['timestamp']
                if base_heal['ability']['guid'] in spells and base_heal['overheal'] > overhealing_treshold:
                    base_duration = spells['ability']['guid']['duration']

                    snipes = [h for h in healing_events[n_0:n_1]
                                if h['ability']['guid'] in spells and
                                get_target_id(h) == get_target_id(base_heal) and
                                h['amount'] > snipe_threshold and
                                'overheal' in h and
                                base_stamp - base_duration + snipe_timeout + spells[h['ability']['guid']]['duration'] <= h['timestamp'] <= base_stamp and
                                not base_heal['sourceID'] == h['sourceID']]
                    snipes = [h for h in snipes if h['amount'] < base_heal['overheal']]
                    if snipes:
                        base_heal.update({'snipes' : snipes})
                        snipe_heals.append(base_heal)
                        fight_str = ""

                        if 'fight' in base_heal:
                            fight_str = f"During {fight_names[base_heal['fight']]} - "
                        else:
                            for fight in fights['fights']:
                                if fight['start_time'] <= base_heal['timestamp'] <= fight['end_time']:
                                    fight_str = f"During {fight['name']} - "
                                    break

                        sniped = player_names[base_heal['sourceID']]

                        sniped_applied = False
                        for snipe in snipes:
                            t_stamp = datetime.fromtimestamp((report['start'] + snipe['timestamp'])/1000).strftime(r'%H:%M:%S.%f')
                            sniper = player_names[snipe['sourceID']]
                            snipe_overheal_str = ''
                            snipe_overheal_str = f"with {snipe['overheal']} overheal "

                            print(f"{t_stamp}: {fight_str}{sniped}'s {base_heal['ability']['name']} sniped by {sniper} for {snipe['amount']} {snipe_overheal_str}using {snipe['ability']['name']} causing {snipe['amount']} extra overhealing.")

                            if sniper in max_snipers:
                                max_snipers.update({sniper : [max_snipers[sniper][0] + snipe['amount'], max_snipers[sniper][1] + snipe['amount'], max_snipers[sniper][2] + 1]})
                            else:
                                max_snipers.update({sniper : [snipe['amount'], base_heal['amount'] + snipe['amount'], 1]})

                            if sniped_applied:
                                max_sniped.update({sniped : [max_sniped[sniped][0] + snipe['amount'], max_sniped[sniped][1], max_sniped[sniped][2] + 1]})
                            else:
                                if sniped in max_sniped:
                                    max_sniped.update({sniped : [max_sniped[sniped][0] + snipe['amount'], max_sniped[sniped][1] + snipe['amount'], max_sniped[sniped][2] + 1]})
                                else:
                                    max_sniped.update({sniped : [snipe['amount'], snipe['amount'], 1]})

                            sniped_applied = True

        max_snipers = {h : v for h, v in sorted(max_snipers.items(), key=lambda item: item[1][2], reverse=True)}
        max_sniped = {h : v for h, v in sorted(max_sniped.items(), key=lambda item: item[1][2], reverse=True)}

        print()
        for sniper, value in max_snipers.items():
            print(f"{sniper} : Sniped {value[2]} times for {value[0]} healing total, causing {value[1]} extra overhealing.")

        print()
        for sniped, value in max_sniped.items():
            print(f"{sniped} : Got sniped {value[2]} times for {value[0]} healing total, causing {value[1]} extra overhealing.")

    except:
        import sys
        print(sys.exc_info()[0])
        import traceback
        print(traceback.format_exc())
    finally:
        print()
        input("Press enter to exit")