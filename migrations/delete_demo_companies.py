from ajb.base import BaseUseCase, Collection

from migrations.base import MIGRATION_REQUEST_SCOPE


class DeleteDemoCompanyUseCase(BaseUseCase):
    def delete_company_sub_entities(self, company_id: str, dry_run: bool = True):
        collection_list = [
            Collection.COMPANY_RECRUITERS,
            Collection.RECRUITER_INVITATIONS,
            Collection.JOBS,
            Collection.APPLICATIONS,
            Collection.APPLICATION_RECRUITER_UPDATES,
            Collection.RESUMES,
            Collection.COMPANY_NOTIFICATIONS,
            Collection.COMPANY_EMAIL_INGRESS_WEBHOOKS,
            Collection.COMPANY_API_EGRESS_WEBHOOKS,
            Collection.COMPANY_API_INGRESS_WEBHOOKS,
            Collection.RAW_INGRESS_APPLICATIONS,
        ]
        for collection in collection_list:
            print(f"Deleting all records in collection: {collection}")
            repo = self.get_repository(collection)
            all_company_records = repo.get_all(company_id=company_id)
            print(f"Found {len(all_company_records)} records to delete")
            for record_batch in range(0, len(all_company_records), 10):
                batch_ids = [
                    record.id
                    for record in all_company_records[record_batch : record_batch + 10]
                ]
                if not dry_run:
                    repo.delete_many(batch_ids)

    def delete_company(self, company_id: str, dry_run: bool = True):
        company_repo = self.get_repository(Collection.COMPANIES)
        company_repo.get(company_id)  # To check if it doesnt exist already
        self.delete_company_sub_entities(company_id, dry_run)
        if not dry_run:
            company_repo.delete(company_id)
        print(f"Company {company_id} deleted successfully")

    def delete_via_cli(self, dry_run: bool = True):
        company_repo = self.get_repository(Collection.COMPANIES)
        all_companies = company_repo.get_all()
        print(f"Starting number of companies: {len(all_companies)}")
        for company in all_companies:
            num_applications = self.get_repository(Collection.APPLICATIONS).get_count(
                company_id=company.id
            )
            num_recruiters = self.get_repository(
                Collection.COMPANY_RECRUITERS
            ).get_count(company_id=company.id)
            do_delete = input(
                f"\n\nDelete company {company.name} with ID {company.id}?\n It has {num_applications} applications and {num_recruiters} recruiters. \n (y/n):\n\n "
            )
            if do_delete == "y":
                self.delete_company(company.id, dry_run=dry_run)
            else:
                print("Skipping company deletion")
        print(f"Ending number of companies: {len(all_companies)}")

    def delete_company_orphaned_documents(self):
        companies_that_dont_exist = []
        companies_that_do_exist = []
        collection_list = [
            Collection.COMPANY_RECRUITERS,
            Collection.RECRUITER_INVITATIONS,
            Collection.JOBS,
            Collection.APPLICATIONS,
            Collection.APPLICATION_RECRUITER_UPDATES,
            Collection.RESUMES,
            Collection.COMPANY_NOTIFICATIONS,
            Collection.COMPANY_EMAIL_INGRESS_WEBHOOKS,
            Collection.COMPANY_API_EGRESS_WEBHOOKS,
            Collection.COMPANY_API_INGRESS_WEBHOOKS,
            Collection.RAW_INGRESS_APPLICATIONS,
        ]

        for collection in collection_list:
            repo = self.get_repository(collection)
            try:
                all_records = repo.get_all()
            except:
                print(f"Could not pull data for collection {collection}")
                continue
            for record in all_records:
                if record.company_id in companies_that_do_exist:
                    continue
                if record.company_id in companies_that_dont_exist:
                    print(
                        f"Deleting record {record.id} with company_id {record.company_id} from collection {collection}"
                    )
                    r = repo.delete(record.id)
                else:
                    try:
                        company = self.get_repository(Collection.COMPANIES).get(
                            record.company_id
                        )
                        companies_that_do_exist.append(company.id)
                    except:
                        print(f"Company {record.company_id} does not exist")
                        companies_that_dont_exist.append(record.company_id)
                        print(
                            f"Deleting record {record.id} with company_id {record.company_id} from collection {collection}"
                        )
                        r = repo.delete(record.id)


def main():
    migration = DeleteDemoCompanyUseCase(MIGRATION_REQUEST_SCOPE)
    migration.delete_via_cli(dry_run=True)
