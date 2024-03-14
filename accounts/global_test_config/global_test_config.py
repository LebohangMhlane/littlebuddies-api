

from django.test import TestCase


class GlobalTestCaseConfig(TestCase):
    def setUp(self) -> None:
        return super().setUp()