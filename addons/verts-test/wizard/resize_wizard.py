from odoo import models, fields

class ResizeWizard(models.TransientModel):
    _name = 'resize.wizard'
    _description = 'Resizable Wizard'

    name = fields.Char(string="Name")
    description = fields.Text(string="Description")
