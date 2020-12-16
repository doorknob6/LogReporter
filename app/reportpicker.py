import os
import re
from datetime import datetime
from WCLApi import WCLApi

class Reportpicker():

    def __init__(self, wcl_config, api=None):

        self.config = wcl_config
        if api:
            self.api= api
        else:
            query_dir = q_d if os.path.isdir(q_d:= os.path.join(os.path.dirname(os.path.realpath(__file__)), wcl_config.content.query_dir)) else None
            self.api = WCLApi(wcl_config.content.api_key, query_dir=query_dir)

    def pick_loop(self):
        report = ''
        while True:
            if self.config.content.region:
                i = input(f'Input Region [Enter to accept]: {self.config.content.region} : ')
                input_region = i if i else self.config.content.region
            else:
                input_region = input('Input Region: ')
            if input_region in ('US', 'EU', 'KR', 'TW', 'CN'):
                self.config.content.region = input_region
                if self.config.content.server:
                    i = input(f'Input Server [Enter to accept]: {self.config.content.server} : ')
                    input_server = i if i else self.config.content.server
                else:
                    input_server = input('Input Server: ')
                if input_server:
                    self.config.content.server = input_server
                    if self.config.content.guild:
                        i =input(f'Input Guild [Enter to accept]: {self.config.content.guild} : ')
                        input_guild = i if i else self.config.content.guild
                    else:
                        input_guild = input('Input Guild: ')
                    if input_guild:
                        self.config.content.guild = input_guild
                        print('\n\tObtaining reports ...')
                        try:
                            reports = self.api.get_guild_reports(input_server, input_region, input_guild)
                            self.config.dump_json()
                            print('\nReports obtained:')
                            n = 15
                            while True:
                                print(f'\t[num]\t[     date      ]\t[       id       ]\t[        title         ]')
                                for report, i in zip(reports[:n], range(1, n)):
                                    line = f'\t[{i:>3}]\t'
                                    line += f" {datetime.fromtimestamp(report['start']/1000).strftime(r'%Y %a %d %b')} \t"
                                    line += f" {report['id']} \t"
                                    line += f" {report['title']}"
                                    print(line)
                                while True:
                                    num_sel = int(input('\nSelect a report number or choose a higher number of reports to be listed [int]: '))
                                    if num_sel:
                                        if num_sel < n:
                                            report = reports[num_sel - 1]
                                            print('\nReport selected: ')
                                            line = f'\t[{num_sel:>3}]\t'
                                            line += f" {datetime.fromtimestamp(report['start']/1000).strftime(r'%Y %a %d %b')} \t"
                                            line += f" {report['id']} \t"
                                            line += f" {report['title']}"
                                            print(line)
                                            return report
                                        else:
                                            n = num_sel + 1
                                            break
                        except:
                            import sys
                            print(sys.exc_info()[0])
                            import traceback
                            print(traceback.format_exc())
                        finally:
                            print()
                            if not report:
                                input("Press enter to re-check the entries")