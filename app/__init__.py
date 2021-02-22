import os
import webbrowser
from bs4 import BeautifulSoup
from datetime import datetime
from WCLApi import WCLApi
from app.config import Config
from app.reportpicker import Reportpicker
from app.healing import HealingSaves, HealingSnipes, HealingManaConsumes, HealingTaps, HealerFrags


class Main():

    def __init__(self, config_dir='stored_configs', figures_dir='stored_figures', reports_dir='stored_reports'):
        print("\nLog Reporter\n")
        self.app_dir = os.path.dirname(os.path.realpath(__file__))
        self.config_dir = os.path.join(self.app_dir, config_dir)
        self.figures_dir = os.path.join(self.app_dir, figures_dir)
        self.reports_dir = os.path.join(self.app_dir, reports_dir)
        self.read_configs(self.config_dir)
        self.query_dir = q_d if os.path.isdir(q_d:= os.path.join(self.app_dir, self.wcl_config.content.query_dir)) else None
        self.api = WCLApi(self.wcl_config.content.api_key, query_dir=self.query_dir)
        self.report = Reportpicker(self.wcl_config, api=self.api).pick_loop()

        self.reports = []
        self.reports.append(HealingSaves(self.report,
                                            self.api,
                                            fig_dir=self.figures_dir,
                                            healing_spells=self.healing_spells.content,
                                            full_report=True))

        self.reports.append(HealingSnipes(self.report,
                                            self.api,
                                            fig_dir=self.figures_dir,
                                            healing_spells=self.healing_spells.content,
                                            full_report=True,
                                            fights=self.reports[0].fights,
                                            tanks=self.reports[0].tanks))

        self.reports.append(HealingManaConsumes(self.report,
                                                self.api,
                                                fig_dir=self.figures_dir,
                                                healing_consumes=self.healing_consumes.content,
                                                server_name=self.wcl_config.content.server,
                                                full_report=True))

        self.reports.append(HealingTaps(self.report,
                                        self.api,
                                        fig_dir=self.figures_dir,
                                        healing_spells=self.healing_spells.content,
                                        full_report=True))

        self.reports.append(HealerFrags(self.report,
                                        self.api,
                                        fig_dir=self.figures_dir,
                                        full_report=True))

        self.report_template = self.read_report_template(self.reports_dir, 'healing_report_template.html')

        self.report_path = os.path.join(self.reports_dir, f'healing_report_{self.reports[0].id}.html')

        self.process_report(self.report_template, self.report_path)

        webbrowser.open(f'file://{self.report_path}', new=2)

        print()

    def read_configs(self, config_dir):
        assert os.path.isdir(config_dir), f'The given config folder path is not a directory: {config_dir}'
        self.config_paths = [os.path.join(config_dir, c) for c in os.listdir(config_dir) if os.path.splitext(c)[-1] == '.json']
        for c in self.config_paths:
            config = Config(c)
            self.__setattr__(config.name, config)

    def read_report_template(self, reports_dir, template_name):
        assert os.path.isdir(reports_dir), f'The given reports folder path is not a directory: {reports_dir}'
        if os.path.isfile(template_path:=os.path.join(reports_dir, template_name)):
            with open(template_path, 'r', encoding='utf8') as f:
                return BeautifulSoup(f.read(), "html.parser")

    def process_report(self, report, report_path):
        self.insert_title(report)
        self.insert_reports(report)
        self.save_report(report, report_path)

    def insert_title(self, report):
        if self.reports:
            self.title = self.reports[0].title
            self.date = datetime.fromtimestamp(self.reports[0].start/1000).strftime(r'%a %d %b %Y')
            date_heading = report.find('h2', id='report-title-date')
            date_heading.string = f"{self.title} - {self.date}"

    def insert_reports(self, report):
        if self.reports:
            for rep in self.reports:
                rep.insert_report(report)

    def save_report(self, report, report_path):
        with open(report_path, 'w', encoding='utf8') as f:
            f.write(report.prettify())
