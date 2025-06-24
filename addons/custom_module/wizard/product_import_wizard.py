import base64
import pandas as pd
from io import BytesIO
from odoo import models, fields, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class ProductImportWizard(models.TransientModel):
    _name = 'product.import.wizard'
    _description = 'Product Import Wizard'

    upload_file = fields.Binary(string="Upload File", required=True)
    filename = fields.Char(string="Filename")

    def get_or_create_attribute_value(self, attribute_name, value_name):
        attr = self.env['product.attribute'].search([('name', '=', attribute_name)], limit=1)
        if not attr:
            attr = self.env['product.attribute'].create({
                'name': attribute_name,
                'create_variant': 'always',
            })

        if attr.create_variant != 'always':
            attr.write({'create_variant': 'always'})

        value = self.env['product.attribute.value'].search([
            ('name', '=', value_name),
            ('attribute_id', '=', attr.id)
        ], limit=1)

        if not value:
            value = self.env['product.attribute.value'].create({
                'name': value_name,
                'attribute_id': attr.id
            })

        return attr, value

    def import_data(self):
        if not self.upload_file or not self.filename:
            raise ValidationError(_('Please upload a valid file.'))

        file_data = base64.b64decode(self.upload_file)

        try:
            if self.filename.endswith('.xlsx'):
                df = pd.read_excel(BytesIO(file_data), header=1)
            elif self.filename.endswith('.csv'):
                df = pd.read_csv(BytesIO(file_data), header=1)
            else:
                raise ValidationError(_('Unsupported file format.'))
        except Exception as e:
            raise ValidationError(_('Error reading file: %s') % str(e))

        df.columns = df.columns.str.strip()
        _logger.info(f"Headers: {df.columns}")
        _logger.info(f"Preview:\n{df.head()}")

        if 'Style Id' not in df.columns:
            raise ValidationError(_('Missing "Style Id" column in the uploaded file.'))

        df.dropna(subset=['Style Id'], inplace=True)
        grouped = df.groupby('Style Id')

        for style_id, group in grouped:
            template_data = group.iloc[0]
            attribute_lines = []

            # Color
            if 'Color Id' in group.columns:
                color_vals = group['Color Id'].dropna().unique()
                if len(color_vals):
                    color_attr, color_val_ids = None, []
                    for val in color_vals:
                        attr, value = self.get_or_create_attribute_value('Color', str(val))
                        color_attr = attr
                        color_val_ids.append(value.id)
                    attribute_lines.append((0, 0, {
                        'attribute_id': color_attr.id,
                        'value_ids': [(6, 0, color_val_ids)]
                    }))

            # Size
            if 'Size' in group.columns:
                size_vals = group['Size'].dropna().unique()
                if len(size_vals):
                    size_attr, size_val_ids = None, []
                    for val in size_vals:
                        attr, value = self.get_or_create_attribute_value('Size', str(val))
                        size_attr = attr
                        size_val_ids.append(value.id)
                    attribute_lines.append((0, 0, {
                        'attribute_id': size_attr.id,
                        'value_ids': [(6, 0, size_val_ids)]
                    }))
            
            # Add this near the top of your import_data method
            type_map = {
                'Goods': 'consu',
                'Service': 'service',
                'Combo': 'combo',
                }
            
            # Create product template
            template = self.env['product.template'].create({
                'name': f"{template_data.get('Style Id', '').strip()} - {template_data.get('Item Category Code', '').strip()}" if template_data.get('Style ID') or template_data.get('Item Category Code') else 'Unnamed Product',
                'type': type_map.get(template_data.get('ProductType', 'Goods'), 'consu'), 
                'default_code': style_id,
                'list_price': template_data.get('Unit Price Including VAT', 0),
                'attribute_line_ids': attribute_lines,
            })

            for variant in template.product_variant_ids:
                color = variant.product_template_attribute_value_ids.filtered(lambda v: v.attribute_id.name == 'Color').mapped('product_attribute_value_id')
                size = variant.product_template_attribute_value_ids.filtered(lambda v: v.attribute_id.name == 'Size').mapped('product_attribute_value_id')


                match_row = group[
                    ((group['Color Id'] == (color.name if color else None)) | pd.isna(group['Color Id'])) &
                    ((group['Size'] == (size.name if size else None)) | pd.isna(group['Size']))
                ]

                if not match_row.empty:
                    row = match_row.iloc[0]
                    variant.write({
                        'default_code': row.get('SKU', ''),
                        'barcode': row.get('No_', ''),
                    })

        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                'title': _('Success'),
                'message': _('Product templates and variants imported successfully.'),
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window_close'
                }
             }
            }
