from odoo import http, fields
from odoo.http import request

class ActiveUserController(http.Controller):
    @http.route('/web/get_active_users', type='json', auth='public')
    def get_active_users(self):
        # Get the faculty member group record.
        faculty_group = request.env.ref('faculty_management.group_faculty_member', raise_if_not_found=False)
        domain = [('active', '=', True)]
        if faculty_group:
            domain.append(('groups_id', 'in', faculty_group.id))
        # Search for active users who are in the faculty member group.
        users = request.env['res.users'].sudo().search(domain)
        # Return necessary details for each active user.
        return [{
            'userId': user.id,
            'name': user.name,
            'login': user.login,
            'partnerId': user.partner_id.id,
            'partnerWriteDate': user.partner_id.write_date and fields.Datetime.to_string(user.partner_id.write_date) or "",
        } for user in users]
