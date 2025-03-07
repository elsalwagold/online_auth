# tests/test_sync_attendance.py
import logging
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)

class TestAttendanceSync(TransactionCase):

    def setUp(self):
        super(TestAttendanceSync, self).setUp()
        self.sync_wizard_model = self.env['attendance.sync.wizard']

    def test_sync_attendance(self):
        """Test syncing attendance records to the remote instance."""
        # Create an instance of the sync wizard (without any required fields)
        wizard = self.sync_wizard_model.create({})
        # Call the sync method
        result = wizard.action_sync_attendance()
        _logger.info("Sync action result: %s", result)
        # You can add assertions here based on your expected outcomes
        self.assertTrue(wizard.last_sync, "Last sync time should be updated after synchronization.")
