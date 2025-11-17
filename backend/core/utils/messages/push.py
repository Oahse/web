# Firebase Cloud Messaging (FCM)
import asyncio
# firbasejson ={
#   "type": "service_account",
#   "project_id": "your-project-id",
#   "private_key_id": "some_key_id",
#   "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
#   "client_email": "firebase-adminsdk-xxxx@your-project-id.iam.gserviceaccount.com",
#   "client_id": "some_client_id",
#   "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#   "token_uri": "https://oauth2.googleapis.com/token",
#   "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
#   "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxx%40your-project-id.iam.gserviceaccount.com"
# }

# cred = credentials.Certificate(firbasejson)
# try:
#     firebase_admin.initialize_app(cred)
# except Exception as e:
#     raise e

async def push(id: str, to_user_id: str, title: str, body: str, type: str, token: str, data: dict = {}):
    # Simulate sending notification asynchronously
    print(f"Pushing notification {id} to {to_user_id}")
    # await your actual async send logic here
    # data['type'] = type
    # message = messaging.Message(
    #     notification=messaging.Notification(
    #         title=title,
    #         body=body,
    #     ),
    #     token=token,
    #     data=data or {'type': type},
    # )

    # response = await messaging.send(message)
    # print(f"Notification sent: {response}")

def send_push(id: str, to_user_id: str, title: str, body: str, type: str, token: str, data: dict = {}):
    # If you're inside a running event loop (e.g., FastAPI), use this instead:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # If inside an async context (like FastAPI), schedule push task
        asyncio.create_task(push(id, to_user_id, title, body, type, token, data))
    else:
        # Otherwise, run it synchronously (blocking) as entry point
        asyncio.run(push(id, to_user_id, title, body, type, token, data))