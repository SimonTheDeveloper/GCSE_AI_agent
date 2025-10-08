import os

ALLOWED_EMAILS = {x.strip().lower() for x in os.getenv("ALLOWED_EMAILS", "").split(",") if x.strip()}
ALLOWED_DOMAINS = {x.strip().lower().lstrip("@") for x in os.getenv("ALLOWED_DOMAINS", "").split(",") if x.strip()}

def handler(event, context):
    # event.request.userAttributes.email is available for Hosted UI sign-up
    email = (event.get("request", {}).get("userAttributes", {}).get("email") or "").lower().strip()
    if not email:
        raise Exception("Email is required.")

    # If no allowlist configured, allow all (you can change to deny by default if preferred)
    if not ALLOWED_EMAILS and not ALLOWED_DOMAINS:
        return event

    if email in ALLOWED_EMAILS:
        return event
    if "@" in email and email.split("@", 1)[1] in ALLOWED_DOMAINS:
        return event

    # Block sign-up if not in allowlist
    raise Exception("Sign-up is not permitted for this account.")
