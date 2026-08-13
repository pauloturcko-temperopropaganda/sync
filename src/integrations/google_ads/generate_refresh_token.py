import os

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow


load_dotenv(".env.admin")

CLIENT_ID = os.getenv("GOOGLE_ADS_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_ADS_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError(
        "GOOGLE_ADS_CLIENT_ID ou GOOGLE_ADS_CLIENT_SECRET não encontrado."
    )

client_config = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost"],
    }
}

flow = InstalledAppFlow.from_client_config(
    client_config,
    scopes=["https://www.googleapis.com/auth/adwords"],
)

credentials = flow.run_local_server(
    port=8080,
    access_type="offline",
    prompt="consent",
)

print()
print("=" * 60)
print("REFRESH TOKEN GERADO")
print("=" * 60)
print(credentials.refresh_token)
print("=" * 60)