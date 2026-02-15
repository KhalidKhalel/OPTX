# Playbook Configurations for OPTX
# Two-Session Design: Each session must complete within 1 minute
# Session 1: Form submission
# Email Polling: Via API (no browser)
# Session 2: Verification link click

PLAYBOOKS = {
    "peoplesearchnow.com": {
        "name": "PeopleSearchNow",
        "slug": "peoplesearchnow",
        "url": "https://www.peoplesearchnow.com/",
        "opt_out_url": "https://www.peoplesearchnow.com/opt-out",
        "required_fields": ["first_name", "last_name", "city", "state"],
        
        # Email verification patterns for this broker
        "email_config": {
            "expected_from": "peoplesearchnow",
            "link_patterns": ["validate-record-info", "verify", "confirm"],
            "poll_interval": 10,  # seconds
            "poll_timeout": 180,  # 3 minutes max
        },
        
        # SESSION 1: Initial form submission (must complete in < 60 seconds)
        "session_1_steps": [
            {"action": "navigate", "url": "https://www.peoplesearchnow.com/opt-out"},
            # Gate: ensure form is fully loaded before typing (navigate already waits for CF)
            {"action": "wait_for", "selector": "#verifyEmailForm", "timeout": 15},
            {"action": "scroll_to", "selector": "#verifyEmailForm"},
            # Fill Initial Form
            {"action": "select", "selector": "#user-type", "value": "subject"},
            {"action": "human_type", "selector": "#subject-firstname", "field": "first_name"},
            {"action": "human_type", "selector": "#subject-lastname", "field": "last_name"},
            {"action": "human_type", "selector": "#subject-email", "context_key": "email"},
            {"action": "click", "selector": "#agreement"},
            {"action": "scroll_to", "selector": ".g-recaptcha"},
            {"action": "wait", "seconds": 2},
            {"action": "solve_captcha"},
            # Submit form
            {"action": "click", "selector": "#BRP"},
            {"action": "wait", "seconds": 2},
            # Verify submission success - look for confirmation message
            {
                "action": "verify_text",
                "patterns": ["email has been sent", "check your inbox", "verification email"],
                "timeout": 10,
            },
        ],
        
        # SESSION 2: Verification link handling (must complete in < 60 seconds)
        "session_2_steps": [
            # Navigate to the verification link (provided dynamically)
            {"action": "navigate", "context_key": "verification_link"},
            {"action": "wait", "seconds": 3},
            # Check if we need to fill a detailed form or just confirm
            {"action": "wait_for", "selector": "#removalForm", "timeout": 15, "optional": True},
            # If removal form exists, fill it
            {
                "action": "conditional_block",
                "condition": {"selector_exists": "#removalForm"},
                "steps": [
                    {"action": "scroll_to", "selector": "#removalForm"},
                    {"action": "human_type", "selector": "#subject-firstname", "field": "first_name"},
                    {"action": "human_type", "selector": "#subject-lastname", "field": "last_name"},
                    {"action": "human_type", "selector": "#subject-phone", "field": "phone", "optional": True},
                    {"action": "human_type", "selector": "#subject-streetaddress", "field": "street", "optional": True},
                    {"action": "human_type", "selector": "#subject-city", "field": "city"},
                    {"action": "select_state", "selector": "#subject-state", "format": "abbr"},
                    {"action": "human_type", "selector": "#subject-zipcode", "field": "zip", "optional": True},
                    {"action": "human_type", "selector": "#subject-email", "context_key": "email"},
                    {"action": "fill", "selector": "#subject-dob", "field": "dob", "optional": True},
                    {"action": "click", "selector": "#accuracy-agreement", "optional": True},
                    {"action": "scroll_to", "selector": ".g-recaptcha", "optional": True},
                    {"action": "wait", "seconds": 1},
                    {"action": "solve_captcha"},
                    {"action": "click", "selector": "#CRP"},
                    {"action": "wait", "seconds": 5},
                ],
            },
            # Verify final confirmation
            {
                "action": "verify_text",
                "patterns": ["Opt-Out Request Confirmation", "removal confirmed", "request has been processed", "record will be removed", "successfully submitted"],
                "timeout": 10,
            },
        ],
    },
}
