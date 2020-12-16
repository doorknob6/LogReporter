from WCLApi import WCLApi
from NexusApi import NexusApi, Price
import json
import os
import math
from datetime import datetime, timedelta

def get_consume_prices(consume_list, nexus_server_id):
    CostsApi = NexusApi()

    for consume in consume_list:
        if consume['name'] == 'Dark Rune':
            cost_data = CostsApi.get_items_items(nexus_server_id, consume['itemid'])
            consume.update({'cost_price' : Price(cost_data['stats']['current']['marketValue'])})
            c_2 = [i for i in consume_list if i['name'] == 'Demonic Rune'][0]
            c_2.update({'cost_price' : Price(cost_data['stats']['current']['marketValue'])})
        elif consume['name'] == "Night Dragon's Breath":
            consume.update({'cost_price' : Price(0)})
        elif consume['name'] == 'Demonic Rune':
            pass
        else:
            cost_data = CostsApi.get_items_items(nexus_server_id, consume['itemid'])
            consume.update({'cost_price' : Price(cost_data['stats']['current']['marketValue'])})
        consume.update({'total_cost' : Price(0)})
    return consume_list

#TODO: centralize
def get_fight_names(fights):
    fight_names = {}
    for fight in fights['fights']:
        fight_names.update({fight['id'] : fight['name']})
    return fight_names

def get_player_names(fights):
    friendlies = fights["friendlies"]
    player_names = {}

    for f in friendlies:
        player_names.update({f["id"] : f["name"]})
    return player_names

def get_cast_events(consume_list, classes):
    events = []
    for consume in consume_list:
        for game_class in classes:
            resp = LogsApi.get_report_events('casts', report['id'],
                                                end_time = report['end'] - report['start'],
                                                abilityid=consume['abilityid'],
                                                sourceclass=game_class)
            events += resp['events']

    events = sorted(events, key=lambda item: item['timestamp'])

    return events

if __name__ == '__main__':
    try:
        #TODO: Remove the server // move to stored configs
        server = 'Nethergarde Keep'
        #TODO: Remove the region // move to stored configs
        region = 'EU'
        #TODO: Remove the guild // move to stored configs
        guild = 'Nerf Inc'

        #TODO: Remove the nexus_server_id
        nexus_server_id = 'nethergarde-keep-alliance'

        #TODO: move this to stored configs
        consume_list = [{'abilityid': 27869, 'itemid' : 20520, 'name' : 'Dark Rune', 'amount' : 0},
                        {'abilityid': 16666, 'itemid' : 12662, 'name' : 'Demonic Rune', 'amount' : 0},
                        {'abilityid': 17531, 'itemid' : 13444, 'name' : 'Major Mana Potion', 'amount' : 0},
                        {'abilityid': 17530, 'itemid' : 13443, 'name' : 'Superior Mana Potion', 'amount' : 0},
                        {'abilityid': 11903, 'itemid' : 6149, 'name' : 'Greater Mana Potion', 'amount' : 0},
                        {'abilityid': 15701, 'itemid' : 11952, 'name' : "Night Dragon's Breath", 'amount' : 0}]

        #TODO: Move this as a choosable var
        classes = ['Priest', 'Druid', 'Paladin']

        #TODO: Remove the api_key // move to stored configs
        api_key = "4819a49d98df207962535387d1b699a1"

        consume_list = get_consume_prices(consume_list, nexus_server_id)

        #TODO: report retrieval
        LogsApi = WCLApi(api_key)
        reports = LogsApi.get_guild_reports(server, region, guild)

        report = reports[0]

        report.update({'start_datetime' : datetime.fromtimestamp(report['start']/1000).strftime('%c')})
        report.update({'end_datetime' : datetime.fromtimestamp(report['end']/1000).strftime('%c')})

        print(f"Reports found for {guild}, {server} ({region})")
        print(f"First report: {report['title']}, uploaded by {report['owner']}")
        print(f"    Start: {report['start_datetime']}")
        print(f"    End:   {report['end_datetime']}")

        fights = LogsApi.get_report_fights(report['id'])

        fight_names = get_fight_names(fights)

        player_names = get_player_names(fights)

        events = get_cast_events(consume_list, classes)

        print()

        consumes = {}
        healers = {}
        total_cost = Price(0)
        for c in events:
            t_stamp = datetime.fromtimestamp((report['start'] + c['timestamp'])/1000).strftime(r'%H:%M:%S')
            healer = player_names[c['sourceID']]
            consume = [i for i in consume_list if i['abilityid'] == c['ability']['guid']][0]

            if 'amount' in consume:
                consume.update({'amount' : consume['amount'] + 1})
            else:
                consume.update({'amount' : 1})
            consume.update({'total_cost' : Price(consume['amount'] * consume['cost_price'])})

            total_cost = Price(total_cost + consume['cost_price'])

            fight_str = ""
            if 'fight' in c:
                fight_str = f"During {fight_names[c['fight']]} - "
            else:
                for fight in fights['fights']:
                    if fight['start_time'] <= c['timestamp'] <= fight['end_time']:
                        fight_str = f"During {fight['name']} - "
                        break

            print(f"{t_stamp}: {fight_str}{healer} used a {consume['name']}")

            if healer in healers:
                if consume['name'] in healers[healer]:
                    healers[healer].update({consume['name'] : healers[healer][consume['name']] + 1})
                else:
                    healers[healer].update({consume['name'] : 1})
            else:
                healers.update({healer : {consume['name'] : 1}})

            if 'total_cost' in healers[healer]:
                healers[healer].update({'total_cost' : Price(healers[healer]['total_cost'] + consume['cost_price'])})
            else:
                healers[healer].update({'total_cost' : consume['cost_price']})

        print()

        consume_list = sorted(consume_list, key=lambda item: item['total_cost'], reverse=True)

        for c in consume_list:
            print(f"{c['name']} : {c['amount']} x {c['cost_price'].g}g {c['cost_price'].s}s {c['cost_price'].c}c = " \
                    f"{c['total_cost'].g}g {c['total_cost'].s}s {c['total_cost'].c}c")

        print()

        print(f"Total raid mana consumables cost: {total_cost.g}g {total_cost.s}s {total_cost.c}c")

        print()

        healers = {h : v for h, v in sorted(healers.items(), key=lambda item: item[1]['total_cost'].price, reverse=True)}

        for healer, value in healers.items():
            c_str = ''
            for c, n in value.items():
                if 'total' not in c:
                    if c_str:
                        c_str += f", {n} {c}"
                    else:
                        c_str += f"{n} {c}"
            print(f"{healer} : took {c_str} for a total of {value['total_cost'].g}g {value['total_cost'].s}s {value['total_cost'].c}c")
    except:
        import sys
        print(sys.exc_info()[0])
        import traceback
        print(traceback.format_exc())
    finally:
        print()
        input("Press enter to exit")