"""
API client for interacting with external Odoo instances.
"""
import xmlrpc.client
import logging
import json
import requests
from .utils import log_error, validate_url

_logger = logging.getLogger(__name__)

class OdooApiClient:
    """
    Client for interacting with external Odoo instances via XML-RPC.
    """
    
    def __init__(self, url, db, username, password, token=None):
        """
        Initialize the Odoo API client.
        
        Args:
            url (str): The URL of the Odoo instance
            db (str): The database name
            username (str): The username for authentication
            password (str): The password for authentication
            token (str, optional): The API token for authentication
        """
        if not validate_url(url):
            raise ValueError("Invalid URL: {}".format(url))
        
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.password = password
        self.token = token
        self.uid = None
        self.common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(self.url))
        self.models = None
    
    def authenticate(self):
        """
        Authenticate to the Odoo instance.
        
        Returns:
            int: The user ID if authentication is successful, None otherwise
        """
        try:
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})
            if self.uid:
                self.models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.url))
                return self.uid
            return None
        except Exception as e:
            log_error("Authentication failed", e)
            return None
    
    def search_read(self, model, domain=None, fields=None, limit=None, offset=0, order=None):
        """
        Search and read records from the Odoo instance.
        
        Args:
            model (str): The model to search
            domain (list, optional): The search domain
            fields (list, optional): The fields to return
            limit (int, optional): The maximum number of records to return
            offset (int, optional): The number of records to skip
            order (str, optional): The order by clause
            
        Returns:
            list: The records matching the search criteria
        """
        if not self.uid or not self.models:
            if not self.authenticate():
                return []
        
        domain = domain or []
        fields = fields or []
        
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'search_read',
                [domain],
                {
                    'fields': fields,
                    'limit': limit,
                    'offset': offset,
                    'order': order,
                }
            )
        except Exception as e:
            log_error("Search read failed for model {}".format(model), e)
            return []
    
    def create(self, model, values):
        """
        Create a record in the Odoo instance.
        
        Args:
            model (str): The model to create a record in
            values (dict): The values for the new record
            
        Returns:
            int: The ID of the created record, or None if creation failed
        """
        if not self.uid or not self.models:
            if not self.authenticate():
                return None
        
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'create',
                [values]
            )
        except Exception as e:
            log_error("Create failed for model {}".format(model), e)
            return None
    
    def write(self, model, ids, values):
        """
        Update records in the Odoo instance.
        
        Args:
            model (str): The model to update records in
            ids (list): The IDs of the records to update
            values (dict): The values to update
            
        Returns:
            bool: True if the update was successful, False otherwise
        """
        if not self.uid or not self.models:
            if not self.authenticate():
                return False
        
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'write',
                [ids, values]
            )
        except Exception as e:
            log_error("Write failed for model {}".format(model), e)
            return False
    
    def unlink(self, model, ids):
        """
        Delete records from the Odoo instance.
        
        Args:
            model (str): The model to delete records from
            ids (list): The IDs of the records to delete
            
        Returns:
            bool: True if the deletion was successful, False otherwise
        """
        if not self.uid or not self.models:
            if not self.authenticate():
                return False
        
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'unlink',
                [ids]
            )
        except Exception as e:
            log_error("Unlink failed for model {}".format(model), e)
            return False 