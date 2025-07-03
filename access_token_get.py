from ctrader_open_api import Client, Protobuf, TcpProtocol, Auth, EndPoints
from ctrader_open_api.endpoints import EndPoints
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *
from twisted.internet import reactor
from inputimeout import inputimeout, TimeoutOccurred
import webbrowser
import datetime
import calendar
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    currentAccountId = int(os.getenv("ACCOUNT_ID", "0"))
    hostType = os.getenv("HOST_TYPE", "demo")

    if not currentAccountId:
        raise RuntimeError("ACCOUNT_ID environment variable must be set")

    while hostType != "live" and hostType != "demo":
        print(f"{hostType} is not a valid host type.")
        hostType = input("Host (Live/Demo): ")

    appClientId = os.getenv("CLIENT_ID")
    appClientSecret = os.getenv("CLIENT_SECRET")
    accessToken = os.getenv("ACCESS_TOKEN")
    isTokenAvailable = accessToken is not None or input("Do you have an access token? (Y/N): ").lower() == "y"

    if not appClientId or not appClientSecret:
        raise RuntimeError("CLIENT_ID and CLIENT_SECRET environment variables must be set")

    if not isTokenAvailable:
        appRedirectUri = input("App Redirect URI: ")
        auth = Auth(appClientId, appClientSecret, appRedirectUri)
        authUri = auth.getAuthUri()
        print(f"Please continue the authentication on your browser:\n {authUri}")
        webbrowser.open_new(authUri)
        print("\nThen enter the auth code that is appended to redirect URI immediatly (the code is after ?code= in URI)")
        authCode = input("Auth Code: ")
        token = auth.getToken(authCode)
        if "accessToken" not in token:
            raise KeyError(token)
        print("Token: \n", token)
        accessToken = token["accessToken"]
    elif accessToken is None:
        accessToken = input("Access Token: ")

    client = Client(EndPoints.PROTOBUF_LIVE_HOST if hostType.lower() == "live" else EndPoints.PROTOBUF_DEMO_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)

    def connected(client): # Callback for client connection
        print("\nConnected")
        request = ProtoOAApplicationAuthReq()
        request.clientId = appClientId
        request.clientSecret = appClientSecret
        deferred = client.send(request)
        deferred.addErrback(onError)

    def disconnected(client, reason): # Callback for client disconnection
        print("\nDisconnected: ", reason)

    def onMessageReceived(client, message): # Callback for receiving all messages
        if message.payloadType in [ProtoOASubscribeSpotsRes().payloadType, ProtoOAAccountLogoutRes().payloadType, ProtoHeartbeatEvent().payloadType]:
            return
        elif message.payloadType == ProtoOAApplicationAuthRes().payloadType:
            print("API Application authorized\n")
            print("Please use setAccount command to set the authorized account before sending any other command, try help for more detail\n")
            print("To get account IDs use ProtoOAGetAccountListByAccessTokenReq command")
            if currentAccountId is not None:
                sendProtoOAAccountAuthReq()
                return
        elif message.payloadType == ProtoOAAccountAuthRes().payloadType:
            protoOAAccountAuthRes = Protobuf.extract(message)
            print(f"Account {protoOAAccountAuthRes.ctidTraderAccountId} has been authorized\n")
            print("This acccount will be used for all future requests\n")
            print("You can change the account by using setAccount command")
        else:
            print("Message received: \n", Protobuf.extract(message))
        reactor.callLater(3, callable=executeUserCommand)

    def onError(failure): # Call back for errors
        print("Message Error: ", failure)
        reactor.callLater(3, callable=executeUserCommand)