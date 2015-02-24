# This file is part product_measurements_shape module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from .product import *
from .configuration import *


def register():
    Pool.register(
        Configuration,
        Template,
        ProductMeasurementsShapeCreationAsk,
        module='product_measurements_shape', type_='model')
    Pool.register(
        ProductMeasurementsShapeCreation,
        module='product_measurements_shape', type_='wizard')
