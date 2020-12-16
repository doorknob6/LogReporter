from dataclasses import dataclass


@dataclass
class wcl_config:
    """Class containing the data for a Warcraftlogs Client"""
    name: str
    api_key: str
    query_dir: str
    region: str
    server: str
    guild: str

@dataclass
class healing_consume:
    """Class containing the data for a healing consume"""
    name: str
    item_id: int
    ability_id: int

@dataclass
class healing_spell:
    """Class containing the data for a healing spell"""
    name: str
    spell_id: int
    duration: int

config_mapping = {"wcl_config" : wcl_config,
                  "healing_consumes" : healing_consume,
                  "healing_spells" : healing_spell}