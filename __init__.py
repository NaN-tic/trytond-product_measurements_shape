# This file is part product_measurements_density module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from .product import *
from .configuration import *


def register():
    Pool.register(
        Template,
        Configuration,
        module='product_measurements_density', type_='model')
