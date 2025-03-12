from odoo import models, fields

class FacultyMember(models.Model):
    _name = "faculty.member"
    _description = "Faculty Member"

    name = fields.Char()

