
import os
import mimetypes
import requests
from urllib.parse import urlparse
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client

app = Flask(__name__)

def send_media_url_to_api(media_url):
    """
    Send the MediaUrl0 to the specified API endpoint
    
    Args:
        media_url (str): The media URL to send to the API
    
    Returns:
        bool: True if successful, False otherwise
    """
    api_url = os.getenv('LANGFLOW_API_URL')
    
    if not api_url:
        print("[ERROR] LANGFLOW_API_URL environment variable not set")
        return False
    
    payload = {
        "input_value": media_url,  # The MediaUrl0 value
        "output_type": "chat",     # Specifies the expected output format
        "input_type": "chat"       # Specifies the input format
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"[DEBUG] Sending MediaUrl0 to API: {media_url}")
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()  # Raise exception for bad status codes
        
        print(f"[DEBUG] API response status: {response.status_code}")
        print(f"[DEBUG] API response: {response.text}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error making API request: {e}")
        return False
    except ValueError as e:
        print(f"[ERROR] Error parsing response: {e}")
        return False

@app.route("/reply_sms", methods=['POST'])
def reply_sms():
    # Print out whatever is received to stdout
    print("Received headers:", dict(request.headers))
    print("Received data:", request.data.decode('utf-8'))
    print("Received form:", request.form)
    # Parse x-www-form-urlencoded data
    if request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
        print("Parsed x-www-form-urlencoded data:")
        for key, value in request.form.items():
            print(f"  {key}: {value}")
    # Download media if present
    media_url = request.form.get('MediaUrl0')
    media_content_type = request.form.get('MediaContentType0')
    if media_url:
        # Send MediaUrl0 to API endpoint first
        api_success = send_media_url_to_api(media_url)
        if api_success:
            print("[INFO] Successfully sent MediaUrl0 to API endpoint")
        else:
            print("[WARNING] Failed to send MediaUrl0 to API endpoint")
        
        # Get Twilio credentials from environment variables
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        print(f"[DEBUG] account_sid: {account_sid}")
        print(f"[DEBUG] auth_token: {'set' if auth_token else 'not set'}")
        if not account_sid or not auth_token:
            print('Twilio credentials not set in environment variables.')
        else:
            print(f"[DEBUG] Downloading media from: {media_url}")
            try:
                response = requests.get(media_url, auth=(account_sid, auth_token), timeout=10)
                print(f"[DEBUG] Response status code: {response.status_code}")
                print(f"[DEBUG] Response headers: {response.headers}")
                if response.status_code == 200:
                    file_extension = mimetypes.guess_extension(media_content_type) or ''
                    media_sid = os.path.basename(urlparse(media_url).path)
                    filename = f"{media_sid}{file_extension}"
                    
                    # Create downloads directory relative to script location
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    downloads_dir = os.path.join(script_dir, '..', '.downloads')
                    os.makedirs(downloads_dir, exist_ok=True)
                    
                    # Full path for the file
                    file_path = os.path.join(downloads_dir, filename)
                    
                    print(f"[DEBUG] Saving file as: {file_path}")
                    print(f"[DEBUG] File size: {len(response.content)} bytes")
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    print(f"Media saved as {file_path}")
                    print(f"[DEBUG] File exists after save: {os.path.exists(file_path)}")
                else:
                    print(f"Failed to download media: {response.status_code}")
            except Exception as e:
                print(f"Error downloading media: {e}")
    # Create a new Twilio MessagingResponse
    resp = MessagingResponse()
    # resp.message("The Robots are coming! Head for the hills!")
    # Return the TwiML (as XML) response
    return Response(str(resp), mimetype='text/xml')

if __name__ == "__main__":
    app.run(port=3000)
