import os
import json
from ajb.base import ParentRepository, RepositoryRegistry, Collection
from .models import StaticData, CreateStaticData, StaticDataTypes


class StaticDataRepository(ParentRepository[CreateStaticData, StaticData]):
    collection = Collection.STATIC_DATA
    entity_model = StaticData
    search_fields = ("name",)

    def _get_default_file_data(self, file_name: str):
        file_path = os.path.join(
            os.path.dirname(__file__), f"defaults/{file_name}.json"
        )
        with open(file_path) as f:
            benefits = json.load(f)
        return benefits

    def load_default_data(self):
        for data_type in StaticDataTypes:
            default_data = self._get_default_file_data(data_type.value)
            for data in default_data:
                self.upsert(
                    CreateStaticData(**data, type=data_type), overridden_id=data["id"]
                )


RepositoryRegistry.register(StaticDataRepository)
