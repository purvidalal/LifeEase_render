# alert_service.py
from twilio.rest import Client
import os

# Twilio credentials - put real values here or use env vars
account_sid = 'AC6f9319b45394b76ec22b99ec30586624'
auth_token = 'cc8feda5f3d7f728613fa8857c8c292f'
twilio_number = '+Your_Twilio_Number'
target_number = '+610490373419'  # your number for testing

client = Client(account_sid, auth_token)

def send_alert(message):
    try:
        sent = client.messages.create(
            body=message,
            from_=twilio_number,
            to=target_number
        )
        print(f"✅ Alert sent! SID: {sent.sid}")
    except Exception as e:
        print(f"❌ Failed to send SMS alert: {e}")