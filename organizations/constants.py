"""Constants for organizations module."""

# Timezone choices for Location model
TIMEZONE_CHOICES = [
    # America
    ('America/New_York', 'America/New_York (EST/EDT)'),
    ('America/Chicago', 'America/Chicago (CST/CDT)'),
    ('America/Denver', 'America/Denver (MST/MDT)'),
    ('America/Los_Angeles', 'America/Los_Angeles (PST/PDT)'),
    ('America/Phoenix', 'America/Phoenix (MST)'),
    ('America/Toronto', 'America/Toronto (EST/EDT)'),
    ('America/Vancouver', 'America/Vancouver (PST/PDT)'),
    ('America/Mexico_City', 'America/Mexico_City (CST/CDT)'),
    ('America/Bogota', 'America/Bogota (COT)'),
    ('America/Lima', 'America/Lima (PET)'),
    ('America/Santiago', 'America/Santiago (CLT/CLST)'),
    ('America/Sao_Paulo', 'America/Sao_Paulo (BRT/BRST)'),
    ('America/Buenos_Aires', 'America/Buenos_Aires (ART)'),
    # Asia
    ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh (GMT+7)'),
    ('Asia/Bangkok', 'Asia/Bangkok (GMT+7)'),
    ('Asia/Jakarta', 'Asia/Jakarta (WIB)'),
    ('Asia/Singapore', 'Asia/Singapore (GMT+8)'),
    ('Asia/Hong_Kong', 'Asia/Hong_Kong (HKT)'),
    ('Asia/Shanghai', 'Asia/Shanghai (CST)'),
    ('Asia/Tokyo', 'Asia/Tokyo (JST)'),
    ('Asia/Seoul', 'Asia/Seoul (KST)'),
    ('Asia/Manila', 'Asia/Manila (PST)'),
    ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur (MYT)'),
    ('Asia/Taipei', 'Asia/Taipei (NST)'),
    ('Asia/Dubai', 'Asia/Dubai (GST)'),
    ('Asia/Riyadh', 'Asia/Riyadh (AST)'),
    ('Asia/Qatar', 'Asia/Qatar (AST)'),
    ('Asia/Kolkata', 'Asia/Kolkata (IST)'),
    ('Asia/Mumbai', 'Asia/Mumbai (IST)'),
    ('Asia/Karachi', 'Asia/Karachi (PKT)'),
    ('Asia/Dhaka', 'Asia/Dhaka (BST)'),
    ('Asia/Colombo', 'Asia/Colombo (IST)'),
    ('Asia/Yangon', 'Asia/Yangon (MMT)'),
    # Common UTC
    ('UTC', 'UTC'),
]
