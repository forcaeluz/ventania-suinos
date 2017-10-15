from unittest import mock
from django.test import TestCase

from .forms import AnimalTransferToForm, AnimalTransferFromForm
from .tests import FarmTestClass


class TestAnimalTransferFromForm(FarmTestClass):

    def test_empty_constructor(self):
        form = AnimalTransferFromForm()
        self.assertFalse(form.is_bound)
        self.assertFalse(form.is_valid())

    def test_constructor_with_data(self):
        form_data = {'date': '2017-03-15',
                     'number_of_animals': '1',
                     'rooms': [1]
                     }
        form = AnimalTransferFromForm(data=form_data)
        self.assertTrue(form.is_bound)
        self.assertTrue(form.is_valid())

    def test_constructor_with_data_from_two_rooms(self):
        form_data = {'date': '2017-03-15',
                     'number_of_animals': '24',
                     'rooms': [1, 2]
                     }
        form = AnimalTransferFromForm(data=form_data)
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())

    def test_constructor_with_invalid_data(self):
        form_data = {'date': '2017-03-15',
                     'number_of_animals': '13',
                     'rooms': [1]
                     }
        form = AnimalTransferFromForm(data=form_data)
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())


class TestAnimalTransferToForm(FarmTestClass):

    def test_empty_constructor(self):
        form = AnimalTransferToForm()
        self.assertFalse(form.is_bound)
        self.assertFalse(form.is_valid())
