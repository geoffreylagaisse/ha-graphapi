"""
Example scripts that performs authentication
"""
import argparse
import asyncio
import os
import webbrowser

from aiohttp import ClientSession, web

from hagraphapi.auth.manager import AuthManager
from hagraphapi.client import GraphApiClient


CLIENT_ID = ""
CLIENT_SECRET = ""
REDIRECT_URI = "http://localhost:8080/auth/callback"

queue = asyncio.Queue(1)


async def auth_callback(request):
    error = request.query.get("error")
    if error:
        description = request.query.get("error_description")
        print(f"Error in auth_callback: {description}")

    # Run in task to not make unsuccessful parsing the HTTP response fail
    asyncio.create_task(queue.put(request.query.get("code")))
    return web.Response(
        headers={"content-type": "text/html"},
        text="<html><body><h1>Auth Completed</h1></body></html>",
    )


async def async_main(
    client_id: str, client_secret: str, redirect_uri: str
):

    async with ClientSession() as session:
        auth_mgr = AuthManager(
            session, client_id, client_secret, redirect_uri
        )

        auth_url = auth_mgr.generate_authorization_url()
        webbrowser.open(auth_url)
        code = await queue.get()

        if not code:
            return

        await auth_mgr.request_token(code)

        # Make presence call
        client = GraphApiClient(auth_mgr)
        resp = await client.presence.get_presence()
        print(resp.json())


def main():
    parser = argparse.ArgumentParser(description="Authenticate with Microsoft Graph")
    parser.add_argument(
        "--client-id",
        "-cid",
        default=os.environ.get("CLIENT_ID", CLIENT_ID),
        help="OAuth2 Client ID",
    )
    parser.add_argument(
        "--client-secret",
        "-cs",
        default=os.environ.get("CLIENT_SECRET", CLIENT_SECRET),
        help="OAuth2 Client Secret",
    )
    parser.add_argument(
        "--redirect-uri",
        "-ru",
        default=os.environ.get("REDIRECT_URI", REDIRECT_URI),
        help="OAuth2 Redirect URI",
    )

    args = parser.parse_args()

    app = web.Application()
    app.add_routes([web.get("/auth/callback", auth_callback)])
    runner = web.AppRunner(app)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, "localhost", 8080)
    loop.run_until_complete(site.start())
    loop.run_until_complete(
        async_main(args.client_id, args.client_secret, args.redirect_uri)
    )


if __name__ == "__main__":
    main()