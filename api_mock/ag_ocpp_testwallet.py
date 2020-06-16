# basic test for wallet api

from ag_ocpp_stub import *
import json
import pprint

# -----------------------------------------------------------------
#wallet create
response = ag_wallet()
wid_juan = json.loads(response)

response = ag_wallet_getbalance(wid_juan)

response = ag_wallet_withdraw(wid_juan, "tosomeaddr", 1)

#XXX: stub is in VERBOSE mode, so history will be printed from it
response = ag_wallet_gethistory(wid_juan)
#pprint.pprint(response)
response = ag_wallet_getbalance(wid_juan)

# -----------------------------------------------------------------
#wallet open
response = ag_wallet(wid_juan)
response = ag_wallet_withdraw(wid_juan, "otheraddr", 10)
response = ag_wallet_gethistory(wid_juan)
response = ag_wallet_getbalance(wid_juan)


