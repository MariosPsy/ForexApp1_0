from multiprocessing import Queue
from client import TraderClient
import os


if __name__ == "__main__":
    """Run the Trader client using credentials from environment variables."""
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
    ACCOUNT_ID = int(os.getenv("ACCOUNT_ID", "0"))

    if not all([CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN, ACCOUNT_ID]):
        raise RuntimeError(
            "Required credentials are not set. Please provide CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN and ACCOUNT_ID as environment variables."
        )

    q = Queue()
    q.put("ProtoOAGetTrendbarsReq 70 D1 1")


    marios_trader = TraderClient(CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN, ACCOUNT_ID, command_queue=q)
    marios_trader.setup_client()