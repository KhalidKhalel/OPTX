# backend/phone_lookup.py
"""
OPTX - Phone Carrier & CNAM Lookup Module
Handles real-time API lookups and local database enrichment.
"""

import re
import requests
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any
from functools import lru_cache
import logging
# Note: NANPA functions removed - using LocalCallingGuide API only

logger = logging.getLogger(__name__)

# API endpoints
LOCALCALLING_API = "https://www.localcallingguide.com/xmlprefix.php"

# Carrier SMS/MMS Gateway Database
# Maps carrier names (or partial matches) to their gateway addresses
CARRIER_GATEWAYS = {
    # Major US Carriers
    "verizon": {"sms": "@vtext.com", "mms": "@vzwpix.com", "wireless": True},
    "at&t": {"sms": "@txt.att.net", "mms": "@mms.att.net", "wireless": True},
    "att": {"sms": "@txt.att.net", "mms": "@mms.att.net", "wireless": True},
    "cingular": {"sms": "@txt.att.net", "mms": "@mms.att.net", "wireless": True},
    "t-mobile": {"sms": "@tmomail.net", "mms": "@tmomail.net", "wireless": True},
    "tmobile": {"sms": "@tmomail.net", "mms": "@tmomail.net", "wireless": True},
    "sprint": {"sms": "@messaging.sprintpcs.com", "mms": "@pm.sprint.com", "wireless": True},
    "us cellular": {"sms": "@email.uscc.net", "mms": "@mms.uscc.net", "wireless": True},
    "boost": {"sms": "@sms.myboostmobile.com", "mms": "@myboostmobile.com", "wireless": True},
    "cricket": {"sms": "@sms.cricketwireless.net", "mms": "@mms.cricketwireless.net", "wireless": True},
    "metro": {"sms": "@mymetropcs.com", "mms": "@mymetropcs.com", "wireless": True},
    "metropcs": {"sms": "@mymetropcs.com", "mms": "@mymetropcs.com", "wireless": True},
    "virgin": {"sms": "@vmobl.com", "mms": "@vmpix.com", "wireless": True},
    "tracfone": {"sms": "@mmst5.tracfone.com", "mms": "@mmst5.tracfone.com", "wireless": True},
    "straight talk": {"sms": "@vtext.com", "mms": "@mypixmessages.com", "wireless": True},
    "google fi": {"sms": "@msg.fi.google.com", "mms": "@msg.fi.google.com", "wireless": True},
    "xfinity": {"sms": "@vtext.com", "mms": "@mypixmessages.com", "wireless": True},
    "spectrum": {"sms": "@vtext.com", "mms": "@mypixmessages.com", "wireless": True},
    # Regional Carriers
    "c spire": {"sms": "@cspire1.com", "mms": "@cspire1.com", "wireless": True},
    "consumer cellular": {"sms": "@mailmymobile.net", "mms": None, "wireless": True},
    # Landline/VoIP (no SMS gateway)
    "bellsouth": {"sms": None, "mms": None, "wireless": False},
    "centurylink": {"sms": None, "mms": None, "wireless": False},
    "frontier": {"sms": None, "mms": None, "wireless": False},
    "windstream": {"sms": None, "mms": None, "wireless": False},
    "cox": {"sms": None, "mms": None, "wireless": False},
    "comcast": {"sms": None, "mms": None, "wireless": False},
    "vonage": {"sms": None, "mms": None, "wireless": False},
    "bandwidth": {"sms": None, "mms": None, "wireless": False},
}

# US State abbreviation to full name mapping
STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
    "PR": "Puerto Rico", "VI": "Virgin Islands", "GU": "Guam"
}

# Carrier legal name to consumer-friendly name mapping
CARRIER_FRIENDLY_NAMES = {
    "OMNIPOINT COMMUNICATIONS": "T-Mobile",
    "T-MOBILE USA": "T-Mobile",
    "METROPCS": "T-Mobile (Metro)",
    "NEW CINGULAR WIRELESS": "AT&T",
    "CINGULAR WIRELESS": "AT&T",
    "AT&T MOBILITY": "AT&T",
    "CELLCO PARTNERSHIP": "Verizon",
    "VERIZON WIRELESS": "Verizon",
    "SPRINT SPECTRUM": "T-Mobile (Sprint)",
    "SPRINT PCS": "T-Mobile (Sprint)",
    "US CELLULAR": "US Cellular",
    "UNITED STATES CELLULAR": "US Cellular",
    "CRICKET": "AT&T (Cricket)",
    "BOOST": "T-Mobile (Boost)",
    "GOOGLE VOICE": "Google Voice",
    "BANDWIDTH": "Bandwidth.com",
    "LEVEL 3": "Lumen (Level 3)",
    "COMCAST": "Xfinity",
    "XFINITY": "Xfinity",
    "VONAGE": "Vonage",
    "MAGICJACK": "magicJack",
    "TRACFONE": "TracFone",
    "STRAIGHT TALK": "Straight Talk",
}


def get_friendly_name(company_name: str) -> Optional[str]:
    """Convert legal carrier name to consumer-friendly name."""
    if not company_name:
        return None
    upper = company_name.upper()
    for key, friendly in CARRIER_FRIENDLY_NAMES.items():
        if key in upper:
            return friendly
    # Return cleaned-up original name
    return company_name.replace(", LLC", "").replace(" - ", " ").strip()


def normalize_phone(phone: str) -> str:
    """
    Cleans phone number input for consistent lookup.
    Removes all non-digit characters and strips a leading '1' if present for US numbers.
    """
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]
    return digits


def parse_phone(phone: str) -> Dict[str, str]:
    """Parse phone number into NPA (area code), NXX (prefix), and line number."""
    digits = normalize_phone(phone)
    if len(digits) != 10:
        raise ValueError(f"Invalid phone number: {phone}")
    
    return {
        "npa": digits[:3],  # Area code
        "nxx": digits[3:6],  # Prefix
        "line": digits[6:],  # Line number
        "formatted": f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    }


@lru_cache(maxsize=500)
def lookup_cnam(phone: str) -> Dict[str, Any]:
    """
    Caller ID Name (CNAM) lookup.
    
    NOTE: CNAM APIs require signup/API keys:
    - Twilio Lookup - paid, $0.01/lookup
    - Telnyx - paid, $0.003/lookup
    - Telebroad - requires Telebroad account
    """
    digits = normalize_phone(phone)
    
    result = {
        "name": None,
        "source": {
            "name": "CNAM Database",
            "url": None,
            "description": "Caller ID Name from carrier LIDB database",
            "removal": "Contact your carrier to change your 'Caller ID Name' or 'Share Name ID' setting."
        },
        "error": None,
        "note": "CNAM lookup not available - requires carrier database access"
    }
    
    # Return without making API call - no free CNAM API available
    result["error"] = "CNAM lookup not available"
    
    return result


def get_carrier_gateway(carrier_name: str) -> Dict[str, Any]:
    """
    Look up SMS/MMS gateway addresses for a carrier.
    Returns gateway info if carrier is found in database.
    """
    if not carrier_name:
        return {"sms_gateway": None, "mms_gateway": None, "is_wireless": None}
    
    carrier_lower = carrier_name.lower()
    
    # Try to find a matching carrier
    for key, gateway_info in CARRIER_GATEWAYS.items():
        if key in carrier_lower:
            return {
                "sms_gateway": gateway_info["sms"],
                "mms_gateway": gateway_info["mms"],
                "is_wireless": gateway_info["wireless"]
            }
    
    # No carrier match found
    return {"sms_gateway": None, "mms_gateway": None, "is_wireless": None}


@lru_cache(maxsize=500)
def lookup_carrier(phone: str) -> Dict[str, Any]:
    """
    Primary carrier lookup function using LocalCallingGuide.com API.
    Retrieves real-time carrier, rate center, LATA, OCN, and switch data.
    Enriches results with NANPA database data for assignment history.
    """
    parsed = parse_phone(phone)
    
    # Get the first digit of the line number (X in NPA-NXX-X)
    thousands_block = parsed["line"][0] if parsed["line"] else "0"
    
    result = {
        "carrier": None,
        "rate_center": None,
        "state": None,
        "lata": None,
        "ocn": None,
        "switch_clli": None,
        "line_type": None,
        "thousands_block": thousands_block,
        "is_voip": False,
        "is_valid": False,
        "is_wireless": False,
        "last_verified": None,
        "source": {
            "name": "LocalCallingGuide.com",
            "url": f"https://www.localcallingguide.com/xmlprefix.php?npa={parsed['npa']}&nxx={parsed['nxx']}",
            "description": "Public FCC/NANPA telecom numbering data (NPA-NXX-X)",
            "removal": "This is public telecom assignment data from FCC/NANPA. It cannot be removed as it's part of the phone numbering system."
        },
        "error": None
    }
    
    try:
        response = requests.get(
            LOCALCALLING_API,
            params={"npa": parsed["npa"], "nxx": parsed["nxx"]},
            timeout=10,
            headers={"User-Agent": "OPTX Privacy Tool"}
        )
        
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            
            # Find ALL prefix data blocks
            all_prefix_data = root.findall(".//prefixdata")
            
            # Note: Using module-level CARRIER_FRIENDLY_NAMES and get_friendly_name()
            
            # Find X=A block (NPA-NXX level) - original carrier (CO code holder)
            npa_nxx_block = None
            for prefix_data in all_prefix_data:
                x_value = prefix_data.findtext("x")
                if x_value == "A":
                    npa_nxx_block = prefix_data
                    break

            # Find specific thousands block (X=digit) - THIS HAS THE CORRECT UDATE
            thousands_block_data = None
            for prefix_data in all_prefix_data:
                x_value = prefix_data.findtext("x")
                if x_value == thousands_block:
                    thousands_block_data = prefix_data
                    break
            
            # Use the specific X block if available, otherwise fall back to X=A
            # The X-specific block has the correct udate, coordinates, and switch info
            use_block = thousands_block_data if thousands_block_data is not None else npa_nxx_block
            if use_block is None and all_prefix_data:
                use_block = all_prefix_data[0]
            
            if use_block is not None:
                # Extract carrier info from LCG (this is CLEC infrastructure, not actual carrier)
                # We'll override this with NANPA data later
                company = use_block.findtext("company-name")
                if company:
                    result["carrier"] = company
                    result["carrier_friendly"] = get_friendly_name(company)
                
                # Rate center (city)
                rc = use_block.findtext("rc")
                if rc:
                    result["rate_center"] = rc
                
                # State
                state = use_block.findtext("region")
                if state:
                    result["state"] = state
                
                # LATA
                lata = use_block.findtext("lata")
                if lata:
                    result["lata"] = lata
                
                # OCN (Operating Company Number) - will be overridden by NANPA
                ocn = use_block.findtext("ocn")
                if ocn:
                    result["ocn"] = ocn
                
                # Switch CLLI code - try use_block first, fallback to X=A block
                switch = use_block.findtext("switch")
                if not switch and npa_nxx_block is not None:
                    switch = npa_nxx_block.findtext("switch")
                if switch:
                    result["switch_clli"] = switch
                
                # Switch type - try use_block first, fallback to X=A block
                switch_type = use_block.findtext("switchtype")
                if not switch_type and npa_nxx_block is not None:
                    switch_type = npa_nxx_block.findtext("switchtype")
                if switch_type:
                    result["switch_type"] = switch_type
                
                # Switch name (human readable) - try use_block first, fallback to X=A
                switch_name = use_block.findtext("switchname")
                if not switch_name and npa_nxx_block is not None:
                    switch_name = npa_nxx_block.findtext("switchname")
                if switch_name:
                    result["switch_name"] = switch_name
                
                # Company type - determines line type
                company_type = use_block.findtext("company-type")
                if company_type:
                    type_map = {"W": "Wireless", "C": "CLEC", "I": "ILEC", "L": "Landline", "V": "VoIP"}
                    result["line_type"] = type_map.get(company_type, company_type)
                    result["line_type_code"] = company_type
                    result["is_valid"] = True
                
                # ILEC (Incumbent Local Exchange Carrier) - ORIGINAL block owner
                ilec_name = use_block.findtext("ilec-name")
                if ilec_name:
                    result["ilec_name"] = ilec_name
                    result["original_carrier"] = {
                        "company": ilec_name,
                        "company_friendly": get_friendly_name(ilec_name),
                        "ocn": use_block.findtext("ilec-ocn")
                    }
                
                ilec_ocn = use_block.findtext("ilec-ocn")
                if ilec_ocn:
                    result["ilec_ocn"] = ilec_ocn
                
                # Effective date (when this assignment became active)
                effdate = use_block.findtext("effdate")
                if effdate:
                    result["effective_date"] = effdate
                

                
                # Last verified/updated date - use X-specific block for accurate date!
                udate = use_block.findtext("udate")
                if udate:
                    result["last_verified"] = udate
                
                # Rate center coordinates
                rc_lat = use_block.findtext("rc-lat")
                rc_lon = use_block.findtext("rc-lon")
                if rc_lat and rc_lon:
                    result["coordinates"] = {"lat": float(rc_lat), "lon": float(rc_lon)}
                
                # Exchange
                exch = use_block.findtext("exch")
                if exch:
                    result["exchange"] = exch
                
                # Switch type (POI=Point of Interconnection, etc)
                switchtype = use_block.findtext("switchtype")
                if switchtype:
                    switch_type_map = {
                        "POI": "Point of Interconnection",
                        "STP": "Signal Transfer Point",
                        "SSP": "Service Switching Point",
                        "ISDN": "ISDN Switch",
                        "HOST": "Host Switch",
                        "REMOTE": "Remote Switch",
                        "TG": "Tandem Gateway",
                        "TANDEM": "Tandem Switch",
                        "EO": "End Office",
                        "5ESS": "5ESS Switch",
                        "DMS": "DMS Switch",
                        "GTD-5": "GTD-5 Switch",
                    }
                    result["switch_type"] = switch_type_map.get(switchtype, switchtype)
                    result["switch_type_code"] = switchtype
                
                result["is_valid"] = True
                
        else:
            result["error"] = f"API returned status {response.status_code}"
            
    except ET.ParseError as e:
        logger.error(f"XML parsing failed: {e}")
        result["error"] = f"XML parse error: {e}"
    except requests.RequestException as e:
        logger.error(f"Carrier lookup failed: {e}")
        result["error"] = str(e)
    

    # Note: NANPA local data removed - using LocalCallingGuide API only

    
    # Determine porting by comparing ILEC (original block owner) vs current carrier (NANPA)
    # If ILEC exists and is different from the current carrier, the number was ported
    ilec_name = result.get('ilec_name', '')
    current_carrier = result.get('carrier', '')
    
    if ilec_name and current_carrier:
        # Normalize names for comparison (remove suffixes like "- TN", ", LLC")
        ilec_normalized = ilec_name.upper().split(' - ')[0].split(',')[0].strip()
        carrier_normalized = current_carrier.upper().split(' - ')[0].split(',')[0].strip()
        
        # Check if original (ILEC) matches current carrier
        # If they don't match, the block was assigned to a different carrier
        if ilec_normalized != carrier_normalized:
            # Additional check: look for common name fragments
            ilec_keywords = set(ilec_normalized.split())
            carrier_keywords = set(carrier_normalized.split())
            common = ilec_keywords & carrier_keywords
            
            # If less than 50% common words, consider it ported
            if len(common) < min(len(ilec_keywords), len(carrier_keywords)) * 0.5:
                result['is_ported'] = True
                result['status'] = 'Ported'
            else:
                result['is_ported'] = False
                result['status'] = 'Assigned'
        else:
            result['is_ported'] = False
            result['status'] = 'Assigned'
    else:
        result['is_ported'] = False
        result['status'] = 'Assigned'
    
    return result


def full_phone_lookup(phone: str) -> Dict[str, Any]:
    """
    Perform full phone lookup with CNAM and carrier data.
    Returns all available info with data sources for transparency.
    """
    import datetime
    
    parsed = parse_phone(phone)
    cnam_result = lookup_cnam(phone)
    carrier_result = lookup_carrier(phone)
    
    # Get SMS/MMS gateway info based on carrier
    carrier_name = carrier_result.get("carrier", "")
    gateway_info = get_carrier_gateway(carrier_name)
    
    # Add gateway info to carrier result
    carrier_result["sms_gateway"] = gateway_info["sms_gateway"]
    carrier_result["mms_gateway"] = gateway_info["mms_gateway"]
    # Use gateway is_wireless if available, otherwise use line_type
    if gateway_info["is_wireless"] is not None:
        carrier_result["is_wireless_detected"] = gateway_info["is_wireless"]
    
    # NANPA metadata removed - using LocalCallingGuide API only
    
    # NANPA metadata removed - using LocalCallingGuide API only
    nanpa_metadata = {}
    
    return {
        "phone": {
            "number": normalize_phone(phone),
            "formatted": parsed["formatted"],
            "area_code": parsed["npa"],
            "prefix": parsed["nxx"],
            "line": parsed["line"]
        },
        "lookup_date": datetime.datetime.now().isoformat(),
        "caller_id": cnam_result,
        "carrier": carrier_result,
        "nanpa_metadata": nanpa_metadata,  # File update dates
        "sources": [
            {
                "name": "Carrier CNAM Database",
                "data_type": "Caller ID Name (CNAM)",
                "description": "The name registered with your carrier in the LIDB database",
                "can_remove": True,
                "removal_instructions": "Contact your carrier to change your 'Caller ID Name'. For Verizon: https://www.verizon.com/support/knowledge-base-49073/"
            },
            {
                "name": "LocalCallingGuide.com",
                "data_type": "Carrier & Location Data",
                "description": "Public FCC/NANPA telecom numbering data - which carrier owns the number and where",
                "can_remove": False,
                "removal_instructions": "This is public telecom infrastructure data. The only way to 'remove' it is to cancel your phone number."
            },
            {
                "name": "NANPA Database",
                "data_type": "Number Assignment Data",
                "description": "Official NANPA (North American Numbering Plan Administration) assignment records",
                "can_remove": False,
                "removal_instructions": "This is public regulatory data from the FCC/NANPA."
            }
        ]
    }



