# -*- coding: utf-8 -*-
# This file is part product_measurements_density module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pyson import Id
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from product import _SHAPE

__all__ = ['Configuration']
__metaclass__ = PoolMeta


class Configuration:
    __name__ = 'product.configuration'
    shape = fields.Selection(_SHAPE, 'Shape',
        help='Default value of the shape field in template form.')
    length_uom = fields.Many2One('product.uom', 'Length UoM',
        domain=[('category', '=', Id('product', 'uom_cat_length'))],
        help='Default value of the Length UoM field in template form.')
    height_uom = fields.Many2One('product.uom', 'Height UoM',
        domain=[('category', '=', Id('product', 'uom_cat_length'))],
        help='Default value of the Height UoM field in template form.')
    width_uom = fields.Many2One('product.uom', 'Width UoM',
        domain=[('category', '=', Id('product', 'uom_cat_length'))],
        help='Default value of the Width UoM field in template form.')
    diameter_uom = fields.Many2One('product.uom', 'Diameter UoM',
        domain=[('category', '=', Id('product', 'uom_cat_length'))],
        help='Default value of the Diameter UoM field in template form.')
    weight_uom = fields.Many2One('product.uom', 'Weight UoM',
        domain=[('category', '=', Id('product', 'uom_cat_weight'))],
        help='Default value of the Weight UoM field in template form.')
    density_weight_uom = fields.Many2One('product.uom', 'Density Weight UoM',
        domain=[('category', '=', Id('product', 'uom_cat_weight'))],
        help='Default value of the Density Weight UoM field in template form.')
    density_volume_uom = fields.Many2One('product.uom', 'Density Volume UoM',
        domain=[('category', '=', Id('product', 'uom_cat_volume'))],
        help='Default value of the Density Volume UoM field in template form.')
    measurement_code_formula = fields.Char('Measurement Code Formula',
        help="Python expression to compute the code from measurements.\n"
        "It can use the following product template fields:\n"
        "type, shape, length, length_uom, height, height_uom, width, "
        "width_uom, diameter, diameter_uom, weight, weight_uom, density, "
        "density_weight_uom, density_volume_uom")

    @classmethod
    def __setup__(cls):
        super(Configuration, cls).__setup__()
        cls._error_messages.update({
                'invalid_formula': (
                    'Invalid formula\n%(formula)s\n\n%(error)s'),
                })

    @staticmethod
    def default_measurement_code_formula():
        return ("'' if type == 'service' else "
            "str(length if length else '') + "
            "str(length_uom.symbol if length_uom else '') + ' x ' + "
            "str(height if height else '') + "
            "str(height_uom.symbol if height_uom else '') + ' x ' + "
            "str(width if width else '') + "
            "str(width_uom.symbol if width_uom else '') "
            "if shape == 'parallelepiped' else "
            "str(length if length else '') + "
            "str(length_uom.symbol if length_uom else '') + ' x ' + "
            "str(diameter if diameter else '') + "
            "str(diameter_uom.symbol if diameter_uom else '') + '∅' "
            "if shape == 'cylinder' else ''")

    @classmethod
    def validate(cls, configurations):
        super(Configuration, cls).validate(configurations)
        for configuration in configurations:
            configuration.check_formula()

    def check_formula(self):
        '''
        Check formula
        '''
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        Uom = pool.get('product.uom')
        Template = pool.get('product.template')

        meter = Uom(ModelData.get_id('product', 'uom_meter'))
        kilogram = Uom(ModelData.get_id('product', 'uom_kilogram'))
        liter = Uom(ModelData.get_id('product', 'uom_liter'))
        formula = self.measurement_code_formula

        product = Template()
        product.type = 'goods'
        product.shape = 'parallelepiped'
        product.length = product.height = product.width = 0
        product.length_uom = product.height_uom = product.width_uom = meter
        product.diameter = product.weight = product.density = 0
        product.diameter_uom = meter
        product.weight_uom = product.density_weight_uom = kilogram
        product.density_volume_uom = liter
        context = product._get_context_measurement_code()
        with Transaction().set_context(**context):
            try:
                if not isinstance(product.get_measurement_code(formula), str):
                    raise Exception('The result is not a string.')
            except Exception, error:
                self.raise_user_error('invalid_formula', {
                        'formula': formula,
                        'error': error,
                        })

        product.shape = 'cylinder'
        context = product._get_context_measurement_code()
        with Transaction().set_context(**context):
            try:
                if not isinstance(product.get_measurement_code(formula), str):
                    raise Exception('The result is not a string.')
            except Exception, error:
                self.raise_user_error('invalid_formula', {
                        'formula': formula,
                        'error': error,
                        })
