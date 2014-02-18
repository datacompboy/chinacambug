#!/usr/bin/env python
import socket
import time
import random

host = '172.28.1.95'

def connect(host):
    setupmsg = "SETUP rtsp://"+host+"/mpeg4/track1 RTSP/1.0\r\nCSeq: 1\r\nTransport: RTP/AVP/TCP;unicast\r\n"
    playmsg = "PLAY rtsp://"+host+"/mpeg4/ RTSP/1.0\r\nCSeq: 2\r\nRange: npt=0.000-"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16*1024*1024)
    #s.setsockopt(socket.SOL_SOCKET, socket.TCP_WINDOW_CLAMP, 16*512*1024)
    s.connect((host, 554))
    s.send(setupmsg+"\r\n")
    res = s.recv(1500)
    sess = res.split("\r\n")[-2]
    s.send(playmsg+sess+"\r\n"+"\r\n", 0)
    res = s.recv(1500)
    pos = res.find("\r\n\r\n")
    if pos>-1:
        res = res[pos+4:]
    else:
        res = ""
    return (s, res)

rtp = 0
rtpl = 0
k=1
q=1
sl=0
sll=0
st=1
s,buf=connect(host)
prev=None
loss=0
start = time.time()

while True:
  d = time.time()-start
  if (round(d*10)%3)==0:
    if k==0:
      print "RTP ", rtp/d, rtpl/d, "last", prev, "loss", loss, loss/st
      loss=0
      k=1
  else:
    k=0
  if (round(d)%2==0):
    if q==0:
      st = 0.5+round(random.random()*3,2) # 0.5+d.round/100.0
      print "Sleep ", st
      time.sleep(st)
      q=1
      sl=1
  else:
    q=0
  while len(buf)<4:
    buf += s.recv(4-len(buf))
  if buf[0]=="$":
    l = (ord(buf[2])<<8)+ord(buf[3])
    while len(buf)-4 < l:
      buf += s.recv(l+4-len(buf))
    if buf[1]=="\x00":
      packno = (ord(buf[6])<<8)+ord(buf[7])
      if prev is not None:
          if prev>packno: prev-=65536
          loss += packno-prev-1
      prev = packno
      rtp += 1
      rtpl += l
      if sl==1:
        sll += l+4
    elif buf[1]=="\x01":
      print "RTCP ", l
    else:
      raise Exception("Garbage 1")
    buf = buf[4+l:]
  else:
     #Hexdump.dump(res)
    print Exception("Garbage 2 "+str(sll)+" loss="+str(loss))
    # try to resync
    if False:
        s,buf=connect(host)
    else:
        sync = -1
        last = 0
        while sync<0 and len(buf)<5000:
            buf += s.recv(1500)
            while last<len(buf)-4:
                if buf[last]=="$" and buf[last+1]=="\x00":
                    synclen = (ord(buf[last+2])<<8)+ord(buf[last+3])
                    if synclen < 1500:
                        if len(buf)>last+4+synclen:
                            if buf[last+4+synclen]=="$":
                                sync = last # found correct resync position
                                break
                            else:
                                last += 1 # wrong position, check next
                        else:
                            break # need more info to verify is correct resync position
                    else:
                        last += 1 # wrong position, check next
                else:
                    last += 1 # wrong position, check next
        if sync >= 0:
            buf = buf[sync:]
        else:
            raise Exception("Can't resync")
s.close()
