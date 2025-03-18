import xmlrpc.client
import logging
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Remove hardcoded credentials
# REMOTE_URL = 'https://smartfitnesssa-fitness-gym.odoo.com'
# REMOTE_DB = 'smartfitnesssa-fitness-gym-main-17599672'
# REMOTE_USERNAME = 'accountant@smartfitness.com.sa'
# REMOTE_PASSWORD = 'Sf@1475963'
# REMOTE_TOKEN = 'bdc18716c1a86504b7955a7aec06d445f2a2a84c'


class AttendanceSyncWizard(models.TransientModel):
    _name = 'attendance.sync.wizard'
    _description = 'Wizard to sync local attendance records to a remote instance'

    company_credentials_id = fields.Many2one(
        'online.auth.company.credentials',
        string='Company Credentials',
        required=True,
        domain=[('is_active', '=', True)],
        help='Select the company credentials to use for synchronization'
    )
    last_sync = fields.Datetime(string="Last Sync", readonly=True)
    attendance_preview = fields.Text(string="Attendance Preview", readonly=True)
    sync_report = fields.Text(string="Synchronization Report", readonly=True)
    skip_existing = fields.Boolean(string="Skip Existing Records", default=True, 
                                  help="If checked, records that already exist on the remote system will be skipped")
    update_existing = fields.Boolean(string="Update Existing Records", default=False,
                                    help="If checked, existing records will be updated instead of skipped")

    @api.onchange('company_credentials_id')
    def _onchange_company_credentials_id(self):
        if self.company_credentials_id:
            self.last_sync = self.company_credentials_id.last_sync

    def _check_license(self):
        """Check if the license is valid before proceeding."""
        return self.env['online.auth.license'].validate_license()

    def action_test_authentication(self):
        """Tests the authentication with the remote Odoo instance."""
        # Validate license first
        if not self._check_license():
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("License Error"),
                    'message': _("Your license is not valid or has expired. Please contact support."),
                    'sticky': True,
                    'type': 'danger',
                },
            }
            
        _logger.info("Testing remote authentication...")
        
        if not self.company_credentials_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Error"),
                    'message': _("Please select company credentials first."),
                    'sticky': True,
                    'type': 'danger',
                },
            }
            
        try:
            common = xmlrpc.client.ServerProxy(f'{self.company_credentials_id.url}/xmlrpc/2/common')
            uid = common.authenticate(
                self.company_credentials_id.database,
                self.company_credentials_id.login,
                self.company_credentials_id.password,
                {}
            )
            if not uid:
                _logger.error("Authentication failed!")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Authentication Failed"),
                        'message': _("Could not authenticate with remote Odoo instance."),
                        'sticky': True,
                        'type': 'danger',
                    },
                }
            _logger.info("Remote authentication successful. UID: %s", uid)
            
            # Update last sync time
            self.company_credentials_id.update_last_sync()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Success"),
                    'message': _("Successfully authenticated with remote Odoo instance."),
                    'sticky': False,
                    'type': 'success',
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
                    'type': 'danger',
                },
            }

    def action_preview_attendance(self):
        """Previews attendance records that will be synchronized."""
        # Validate license first
        if not self._check_license():
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("License Error"),
                    'message': _("Your license is not valid or has expired. Please contact support."),
                    'sticky': True,
                    'type': 'danger',
                },
            }
            
        if not self.company_credentials_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Error"),
                    'message': _("Please select company credentials first."),
                    'sticky': True,
                    'type': 'danger',
                },
            }
            
        # Get attendance records that haven't been synced yet
        attendance_records = self.env['hr.attendance'].search([])
        
        if not attendance_records:
            self.attendance_preview = _("No attendance records found to synchronize.")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("No Records"),
                    'message': _("No attendance records found to synchronize."),
                    'sticky': False,
                    'type': 'warning',
                },
            }
            
        # Generate preview text
        preview_lines = [_("Found %s attendance records to synchronize:") % len(attendance_records)]
        
        for record in attendance_records:
            employee = record.employee_id
            check_in = record.check_in.strftime('%Y-%m-%d %H:%M:%S') if record.check_in else 'N/A'
            check_out = record.check_out.strftime('%Y-%m-%d %H:%M:%S') if record.check_out else 'N/A'
            
            # Check for missing required fields
            missing_fields = []
            if not employee:
                missing_fields.append("Employee")
            elif not employee.work_email:
                missing_fields.append("Work Email")
                
            if not record.check_in:
                missing_fields.append("Check In")
                
            status = _("Ready") if not missing_fields else _("Missing: %s") % ", ".join(missing_fields)
            
            preview_lines.append(_(
                "Employee: %s, Check In: %s, Check Out: %s, Status: %s"
            ) % (
                employee.name if employee else 'N/A',
                check_in,
                check_out,
                status
            ))
            
        self.attendance_preview = "\n".join(preview_lines)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'attendance.sync.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }

    def action_sync_attendance(self):
        """Syncs local attendance records to the remote instance."""
        # Validate license first
        if not self._check_license():
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("License Error"),
                    'message': _("Your license is not valid or has expired. Please contact support."),
                    'sticky': True,
                    'type': 'danger',
                },
            }
            
        if not self.company_credentials_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Error"),
                    'message': _("Please select company credentials first."),
                    'sticky': True,
                    'type': 'danger',
                },
            }
            
        _logger.info("Starting attendance synchronization process...")
        report_lines = []
        report_lines.append(f"🔄 Starting synchronization at {fields.Datetime.now()}")
        report_lines.append(f"⚙️ Options: Skip Existing: {self.skip_existing}, Update Existing: {self.update_existing}")
        
        # Authentication process
        try:
            common = xmlrpc.client.ServerProxy(f'{self.company_credentials_id.url}/xmlrpc/2/common')
            uid = common.authenticate(
                self.company_credentials_id.database,
                self.company_credentials_id.login,
                self.company_credentials_id.password,
                {}
            )
            if not uid:
                raise ValueError("Authentication failed!")

            remote_obj = xmlrpc.client.ServerProxy(f'{self.company_credentials_id.url}/xmlrpc/2/object')
            report_lines.append(f"✅ Authentication successful at {fields.Datetime.now()}")
        except Exception as e:
            _logger.error("Authentication Error: %s", e)
            report_lines.append(f"❌ Authentication failed: {str(e)}")
            self.sync_report = "\n".join(report_lines)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Authentication Error"),
                    'message': _("Failed to authenticate with remote Odoo instance."),
                    'sticky': True,
                    'type': 'danger',
                },
            }

        # Retrieve attendance records
        attendance_records = self.env['hr.attendance'].search([])
        report_lines.append(f"📊 Total attendance records found: {len(attendance_records)}")
        
        # Initialize counters
        success_count = 0
        failed_count = 0
        skipped_count = 0
        updated_count = 0
        existing_count = 0
        
        for record in attendance_records:
            employee = record.employee_id
            employee_name = employee.name if employee else 'Unknown'
            report_lines.append(f"🔄 Processing Attendance ID: {record.id} (Employee: {employee_name})")
            
            # Create sync report record
            sync_report_vals = {
                'employee_name': employee_name,
                'biometric_device_id': employee.biometric_device_id if employee else '',
                'work_email': employee.work_email if employee and employee.work_email else '',
                'synced_fields': '',
                'empty_fields': '',
                'status': 'success',
            }
            
            # Collect missing fields
            missing_fields = []
            if not employee:
                missing_fields.append("Employee")
            elif not employee.work_email:
                missing_fields.append("Work Email")
            if not record.check_in:
                missing_fields.append("Check-in")
                
            if missing_fields:
                report_lines.append(f"⚠️ Missing fields: {', '.join(missing_fields)}")
                sync_report_vals['empty_fields'] = ', '.join(missing_fields)
                sync_report_vals['status'] = 'failed'
                self.env['attendance.sync.report'].create(sync_report_vals)
                skipped_count += 1
                continue  # Skip this record if critical fields are missing
                
            try:
                # Convert data for remote sync
                check_in = record.check_in.strftime('%Y-%m-%d %H:%M:%S') if record.check_in else False
                check_out = record.check_out.strftime('%Y-%m-%d %H:%M:%S') if record.check_out else False
                
                # Find remote employee or create new
                remote_employee_id = False
                existing_employee = remote_obj.execute_kw(
                    self.company_credentials_id.database, uid, self.company_credentials_id.password,
                    'hr.employee', 'search_read',
                    [[('work_email', '=', employee.work_email)]],
                    {'fields': ['id']}
                )
                
                if existing_employee:
                    remote_employee_id = existing_employee[0]['id']
                    report_lines.append(f"🔹 Employee found remotely with ID: {remote_employee_id}")
                else:
                    employee_data = {
                        'name': employee.name,
                        'work_email': employee.work_email,
                        'biometric_device_id': employee.biometric_device_id or '',
                    }
                    remote_employee_id = remote_obj.execute_kw(
                        self.company_credentials_id.database, uid, self.company_credentials_id.password,
                        'hr.employee', 'create', [employee_data]
                    )
                    report_lines.append(f"✅ New employee created with ID: {remote_employee_id}")
                
                # Check if attendance record already exists
                existing_attendance = False
                if self.skip_existing or self.update_existing:
                    # Search for existing attendance with same employee and check-in time
                    domain = [
                        ('employee_id', '=', remote_employee_id),
                        ('check_in', '=', check_in)
                    ]
                    existing_attendance = remote_obj.execute_kw(
                        self.company_credentials_id.database, uid, self.company_credentials_id.password,
                        'hr.attendance', 'search_read',
                        [domain],
                        {'fields': ['id']}
                    )
                
                if existing_attendance:
                    existing_id = existing_attendance[0]['id']
                    report_lines.append(f"🔍 Found existing attendance record with ID: {existing_id}")
                    existing_count += 1
                    
                    if self.update_existing:
                        # Update the existing record
                        attendance_data = {
                            'check_out': check_out,
                        }
                        remote_obj.execute_kw(
                            self.company_credentials_id.database, uid, self.company_credentials_id.password,
                            'hr.attendance', 'write',
                            [[existing_id], attendance_data]
                        )
                        report_lines.append(f"🔄 Updated existing attendance record with ID: {existing_id}")
                        
                        # Update sync report
                        sync_report_vals['synced_fields'] = 'check_out'
                        self.env['attendance.sync.report'].create(sync_report_vals)
                        updated_count += 1
                    else:
                        # Skip the record
                        report_lines.append(f"⏭️ Skipped existing attendance record")
                        
                        # Update sync report
                        sync_report_vals['status'] = 'skipped'
                        sync_report_vals['empty_fields'] = 'Record already exists'
                        self.env['attendance.sync.report'].create(sync_report_vals)
                        skipped_count += 1
                else:
                    # Create attendance record remotely
                    attendance_data = {
                        'employee_id': remote_employee_id,
                        'check_in': check_in,
                        'check_out': check_out,
                    }
                    
                    remote_attendance_id = remote_obj.execute_kw(
                        self.company_credentials_id.database, uid, self.company_credentials_id.password,
                        'hr.attendance', 'create', [attendance_data]
                    )
                    
                    report_lines.append(f"✅ Remote attendance created with ID: {remote_attendance_id}")
                    
                    # Update sync report
                    sync_report_vals['synced_fields'] = 'employee_id, check_in, check_out'
                    self.env['attendance.sync.report'].create(sync_report_vals)
                    success_count += 1
                
            except Exception as e:
                _logger.error("Error syncing attendance record %s: %s", record.id, str(e))
                report_lines.append(f"❌ Error: {str(e)}")
                
                # Update sync report
                sync_report_vals['status'] = 'failed'
                sync_report_vals['empty_fields'] = str(e)
                self.env['attendance.sync.report'].create(sync_report_vals)
                failed_count += 1
        
        # Update last sync time
        self.last_sync = fields.Datetime.now()
        self.company_credentials_id.update_last_sync()
        
        # Add summary to report
        report_lines.append("\n📊 Synchronization Summary:")
        report_lines.append(f"✅ Successfully synchronized: {success_count}")
        report_lines.append(f"🔄 Updated existing records: {updated_count}")
        report_lines.append(f"⏭️ Skipped existing records: {skipped_count - updated_count}")
        report_lines.append(f"❌ Failed to synchronize: {failed_count}")
        report_lines.append(f"⚠️ Skipped due to missing data: {skipped_count - (existing_count - updated_count)}")
        report_lines.append(f"🕒 Completed at: {self.last_sync}")
        
        # Save report
        self.sync_report = "\n".join(report_lines)
        _logger.info("Synchronization completed. Report saved.")
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'attendance.sync.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
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

