# basic test for channel api

from ag_ocpp_stub import *
import os
import json
import pprint


#student account creation
print("\n\n------------------------------------------------------")
print("@student: logged into agoraslive")
response = ag_wallet()
wid_student = json.loads(response)
response = ag_wallet_getbalance(wid_student)

#einstein account creation
print("\n\n------------------------------------------------------")
print("@einstein: logged into agoraslive")
response = ag_wallet()
wid_einstein  = json.loads(response)
response = ag_wallet_getbalance(wid_einstein)

#student-einstein interaction
print("\n\n------------------------------------------------------")
print("@student: hey einstein! give me a lesson please")

# ts_start = 0, ts_end = 30 -> 30 seconds session at 10 tokens per sercond
response = ag_channel(wid_student, wid_einstein, 0, 30, 10)

print("\n\n------------------------------------------------------")
print("@einstein: ok mr student! let me see if you can pay for my")
print("           universal knowledge")

response = ag_channel_status(wid_einstein, wid_student)

print("@einstein: oooh FUNDED nice!")

print("\n\n------------------------------------------------------")
print("@student & @einstein: lets see our faces and talk ...")

response = ag_channel_start(wid_student, wid_einstein)

time.sleep(7)     

print("\n\n------------------------------------------------------")
print("@student: enough of relativity, thanks but will check with newton ...")

response = ag_channel_stop(wid_student, wid_einstein)     

response = ag_channel_status(wid_einstein, wid_student)

print("\n\n------------------------------------------------------")
print("@einstein: newton pff, lets see how much i made today ...")
response = ag_wallet_getbalance(wid_einstein)
response = ag_wallet_gethistory(wid_einstein)

print("\n\n------------------------------------------------------")
print("@student: hmm, lets see how much i have for keep learning here...")
response = ag_wallet_getbalance(wid_student)
response = ag_wallet_gethistory(wid_student)

