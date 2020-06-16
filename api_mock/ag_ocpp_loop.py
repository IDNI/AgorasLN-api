import sys, os
from ag_ocpp_stub import *
 
print(sys.argv[0])
n_iter = int(sys.argv[1])
ts = int(sys.argv[2])
payer_id = sys.argv[3]
payee_id = sys.argv[4]

handler = api_clightning(payer_id)
handler_peer = api_clightning(payee_id)

for i in range(n_iter):
    print(os.getpid(), "# micropayment channel running, iter:", i)
    time.sleep(ts)     
    handler.step(handler_peer)


   


