#!/usr/bin/env python
import socket
import time
import random
import re

host = '172.28.1.95'
url = '/mpeg4/track1'
port = 554

host = '91.135.150.xx' #:1554/h264
url = '/h264/track1'
port = 1554

host = '172.28.1.94'
url = '/user=admin&password=admink&channel=1&stream=0.sdp?real_stream' # 92 93 94
port = 554

def hx(s):
    return " ".join("{:02x}".format(ord(c)) for c in s)

def connect():
    descmsg = "DESCRIBE rtsp://"+host+url+" RTSP/1.0\r\nCSeq: 0\r\n"
    setupmsg = "SETUP rtsp://"+host+url+" RTSP/1.0\r\nCSeq: 1\r\nTransport: RTP/AVP/TCP;unicast\r\n"
    playmsg = "PLAY rtsp://"+host+url+" RTSP/1.0\r\nCSeq: 2\r\nRange: npt=0.000-\r\n"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16*1024*1024)
    #s.setsockopt(socket.SOL_SOCKET, socket.TCP_WINDOW_CLAMP, 16*512*1024)
    s.connect((host, port))
    if False:
        s.send(descmsg+"\r\n")
        print descmsg
        res = s.recv(1500)
        print res
    s.send(setupmsg+"\r\n")
    print setupmsg
    res = s.recv(1500)
    print res
    sess = re.search("\r\n(Session:.*?)(?:;|\r\n)", res).group(1)+"\r\n"
    s.send(playmsg+sess+"\r\n", 0)
    print playmsg+sess
    res = s.recv(1500)
    print res
    pos = res.find("\r\n\r\n")
    if pos>-1:
        res = res[pos+4:]
    else:
        res = ""
    return (s, res, sess)

def ping(s, sess, cseq):
    pingmsg = "GET_PARAMETER rtsp://"+host+url+" RTSP/1.0\r\n CSeq: "+str(cseq)+"\r\n"+sess+"\r\n"
    s.send(pingmsg, 0)
    return cseq+1

rtp = 0
rtpl = 0
k=1
q=1
pi=1
sl=0
sll=0
st=1
s,buf,sess=connect()
cseq = 3
prevts=None
prev=None
loss=0
frames=0
framesimp=0
framesimpt = 0
start = time.time()

while True:
  d = time.time()-start
  if (round(d)%30)<10:
    if pi==0:
      cseq=ping(s, sess, cseq)
      pi = 1
  else:
    pi = 0
  if (round(d*10)%3)==0:
    if k==0:
      #cseq=ping(s, sess, cseq)
      print d, "RTP ", rtp/d, rtpl/d, " fps=%.3f [%.1f]"%(frames/d, (frames-framesimp)/(d-framesimpt)), "last", prev, "loss", loss, loss/st
      framesimp = frames
      framesimpt = d
      loss=0
      k=1
  else:
    k=0
  if (round(d)%4==0):
    if q==0:
      st = 0.5+round(random.random()*5,2) # 0.5+d.round/100.0
      #print "Sleep ", st
      #time.sleep(st)
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

      ts = (ord(buf[8])<<24)+(ord(buf[9])<<16)+(ord(buf[10])<<8)+ord(buf[11])
      if prevts is not None:
          if ts!=prevts:
              frames += 1
      prevts = ts
      rtp += 1
      rtpl += l
      if sl==1:
        sll += l+4
    elif buf[1]=="\x01":
      print "RTCP ", l
    else:
      raise Exception("Garbage 1"+hx(buf))
    buf = buf[4+l:]
  else:
    #Hexdump.dump(res)
    print Exception("Garbage 2 "+str(sll)+" loss="+str(loss)+" "+hx(buf[0:4]))
    # try to resync
    if False:
        s,buf=connect()
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
            print "Skipped for resync ", sync, " bytes"
            print hx(buf[:sync])
            buf = buf[sync:]
        else:
            raise Exception("Can't resync")
s.close()
