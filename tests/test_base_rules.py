import pytest
from pydantic import BaseModel
from ajb.base import BaseDataModel, ParentRepository, Collection
from ajb.base.rules import (
    Rule,
    RuleSet,
    ValidationResult,
    EntityExistsRule,
    OnlyOneEntityExistsRule,
    EntityDoesNotExistRule,
    ValidationException,
)
from ajb.vendor.arango.models import Filter


TEST_EMAIL = "great@email.com"


class ExampleSuccessCustomRule(Rule):
    code = "example"
    message = "example"

    def run(self) -> ValidationResult:
        # Some logic would go here
        return ValidationResult(successful=True, code=None, message=None)


class ExampleFailureCustomRule(Rule):
    code = "example_two"
    message = "example_two"
    overridable = True

    def run(self) -> ValidationResult:
        # Some other logic would go here
        return ValidationResult(successful=False, code="example", message="example")


class ExampleRuleSet(RuleSet):
    def _get_rules(self):
        yield ExampleSuccessCustomRule()
        yield ExampleFailureCustomRule()


def test_example_rule_set():
    rule_set = ExampleRuleSet()
    results = rule_set.run()
    assert len(results) == 2
    assert results[0].successful is True
    assert results[0].code is None
    assert results[0].message is None
    assert results[1].successful is False
    assert results[1].code == "example"
    assert results[1].message == "example"

    overridden_results = rule_set.run(overridden_rules=["example_two"])
    assert len(overridden_results) == 1
    assert all(result.successful for result in overridden_results)


class CreateTestModel(BaseModel):
    name: str | None = None
    age: int | None = None
    email: str | None = None
    is_cool: bool | None = None
    text_one: str | None = None
    text_two: str | None = None
    text_three: str | None = None


class TestModel(BaseDataModel, CreateTestModel):
    ...


class TestRepository(ParentRepository[CreateTestModel, TestModel]):
    collection = Collection.ADMIN_USERS
    entity_model = TestModel


class AdminUserExistsRule(EntityExistsRule):
    code = "admin_user_exists"
    message = "The Admin user must exist"

    def __init__(self, repository: TestRepository, admin_user_id: str):
        super().__init__(repository, admin_user_id)


class SingleAdminByEmailRule(OnlyOneEntityExistsRule):
    code = "single_admin_by_email"
    message = "There can only be one admin with this email"

    def __init__(self, repository: TestRepository, email: str):
        super().__init__(
            repository,
            [
                Filter(field="email", value=email),
            ],
        )


class AdminWithSillyNameDoesNotExistRule(EntityDoesNotExistRule):
    code = "admin_with_silly_name_does_not_exist"
    message = "Admins with a silly name should not exist"

    def __init__(self, repository: TestRepository):
        super().__init__(
            repository,
            [
                Filter(field="name", value="silly name"),
            ],
        )


class AdminUserExistRuleSet(RuleSet):
    def __init__(
        self,
        repository: TestRepository,
        admin_user_id: str,
        admin_email: str,
    ):
        self.repository = repository
        self.admin_user_id = admin_user_id
        self.admin_email = admin_email

    def _get_rules(self):
        yield AdminUserExistsRule(self.repository, self.admin_user_id)
        yield SingleAdminByEmailRule(self.repository, self.admin_email)
        yield AdminWithSillyNameDoesNotExistRule(self.repository)


def test_example_entity_rule_sets(request_scope):
    repo = TestRepository(request_scope)

    # Prep some data
    created_record = repo.create(CreateTestModel(name="not silly", email=TEST_EMAIL))

    # Run the rule set
    rule_set = AdminUserExistRuleSet(
        repository=repo, admin_user_id=created_record.id, admin_email=TEST_EMAIL
    )
    results = rule_set.run()
    assert len(results) == 3
    assert all(result.successful for result in results)

    # Now with a bad ID and email
    rule_set = AdminUserExistRuleSet(
        repository=repo, admin_user_id="bad_id", admin_email="bad_too"
    )
    results = rule_set.run()
    assert len(results) == 3
    assert results[0].successful is False
    assert results[1].successful is False
    assert results[2].successful is True

    # Add a silly name
    repo.create(CreateTestModel(name="silly name"))

    # Now the silly name should throw
    rule_set = AdminUserExistRuleSet(
        repository=repo, admin_user_id=created_record.id, admin_email=TEST_EMAIL
    )
    results = rule_set.run()
    assert len(results) == 3
    assert results[0].successful is True
    assert results[1].successful is True
    assert results[2].successful is False


def test_rule_set_throws_exception(request_scope):
    repo = TestRepository(request_scope)

    # Prep some data
    repo.create(CreateTestModel(name="not silly", email=TEST_EMAIL))

    # Run the rule set
    rule_set = AdminUserExistRuleSet(
        repository=repo, admin_user_id="doesntexist", admin_email=TEST_EMAIL
    )
    with pytest.raises(ValidationException):
        rule_set.run(raise_exception=True)
