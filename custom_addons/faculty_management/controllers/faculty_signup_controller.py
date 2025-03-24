from odoo import http, fields, _
from odoo.http import request


class FacultySignupController(http.Controller):

    @http.route(['/signup'], type='http', auth="public", website=True, csrf=True)
    def faculty_signup(self, token, **kw):
        """
        1) Validate the token => fetch the corresponding faculty record & check expiration.
        2) If a user is logged in & their email matches the faculty email, skip to confirm.
        3) Otherwise, render the signup page to let them create or link a new user.
        """
        # Basic token check
        if not token:
            return request.render("website.404", {'error': _("No token provided.")})

        # Look up the faculty record
        faculty = request.env['faculty.member'].sudo().search([('signup_token', '=', token)], limit=1)
        if not faculty:
            return request.render("website.404", {'error': _("Invalid or missing token.")})

        # Check expiration
        if faculty.signup_token_expiration and faculty.signup_token_expiration < fields.Datetime.now():
            return request.render("website.404", {'error': _("The signup link has expired.")})

        # If user is logged in, only skip form if user's email == faculty.email
        if request.session.uid:
            user = request.env['res.users'].sudo().browse(request.session.uid)
            if user and user.exists():
                if user.login.lower() == (faculty.email or "").lower():
                    # Auto-link flow: skip form
                    return request.redirect("/signup/confirm?token=%s" % token)
                else:
                    # Logged in as a different user => show form w/ a warning
                    return request.render("faculty_management.faculty_signup_page", {
                        'token': token,
                        'error': _(
                            "You are logged in as %s, but this invite is for %s. "
                            "Please log out or continue with a new account."
                        ) % (user.login, faculty.email),
                    })
            else:
                # No valid user => show form
                return request.render("faculty_management.faculty_signup_page", {
                    'token': token,
                })

        # Otherwise, not logged in => show the signup page
        return request.render("faculty_management.faculty_signup_page", {
            'token': token,
        })

    @http.route(['/signup/confirm'], type='http', auth="public", website=True, csrf=True)
    def faculty_signup_confirm(self, **post):
        """
        POST route for finalizing signup:
          - if user is logged in & matches email => link them & skip password creation
          - else create a new user from the posted password
        """
        token = post.get('token')
        password = post.get('password')

        # Retrieve faculty record
        faculty = request.env['faculty.member'].sudo().search([('signup_token', '=', token)], limit=1)
        if not faculty:
            return request.render("website.404", {'error': _("Invalid token.")})

        # Check expiration again
        if faculty.signup_token_expiration and faculty.signup_token_expiration < fields.Datetime.now():
            return request.render("website.404", {'error': _("The signup link has expired.")})

        # If user is already logged in => check if their email matches
        existing_uid = request.session.uid
        if existing_uid:
            user = request.env['res.users'].sudo().browse(existing_uid)
            if user and user.exists():
                # Check mismatch or if record is already linked
                if (user.login or "").lower() != (faculty.email or "").lower():
                    # Logged in user does not match invite => show error or the form again
                    return request.render("faculty_management.faculty_signup_page", {
                        'error': _("You are logged in as %s, but this invite is for %s.") 
                                  % (user.login, faculty.email),
                        'token': token
                    })
                if faculty.user_id and faculty.user_id != user:
                    return request.render("faculty_management.faculty_signup_page", {
                        'error': _("This faculty record is already linked to a different user."),
                        'token': token
                    })
                # Everything matches, link current user
                faculty.update_user_link(user.id)
                # Optionally add user to the faculty group
                faculty_group = request.env.ref('faculty_management.group_faculty_member', False)
                if faculty_group:
                    user.sudo().write({'groups_id': [(4, faculty_group.id)]})
                return request.render("faculty_management.faculty_signup_success", {'faculty': faculty})
            else:
                return request.render("website.404", {'error': _("Could not find your user account.")})

        # If user is NOT logged in => create new user from password
        if not password:
            return request.render("faculty_management.faculty_signup_page", {
                'error': _("Password is required."),
                'token': token
            })

        faculty_group = request.env.ref('faculty_management.group_faculty_member', False)
        internal_group = request.env.ref('base.group_user', False)

        user_vals = {
            'name': faculty.name,
            'login': faculty.email,
            'email': faculty.email,
            'password': password,
            'groups_id': [(6, 0, [faculty_group.id, internal_group.id])],
        }
        try:
            new_user = request.env['res.users'].sudo().create(user_vals)
        except Exception as e:
            return request.render("faculty_management.faculty_signup_page", {
                'error': _("Error creating user: %s") % e,
                'token': token
            })

        # Link the newly created user
        faculty.update_user_link(new_user.id)
        return request.render("faculty_management.faculty_signup_success", {'faculty': faculty})
