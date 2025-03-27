# models/res_users_inherit.py
from odoo import models, api, SUPERUSER_ID

class ResUsers(models.Model):
    _inherit = "res.users"

    @classmethod
    def authenticate(cls, db, credential, user_agent_env=None):
        # 1) Let Odoo handle the normal credentials check, which returns a dict
        auth_info = super(ResUsers, cls).authenticate(db, credential, user_agent_env)

        # 2) If auth_info has a valid 'uid', login succeeded
        if auth_info and auth_info.get('uid'):
            env = api.Environment(cls.pool.cursor(), SUPERUSER_ID, {})
            user = env['res.users'].browse(auth_info['uid'])
            if user.exists():
                FacultyMember = env['faculty.member'].sudo()
                existing_faculty = FacultyMember.search([('user_id', '=', user.id)], limit=1)
                if not existing_faculty:
                    # Link an existing partial record or create a new one
                    partial = FacultyMember.search([('email', '=', user.email), ('user_id', '=', False)], limit=1)
                    if partial:
                        partial.write({'user_id': user.id})
                    else:
                        FacultyMember.create({
                            'name': user.name,
                            'email': user.email,
                            'employee_id': env['ir.sequence'].next_by_code('faculty.member'),
                            'user_id': user.id,
                        })
                    # Optionally add the user to a group
                    faculty_group = env.ref('faculty_management.group_faculty_member', raise_if_not_found=False)
                    if faculty_group and faculty_group.id not in user.groups_id.ids:
                        user.write({'groups_id': [(4, faculty_group.id)]})
            env.cr.commit()
            env.cr.close()

        # 3) Return the same dictionary
        return auth_info


