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

    def action_sync_attendance(self):
        _logger.info("Starting attendance synchronization process...")
        try:
            # Authenticate with remote instance
            common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(REMOTE_URL))
            uid = common.authenticate(REMOTE_DB, REMOTE_USERNAME, REMOTE_PASSWORD, {})
            if not uid:
                _logger.error("Remote authentication failed!")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Authentication Error"),
                        'message': _("Could not authenticate with remote Odoo instance."),
                        'sticky': True,
                    },
                }
            _logger.info("Remote authentication successful. UID: %s", uid)
            remote_obj = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(REMOTE_URL))
        except Exception as e:
            _logger.exception("Exception during remote authentication: %s", e)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Authentication Exception"),
                    'message': _("An exception occurred during remote authentication: %s") % e,
                    'sticky': True,
                },
            }

        # Retrieve local attendance records
        attendance_records = self.env['hr.attendance'].search([])
        _logger.info("Found %s local attendance records to sync.", len(attendance_records))

        for record in attendance_records:
            _logger.info("Processing attendance record ID: %s with mapping_id: %s", record.id, record.mapping_id)
            try:
                check_in = record.check_in.strftime('%Y-%m-%d %H:%M:%S') if record.check_in else False
                check_out = record.check_out.strftime('%Y-%m-%d %H:%M:%S') if record.check_out else False

                # For remote search: if mapping_id is not 'New', you might want to check if it exists.
                # (Since our remote model does not use mapping_id, we simply log and skip the search.)
                if record.mapping_id != 'New':
                    _logger.info("Would search remote attendance for mapping_id '%s' here.", record.mapping_id)
                else:
                    _logger.warning("Attendance record ID %s has mapping_id 'New'. Skipping remote search.", record.id)

                # Always create a new remote employee record using the work email.
                # (No search is done—this means duplicate employees might be created if not handled otherwise.)
                remote_employee_id = False
                _logger.info("Processing local employee - ID: %s, Name: %s, Work Email: %s",
                             record.employee_id.id,
                             record.employee_id.name,
                             record.employee_id.work_email)

                if record.employee_id and record.employee_id.work_email:
                    employee_data = {
                        'name': record.employee_id.name,
                        'work_email': record.employee_id.work_email,
                        # Add additional fields as needed.
                    }
                    _logger.info("Sending employee data to Odoo.sh: %s", employee_data)
                    try:
                        remote_employee_id = remote_obj.execute_kw(
                            REMOTE_DB, uid, REMOTE_PASSWORD,
                            'hr.employee', 'create', [employee_data]
                        )
                        _logger.info("Created remote employee '%s' with ID: %s", record.employee_id.name, remote_employee_id)
                    except Exception as emp_ex:
                        _logger.error("Error creating remote employee for '%s': %s", record.employee_id.name, emp_ex)
                else:
                    _logger.warning("Local employee for attendance record ID %s does not have a work email. Skipping employee creation.", record.id)

                # Build attendance data without the mapping_id field because remote model does not support it.
                attendance_data = {
                    'check_in': check_in,
                    'check_out': check_out,
                }
                if remote_employee_id:
                    attendance_data['employee_id'] = remote_employee_id

                _logger.info("Creating remote attendance record with data: %s", attendance_data)
                try:
                    remote_attendance_id = remote_obj.execute_kw(
                        REMOTE_DB, uid, REMOTE_PASSWORD,
                        'hr.attendance', 'create', [attendance_data]
                    )
                    _logger.info("Created remote attendance record with remote ID: %s", remote_attendance_id)
                except Exception as att_ex:
                    # If the error indicates that the employee is already checked in, log it and continue.
                    err_str = str(att_ex)
                    if "already checked in" in err_str:
                        _logger.warning("Remote validation error: %s", err_str)
                    else:
                        _logger.error("Error creating remote attendance record for local record ID %s: %s", record.id, att_ex)
            except Exception as ex:
                _logger.exception("Exception processing attendance record ID %s: %s", record.id, ex)

        self.last_sync = fields.Datetime.now()
        _logger.info("Attendance synchronization completed at %s", self.last_sync)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Synchronization Completed"),
                'message': _("Attendance records have been synchronized successfully at %s") % self.last_sync,
                'sticky': False,
            },
        }
