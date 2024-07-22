from migrations.base import MIGRATION_REQUEST_SCOPE

from ajb.base import BaseUseCase
from ajb.contexts.billing.discount_codes.repository import (
    DiscountCodeRepository,
    CreateDiscountCode,
)


class CreateAppSumoCodesMigration(BaseUseCase):
    def generate_codes_csv(self, num_codes: int = 1000):
        repo = DiscountCodeRepository(self.request_scope)
        codes = []
        for _ in range(num_codes):
            codes.append(repo.create(CreateDiscountCode.generate_code()))

        with open("codes_internal.csv", "w") as f:
            f.write("code\n")
            for code in codes:
                f.write(f"{code.code}\n")


if __name__ == "__main__":
    CreateAppSumoCodesMigration(MIGRATION_REQUEST_SCOPE).generate_codes_csv(num_codes=5)
