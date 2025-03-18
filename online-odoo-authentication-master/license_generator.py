#!/usr/bin/env python3
"""
Online Odoo Authentication - License Key Generator

This script generates license keys for the Online Odoo Authentication module.
It can be used to create license keys for customers without needing access to the Odoo instance.

Usage:
    python license_generator.py --company "Customer Name" --days 365 --type commercial --users 10 --features "attendance_sync,employee_mapping,api_access"

Author: Sabry Youssef
Email: sabry_youssef@me.com
"""

import argparse
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timedelta


def generate_license_key(company_name, expiration_days=365, license_type="commercial", max_users=0, features=None):
    """Generate a license key with specific parameters."""
    # Generate a unique identifier
    unique_id = str(uuid.uuid4())
    
    # Get current timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    # Create the base string for the license key
    key_base = f"{company_name}-{timestamp}-{unique_id}"
    
    # Generate the license key using SHA-256
    license_key = hashlib.sha256(key_base.encode()).hexdigest()[:32].upper()
    
    # Calculate expiration date
    creation_date = datetime.now()
    expiration_date = creation_date + timedelta(days=expiration_days)
    
    # Create license data dictionary
    license_data = {
        'license_key': license_key,
        'company_name': company_name,
        'creation_date': creation_date.strftime('%Y-%m-%d %H:%M:%S'),
        'expiration_date': expiration_date.strftime('%Y-%m-%d %H:%M:%S'),
        'license_type': license_type,
        'is_trial': license_type.lower() == 'trial',
        'max_users': max_users,
        'features': features or '',
    }
    
    return license_key, license_data


def save_license_data(license_data, output_dir='.'):
    """Save license data to JSON file."""
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create filename based on company name and timestamp
    company_name = license_data['company_name'].replace(' ', '_').lower()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"{company_name}_license_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Write license data to file
    with open(filepath, 'w') as f:
        json.dump(license_data, f, indent=4)
    
    return filepath


def main():
    """Main function to parse arguments and generate license."""
    parser = argparse.ArgumentParser(description='Generate license keys for Online Odoo Authentication module')
    
    parser.add_argument('--company', required=True, help='Customer company name')
    parser.add_argument('--days', type=int, default=365, help='License validity in days (default: 365)')
    parser.add_argument('--type', choices=['trial', 'basic', 'standard', 'premium', 'enterprise', 'commercial'], 
                        default='commercial', help='License type (default: commercial)')
    parser.add_argument('--users', type=int, default=0, help='Maximum number of users (0 for unlimited)')
    parser.add_argument('--features', default='', help='Comma-separated list of enabled features')
    parser.add_argument('--output', default='.', help='Output directory for license files')
    
    args = parser.parse_args()
    
    # Generate license key
    license_key, license_data = generate_license_key(
        company_name=args.company,
        expiration_days=args.days,
        license_type=args.type,
        max_users=args.users,
        features=args.features
    )
    
    # Save license data to file
    filepath = save_license_data(license_data, args.output)
    
    # Print license information
    print("\n=== License Generated Successfully ===")
    print(f"License Key: {license_key}")
    print(f"Company: {args.company}")
    print(f"Type: {args.type}")
    print(f"Expiration: {license_data['expiration_date']}")
    print(f"Max Users: {args.users if args.users > 0 else 'Unlimited'}")
    print(f"Features: {args.features}")
    print(f"\nLicense data saved to: {filepath}")
    print("\nInstructions:")
    print("1. Provide this license key to the customer")
    print("2. The customer should enter this key in Online Authentication > Configuration > License Management")
    print("3. After saving, they should click 'Activate License' to validate and activate it")
    print("=================================\n")


if __name__ == "__main__":
    main() 