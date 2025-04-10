from multiprocessing import Queue
from client import TraderClient


if __name__ == "__main__":
    # Παράδειγμα τιμών - αντικατάστησέ τα με τα δικά σου credentials
    CLIENT_ID = "12898_X4w5r7eDmhqZcSjm7zBORbk9JRAbyO9a8RRvYvqQ3MTUdotn9v"
    CLIENT_SECRET = "AbHdcTMPx3oiBFxIWE1LqtG7kpDbO39Uhcj3iiCo7xKmYKN1AI"
    ACCESS_TOKEN = "KKV56tp57nU89pVsZ9PU1NzxvDHGoY9YM-7iJpfrWDE"
    ACCOUNT_ID = 41974560

    q = Queue()
    q.put("ProtoOAGetTrendbarsReq 2 D1 1")
    # q.put("ProtoOAGetAccountListByAccessTokenReq def456")

    marios_trader = TraderClient(CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN, ACCOUNT_ID, command_queue=q)
    marios_trader.setup_client()