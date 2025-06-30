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

    def get_company_by_name(self, name):
        return self.env['res.company'].sudo().search([('name', 'ilike', name)], limit=1)

    def get_category_by_name(self, name):
        return self.env['product.category'].sudo().search([('name', 'ilike', name)], limit=1)

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

            # Optional company and category
            company = False
            category = False

            if 'Company' in df.columns:
                company_name = str(template_data.get('Company', '')).strip()
                if company_name:
                    company = self.get_company_by_name(company_name)
                    if not company:
                        raise ValidationError(_('Company not found: %s') % company_name)

            if 'Product Category' in df.columns:
                category_name = str(template_data.get('Product Category', '')).strip()
                if category_name:
                    category = self.get_category_by_name(category_name)
                    if not category:
                        raise ValidationError(_('Product Category not found: %s') % category_name)

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

            type_map = {
                'Goods': 'consu',
                'Service': 'service',
                'Combo': 'combo',
            }

            # Prepare product.template values
            template_vals = {
                'name': f"{template_data.get('Style Id', '').strip()} - {template_data.get('Item Category Code', '').strip()}" if template_data.get('Style ID') or template_data.get('Item Category Code') else 'Unnamed Product',
                'type': type_map.get(template_data.get('ProductType', 'Goods'), 'consu'),
                'default_code': style_id,
                'list_price': template_data.get('Unit Price Including VAT', 0),
                'attribute_line_ids': attribute_lines,
            }

            if company:
                template_vals['company_id'] = company.id

            if category:
                template_vals['categ_id'] = category.id

            # Create the product template
            template = self.env['product.template'].with_context(
                force_company=company.id if company else False
            ).create(template_vals)

            # Update variants
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
