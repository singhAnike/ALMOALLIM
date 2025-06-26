from odoo import models, fields

class LoyaltyProgram(models.Model):
    _inherit = 'loyalty.program'

    first_time_only = fields.Boolean("First Time Customer Only")
