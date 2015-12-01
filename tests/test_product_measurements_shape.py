# This file is part of the product_measurements_shape module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase


class ProductMeasurementsShapeTestCase(ModuleTestCase):
    'Test Product Measurements Shape module'
    module = 'product_measurements_shape'


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        ProductMeasurementsShapeTestCase))
    return suite