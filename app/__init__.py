import os
import webbrowser
from WCLApi import WCLApi
from app.config import Config
from app.reportpicker import Reportpicker
from app.healing import HealingSaves, HealingSnipes, HealingManaConsumes, HealingTaps, HealerFrags


class Main():

    def __init__(self, config_dir='stored_configs', figures_dir='stored_figures'):
        print("\nLog Reporter\n")
        self.app_dir = os.path.dirname(os.path.realpath(__file__))
        self.config_dir = os.path.join(self.app_dir, config_dir)
        self.figures_dir = os.path.join(self.app_dir, figures_dir)
        self.read_configs(self.config_dir)
        self.query_dir = q_d if os.path.isdir(q_d:= os.path.join(self.app_dir, self.wcl_config.content.query_dir)) else None
        self.api = WCLApi(self.wcl_config.content.api_key, query_dir=self.query_dir)
        self.report = Reportpicker(self.wcl_config, api=self.api).pick_loop()

        self.healing_saves = HealingSaves(self.report,
                                            self.api,
                                            fig_dir=self.figures_dir,
                                            healing_spells=self.healing_spells.content,
                                            full_report=True)

        self.healing_snipes = HealingSnipes(self.report,
                                            self.api,
                                            fig_dir=self.figures_dir,
                                            healing_spells=self.healing_spells.content,
                                            full_report=True)

        self.healing_mana_consumes = HealingManaConsumes(self.report,
                                                            self.api,
                                                            fig_dir=self.figures_dir,
                                                            healing_consumes=self.healing_consumes.content,
                                                            server_name=self.wcl_config.content.server,
                                                            full_report=True)

        self.tap_heals = HealingTaps(self.report,
                                        self.api,
                                        fig_dir=self.figures_dir,
                                        healing_spells=self.healing_spells.content,
                                        full_report=True)

        self.healer_frags = HealerFrags(self.report,
                                        self.api,
                                        fig_dir=self.figures_dir,
                                        full_report=True)

        # self.report_path = os.path.join(self.figures_dir, f'healing_report_{self.healing_snipes.id}.html')
        # with open(self.report_path, 'a') as f:
        #     f.write(self.healing_saves.plot.to_html(full_html=False, include_plotlyjs='cdn'))
        #     f.write(self.healing_snipes.plot.to_html(full_html=False, include_plotlyjs='cdn'))
        #     f.write(self.healing_mana_consumes.plot.to_html(full_html=False, include_plotlyjs='cdn'))
        #     f.write(self.tap_heals.plot.to_html(full_html=False, include_plotlyjs='cdn'))

        # webbrowser.open(f'file://{self.report_path}', new=2)

        print()

    def read_configs(self, config_dir):
        assert os.path.isdir(config_dir), f'The given config folder path is not a directory: {config_dir}'
        self.config_paths = [os.path.join(config_dir, c) for c in os.listdir(config_dir) if os.path.splitext(c)[-1] == '.json']
        for c in self.config_paths:
            config = Config(c)
            self.__setattr__(config.name, config)