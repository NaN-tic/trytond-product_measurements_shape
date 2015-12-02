# This file is part product_measurements_shape module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelView, fields
from trytond.wizard import Wizard, StateTransition, StateView, StateAction, \
    Button
from trytond.pyson import PYSONEncoder, Eval, Bool, Id
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.tools import safe_eval
from trytond.modules.product_measurements.product import NON_MEASURABLE
from math import pi

__all__ = ['Template', 'ProductMeasurementsShapeCreationAsk',
    'ProductMeasurementsShapeCreation']
__metaclass__ = PoolMeta

_SHAPE = [
    (None, 'None'),
    ('parallelepiped', 'Parallelepiped'),
    ('cylinder', 'Cylinder'),
]

_MEASUREMENT_FIELDS = ['shape', 'length', 'length_uom', 'height', 'height_uom',
    'width', 'width_uom', 'diameter', 'diameter_uom', 'weight', 'weight_uom',
    'density', 'density_weight_uom', 'density_volume_uom']


class Template:
    __name__ = 'product.template'
    shape = fields.Selection(_SHAPE, 'Shape', select=True,
        help="Weight Formula for Parallelepiped = width*height*length*density"
            "\nWeight Formula for Cylinder = (diameter/2)^2*pi*length*density",
        states={
            'invisible': Eval('type').in_(NON_MEASURABLE),
            }, depends=['type'])
    diameter = fields.Float('Diameter',
        digits=(16, Eval('diameter_digits', 2)),
        states={
            'invisible': ((Eval('type').in_(NON_MEASURABLE)) |
                (Eval('shape') != 'cylinder')),
            },
        depends=['type', 'diameter_digits'])
    diameter_uom = fields.Many2One('product.uom', 'Diameter UoM',
        domain=[('category', '=', Id('product', 'uom_cat_length'))],
        states={
            'invisible': ((Eval('type').in_(NON_MEASURABLE)) |
                (Eval('shape') != 'cylinder')),
            'required': Bool(Eval('diameter')),
            },
        depends=['type', 'shape', 'diameter'])
    diameter_digits = fields.Function(fields.Integer('Diameter Digits'),
        'on_change_with_diameter_digits')
    density = fields.Float('Density',
        digits=(16, Eval('density_digits', 2)),
        states={
            'invisible': Eval('type').in_(NON_MEASURABLE),
            },
        depends=['type', 'density_digits'])
    density_weight_uom = fields.Many2One('product.uom', 'Density Weight UoM',
        domain=[('category', '=', Id('product', 'uom_cat_weight'))],
        states={
            'invisible': Eval('type').in_(NON_MEASURABLE),
            'required': Bool(Eval('density')),
            },
        depends=['type', 'density'])
    density_volume_uom = fields.Many2One('product.uom', 'Density Volume UoM',
        domain=[('category', '=', Id('product', 'uom_cat_volume'))],
        states={
            'invisible': Eval('type').in_(NON_MEASURABLE),
            'required': Bool(Eval('density')),
            },
        depends=['type', 'density'])
    density_digits = fields.Function(fields.Integer('Density Digits'),
        'on_change_with_density_digits')
    measurement_code = fields.Function(fields.Char('Measurement code'),
        'on_change_with_measurement_code')

    @classmethod
    def __setup__(cls):
        super(Template, cls).__setup__()
        cls.height.states.update({
                'invisible': ((cls.height.states.get('invisible')) |
                    (Eval('shape') == 'cylinder'))
                })
        cls.height_uom.states.update({
                'invisible': ((cls.height_uom.states.get('invisible')) |
                    (Eval('shape') == 'cylinder'))
                })
        cls.width.states.update({
                'invisible': ((cls.height.states.get('invisible')) |
                    (Eval('shape') == 'cylinder'))
                })
        cls.width_uom.states.update({
                'invisible': ((cls.height_uom.states.get('invisible')) |
                    (Eval('shape') == 'cylinder'))
                })

    @staticmethod
    def default_shape():
        Config = Pool().get('product.configuration')
        config = Config.get_singleton()
        if config:
            return config.shape
        return 'none'

    @staticmethod
    def default_length_uom():
        Config = Pool().get('product.configuration')
        config = Config.get_singleton()
        if config and config.length_uom:
            return config.length_uom.id

    @staticmethod
    def default_height_uom():
        Config = Pool().get('product.configuration')
        config = Config.get_singleton()
        if config and config.height_uom:
            return config.height_uom.id

    @staticmethod
    def default_width_uom():
        Config = Pool().get('product.configuration')
        config = Config.get_singleton()
        if config and config.width_uom:
            return config.width_uom.id

    @staticmethod
    def default_diameter_uom():
        Config = Pool().get('product.configuration')
        config = Config.get_singleton()
        if config and config.diameter_uom:
            return config.diameter_uom.id

    @staticmethod
    def default_weight_uom():
        Config = Pool().get('product.configuration')
        config = Config.get_singleton()
        if config and config.weight_uom:
            return config.weight_uom.id

    @staticmethod
    def default_density_weight_uom():
        Config = Pool().get('product.configuration')
        config = Config.get_singleton()
        if config and config.density_weight_uom:
            return config.density_weight_uom.id

    @staticmethod
    def default_density_volume_uom():
        Config = Pool().get('product.configuration')
        config = Config.get_singleton()
        if config and config.density_volume_uom:
            return config.density_volume_uom.id

    @fields.depends('diameter_uom')
    def on_change_with_diameter_digits(self, name=None):
        return (self.diameter_uom.digits if self.diameter_uom
            else self.default_diameter_digits())

    @staticmethod
    def default_diameter_digits():
        return 2

    @fields.depends('density_weight_uom', 'density_volume_uom')
    def on_change_with_density_digits(self, name=None):
        return (self.density_weight_uom.digits + self.density_volume_uom.digits
            if self.density_weight_uom and self.density_volume_uom
            else self.default_density_digits())

    @staticmethod
    def default_density_digits():
        return 4

    @fields.depends('weight_digits', *_MEASUREMENT_FIELDS)
    def on_change_with_weight(self, name=None):
        '''
        The weight is automatically computed from the measurements and density.
        UoM with factor one: Kilogram, Meter, Liter
        Conversion between Density UoM: kg/m^3 = 1000 * kg/l
        '''
        weight = None
        if self.shape == 'parallelepiped':
            if (self.density_weight_uom and self.density_volume_uom and
                    self.density and self.weight_uom and
                    self.length and self.length_uom and
                    self.height and self.height_uom and
                    self.width and self.width_uom):
                weight = (self.length * self.length_uom.factor *
                    self.height * self.height_uom.factor *
                    self.width * self.width_uom.factor *
                    self.density * self.density_weight_uom.factor * 1000 /
                    (self.weight_uom.factor * self.density_volume_uom.factor))
                weight = round(weight, self.weight_digits)
        elif self.shape == 'cylinder':
            if (self.density_weight_uom and self.density_volume_uom and
                    self.density and self.weight_uom and
                    self.length and self.length_uom and
                    self.diameter and self.diameter_uom):
                radius = self.diameter * self.diameter_uom.factor / 2.0
                weight = (pi * radius * radius *
                    self.length * self.length_uom.factor *
                    self.density * self.density_weight_uom.factor * 1000 /
                    (self.weight_uom.factor * self.density_volume_uom.factor))
                weight = round(weight, self.weight_digits)
        return weight

    @fields.depends(*_MEASUREMENT_FIELDS)
    def on_change_with_density(self, name=None):
        '''
        The density is automatically computed from the measurements and weight.
        UoM with factor one: Kilogram, Meter, Liter
        Conversion between Density UoM: kg/m^3 = 1000 * kg/l
        '''
        density = self.density
        if self.shape == 'parallelepiped':
            if (self.density_weight_uom and self.density_volume_uom and
                    self.weight and self.weight_uom and
                    self.length and self.length_uom and
                    self.height and self.height_uom and
                    self.width and self.width_uom):
                density = (self.weight * self.weight_uom.factor *
                    self.density_volume_uom.factor / (
                    self.length * self.length_uom.factor *
                    self.height * self.height_uom.factor *
                    self.width * self.width_uom.factor *
                    self.density_weight_uom.factor * 1000))
        elif self.shape == 'cylinder':
            if (self.density_weight_uom and self.density_volume_uom and
                    self.weight and self.weight_uom and
                    self.length and self.length_uom and
                    self.diameter and self.diameter_uom):
                radius = self.diameter * self.diameter_uom.factor / 2.0
                density = (self.weight * self.weight_uom.factor *
                    self.density_volume_uom.factor /
                    (pi * radius * radius *
                    self.length * self.length_uom.factor *
                    self.density_weight_uom.factor * 1000))
        return density

    def _get_context_measurement_code(self):
        '''
        Get context for compute measurement code
        '''
        return {
            'type': self.type,
            'shape': self.shape,
            'length': self.length,
            'length_uom': self.length_uom,
            'height': self.height,
            'height_uom': self.height_uom,
            'width': self.width,
            'width_uom': self.width_uom,
            'diameter': self.diameter,
            'diameter_uom': self.diameter_uom,
            'weight': self.weight,
            'weight_uom': self.weight_uom,
            'density': self.density,
            'density_weight_uom': self.density_weight_uom,
            'density_volume_uom': self.density_volume_uom,
        }

    def get_measurement_code(self, formula):
        '''
        Evaluates the formula to compute measurement code with the context data
        '''
        context = Transaction().context.copy()
        return safe_eval(formula, context)

    @fields.depends('type', *_MEASUREMENT_FIELDS)
    def on_change_with_measurement_code(self, name=None):
        code = None
        Config = Pool().get('product.configuration')
        config = Config.get_singleton()
        if config and config.measurement_code_formula:
            with Transaction().set_context(
                    self._get_context_measurement_code()):
                code = self.get_measurement_code(
                    config.measurement_code_formula)
        return code

    def __getattr__(self, name):
        val = super(Template, self).__getattr__(name)
        if name == 'name':
            code = self.measurement_code
            if code:
                val += ' [' + unicode(code, "utf-8") + ']'
        return val


class ProductMeasurementsShapeCreationAsk(ModelView):
    'Product Measurements Shape Creation Ask'
    __name__ = 'product.measurements_shape_creation.ask'
    shape = fields.Selection(_SHAPE, 'Shape',
        states={
            'invisible': Eval('type').in_(NON_MEASURABLE),
            }, depends=['type'])

    length = fields.Float('Length',
        digits=(16, Eval('length_digits', 2)),
        depends=['length_digits'])
    length_uom = fields.Many2One('product.uom', 'Length UoM',
        domain=[('category', '=', Id('product', 'uom_cat_length'))],
        states={
            'required': Bool(Eval('length')),
            },
        depends=['length'])
    length_digits = fields.Function(fields.Integer('Length Digits'),
        'on_change_with_length_digits')
    height = fields.Float('Height',
        digits=(16, Eval('height_digits', 2)),
        states={
            'invisible': Eval('shape') == 'cylinder',
            },
        depends=['shape', 'height_digits'])
    height_uom = fields.Many2One('product.uom', 'Height UoM',
        domain=[('category', '=', Id('product', 'uom_cat_length'))],
        states={
            'invisible': Eval('shape') == 'cylinder',
            'required': Bool(Eval('height')),
            },
        depends=['shape', 'height'])
    height_digits = fields.Function(fields.Integer('Height Digits'),
        'on_change_with_height_digits')
    width = fields.Float('Width',
        digits=(16, Eval('width_digits', 2)),
        states={
            'invisible': Eval('shape') == 'cylinder',
            },
        depends=['shape', 'width_digits'])
    width_uom = fields.Many2One('product.uom', 'Width UoM',
        domain=[('category', '=', Id('product', 'uom_cat_length'))],
        states={
            'invisible': Eval('shape') == 'cylinder',
            'required': Bool(Eval('width')),
            },
        depends=['shape', 'width'])
    width_digits = fields.Function(fields.Integer('Width Digits'),
        'on_change_with_width_digits')
    diameter = fields.Float('Diameter',
        digits=(16, Eval('diameter_digits', 2)),
        states={
            'invisible': Eval('shape') != 'cylinder',
            },
        depends=['diameter_digits'])
    diameter_uom = fields.Many2One('product.uom', 'Diameter UoM',
        domain=[('category', '=', Id('product', 'uom_cat_length'))],
        states={
            'invisible': Eval('shape') != 'cylinder',
            'required': Bool(Eval('diameter')),
            },
        depends=['shape', 'diameter'])
    diameter_digits = fields.Function(fields.Integer('Diameter Digits'),
        'on_change_with_diameter_digits')
    density = fields.Float('Density',
        digits=(16, Eval('density_digits', 2)),
        depends=['density_digits'])
    density_weight_uom = fields.Many2One('product.uom', 'Density Weight UoM',
        domain=[('category', '=', Id('product', 'uom_cat_weight'))],
        states={
            'required': Bool(Eval('density')),
            },
        depends=['density'])
    density_volume_uom = fields.Many2One('product.uom', 'Density Volume UoM',
        domain=[('category', '=', Id('product', 'uom_cat_volume'))],
        states={
            'required': Bool(Eval('density')),
            },
        depends=['density'])
    density_digits = fields.Function(fields.Integer('Density Digits'),
        'on_change_with_density_digits')

    @fields.depends('length_uom')
    def on_change_with_length_digits(self, name=None):
        return (self.length_uom.digits if self.length_uom
            else self.default_length_digits())

    @staticmethod
    def default_length_digits():
        return 2

    @fields.depends('height_uom')
    def on_change_with_height_digits(self, name=None):
        return (self.height_uom.digits if self.height_uom
            else self.default_height_digits())

    @staticmethod
    def default_height_digits():
        return 2

    @fields.depends('width_uom')
    def on_change_with_width_digits(self, name=None):
        return (self.width_uom.digits if self.width_uom
            else self.default_width_digits())

    @staticmethod
    def default_width_digits():
        return 2

    @fields.depends('diameter_uom')
    def on_change_with_diameter_digits(self, name=None):
        return (self.diameter_uom.digits if self.diameter_uom
            else self.default_diameter_digits())

    @staticmethod
    def default_diameter_digits():
        return 2

    @fields.depends('density_weight_uom', 'density_volume_uom')
    def on_change_with_density_digits(self, name=None):
        return (self.density_weight_uom.digits + self.density_volume_uom.digits
            if self.density_weight_uom and self.density_volume_uom
            else self.default_density_digits())

    @staticmethod
    def default_density_digits():
        return 4


class ProductMeasurementsShapeCreation(Wizard):
    'Product Measurements Shape Creation'
    __name__ = 'product.measurements_shape_creation'
    start = StateView('product.measurements_shape_creation.ask',
        'product_measurements_shape.product_measurements_shape_creation_view_form',
        [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Create/Find', 'create_', 'tryton-ok', default=True),
            ])
    create_ = StateAction('product.act_template_form')

    @classmethod
    def __setup__(cls):
        super(ProductMeasurementsShapeCreation, cls).__setup__()
        cls._error_messages.update({
                'not_unique_variant_code': ('The product "%s" is not variant '
                    'unique or does not have a code.'),
                })

    def default_start(self, fields):
        Config = Pool().get('product.configuration')
        Template = Pool().get('product.template')
        Product = Pool().get('product.product')

        context = Transaction().context
        if context['active_model'] == 'product.product':
            product = Product(context['active_id'])
            template = product.template
        else:
            template = Template(context['active_id'])

        if not template.unique_variant or not template.code:
            self.raise_user_error('not_unique_variant_code', (template.name,))

        default = {}
        config = Config.get_singleton()
        default['shape'] = template.shape
        default['length'] = template.length
        default['height'] = template.height
        default['width'] = template.width
        default['diameter'] = template.diameter
        default['density'] = template.density

        if template.length_uom:
            default['length_uom'] = template.length_uom.id
        elif config and config.length_uom:
            default['length_uom'] = config.length_uom.id

        if template.height_uom:
            default['height_uom'] = template.height_uom.id
        elif config and config.height_uom:
            default['height_uom'] = config.height_uom.id

        if template.width_uom:
            default['width_uom'] = template.width_uom.id
        elif config and config.width_uom:
            default['width_uom'] = config.width_uom.id

        if template.diameter_uom:
            default['diameter_uom'] = template.diameter_uom.id
        elif config and config.diameter_uom:
            default['diameter_uom'] = config.diameter_uom.id

        if template.density_weight_uom:
            default['density_weight_uom'] = template.density_weight_uom.id
        elif config and config.density_weight_uom:
            default['density_weight_uom'] = config.density_weight_uom.id

        if template.density_volume_uom:
            default['density_volume_uom'] = template.density_volume_uom.id
        elif config and config.density_volume_uom:
            default['density_volume_uom'] = config.density_volume_uom.id

        return default

    def do_create_(self, action):
        Template = Pool().get('product.template')
        Product = Pool().get('product.product')

        context = Transaction().context
        if context['active_model'] == 'product.product':
            product = Product(context['active_id'])
            template = product.template
        else:
            template = Template(context['active_id'])

        templates = Template.search([
                ('code', '=', template.code),
                ('shape', '=', self.start.shape),
                ('length', '=', self.start.length),
                ('height', '=', self.start.height),
                ('width', '=', self.start.width),
                ('diameter', '=', self.start.diameter),
                ('density', '=', self.start.density),
                ('length_uom', '=', self.start.length_uom),
                ('height_uom', '=', self.start.height_uom),
                ('width_uom', '=', self.start.width_uom),
                ('diameter_uom', '=', self.start.diameter_uom),
                ('density_weight_uom', '=', self.start.density_weight_uom),
                ('density_volume_uom', '=', self.start.density_volume_uom),
                ], limit=1)
        if not templates:
            new_template, = Template.copy([template], {
                    'shape': self.start.shape,
                    'length': self.start.length,
                    'height': self.start.height,
                    'width': self.start.width,
                    'diameter': self.start.diameter,
                    'density': self.start.density,
                    'length_uom': self.start.length_uom,
                    'height_uom': self.start.height_uom,
                    'width_uom': self.start.width_uom,
                    'diameter_uom': self.start.diameter_uom,
                    'density_weight_uom': self.start.density_weight_uom,
                    'density_volume_uom': self.start.density_volume_uom,
                    })
        else:
            new_template, = templates

        action['pyson_context'] = PYSONEncoder().encode({
                'product': new_template.id,
                })
        action['pyson_search_value'] = PYSONEncoder().encode([
                ('id', '=', new_template.id),
                ])
        return action, {}
