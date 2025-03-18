import xmlrpc.client
import logging
from datetime import datetime

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

# Remote instance credentials (update these values as needed)
REMOTE_URL = 'https://smartfitnesssa-fitness-gym.odoo.com'
REMOTE_DB = 'smartfitnesssa-fitness-gym-main-17599672'
REMOTE_USERNAME = 'accountant@smartfitness.com.sa'
REMOTE_PASSWORD = 'Sf@1475963'
REMOTE_TOKEN = 'bdc18716c1a86504b7955a7aec06d445f2a2a84c'


class AttendanceSyncWizard(models.TransientModel):
    _name = 'attendance.sync.wizard'
    _description = 'Wizard to sync local attendance records to a remote instance'

    last_sync = fields.Datetime(string="Last Sync", readonly=True)
    attendance_preview = fields.Text(string="Attendance Preview", readonly=True)
    sync_report = fields.Text(string="Synchronization Report", readonly=True)



    def action_test_authentication(self):
        """Tests the authentication with the remote Odoo instance."""
        _logger.info("Testing remote authentication...")
        try:
            common = xmlrpc.client.ServerProxy(f'{REMOTE_URL}/xmlrpc/2/common')
            uid = common.authenticate(REMOTE_DB, REMOTE_USERNAME, REMOTE_PASSWORD, {})
            if not uid:
                _logger.error("Authentication failed!")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Authentication Failed"),
                        'message': _("Could not authenticate with remote Odoo instance."),
                        'sticky': True,
                    },
                }
            _logger.info("Remote authentication successful. UID: %s", uid)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Success"),
                    'message': _("Successfully authenticated with remote Odoo instance."),
                    'sticky': False,
                },
            }
        except Exception as e:
            _logger.exception("Exception during authentication: %s", e)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Error"),
                    'message': _("Exception during authentication: %s") % str(e),
                    'sticky': True,
                },
            }

    def action_preview_attendance(self):
        """Opens a list view of attendance records to be synchronized."""

        # Find the correct views dynamically
        list_view_id = self.env.ref('hr_attendance.view_attendance_tree',
                                    raise_if_not_found=False)  # 'tree' → 'list' in Odoo 18
        form_view_id = self.env.ref('hr_attendance.view_attendance_form', raise_if_not_found=False)


        # Construct the views list (include only if they exist)
        views = []
        if list_view_id:
            views.append((list_view_id.id, 'list'))  # ✅ Use 'list' instead of 'tree'
        if form_view_id:
            views.append((form_view_id.id, 'form'))

        return {
            'type': 'ir.actions.act_window',
            'name': 'Attendance Records to Sync',
            'res_model': 'hr.attendance',
            'view_mode': 'list,form',  # ✅ Use 'list' instead of 'tree'
            'views': views or [(False, 'list')],  # ✅ Use 'list' instead of 'tree'
            'domain': [],  # ✅ You can filter records if needed
            'context': {'create': False},  # ✅ Disable record creation (optional)
            'target': 'new',  # ✅ Opens as a popup
        }

    def action_sync_attendance(self):
        _logger.info("Starting attendance synchronization process...")

        report_lines = []  # 🆕 Start collecting report data

        # Authentication process
        try:
            common = xmlrpc.client.ServerProxy(f'{REMOTE_URL}/xmlrpc/2/common')
            uid = common.authenticate(REMOTE_DB, REMOTE_USERNAME, REMOTE_PASSWORD, {})
            if not uid:
                raise ValueError("Authentication failed!")

            remote_obj = xmlrpc.client.ServerProxy(f'{REMOTE_URL}/xmlrpc/2/object')
            report_lines.append(f"✅ Authentication successful at {fields.Datetime.now()}\n")
        except Exception as e:
            _logger.error("Authentication Error: %s", e)
            report_lines.append(f"❌ Authentication failed: {str(e)}\n")
            self.sync_report = "\n".join(report_lines)
            return

        # Retrieve attendance records
        attendance_records = self.env['hr.attendance'].search([])
        report_lines.append(f"📊 Total attendance records found: {len(attendance_records)}\n")

        for record in attendance_records:
            report_lines.append(f"🔄 Processing Attendance ID: {record.id} (Employee: {record.employee_id.name})")

            # Collect missing fields
            missing_fields = []
            if not record.check_in:
                missing_fields.append("Check-in")
            if not record.check_out:
                missing_fields.append("Check-out")
            if not record.employee_id.work_email:
                missing_fields.append("Work Email")
            if not record.employee_id.biometric_device_id:
                missing_fields.append("Biometric Device ID")

            if missing_fields:
                report_lines.append(f"⚠️ Missing fields: {', '.join(missing_fields)}")
                continue  # Skip this record if critical fields are missing

            # Convert data for remote sync
            check_in = record.check_in.strftime('%Y-%m-%d %H:%M:%S') if record.check_in else False
            check_out = record.check_out.strftime('%Y-%m-%d %H:%M:%S') if record.check_out else False

            # Find remote employee or create new
            remote_employee_id = False
            existing_employee = remote_obj.execute_kw(
                REMOTE_DB, uid, REMOTE_PASSWORD,
                'hr.employee', 'search_read',
                [[('work_email', '=', record.employee_id.work_email)]],
                {'fields': ['id']}
            )
            if existing_employee:
                remote_employee_id = existing_employee[0]['id']
                report_lines.append(f"🔹 Employee found remotely with ID: {remote_employee_id}")
            else:
                employee_data = {
                    'name': record.employee_id.name,
                    'work_email': record.employee_id.work_email,
                    'biometric_device_id': record.employee_id.biometric_device_id,
                }
                remote_employee_id = remote_obj.execute_kw(
                    REMOTE_DB, uid, REMOTE_PASSWORD,
                    'hr.employee', 'create', [employee_data]
                )
                report_lines.append(f"✅ New employee created with ID: {remote_employee_id}")

            # Create attendance record remotely
            attendance_data = {
                'employee_id': remote_employee_id,
                'check_in': check_in,
                'check_out': check_out,
            }
            remote_attendance_id = remote_obj.execute_kw(
                REMOTE_DB, uid, REMOTE_PASSWORD,
                'hr.attendance', 'create', [attendance_data]
            )
            report_lines.append(f"✅ Remote attendance created with ID: {remote_attendance_id}")

        # Save report
        self.sync_report = "\n".join(report_lines)
        _logger.info("Synchronization completed. Report saved.")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Synchronization Completed"),
                'message': _("Report available in the wizard."),
                'sticky': False,
            },
        }

    # def action_sync_attendance(self):
    #     _logger.info("Starting attendance synchronization process...")
    #
    #     try:
    #         # Authenticate with remote Odoo
    #         common = xmlrpc.client.ServerProxy(f'{REMOTE_URL}/xmlrpc/2/common')
    #         uid = common.authenticate(REMOTE_DB, REMOTE_USERNAME, REMOTE_PASSWORD, {})
    #         if not uid:
    #             _logger.error("Remote authentication failed!")
    #             return {
    #                 'type': 'ir.actions.client',
    #                 'tag': 'display_notification',
    #                 'params': {
    #                     'title': _("Authentication Error"),
    #                     'message': _("Could not authenticate with remote Odoo instance."),
    #                     'sticky': True,
    #                 },
    #             }
    #         _logger.info("Remote authentication successful. UID: %s", uid)
    #         remote_obj = xmlrpc.client.ServerProxy(f'{REMOTE_URL}/xmlrpc/2/object')
    #     except Exception as e:
    #         _logger.exception("Exception during remote authentication: %s", e)
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': _("Authentication Exception"),
    #                 'message': _("An exception occurred during authentication: %s") % str(e),
    #                 'sticky': True,
    #             },
    #         }
    #
    #     # Retrieve local attendance records
    #     attendance_records = self.env['hr.attendance'].search([])
    #     _logger.info("Found %s local attendance records to sync.", len(attendance_records))
    #
    #     for record in attendance_records:
    #         _logger.info("Processing attendance record ID: %s", record.id)
    #
    #         try:
    #             check_in = record.check_in.strftime('%Y-%m-%d %H:%M:%S') if record.check_in else False
    #             check_out = record.check_out.strftime('%Y-%m-%d %H:%M:%S') if record.check_out else False
    #
    #             # Prepare search criteria (work email & biometric device ID)
    #             search_domain = []
    #             if record.employee_id.work_email:
    #                 search_domain.append(('work_email', '=', record.employee_id.work_email))
    #             if record.employee_id.biometric_device_id:
    #                 search_domain.append(('biometric_device_id', '=', record.employee_id.biometric_device_id))
    #
    #             remote_employee_id = False
    #
    #             # Search for employee in remote Odoo
    #             if search_domain:
    #                 existing_employee = remote_obj.execute_kw(
    #                     REMOTE_DB, uid, REMOTE_PASSWORD,
    #                     'hr.employee', 'search_read',
    #                     [search_domain], {'fields': ['id', 'name']}
    #                 )
    #
    #                 if existing_employee:
    #                     remote_employee_id = existing_employee[0]['id']
    #                     _logger.info("Found existing remote employee: %s (ID: %s)",
    #                                  existing_employee[0]['name'], remote_employee_id)
    #
    #             # If no matching employee found, create one
    #             if not remote_employee_id:
    #                 employee_data = {
    #                     'name': record.employee_id.name,
    #                     'work_email': record.employee_id.work_email or False,
    #                     'biometric_device_id': record.employee_id.biometric_device_id or False,
    #                 }
    #                 _logger.info("Creating new remote employee: %s", employee_data)
    #
    #                 try:
    #                     remote_employee_id = remote_obj.execute_kw(
    #                         REMOTE_DB, uid, REMOTE_PASSWORD,
    #                         'hr.employee', 'create', [employee_data]
    #                     )
    #                     _logger.info("Created remote employee '%s' with ID: %s",
    #                                  record.employee_id.name, remote_employee_id)
    #                 except Exception as emp_ex:
    #                     _logger.error("Error creating remote employee for '%s': %s",
    #                                   record.employee_id.name, emp_ex)
    #                     continue  # Skip attendance sync if employee creation fails
    #
    #             # Ensure attendance is correctly linked
    #             attendance_data = {
    #                 'check_in': check_in,
    #                 'check_out': check_out,
    #                 'employee_id': remote_employee_id,
    #             }
    #
    #             _logger.info("Creating remote attendance record: %s", attendance_data)
    #
    #             try:
    #                 remote_attendance_id = remote_obj.execute_kw(
    #                     REMOTE_DB, uid, REMOTE_PASSWORD,
    #                     'hr.attendance', 'create', [attendance_data]
    #                 )
    #                 _logger.info("Created remote attendance record with ID: %s", remote_attendance_id)
    #             except Exception as att_ex:
    #                 _logger.error("Error creating remote attendance for record ID %s: %s", record.id, att_ex)
    #
    #         except Exception as ex:
    #             _logger.exception("Exception processing attendance record ID %s: %s", record.id, ex)
    #
    #     self.last_sync = fields.Datetime.now()
    #     _logger.info("Attendance synchronization completed at %s", self.last_sync)
    #
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': _("Synchronization Completed"),
    #             'message': _("Attendance records have been synchronized successfully at %s") % self.last_sync,
    #             'sticky': False,
    #         },
    #     }

