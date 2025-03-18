import json
from odoo import http
from odoo.http import request


class OnlineAuth(http.Controller):
    @http.route('/online/auth', auth='public', website=True)
    def auth_form(self, **kw):
        # Get all active company credentials
        company_credentials = request.env['online.auth.company.credentials'].sudo().search([('is_active', '=', True)])
        
        # If there are credentials, use the first one as default
        default_credentials = company_credentials[0] if company_credentials else False
        
        values = {
            'company_credentials': company_credentials,
            'default_credentials': default_credentials,
        }
        
        return request.render('online_auth.auth_form_template', values)

    @http.route('/online/auth/submit', auth='public', website=True, methods=['POST'])
    def auth_submit(self, **kw):
        url = kw.get('url')
        db = kw.get('db')
        login = kw.get('login')
        password = kw.get('password')
        token = kw.get('token')
        
        # Check if we're using an existing credential
        credential_id = kw.get('credential_id')
        if credential_id:
            credential = request.env['online.auth.company.credentials'].sudo().browse(int(credential_id))
            if credential.exists():
                url = credential.url
                db = credential.database
                login = credential.login
                password = credential.password
                token = credential.token
                
                # Update last sync time
                credential.update_last_sync()

        # Save credentials if requested
        save_credentials = kw.get('save_credentials')
        if save_credentials:
            company_name = kw.get('company_name')
            if company_name:
                # Check if credentials with this company name already exist
                existing = request.env['online.auth.company.credentials'].sudo().search([
                    ('company_name', '=', company_name)
                ])
                
                if not existing:
                    # Create new credentials
                    request.env['online.auth.company.credentials'].sudo().create({
                        'company_name': company_name,
                        'url': url,
                        'database': db,
                        'login': login,
                        'password': password,
                        'token': token,
                        'is_active': True,
                    })

        request.session['online_odoo_url'] = url
        request.session['online_odoo_db'] = db
        request.session['online_odoo_login'] = login
        request.session['online_odoo_password'] = password
        request.session['online_odoo_token'] = token

        result = f"Authenticated to {url} with database '{db}' as {login}."
        if save_credentials and company_name:
            result += f" Credentials saved as '{company_name}'."
            
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
