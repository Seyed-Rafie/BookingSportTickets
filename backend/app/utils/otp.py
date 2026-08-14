import random
import string

def generate_otp_code(length: int = 6) -> str:
    # Generate random numeric string of specified length
    digits = string.digits
    return ''.join(random.choice(digits) for _ in range(length))

def send_otp_notification(identifier: str, code: str) -> bool:
    # Mock OTP notification sender (Print in terminal/logs for testing)
    # Replace this block with SMS Gateway API (e.g., Kavenegar) or Email Provider for bonus points
    print(f"\n==========================================")
    print(f"[OTP SERVICE] Target: {identifier} | Code: {code}")
    print(f"==========================================\n")
    return True