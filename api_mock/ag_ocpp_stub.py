# -----------------------------------------------------------------------------
# Agoras Off-chain payment system interface methods: ag_wallet and ag_channel
# -----------------------------------------------------------------------------

import os
import subprocess
import time
import json
import pprint
import random
import string
import signal

# -----------------------------------------------------------------------------
#
# - all ag_wallet methods require user_waddr argument
# - all ag_channel methods require user_waddr and peer_user_waddr arguments as 
#   unique identifier for the channel
#
# - gets will retrun serialized json objects 
# - non gets will retrun status messages indicating success, warnings or errors
# -----------------------------------------------------------------------------

def ag_wallet(user_waddr=None):
    handler = api_clightning(user_waddr)
    return handler.open(user_waddr)

def ag_wallet_getaddress(user_waddr):
    handler = api_clightning(user_waddr)
    return handler.address()

def ag_wallet_getbalance(user_waddr):
    handler = api_clightning(user_waddr)
    return handler.balance()
    
def ag_wallet_gethistory(user_waddr):
    handler = api_clightning(user_waddr)
    return handler.history()

def ag_wallet_withdraw(user_waddr, to_addr, amount):
    handler = api_clightning(user_waddr)
    return handler.withdraw(to_addr, amount)

# -----------------------------------------------------------------------------

def ag_channel(user_waddr, peer_user_waddr, from_ts, to_ts, rate, bonus = 0):
    handler = api_clightning(user_waddr)
    handler_peer = api_clightning(peer_user_waddr)
    return handler.connect(handler_peer, from_ts, to_ts, rate, bonus)

def ag_channel_status(user_waddr, peer_user_waddr):
    handler = api_clightning(user_waddr)
    handler_peer = api_clightning(peer_user_waddr)
    return handler.status(handler_peer)

def ag_channel_start(user_waddr, peer_user_waddr):
    handler = api_clightning(user_waddr)
    handler_peer = api_clightning(peer_user_waddr)
    return handler.start(handler_peer)

def ag_channel_stop(user_waddr, peer_user_waddr):
    handler = api_clightning(user_waddr)
    handler_peer = api_clightning(peer_user_waddr)
    return handler.stop(handler_peer)

#def ag_channel_instantpay(amount):

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# ** MOCK ** implementation of th payment system interface 
# -----------------------------------------------------------------------------

# global configurations
MOCK = True
MOCK_INIT_FUNDS=1000
VERBOSE = True
DB_DIR = "/tmp/"

# -----------------------------------------------------------------------------   

class api_clightning(object):

    def __init__(self, user_waddr):
        self.user_waddr = user_waddr
        self.account_data = None
    
    # helpers to access per user data
    def stub_account_getdata(self):
        with open(DB_DIR+self.user_waddr) as f:
            fdata = f.readline()
            account_data = json.loads(fdata)
        return account_data

    def stub_account_setdata(self,account_data):
         with open(DB_DIR+self.user_waddr, 'w') as f:
             f.write(json.dumps(account_data))
    
    # -------------------------------------------------------------------------
    # wallet create/open
    def open(self, waddr):
    
        if self.user_waddr == None:             
            addr = "2"+''.join(random.choices(string.ascii_letters + string.digits, k=34))
            account_data = {\
                'user_waddr' : addr, 'balance' :  MOCK_INIT_FUNDS, 'locked' :  0,\
                'tx_history' : [], 'channels' : []\
            }
            self.user_waddr = addr
            self.stub_account_setdata(account_data)
            return_data = addr
        else: 
            if os.path.isfile(DB_DIR+self.user_waddr) == False:
                return_data = {'status' : 'error: wallet address missing in db : ' + self.user_waddr }
            else:
                return_data = {'status' : 'success on_agwallet_open'}

        if VERBOSE:
            print("")
            print("#open")
            pprint.pprint(return_data)
    
        return json.dumps(return_data)    


    def balance(self):
        data = self.stub_account_getdata()['balance']
        if VERBOSE:
            print("")
            print("#balance", self.user_waddr)
            pprint.pprint(data)
        return json.dumps(data)

    def address(self):
        data = self.stub_account_getdata()['user_waddr']
        if VERBOSE:
            print("")
            print("#address", self.user_waddr)
            pprint.pprint(data)
        return json.dumps(data)

    #transaction history
    def history(self):
        data = self.stub_account_getdata()['tx_history']
        if VERBOSE:
            print("")
            print("#history", self.user_waddr)    
            pprint.pprint(data)
        return json.dumps(data)

    def withdraw(self, address, amount, is_lock=False):
        data = self.stub_account_getdata()

        if VERBOSE:
            print("")
            print("#withdraw", self.user_waddr)
            tx_data = {'tx_id' : 0, 'date': 0, 'from' : self.user_waddr ,'to' : address, 'amount': amount}
            pprint.pprint(tx_data) 

        if(amount > data['balance']):
            return_data = { 'status' : 'error: not enough funds'} 
            return json.dumps(return_info)    

        data['tx_history'].append(tx_data)        
        data['balance'] =  data['balance'] - amount
        if is_lock == True:
            data['locked'] =  data['locked'] + amount

        self.stub_account_setdata(data)
        return_data = { 'status' : 'success on_withdraw'}
        return json.dumps(return_data)    

    # -------------------------------------------------------------------------
    # helper to get index of channels in per-user data record
    def getchindex(self, peer_waddr):
        data = self.stub_account_getdata()
        i = -1
        for k in range(len(data['channels'])):
            if data['channels'][k]['peer_id'] == peer_waddr and\
               data['channels'][k]['status'] == "FUNDED":
                i = k
                break
        return i


    # channel setup
    def connect(self, handler_peer, from_ts, to_ts, rate, extra_x_tip):
      
        i = self.getchindex(handler_peer.user_waddr)  
        if i != -1:
            return_data = { 'status' : 'warning: session already funded'} 
            return json.dumps(return_data)  
        else:
            session_total = (to_ts - from_ts) * rate + extra_x_tip
            if int(self.balance()) < (to_ts - from_ts) * rate + extra_x_tip:
                return_data = { 'status' : 'error: not enough founds to fund session'} 
                return json.dumps(return_info)  
            
            addr = "2"+''.join(random.choices(string.ascii_letters + string.digits, k=34))
            new_channel = {\
                'ch_mode' : 'payer', 'peer_id' : handler_peer.user_waddr,\
                'ch_addr' : addr, 'ch_totalfunds' : session_total, 'status' : 'FUNDED',\
                'paid' : 0, 'step': rate, 'max_loops' : to_ts - from_ts, 'ts_loop' : 1, 'pid' : ''\
            }    
            new_channel_peer = {\
                'ch_mode' : 'payee', 'peer_id' : self.user_waddr,\
                'ch_addr' : addr, 'ch_totalfunds' : session_total, 'status' : 'FUNDED',\
                'paid' : 0, 'step': rate, 'max_loops' : to_ts - from_ts, 'ts_loop' : 1, 'pid' : ''\
            }    
            
            #withdraw with is_lock = True
            self.withdraw(addr, session_total, True)
            #XXX: data dependence here
            data = self.stub_account_getdata()
            data_peer = handler_peer.stub_account_getdata()

            data['channels'].append(new_channel)
            data_peer['channels'].append(new_channel_peer)        
            self.stub_account_setdata(data)
            handler_peer.stub_account_setdata(data_peer)
            return_data = { 'status' : 'success on_schedule_session'} 
        
        if VERBOSE:
            print("")
            print("#connect", self.user_waddr  , "to", handler_peer.user_waddr)
            pprint.pprint(return_data)
        return json.dumps(return_data)    

    # micropayment protocol start
    def start(self, handler_peer):
        data = self.stub_account_getdata()
        data_peer = handler_peer.stub_account_getdata()

        i = self.getchindex(handler_peer.user_waddr)  
        j = handler_peer.getchindex(self.user_waddr)  
        if i == -1 or j == -1:
            return_data = { 'status' : 'error: no channels FUNDED for this peer'} 
            return json.dumps(return_data)              
        else:
            #XXX review how time and iter time are set
            n_iter = str(data['channels'][i]['max_loops'])
            iter_time = str(data['channels'][i]['ts_loop'])
            command = "python3 " + os.getcwd()+"/ag_ocpp_loop.py " + n_iter + " " + iter_time + " "\
                      + self.user_waddr + " " + handler_peer.user_waddr
            p = subprocess.Popen("exec " + command, stderr=subprocess.STDOUT, shell=True);

            data['channels'][i]['pid']  = p.pid
            data_peer['channels'][j]['pid']  = p.pid
            self.stub_account_setdata(data)
            handler_peer.stub_account_setdata(data_peer)

            return_data = { 'status' : 'success on_payment_session_start'} 
            return json.dumps(return_data)
    

    # micropayment protocol step, called from prom the 'loop'
    def step(self, handler_peer):
        data = self.stub_account_getdata()
        data_peer = handler_peer.stub_account_getdata()

        i = self.getchindex(handler_peer.user_waddr)  
        j = handler_peer.getchindex(self.user_waddr)  
        if i == -1 or j == -1:
            #XXX handle this errror from loop
            return_data = { 'status' : 'error: no channels FUNDED for this peer'} 
            return json.dumps(return_data) 

        data['channels'][i]['paid'] = data['channels'][i]['paid'] + data['channels'][i]['step']
        data_peer['channels'][j]['paid'] = data_peer['channels'][j]['paid'] + data_peer['channels'][j]['step']
        self.stub_account_setdata(data)
        handler_peer.stub_account_setdata(data_peer)
         
    # loop termination
    def stop(self, handler_peer):
        data = self.stub_account_getdata()
        data_peer = handler_peer.stub_account_getdata()    

        i = self.getchindex(handler_peer.user_waddr)  
        j = handler_peer.getchindex(self.user_waddr)  
        if i == -1 or j == -1:
            return_data = { 'status' : 'error: no channels FUNDED for this peer'} 
            return json.dumps(return_data) 
        pid = data['channels'][i]['pid']

        # mock's rough way to end the payment session
        os.kill(pid, signal.SIGTERM)  
        
        # negotiation 
        close_amount = data['channels'][i]['ch_totalfunds'] - data['channels'][i]['paid']       
    
        if data['channels'][i]['ch_mode'] == "payer":
            if close_amount != 0:
                tx_data = {'tx_id' : 0, 'date': 0, 'from' : data['channels'][i]['ch_addr'],\
                       'to' : self.user_waddr,\
                       'amount': close_amount}
                data['tx_history'].append(tx_data)        
                data['balance'] =  data['balance'] + tx_data['amount']
                data['locked'] =  0
 
            tx_data_peer = {'tx_id' : 0, 'date': 0, 'from' : data['channels'][i]['ch_addr'],\
                        'to' : handler_peer.user_waddr,\
                        'amount':  data['channels'][i]['paid']}
            data_peer['tx_history'].append(tx_data_peer)        
            data_peer['balance'] =  data_peer['balance'] + tx_data_peer['amount']
        else:
            tx_data = {'tx_id' : 0, 'date': 0, 'from' : data['channels'][i]['ch_addr'],\
                        'to' : self.user_waddr,\
                        'amount':  data['channels'][i]['paid']}
            data['tx_history'].append(tx_data)        
            data['balance'] =  data['balance'] + tx_data['amount']

            if close_amount != 0:
                tx_data_peer = {'tx_id' : 0, 'date': 0, 'from' : data['channels'][i]['ch_addr'],\
                       'to' : handler_peer.user_waddr,\
                       'amount': close_amount}
                data_peer['tx_history'].append(tx_data_peer)        
                data_peer['balance'] =  data_peer['balance'] + tx_data_peer['amount']
                data_peer['locked'] =  0
    
        data['channels'][i]['status'] = "ONCHAIN"
        data['channels'][i]['pid'] = 0
        data_peer['channels'][j]['status'] = "ONCHAIN"
        data_peer['channels'][i]['pid'] = 0
        self.stub_account_setdata(data)
        handler_peer.stub_account_setdata(data_peer)
        return_data = { 'status' : 'success on_payment_session_stop'} 
        return json.dumps(return_data)

    # channel status - FUNDED , ONCHAIN and paid ammout information
    def status(self, handler_peer):
        data = self.stub_account_getdata()
        data_peer = handler_peer.stub_account_getdata()

        channel = None
        if data['channels'] != None:
            channel = [ d for d in data['channels']\
                        if d['peer_id'] == data_peer['user_waddr'] ] 
        if channel == None:
            return_data = { 'status' : 'warning: no channels for this peer'} 
            return json.dumps(return_data)

        ###TODO: properly report FUNDED, ONCHAIN
        if VERBOSE:
            print("")
            print("#status", data['user_waddr'])
            pprint.pprint(channel)
        
        return json.dumps(channel) 

        
        #i = self.getchindex(handler_peer.user_waddr)  
        #if i == -1:
        #    return_data = { 'status' : 'error: no channels FUNDED for this peer'} 
        #    return json.dumps(return_data)
        #else:
        #    if VERBOSE:
        #        print("---------------------------------------------------------")
        #        print("#status", data['user_waddr'])
        #        pprint.pprint(data['channels'][i])
        #    return json.dumps(data['channels'][i]) 

    # -------------------------------------------------------------------------

