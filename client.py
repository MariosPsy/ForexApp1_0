from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from twisted.internet import reactor
import calendar
import datetime

class TraderClient:
    def __init__(self, client_id, client_secret, access_token, account_id, host_type="demo", command_queue=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.account_id = account_id
        self.host_type = host_type
        self.client = None
        self.command_queue = command_queue
        self.commands = {
            "ProtoOAVersionReq": self.sendProtoOAVersionReq,
            "ProtoOAGetAccountListByAccessTokenReq": self.sendProtoOAGetAccountListByAccessTokenReq
        }

    def setup_client(self):
        self.client = Client(
            EndPoints.PROTOBUF_LIVE_HOST if self.host_type == "live" else EndPoints.PROTOBUF_DEMO_HOST,
            EndPoints.PROTOBUF_PORT,
            TcpProtocol
        )
        self.client.setConnectedCallback(self.on_connected)
        self.client.setDisconnectedCallback(self.on_disconnected)
        self.client.setMessageReceivedCallback(self.on_message_received)
        self.client.startService()
        reactor.run()

    def on_connected(self, client):
        print("Connected!")
        request = ProtoOAApplicationAuthReq()
        request.clientId = self.client_id
        request.clientSecret = self.client_secret
        deferred = self.client.send(request)
        deferred.addErrback(self.on_error)

    def on_disconnected(self, client, reason):
        print("Disconnected:", reason)

    def on_message_received(self, client, message):
        print("Message received")
        reactor.callLater(3, self.execute_user_command)

    def on_error(self, failure):
        print("Error:", failure)
        reactor.callLater(3, self.execute_user_command)

    def execute_user_command(self):
        try:
            if self.command_queue and not self.command_queue.empty():
                user_input = self.command_queue.get()
                print(f"[Queue Command] Executing: {user_input}")
            else:
                user_input = input("Command (ex: ProtoOAVersionReq): ")
        except Exception as e:
            print("Error reading command:", e)
            reactor.callLater(3, self.execute_user_command)
            return

        user_input_split = user_input.strip().split(" ")
        if not user_input_split or not user_input_split[0]:
            print("Empty or invalid command.")
            reactor.callLater(3, self.execute_user_command)
            return

        command = user_input_split[0]
        parameters = [param.lstrip("*") for param in user_input_split[1:]]

        try:
            if command in self.commands:
                self.commands[command](*parameters)
            else:
                print("Invalid command:", command)
        except Exception as e:
            print("Command execution error:", e)

        reactor.callLater(3, self.execute_user_command)

    def sendProtoOAVersionReq(self, clientMsgId=None):
        request = ProtoOAVersionReq()
        deferred = self.client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)

    def sendProtoOAGetAccountListByAccessTokenReq(self, clientMsgId=None):
        request = ProtoOAGetAccountListByAccessTokenReq()
        request.accessToken = self.access_token
        deferred = self.client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)