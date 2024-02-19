import struct
import urllib.parse

def urldecode(str_):
    return urllib.parse.unquote(str_)

def reader(name_file):
	f=open(name_file,'rb')
	file=f.read()
	if file[0:4]!="KFNB".encode("utf-8"):
		return None
	head=[]
	i=4
	while True:
		sl={}
		sl["h"]=struct.unpack(">4s",file[i:i+4])
		sl["h"]=sl["h"][0].decode("utf-8")
		i+=4
		sl["f"]=file[i]
		i+=1
		sl["v"]=struct.unpack("<1i",file[i:i+4])
		sl["v"]=sl["v"][0]
		i+=4
		if sl["f"]==2:
			sl["str"]=struct.unpack(f">{sl['v']}s",file[i:i+sl["v"]])
			sl["str"]=sl["str"][0].decode("utf-8")
			i+=sl["v"]
		head.append(sl)
		if sl["h"]=="ENDH":
			break


	len_files=struct.unpack("<1i",file[i:i+4])
	len_files=len_files[0]
	i+=4


	header=[]
	for n in range(len_files):
		sl={}
		sl["len_name"]=struct.unpack("<1i",file[i:i+4])
		sl["len_name"]=sl["len_name"][0]
		i+=4
		m=str(sl["len_name"])
		sl["name"]=struct.unpack(f">{m}s",file[i:i+sl["len_name"]])
		sl["name"]=sl["name"][0]#.decode("utf-8")
		i+=sl["len_name"]
		sl["type"]=file[i]
		i+=4
		sl["length1"]=struct.unpack("<1i",file[i:i+4])
		sl["length1"]=sl["length1"][0]
		i+=4
		sl["offset"]=struct.unpack("<1i",file[i:i+4])
		sl["offset"]=sl["offset"][0]
		i+=4
		sl["length2"]=struct.unpack("<1i",file[i:i+4])
		sl["length2"]=sl["length2"][0]
		i+=4
		sl["flags"]=struct.unpack("<1i",file[i:i+4])
		sl["flags"]=sl["flags"][0]
		i+=4
		header.append(sl)


	end_header=i

	try:
		for h in head:
			if h["h"]=="SORC":
				razreh=h["str"].split(".")
				break
		muz=f"muz.{razreh[-1]}"
	except:
		muz="muz.mp3"

	song_ini=""
	for h in header:
		if h["type"]==1:
			song_ini=file[h["offset"]+end_header:h["offset"]+h["length1"]+end_header]#.decode("utf-8")

		if h["type"]==2:
			with open(muz, "wb") as f:
				f.write(bytes(file[h["offset"]+end_header:h["offset"]+h["length1"]+end_header]))


	song_ini=urldecode(song_ini)

	song_strings=song_ini.split("\n")


	sync=[]
	text_strings=[]
	for song in song_strings:
		if song[0:4]=="Sync":
			prom=song.split("=")
			prom=prom[1].split(",")
			for elem in prom:
				sync.append(elem)
		if song[0:4]=="Text" and song[0:9]!="TextCount":
			prom=song.split("=")
			prom=prom[1]#.replace("/","")
			if prom!="" and prom!="\r":
				text_strings.append(prom)


	return muz,head,sync,text_strings

