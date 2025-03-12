from odoo import models, fields

class FacultyMember(models.Model):
    _name = "faculty.member"
    _description = "Faculty Member"

    name = fields.Char(string="Full Name", required=True)
    employee_id = fields.Char(string="Employee ID", required=True, unique=True)
    email = fields.Char(string="Email", required=True)
    years_of_service = fields.Integer(string="Years of Service")
    fte = fields.Float(string="FTE")
    last_academic_leave = fields.Date(string="Last Academic Leave")
    next_eligible_leave = fields.Date(string="Next Eligible Academic Leave")
    negotiated_leave = fields.Text(string="Negotiated Leave")
    grants_held = fields.Text(string="Past Grants Held")
    current_grants = fields.Text(string="Current Grants")
    courses_taught = fields.Text(string="Courses Taught")
    courses_current_year = fields.Text(string="Courses This Year")
    teaching_release = fields.Text(string="Teaching Release")

    past_supervision_ba = fields.Text(string="Past BA Supervision")
    past_supervision_ma = fields.Text(string="Past MA Supervision")
    past_supervision_phd = fields.Text(string="Past PhD Supervision")
    current_supervision = fields.Text(string="Current Supervision")

    service_duties = fields.Text(string="Service Duties")
    major_service_duties = fields.Text(string="Major Service Duties")
    current_service = fields.Text(string="Current Service")

