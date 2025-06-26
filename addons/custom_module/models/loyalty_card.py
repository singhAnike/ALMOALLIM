from odoo import models, api

class LoyaltyCard(models.Model):
    _inherit = 'loyalty.card' 

    @api.model_create_multi
    def create(self, vals_list):
        filtered_vals = []
        for vals in vals_list:
            program_id = self.env['loyalty.program'].browse(vals.get('program_id'))
            partner_id = vals.get('partner_id')

            if program_id.first_time_only and partner_id:
                existing_cards = self.search_count([
                    ('partner_id', '=', partner_id),
                    ('program_id', '=', program_id.id)
                ])
                if existing_cards > 0:
                    continue  # skip creation

            filtered_vals.append(vals)

        res = super().create(filtered_vals)
        res._send_creation_communication()
        return res


# original defination 
#  @api.model_create_multi
#     def create(self, vals_list):
#         res = super().create(vals_list)
#         res._send_creation_communication()
#         return res