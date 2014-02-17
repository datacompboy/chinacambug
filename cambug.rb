require 'socket'

host = '172.28.1.95'
conn = TCPSocket.new(host, 554)

setupmsg = "SETUP rtsp://#{host}/mpeg4/track1 RTSP/1.0\r\nCSeq: 1\r\nTransport: RTP/AVP/TCP;unicast\r\n"
playmsg = "PLAY rtsp://#{host}/mpeg4/ RTSP/1.0\r\nCSeq: 2\r\nRange: npt=0.000-"

conn.send(setupmsg+"\r\n", 0)
res, = conn.recvfrom 1500
sess = res.split("\r\n")[-1]
playmsg += sess+"\r\n"

conn.send(playmsg+"\r\n", 0)
res, = conn.recvfrom 1500

rtp = 0
rtpl = 0
k=1
q=1
sl=0
sll=0
start = Time.now

while(true) do
  d = Time.now-start
  if ((d*10).round%3)==0
    if k==0
      puts "RTP #{rtp/d} #{rtpl/d}"
      k=1
    end 
  else
    k=0
  end
  if (d.round%20==0)
    if q==0
      st = 1.0 # 0.5+d.round/100.0
      puts "Sleep #{st}!"
      sleep st
      q=1
      sl=1
    end
  else
    q=0
  end
  res, = conn.recvfrom 4
  if res.length==4 && res[0]=="$"
    len = (res[2].ord<<8)+(res[3].ord)
    block = ""
    while block.length < len
      p, = conn.recvfrom len-block.length
      block += p
    end
    if res[1]=="\x00"
      rtp += 1
      rtpl += len
      if sl==1
        sll += res.length+len
      end
      #puts "RTP #{len} #{block.length} #{len==block.length}"
    elsif res[1]=="\x01"
      puts "RTCP #{len} #{block.length} #{len==block.length}"
    else
      raise "Garbage 1"
    end
  else
    raise "Garbage 2 #{sll}"
  end
end

conn.close()
