import json
import os
import random
import zipfile


class UserAgent:
    ATTRIBUTES_MAP = {
        'hardware_types': [],
        'software_types': [],
        'software_names': [],
        'software_engines': [],
        'operating_systems': [],
        'popularity': [],
    }

    def __init__(self, limit=None, *args, **kwargs):
        self.user_agents = []

        for attribute, values in self.ATTRIBUTES_MAP.items():
            setattr(self, attribute, kwargs.get(attribute, [v.lower() for v in values]))

        for user_agent in self.load_user_agents():

            if limit is not None and len(self.user_agents) >= limit:
                break

            if self.hardware_types and user_agent['hardware_type'].lower() not in self.hardware_types:
                continue

            if self.software_types and user_agent['software_type'].lower() not in self.software_types:
                continue

            if self.software_names and user_agent['software_name'].lower() not in self.software_names:
                continue

            if self.software_engines and user_agent['software_engine'].lower() not in self.software_engines:
                continue

            if self.operating_systems and user_agent['operating_system'].lower() not in self.operating_systems:
                continue

            if self.popularity and user_agent['popularity'].lower() not in self.popularity:
                continue

            self.user_agents.append(user_agent)

    def load_user_agents(self):
        file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data/user_agents.zip')

        with zipfile.ZipFile(file_path) as zipped_user_agents:
            with zipped_user_agents.open('user_agents.jl') as user_agents:
                for user_agent in user_agents:

                    if hasattr(user_agent, 'decode'):
                        user_agent = user_agent.decode()

                    yield json.loads(user_agent)

    def get_user_agents(self):
        return self.user_agents

    def get_random_user_agent(self):
        return random.choice(self.user_agents)['user_agent']
