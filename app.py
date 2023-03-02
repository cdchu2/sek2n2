from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from httpx import AsyncClient
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
import urllib
import httpx

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="secret")

app.mount("/sek2n2/static", StaticFiles(directory="static"), name="static")


config = Config('.env')
templates = Jinja2Templates(directory="templates")
github_client_id = config("GITHUB_CLIENT_ID")
github_client_secret = config("GITHUB_CLIENT_SECRET")
github_redirect_uri = config("GITHUB_REDIRECT_URI")
github_authorize_url = "https://github.com/login/oauth/authorize"
github_token_url = "https://github.com/login/oauth/access_token"
github_api_url = "https://api.github.com/user"

@app.get("/")
async def index(request: Request):
    # if "user" in request.session:
    #     return RedirectResponse("/profile")
    context = {"request": request}
    return templates.TemplateResponse("index.html", context=context)


@app.get("/login")
async def login(request: Request, response: Response):
    params = {
        "client_id": github_client_id,
        "redirect_uri": github_redirect_uri,
        "scope": "read:user",
        "state": "randomstring",
    }
    url = f"{github_authorize_url}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url)


@app.get("/login/callback")
async def callback(request: Request, response: Response, code: str, state: str):
    params = {
        "client_id": github_client_id,
        "client_secret": github_client_secret,
        "code": code,
        "redirect_uri": github_redirect_uri,
        "state": state,
    }
    async with AsyncClient() as client:
        response = await client.post(github_token_url, data=params)
        response_dict = urllib.parse.parse_qs(response.text)
        access_token = response_dict["access_token"][0]

    headers = {"Authorization": f"Bearer {access_token}"}
    user_url = 'https://api.github.com/user'
    
    async with AsyncClient() as client:
        user_response = await client.get(user_url, headers=headers)
    user_data = user_response.json()
    profile_url = user_data['html_url']
    return RedirectResponse(url=profile_url)

