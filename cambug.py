#!/usr/bin/env python
import socket
import time

host = '172.28.1.95'
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

rtp = 0
rtpl = 0
k=1
q=1
sl=0
sll=0
start = time.time()
prev=None
loss=0

while True:
  d = time.time()-start
  if (round(d*10)%3)==0:
    if k==0:
      print "RTP ", rtp/d, rtpl/d, "last", prev, "loss", loss
      #loss=0
      k=1
  else:
    k=0
  if (round(d)%2==1):
    if q==0:
      st = 1 # 0.5+d.round/100.0
      print "Sleep ", st
      time.sleep(st)
      q=1
      sl=1
  else:
    q=0
  res = s.recv(4)
  if len(res)==4 and res[0]=="$":
    l = (ord(res[2])<<8)+ord(res[3])
    block = ""
    while len(block) < l:
      p = s.recv(l-len(block))
      block += p
    if res[1]=="\x00":
      packno = (ord(block[2])<<8)+ord(block[3])
      if prev is not None:
          if prev>packno: packno+=65536
          loss += packno-prev-1
      prev = packno
      rtp += 1
      rtpl += l
      if sl==1:
        sll += len(res)+l
    elif res[1]=="\x01":
      print "RTCP #{len} #{block.length} #{len==block.length}"
    else:
        #Hexdump.dump(res)
      raise Exception("Garbage 1")
  else:
      #Hexdump.dump(res)
    raise Exception("Garbage 2 "+str(sll)+" loss="+str(loss))

s.close()
