import json
import requests


# Remove after implementation
# Treez Ticket body
def treez_ticket_object():
    return  {
                "event_type": "TICKET",
                "data": {
                    "type": "POS",
                    "ticket_id": "13b3097f-a1e7-4383-a427-236c411704b7",
                    "order_number": "56HN0Y",
                    "external_order_number": "null",
                    "order_source": "IN_STORE",
                    "total": 101,
                }
            }


# Create maping for env
# Dev, Pre-Prod, Prod
def env_maping(env: str):
    if env.lower() == "preprod" or env.lower() == "pre-prod":
        return "preprod"
    if env.lower() == "prod" or env.lower() == "production":
        return "prod"
    return "dev"  


# Get auth url
def get_auth_url_for_env(env: str):
    if env == "preprod":
        return "https://auth.preprod.swifterhq.com/oauth2/token"

    if env == "production":
        return "https://auth.swifterhq.com/oauth2/token"
    
    return "https://treezpay-auth.dev.swifterhq.com/oauth2/token"

# Get api url
def get_api_url(env: str):
    if env == "preprod":
        return "https://api.preprod.swifterhq.com/api/v2.0/payment_links"

    if env == "production":
        return "https://api.swifterhq.com/api/v2.0/payment_links"
    
    return "https://treezpay-api.dev.swifterhq.com/api/v2.0/payment_links"


# Create payment link for treez order
def create_payment_link(env: str, client_id: str, client_secret: str, org_id:str, ticket_number:str):
    '''
    Body: will contain the entire ticket information
    auth_code: will contain base64 encoded api-key and secret key
    Steps to follow
    1. Get ticket number from the body
    3. Call auth token to get access_token
    2. Call create payment link public api with auto_charge = False and notification channel as ["email"] 
    '''

    # Get auth url for env
    auth_url = get_auth_url_for_env(env=env)

    # Get api url for env
    api_url = get_api_url(env=env)


    # Get bearer token using swifter auth url
    access_token = requests.post(url=auth_url,auth=(client_id,client_secret),data={'grant_type': 'client_credentials'})

    # Convert token to json
    access_token = access_token.json()
    token = access_token.get("access_token")

    notify_data = {
            "invoice_type": "treez",
            "notification_channel": ["email", "sms"],
            "invoice_number": ticket_number,
            "auto_charge": False
        }

    notify_header = {"X-Organization-Id":org_id,"Authorization": f"Bearer {token}",'Content-Type': 'application/json'}
    # Call notification api from root
    notify = requests.post(url=api_url,headers=notify_header, json=notify_data )
    
    return notify


def notify(event, context):
    
    print("Initiate lambda to run notification delivery.")

    query_params = event.get('queryStringParameters', {})

    client_id = query_params.get('client_id')
    # client_id = "pk_4LYK74iCWy4DHGAXdhfnMc"
    
    client_secret = query_params.get('client_secret')
    # client_secret = "YUtFJG4O.74gVz99DF~dTn9xRt"
    
    organization_id = query_params.get('organization_id')
    # organization_id = "org_9ZegBnwMxr35XUYKCAPSaG"

    env = query_params.get('env')

    env_value = env_maping(env=env)

    request_body = json.loads(event.get('body', '{}'))

    # treez_ticket = treez_ticket_object()

    ticket_data = request_body.get("data",{})

    # Check total is greater than $100
    total_amount = ticket_data["total"]

    order_number = ticket_data["order_number"]

    
    if total_amount >= 100:
        try:
            notify_ = create_payment_link(env=env_value,client_id=client_id,client_secret=client_secret,org_id=organization_id,ticket_number=order_number)
            print(f"Created payment link with payment_link_id={notify_.json()}")
            response = {
                "statusCode": 200,
                "body": json.dumps(notify_.text)
            }
            return response
        except Exception as e:
            print("Could not create payment link.")
            response = {
                "statusCode": 400,
                "body": json.dumps(e)
            }
    
            return response
    