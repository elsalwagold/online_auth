import json
from odoo import http
from odoo.http import request


class OnlineAuth(http.Controller):
    @http.route('/online/auth', auth='public', website=True)
    def auth_form(self, **kw):
        return request.render('online_auth.auth_form_template')

    @http.route('/online/auth/submit', auth='public', website=True, methods=['POST'])
    def auth_submit(self, **kw):
        url = kw.get('url')
        db = kw.get('db')
        login = kw.get('login')
        password = kw.get('password')
        token = kw.get('token')

        request.session['online_odoo_url'] = url
        request.session['online_odoo_db'] = db
        request.session['online_odoo_login'] = login
        request.session['online_odoo_password'] = password
        request.session['online_odoo_token'] = token

        result = f"Authenticated to {url} with database '{db}' as {login}. Token: {token}"
        return request.render('online_auth.auth_result_template', {'result': result})

    @http.route('/online/auth/attendance', auth='public', website=True, methods=['GET'])
    def get_attendance_records(self, **kw):
        try:
            # Retrieve all attendance records with sudo rights
            attendance_records = request.env['hr.attendance'].sudo().search([])
            data = []
            for record in attendance_records:
                # Get the employee's custom field from the related employee record.
                employee_no = ''
                if record.employee_id:
                    employee_no = record.employee_id.x_studio_x_employee_no_1 or ''

                data.append({
                    'employee_no': employee_no,
                    'check_in': record.check_in.strftime('%Y-%m-%d %H:%M:%S') if record.check_in else '',
                    'check_out': record.check_out.strftime('%Y-%m-%d %H:%M:%S') if record.check_out else '',
                })

            # Return the data as JSON
            return request.make_response(
                json.dumps(data),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            error_data = {
                'error': 'An error occurred while retrieving attendance records.',
                'details': str(e)
            }
            return request.make_response(
                json.dumps(error_data),
                headers=[('Content-Type', 'application/json')]
            )
