from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *
from twisted.internet import reactor
from converters import proto_dict_connert
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
        self.account_authorized = False

        self.commands = {
            "ProtoOAVersionReq": self.sendProtoOAVersionReq, #ΟΚ
            "ProtoOAGetAccountListByAccessTokenReq": self.sendProtoOAGetAccountListByAccessTokenReq, # OK
            "ProtoOAGetTrendbarsReq": self.sendProtoOAGetTrendbarsReq, #OK
            "ProtoOAAccountLogoutReq": self.sendProtoOAAccountLogoutReq, # Do NOT Test
            "ProtoOAAssetClassListReq": self.sendProtoOAAssetClassListReq, #ΟΚ
            "ProtoOASymbolCategoryListReq": self.sendProtoOASymbolCategoryListReq, #ΟΚ
            "ProtoOASymbolsListReq": self.sendProtoOASymbolsListReq, #ΟΚ
            "ProtoOATraderReq": self.sendProtoOATraderReq, #ΟΚ
            "ProtoOAUnsubscribeSpotsReq": self.sendProtoOAUnsubscribeSpotsReq, #OK
            "ProtoOASubscribeSpotsReq": self.sendProtoOASubscribeSpotsReq, #OK
            "ProtoOAReconcileReq": self.sendProtoOAReconcileReq, #OK
            "ProtoOAGetTickDataReq": self.sendProtoOAGetTickDataReq, # OK
            "ProtoOANewOrderReq": self.sendProtoOANewOrderReq,
            "NewMarketOrder": self.sendNewMarketOrder,
            "NewLimitOrder": self.sendNewLimitOrder,
            "NewStopOrder": self.sendNewStopOrder,
            "ProtoOAClosePositionReq": self.sendProtoOAClosePositionReq,
            "sendProtoOACancelOrderReq": self.sendProtoOACancelOrderReq,
            "ProtoOADealOffsetListReq": self.sendProtoOADealOffsetListReq,
            "ProtoOAGetPositionUnrealizedPnLReq": self.sendProtoOAGetPositionUnrealizedPnLReq,
            "ProtoOAOrderDetailsReq": self.sendProtoOAOrderDetailsReq,
            "ProtoOAOrderListByPositionIdReq": self.sendProtoOAOrderListByPositionIdReq

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
        deferred.addCallback(lambda _: self.send_account_auth())
        deferred.addErrback(self.on_error)

    def send_account_auth(self, clientMsgId=None):
        print("Sending account authorization...")
        request = ProtoOAAccountAuthReq()
        request.ctidTraderAccountId = self.account_id
        request.accessToken = self.access_token
        deferred = self.client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)

    def on_disconnected(self, client, reason):
        print("Disconnected:", reason)

    def on_message_received(self, client, message):
        print("\n--- New Message Received ---")
        print(f"Payload Type: {message.payloadType}")

        try:
            extracted_message = Protobuf.extract(message)
            print("Extracted message content:")
            print(extracted_message)

            if message.payloadType == ProtoOAAccountAuthRes().payloadType:
                print("✅ Λογαριασμός αυθεντικοποιήθηκε επιτυχώς.")
                self.account_authorized = True

            if message.payloadType == ProtoOAGetTrendbarsRes().payloadType:
                trendbars = proto_dict_connert(extracted_message.trendbar)
                print("\n--- Trendbars converted to dict list ---")
                print(trendbars)
                print("--- CSV has been saved as trentbars_data.csv ---")
        except Exception as e:
            print("Error while processing message:", e)

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
                print("No command in queue, skipping...")
                reactor.callLater(3, self.execute_user_command)
                return
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

        if not self.account_authorized:
            print("⏳ Περιμένω αυθεντικοποίηση λογαριασμού πριν συνεχίσω...")
            reactor.callLater(1, self.execute_user_command)
            return

        reactor.callLater(3, self.execute_user_command)

    def sendProtoOAVersionReq(self, clientMsgId=None):
        """Αποστέλλει αίτημα για την έκδοση (version) του cTrader Open API
         από τον server και χειρίζεται τυχόν σφάλματα."""
        request = ProtoOAVersionReq()
        deferred = self.client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)

    def sendProtoOAGetAccountListByAccessTokenReq(self, clientMsgId=None):
        """Αποστέλλει αίτημα για λήψη της λίστας λογαριασμών που συνδέονται
         με το access token και χειρίζεται τυχόν σφάλματα."""
        request = ProtoOAGetAccountListByAccessTokenReq()
        request.accessToken = self.access_token
        deferred = self.client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)

    def sendProtoOAAccountLogoutReq(self, clientMsgId=None):
        """Αποσυνδέει τον τρέχοντα λογαριασμό trader από την πλατφόρμα cTrader Open API."""
        request = ProtoOAAccountLogoutReq()
        request.ctidTraderAccountId = self.account_id
        deferred = self.client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)

    def sendProtoOAAssetClassListReq(self, clientMsgId=None):
        """Αποστέλλει αίτημα για λήψη της λίστας των κατηγοριών
        περιουσιακών στοιχείων (Asset Classes) για τον συγκεκριμένο λογαριασμό trader."""
        request = ProtoOAAssetClassListReq()
        request.ctidTraderAccountId = self.account_id
        deferred = self.client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)

    def sendProtoOASymbolCategoryListReq(self, clientMsgId=None):
        """Αποστέλλει αίτημα για λήψη της λίστας κατηγοριών συμβόλων
        (π.χ. Forex, Stocks, Indices, Commodities, Crypto)"""
        request = ProtoOASymbolCategoryListReq()
        request.ctidTraderAccountId = self.account_id
        deferred = self.client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)

    def sendProtoOASymbolsListReq(self, includeArchivedSymbols=False, clientMsgId=None):
        """Αποστέλλει αίτημα για λήψη της λίστας όλων των συμβόλων
        (π.χ. EUR/USD, AAPL), με επιλογή για να εμφανιστούν τα αρχειοθετημένα.(αλλάζοντας σε True την παράμετρο)"""
        request = ProtoOASymbolsListReq()
        request.ctidTraderAccountId = self.account_id
        request.includeArchivedSymbols = includeArchivedSymbols if type(includeArchivedSymbols) is bool else bool(
            includeArchivedSymbols)
        deferred = self.client.send(request)
        deferred.addErrback(self.on_error)

    def sendProtoOATraderReq(self, clientMsgId=None):
        """Αποστέλλει αίτημα για πληροφορίες του trader
        (π.χ. υπόλοιπο, περιθώριο, καταστάσεις λογαριασμού)"""
        request = ProtoOATraderReq()
        request.ctidTraderAccountId = self.account_id
        deferred = self.client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)

    def sendProtoOAUnsubscribeSpotsReq(self, symbolId, clientMsgId=None):
        """Αποστέλλει αίτημα για διακοπή παρακολούθησης live τιμών (spot prices) για το συγκεκριμένο σύμβολο.
        # symbolId      -> ID του συμβόλου που θέλεις να σταματήσεις την παρακολούθηση (π.χ. 1 για EUR/USD)"""
        request = ProtoOAUnsubscribeSpotsReq()
        request.ctidTraderAccountId = self.account_id
        request.symbolId.append(int(symbolId))
        deferred = self.client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)

    def sendProtoOASubscribeSpotsReq(self, symbolId, timeInSeconds, subscribeToSpotTimestamp=False, clientMsgId=None):
        """Αποστέλλει αίτημα για ενεργοποίηση παρακολούθησης live τιμών (spot prices) για το σύμβολο και την απενεργοποιεί μετά από συγκεκριμένο χρόνο.
            # ΠΑΡΑΜΕΤΡΟΙ:
            # symbolId                -> ID του συμβόλου για παρακολούθηση (π.χ. 1 για EUR/USD)
            # timeInSeconds           -> διάρκεια (σε δευτερόλεπτα) που θα γίνεται η παρακολούθηση
            # subscribeToSpotTimestamp -> (προαιρετικό) αν θα περιλαμβάνεται και το timestamp στη ροή δεδομένων (π.χ. True/False)"""
        request = ProtoOASubscribeSpotsReq()
        request.ctidTraderAccountId = self.account_id
        request.symbolId.append(int(symbolId))
        request.subscribeToSpotTimestamp = subscribeToSpotTimestamp if type(subscribeToSpotTimestamp) is bool else bool(
            subscribeToSpotTimestamp)
        deferred = self.client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)
        reactor.callLater(int(timeInSeconds), self.sendProtoOAUnsubscribeSpotsReq, symbolId)

    def sendProtoOAReconcileReq(self, clientMsgId=None):
        """
        Αποστέλλει αίτημα συγχρονισμού (Reconcile) για να ενημερώσει τον client με την πλήρη και ακριβή κατάσταση του λογαριασμού από τον server.

        ΠΑΡΑΜΕΤΡΟΙ:
        clientMsgId -> (προαιρετικό) μοναδικό ID μηνύματος για παρακολούθηση
        """
        request = ProtoOAReconcileReq()
        request.ctidTraderAccountId = self.account_id
        deferred = self.client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)

    def sendProtoOAGetTrendbarsReq(self, weeks, period, symbolId, clientMsgId=None):
        """Αποστέλλει αίτημα για ιστορικά δεδομένα (trendbars) ενός συμβόλου για συγκεκριμένη περίοδο
            # ΠΑΡΑΜΕΤΡΟΙ:
            # weeks      -> αριθμός εβδομάδων πίσω από το τρέχον UTC (π.χ. "2")
            # period     -> χρονικό διάστημα κάθε κερί (π.χ. "D1", "H1", "M1")
            # symbolId   -> ID του συμβόλου (π.χ. "1" για EUR/USD)
            # clientMsgId (προαιρετικό) -> μοναδικό ID μηνύματος για tracking"""
        try:
            request = ProtoOAGetTrendbarsReq()
            request.ctidTraderAccountId = self.account_id
            request.period = ProtoOATrendbarPeriod.Value(period.upper())

            now = datetime.datetime.utcnow()
            from_ts = int(calendar.timegm((now - datetime.timedelta(weeks=int(weeks))).utctimetuple()) * 1000)
            to_ts = int(calendar.timegm(now.utctimetuple()) * 1000)

            request.fromTimestamp = from_ts
            request.toTimestamp = to_ts
            request.symbolId = int(symbolId)

            deferred = self.client.send(request, clientMsgId=clientMsgId)
            deferred.addErrback(self.on_error)
        except Exception as e:
            print("Trendbars request error:", e)

    def sendProtoOAGetTickDataReq(self, days, quoteType, symbolId, clientMsgId=None):
        """
            Αποστέλλει αίτημα για ιστορικά tick data (π.χ. bid/ask τιμές) συγκεκριμένου συμβόλου για καθορισμένο αριθμό ημερών.

            ΠΑΡΑΜΕΤΡΟΙ:
            days        -> αριθμός ημερών πίσω από σήμερα (π.χ. "3")
            quoteType   -> τύπος τιμής ("BID", "ASK", "LAST")
            symbolId    -> ID του συμβόλου (π.χ. 1 για EUR/USD)
            clientMsgId -> (προαιρετικό) μοναδικό ID μηνύματος για παρακολούθηση
            """
        request = ProtoOAGetTickDataReq()
        request.ctidTraderAccountId = self.account_id
        request.type = ProtoOAQuoteType.Value(quoteType.upper())
        request.fromTimestamp = int(
            calendar.timegm((datetime.datetime.utcnow() - datetime.timedelta(days=int(days))).utctimetuple())) * 1000
        request.toTimestamp = int(calendar.timegm(datetime.datetime.utcnow().utctimetuple())) * 1000
        request.symbolId = int(symbolId)
        deferred = self.client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)

    def sendProtoOANewOrderReq(self, symbolId, orderType, tradeSide, volume, price=None, clientMsgId=None):
        """
        Αποστέλλει αίτημα για δημιουργία νέας εντολής αγοράς ή πώλησης (Market, Limit ή Stop) για συγκεκριμένο σύμβολο.

        ΠΑΡΑΜΕΤΡΟΙ:
        symbolId    -> ID του συμβόλου (π.χ. 1 για EUR/USD)
        orderType   -> τύπος εντολής: "MARKET", "LIMIT" ή "STOP"
        tradeSide   -> πλευρά συναλλαγής: "BUY" ή "SELL"
        volume      -> όγκος σε μονάδες (πολλαπλασιάζεται με 100 για συμβατότητα με API)
        price       -> (προαιρετικό) απαιτείται για LIMIT ή STOP εντολές
        clientMsgId -> (προαιρετικό) μοναδικό ID μηνύματος για παρακολούθηση
        """
        request = ProtoOANewOrderReq()
        request.ctidTraderAccountId = self.account_id
        request.symbolId = int(symbolId)
        request.orderType = ProtoOAOrderType.Value(orderType.upper())
        request.tradeSide = ProtoOATradeSide.Value(tradeSide.upper())
        request.volume = int(volume) * 100
        if request.orderType == ProtoOAOrderType.LIMIT:
            request.limitPrice = float(price)
        elif request.orderType == ProtoOAOrderType.STOP:
            request.stopPrice = float(price)
        deferred = self.client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)

    def sendNewMarketOrder(self, symbolId, tradeSide, volume, clientMsgId = None):
        """
        Δημιουργεί και αποστέλλει εντολή Market Order (άμεση εκτέλεση) για συγκεκριμένο σύμβολο, κατεύθυνση και όγκο.

        ΠΑΡΑΜΕΤΡΟΙ:
        symbolId    -> ID του συμβόλου (π.χ. 1 για EUR/USD)
        tradeSide   -> πλευρά συναλλαγής: "BUY" ή "SELL"
        volume      -> όγκος σε μονάδες (θα πολλαπλασιαστεί με 100 στην κύρια συνάρτηση)
        clientMsgId -> (προαιρετικό) μοναδικό ID μηνύματος για παρακολούθηση
        """
        self.sendProtoOANewOrderReq(symbolId, "MARKET", tradeSide, volume, clientMsgId = clientMsgId)

    def sendNewLimitOrder(self, symbolId, tradeSide, volume, price, clientMsgId = None):
        """
        Δημιουργεί και αποστέλλει Limit Order για συγκεκριμένο σύμβολο, κατεύθυνση και όγκο σε καθορισμένη τιμή.

        ΠΑΡΑΜΕΤΡΟΙ:
        symbolId    -> ID του συμβόλου (π.χ. 1 για EUR/USD)
        tradeSide   -> "BUY" ή "SELL"
        volume      -> όγκος συναλλαγής (πολλαπλασιάζεται εσωτερικά με 100)
        price       -> η τιμή εκτέλεσης της εντολής (Limit)
        clientMsgId -> (προαιρετικό) μοναδικό ID μηνύματος για παρακολούθηση
        """
        self.sendProtoOANewOrderReq(symbolId, "LIMIT", tradeSide, volume, price, clientMsgId)

    def sendNewStopOrder(self, symbolId, tradeSide, volume, price, clientMsgId = None):
        """
        Δημιουργεί και αποστέλλει Stop Order για συγκεκριμένο σύμβολο,
        κατεύθυνση και όγκο, το οποίο ενεργοποιείται όταν η τιμή φτάσει σε καθορισμένο επίπεδο.

        ΠΑΡΑΜΕΤΡΟΙ:
        symbolId    -> ID του συμβόλου (π.χ. 1 για EUR/USD)
        tradeSide   -> "BUY" ή "SELL"
        volume      -> όγκος συναλλαγής (πολλαπλασιάζεται εσωτερικά με 100)
        price       -> τιμή ενεργοποίησης της εντολής (Stop Price)
        clientMsgId -> (προαιρετικό) μοναδικό ID μηνύματος για παρακολούθηση
        """
        self.sendProtoOANewOrderReq(symbolId, "STOP", tradeSide, volume, price, clientMsgId)

    def sendProtoOAClosePositionReq(self, positionId, volume, clientMsgId=None):
        """
        Αποστέλλει αίτημα για μερικό ή πλήρες κλείσιμο ανοιχτής θέσης (position) συγκεκριμένου όγκου.

        ΠΑΡΑΜΕΤΡΟΙ:
        positionId  -> ID της θέσης που θέλεις να κλείσεις
        volume      -> όγκος για κλείσιμο (πολλαπλασιάζεται με 100 για API συμβατότητα)
        clientMsgId -> (προαιρετικό) μοναδικό ID μηνύματος για παρακολούθηση
        """
        request = ProtoOAClosePositionReq()
        request.ctidTraderAccountId = self.account_id
        request.positionId = int(positionId)
        request.volume = int(volume) * 100
        deferred = self.client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)

    def sendProtoOACancelOrderReq(self, orderId, clientMsgId=None):
        """
        Αποστέλλει αίτημα για ακύρωση εντολής (Limit ή Stop) που δεν έχει εκτελεστεί ακόμη.

        ΠΑΡΑΜΕΤΡΟΙ:
        orderId     -> ID της εντολής που θέλεις να ακυρώσεις
        clientMsgId -> (προαιρετικό) μοναδικό ID μηνύματος για παρακολούθηση
        """
        request = ProtoOACancelOrderReq()
        request.ctidTraderAccountId = self.account_id
        request.orderId = int(orderId)
        deferred = self.client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)

    def sendProtoOADealOffsetListReq(self, dealId, clientMsgId=None):
        """
        Αποστέλλει αίτημα για λήψη της λίστας offset συναλλαγών (deals) που σχετίζονται με συγκεκριμένο deal ID.

        ΠΑΡΑΜΕΤΡΟΙ:
        dealId      -> ID της συναλλαγής (deal) για την οποία θέλεις τα offset deals
        clientMsgId -> (προαιρετικό) μοναδικό ID μηνύματος για παρακολούθηση
        """
        request = ProtoOADealOffsetListReq()
        request.ctidTraderAccountId = self.account_id
        request.dealId = int(dealId)
        deferred = self.client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)

    def sendProtoOAGetPositionUnrealizedPnLReq(self, clientMsgId=None):
        """
        Αποστέλλει αίτημα για λήψη των μη πραγματοποιημένων κερδών/ζημιών (Unrealized PnL)
        των ανοιχτών θέσεων του λογαριασμού.

        ΠΑΡΑΜΕΤΡΟΙ:
        clientMsgId -> (προαιρετικό) μοναδικό ID μηνύματος για παρακολούθηση
        """
        request = ProtoOAGetPositionUnrealizedPnLReq()
        request.ctidTraderAccountId = self.account_id
        deferred = self.client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)

    def sendProtoOAOrderDetailsReq(self, orderId, clientMsgId=None):
        """
        Αποστέλλει αίτημα για λήψη αναλυτικών πληροφοριών εντολής (Order) βάσει του μοναδικού της ID.

        ΠΑΡΑΜΕΤΡΟΙ:
        orderId     -> ID της εντολής που θέλεις να ελέγξεις
        clientMsgId -> (προαιρετικό) μοναδικό ID μηνύματος για παρακολούθηση
        """
        request = ProtoOAOrderDetailsReq()
        request.ctidTraderAccountId = self.account_id
        request.orderId = int(orderId)
        deferred = self.client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)

    def sendProtoOAOrderListByPositionIdReq(self, positionId, fromTimestamp=None, toTimestamp=None, clientMsgId=None):
        """
        Αποστέλλει αίτημα για λήψη της λίστας εντολών που σχετίζονται με συγκεκριμένη θέση (position), με δυνατότητα χρονικού φιλτραρίσματος.

        ΠΑΡΑΜΕΤΡΟΙ:
        positionId   -> ID της θέσης για την οποία θέλεις τις σχετικές εντολές
        fromTimestamp -> (προαιρετικό) χρονικό σημείο έναρξης (UTC timestamp σε ms)
        toTimestamp   -> (προαιρετικό) χρονικό σημείο λήξης (UTC timestamp σε ms)
        clientMsgId   -> (προαιρετικό) μοναδικό ID μηνύματος για παρακολούθηση
        """
        request = ProtoOAOrderListByPositionIdReq()
        request.ctidTraderAccountId = self.account_id
        request.positionId = int(positionId)
        deferred = self.client.send(request, fromTimestamp=fromTimestamp, toTimestamp=toTimestamp, clientMsgId=clientMsgId)
        deferred.addErrback(self.on_error)
