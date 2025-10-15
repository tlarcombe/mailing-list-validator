"""
Output schema definition for the consolidated contact database.
"""

OUTPUT_FIELDS = [
    'EMAIL',
    'FIRSTNAME',
    'LASTNAME',
    'FULLNAME',
    'COMPANYNAME',
    'SMS',
    'LANDLINE_NUMBER',
    'WHATSAPP',
    'INTERESTS',
    'LINKEDIN',
    'FACEBOOK',
    'WEBSITE',
    'ADDRESS1',
    'ADDRESS2',
    'CITY',
    'COUNTRY',
    'POSTCODE'
]

# Mapping patterns for field detection (case-insensitive)
# Maps various input field names to our standardized output fields
FIELD_MAPPINGS = {
    'EMAIL': [
        'email', 'e-mail', 'email address', 'e_mail', 'mail',
        'hq email', 'primary contact email', 'contact email'
    ],
    'FULLNAME': [
        'fullname', 'full name', 'name', 'full_name',
        'contact name', 'primary contact'
    ],
    'FIRSTNAME': [
        'firstname', 'first name', 'first_name', 'fname',
        'given name', 'givenname'
    ],
    'COMPANYNAME': [
        'company', 'companyname', 'company name', 'company_name',
        'organization', 'organisation', 'org', 'firm',
        'investors', 'investor', 'investor name'
    ],
    'LASTNAME': [
        'lastname', 'last name', 'last_name', 'lname',
        'surname', 'family name', 'familyname'
    ],
    'SMS': [
        'sms', 'mobile', 'mobile number', 'mobile phone',
        'cell', 'cellphone', 'cell phone', 'mobile_phone'
    ],
    'LANDLINE_NUMBER': [
        'landline', 'landline number', 'phone', 'telephone',
        'phone number', 'tel', 'hq phone', 'primary contact phone'
    ],
    'WHATSAPP': [
        'whatsapp', 'whatsapp number', 'wa', 'whatsapp_number'
    ],
    'INTERESTS': [
        'interests', 'interest', 'tags', 'categories',
        'preferred industry', 'preferred verticals', 'verticals',
        'primary industry sector', 'description'
    ],
    'LINKEDIN': [
        'linkedin', 'linkedin url', 'linkedin profile',
        'linkedin_url', 'linkedin_profile'
    ],
    'FACEBOOK': [
        'facebook', 'facebook url', 'facebook profile',
        'facebook_url', 'facebook_profile'
    ],
    'WEBSITE': [
        'website', 'web', 'url', 'site', 'homepage',
        'web site', 'web_site', 'company website'
    ],
    'ADDRESS1': [
        'address1', 'address line 1', 'address_line_1',
        'address', 'street', 'street address',
        'hq address line 1', 'hq address'
    ],
    'ADDRESS2': [
        'address2', 'address line 2', 'address_line_2',
        'address line2', 'hq address line 2'
    ],
    'CITY': [
        'city', 'town', 'municipality',
        'hq city', 'hq location'
    ],
    'COUNTRY': [
        'country', 'country/territory', 'nation',
        'hq country', 'hq country/territory'
    ],
    'POSTCODE': [
        'postcode', 'post code', 'postal code', 'zip',
        'zip code', 'postal_code', 'zipcode',
        'state_province_region', 'hq post code'
    ]
}


def get_output_template():
    """
    Returns an empty dictionary with all output fields initialized to empty strings.
    """
    return {field: '' for field in OUTPUT_FIELDS}
