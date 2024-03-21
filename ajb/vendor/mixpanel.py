from mixpanel import Mixpanel
from ajb.config.settings import SETTINGS


class MixpanelService:
    def __init__(self):
        self.mp: Mixpanel | None = None
        if SETTINGS.MIXPANEL_TOKEN:
            self.mp = Mixpanel(SETTINGS.MIXPANEL_TOKEN)

    def track(self, company_id: str, user_id: str, event: str, properties: dict):
        properties["company_id"] = company_id
        if self.mp:
            self.mp.track(user_id, event, properties)

    def update_user_profile(self, user_id: str, properties: dict):
        if self.mp:
            self.mp.people_set(user_id, properties)

    def update_company_profile(self, company_id: str, properties: dict):
        if self.mp:
            self.mp.group_set(group_key="company_id", group_id=company_id, properties=properties)
