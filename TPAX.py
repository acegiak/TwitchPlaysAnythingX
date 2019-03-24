#!/usr/bin/python3
import json
import re
import socket
from xdo import Xdo
import time
import random
import os
import threading

xdo = Xdo()
chose = ""
last = time.time()
votes={}

with open("config.json", "r") as read_file:
    config = json.load(read_file)
print(config)

def do_key(keyname):
    global xdo,config
    coq = xdo.search_windows(config['windowname'].encode())
    if len(coq):
        xdo.activate_window(coq[0])
        xdo.send_keysequence_window(coq[0],keyname.encode()) 
    else:
        print("No matching window found.")

def countVotes():
    global last, votes, chose
    while True:
        os.system('clear')
        print("Did: "+chose)
        highest = None
        highestKey = []
        for key in votes.keys():
            print(key+": "+str(votes[key]))
            if highest is None or votes[key] > highest:
                highest = votes[key]
                highestKey = [key]
            elif votes[key] == highest:
                highestKey.append(key)
        if time.time()-last >config['voteinterval']:
            last = time.time()
            if len(highestKey) > 0:
                chose = random.choice(highestKey)
                do_key(chose)
            else:
                chose = "None"
            votes={}
        time.sleep(0.25)


def vote(keyname):
    global last, votes, config
    if "mappings" in config.keys():
        if keyname in config['mappings'].keys():
            keyname = config['mappings'][keyname]
    if keyname not in votes:
        votes[keyname] = 1
    else:
        votes[keyname] = votes[keyname]+1

thread = threading.Thread(target=countVotes)
thread.start()

# --------------------------------------------- Start Settings ----------------------------------------------------
HOST = "irc.twitch.tv"                          # Hostname of the IRC-Server in this case twitch's
PORT = 6667                                     # Default IRC-Port
# --------------------------------------------- End Settings -------------------------------------------------------


# --------------------------------------------- Start Functions ----------------------------------------------------
def send_pong(msg):
    con.send(bytes('PONG %s\r\n' % msg, 'UTF-8'))


def send_message(chan, msg):
    con.send(bytes('PRIVMSG %s :%s\r\n' % (chan, msg), 'UTF-8'))


def send_nick(nick):
    con.send(bytes('NICK %s\r\n' % nick, 'UTF-8'))


def send_pass(password):
    con.send(bytes('PASS %s\r\n' % password, 'UTF-8'))


def join_channel(chan):
    con.send(bytes('JOIN %s\r\n' % chan, 'UTF-8'))


def part_channel(chan):
    con.send(bytes('PART %s\r\n' % chan, 'UTF-8'))
# --------------------------------------------- End Functions ------------------------------------------------------


# --------------------------------------------- Start Helper Functions ---------------------------------------------
def get_sender(msg):
    result = ""
    for char in msg:
        if char == "!":
            break
        if char != ":":
            result += char
    return result


def get_message(msg):
    result = ""
    i = 3
    length = len(msg)
    while i < length:
        result += msg[i] + " "
        i += 1
    result = result.lstrip(':')
    return result


def parse_message(sender,msg):
    if len(msg) >= 1:
        msg = msg.split(' ')
        if(msg[0] == "^"):
            vote(msg[1])

# --------------------------------------------- End Helper Functions -----------------------------------------------

con = socket.socket()
con.connect((HOST, PORT))

send_pass(config['oauth'])
send_nick(config['username'])
join_channel(config['channel'])

data = ""

while True:
    try:
        data = data+con.recv(1024).decode('UTF-8')
        data_split = re.split(r"[~\r\n]+", data)
        data = data_split.pop()

        for line in data_split:
            line = str.rstrip(line)
            line = str.split(line)

            if len(line) >= 1:
                if line[0] == 'PING':
                    send_pong(line[1])

                if line[1] == 'PRIVMSG':
                    sender = get_sender(line[0])
                    message = get_message(line)
                    parse_message(sender,message)

                    #print(sender + ": " + message)

    except socket.error:
        print("Socket died")

    except socket.timeout:
        print("Socket timeout")