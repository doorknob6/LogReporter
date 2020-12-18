from datetime import datetime
from app.report import Report
from tqdm import tqdm
import numpy as np
import plotly.graph_objects as go


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
                                
                                target_name = self.friendly_names[damage['targetID']]
                                damage.update({'targetName' : target_name})
                                fight_name = self.get_fight_name(damage)

                                damage.update({'fightName' : fight_name})

                                fight_str = f"During {fight_name} - "
                                save_amount = 0

                                for save in saves:
                                    save_amount += save['amount']
                                    save.update({'saveDamage' : damage})
                                    save.update({'fightname' : fight_name})
                                    healer = self.friendly_names[save['sourceID']]
                                    save.update({'healerName' : healer})
                                    save.update({'targetName' : target_name})
                                    save.update({'timeString' : datetime.fromtimestamp((self.start + save['timestamp'])/1000).strftime(r'%H:%M:%S')})
                                    save.update({'eventString' : f"{save['timeString']} {healer} saved {target_name} at {damage['hitPoints']}% hp using {save['ability']['name']} for {save['amount']} during {fight_name}"})
                                    if healer in self.save_healers:
                                        self.save_healers[healer].update({'healing amount' : self.save_healers[healer]['healing amount'] + save['amount']})
                                        self.save_healers[healer]['saves'].append(save)
                                        self.save_healers[healer].update({'completeString' : f"{healer} : saved people {len(self.save_healers[healer]['saves'])} times for {self.save_healers[healer]['healing amount']} healing total"})
                                    else:
                                        self.save_healers.update({healer : {'healing amount' : save['amount'], 'saves' : [save]}})
                                        self.save_healers[healer].update({'completeString' : f"{healer} : saved people {len(self.save_healers[healer]['saves'])} times for {self.save_healers[healer]['healing amount']} healing total"})

                                saves_str = ', '.join([f"{s['healerName']} : {s['amount']}" for s in saves])                            
                                damage_string = f"{t_stamp}: {fight_str}Near death of {target_name} with {damage['hitPoints']}% hp saved by {saves_str}"
                                damage.update({'eventString' : damage_string})

                                damage.update({'amount' : save_amount})
                                damage.update({'timeString' : t_stamp})
                                print(damage_string)

        print()

        self.save_healers = {h : v for h, v in sorted(self.save_healers.items(), key=lambda item: len(item[1]['saves']), reverse=True)}

        for healer in self.save_healers:
            print(self.save_healers[healer]['completeString'])

        print('done')

    def get_fight_name(self, event):
        if 'fight' in event:
            if self.fight_names:
                return self.fight_names[event['fight']]
        else:
            if self.fights:
                for fight in self.fights['fights']:
                    if fight['start_time'] <= event['timestamp'] <= fight['end_time']:
                        return fight['name']
        return None

    def make_event_plot(self, events):
        timestamps = np.array([self.start] + [e['timestamp'] for e in events] + [self.end])
        event_vals = np.array([0] + [e['amount'] for e in events] + [0])
        event_strings = np.array([''] + [e['eventString'] for e in events] + [''])
        fig = go.Figure()
        fig.add_trace(go.Bar(x=timestamps, y=event_vals, hovertext=event_strings))
        fig.show()




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