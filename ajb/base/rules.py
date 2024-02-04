"""
This module is a base module for running rulesets on data operations.
There are several common rules that are defined such as value equals or entity exists.

For any given usecase that requires significant validation we can define these
rule sets using this base rule class
"""

import typing as t
from abc import abstractmethod, ABC
from pydantic import BaseModel
from ajb.vendor.arango.models import Filter
from ajb.exceptions import EntityNotFound, MultipleEntitiesReturned

from ajb.base.repository import BaseRepository


class ValidationResult(BaseModel):
    successful: bool
    code: str | None
    message: str | None


SUCCESSFUL_VALIDATION = ValidationResult(successful=True, code=None, message=None)


class ValidationException(Exception):
    def __init__(self, codes: list[str | None], messages: list[str | None]):
        super().__init__("\n".join(filter(None, messages)) or "No message")
        self.codes = "\n".join(
            code if code is not None else "no_code" for code in codes
        )
        self.messages = "\n".join(
            message if message is not None else "no message" for message in messages
        )

    def __str__(self):
        return f"Codes: {self.codes}\nMessages: {self.messages}"


class Rule(ABC):
    code: str
    message: str
    overridable: bool = False

    @abstractmethod
    def run(self) -> ValidationResult:
        pass


class EntityExistsRule(Rule):
    message: str = "Entity does not exist"

    def __init__(self, repository: BaseRepository, entity_id: str):
        self.repository = repository
        self.entity_id = entity_id

    def run(self) -> ValidationResult:
        try:
            self.repository.get(self.entity_id)
            return SUCCESSFUL_VALIDATION
        except EntityNotFound:
            return ValidationResult(
                successful=False, code=self.code, message=self.message
            )


class OnlyOneEntityExistsRule(Rule):
    def __init__(self, repository: BaseRepository, filters: list[Filter]):
        self.repository = repository
        self.filters = filters

    def run(self) -> ValidationResult:
        try:
            filters_as_dict = {filter.field: filter.value for filter in self.filters}
            self.repository.get_one(**filters_as_dict)
            return SUCCESSFUL_VALIDATION
        except EntityNotFound:
            return ValidationResult(
                successful=False, code=self.code, message=self.message
            )
        except MultipleEntitiesReturned:
            return ValidationResult(
                successful=False, code=self.code, message=self.message
            )


class EntityDoesNotExistRule(Rule):
    def __init__(self, repository: BaseRepository, filters: list[Filter]):
        self.repository = repository
        self.filters = filters

    def run(self) -> ValidationResult:
        try:
            filters_as_dict = {filter.field: filter.value for filter in self.filters}
            self.repository.get_one(**filters_as_dict)
            return ValidationResult(
                successful=False, code=self.code, message=self.message
            )
        except EntityNotFound:
            return SUCCESSFUL_VALIDATION
        except MultipleEntitiesReturned:
            return ValidationResult(
                successful=False, code=self.code, message=self.message
            )


class RuleSet:
    @abstractmethod
    def _get_rules(self) -> t.Generator[Rule, None, None]:
        raise NotImplementedError("Must implement _get_rules method")

    def run(
        self, overridden_rules: list[str] = [], raise_exception: bool = False
    ) -> list[ValidationResult]:
        output: list[ValidationResult] = []
        for rule in self._get_rules():
            if rule.code not in overridden_rules:
                output.append(rule.run())

        if not raise_exception:
            return output
        failed_validations = [result for result in output if not result.successful]
        if not failed_validations:
            return output
        raise ValidationException(
            codes=[validation.code for validation in failed_validations],
            messages=[validation.message for validation in failed_validations],
        )
