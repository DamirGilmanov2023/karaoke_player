import struct, re
class midifile:
    def __init__(self):
        # Instance attributes
        self.fileobject=None
        self.closeonreturn=False
        self.error=False
        # Tempo and real time at which it was set
        self.bpm=[[120,0.]] # bpm using actual time signature
        self.microsecondsperquarternote=[[60000000./120,0.]]
        self.num=[[4, 0.]]
        self.den=[[4, 0.]]
        # For karaoke .kar files
        self.karfile=False
        self.kartrack=0
        self.karsyl=list()
        self.kartimes=list()
        self.karlinea=['']*3
        self.karlineb=['']*3
        self.karievent0=[-1]*3
        self.karievent1=[-1]*3
        self.karidx=0
        # Track information
        self.ntracks=0
        self.tracknames=list()
        # Note information
        self.patchesused=list()
        self.notes=list()
        return

    def read_var_length(self):
        read=129
        values=list()
        while read > 0b10000000:
            read=struct.unpack('>B',self.fileobject.read(1))[0]
            values.append(read)
        iread=len(values)
        var=values[iread-1] # Least-significant byte
        for i in range(iread-1):
            var=var+(values[i]-128)*(128**(iread-1-i))

        bytesread=map(ord,struct.pack('B'*iread,*values))

        return [var,iread,bytesread] # Return value and number of bytes read


    def load_file(self,fileobject):
        
        if type(fileobject) == str:
            self.fileobject=open(fileobject,'rb')
            self.closeonreturn=True
        else:
            self.fileobject=fileobject

        headerid=self.fileobject.read(4).decode("utf-8")
        headerlen=struct.unpack('>I',self.fileobject.read(4))[0] # > is for big-endian, i for integer
        fileformat=struct.unpack('>H',self.fileobject.read(2))[0]
        self.ntracks=struct.unpack('>H',self.fileobject.read(2))[0]
        self.tracknames=['']*self.ntracks
        division=struct.unpack('>h',self.fileobject.read(2))[0] # Ticks per quarter note
        if division < 0: # It's a different format SMTPE
            self.error=1
            if self.closeonreturn:
                self.fileobject.close()
            return self.error

        for itrack in range(self.ntracks):
            currentpatch=0
            mastertime=0
            trackid=str(self.fileobject.read(4))
            tracklen=struct.unpack('>I',self.fileobject.read(4))[0]
            # track event
            metatype=0
            iread=0
            while iread < tracklen and metatype != 0x2f:
                [dtime,nbytesread,bytesread]=self.read_var_length()
                iread=iread+nbytesread
                # Midi event
                status=struct.unpack('>B',self.fileobject.read(1))[0]
                iread=iread+1

                # Set timing conversion. Find tempo for previous event at mastertime
                i0=len(self.microsecondsperquarternote)-1
                while (self.microsecondsperquarternote[i0][1]) > mastertime:
                    i0=i0-1
                # Try with that tempo
                tickspermicrosecond=division/self.microsecondsperquarternote[i0][0]
                secondspertick=1./tickspermicrosecond*1e-6
                dtimesec=dtime*secondspertick
                # Check if there has been a tempo change in that interval
                i1=len(self.microsecondsperquarternote)-1
                while (self.microsecondsperquarternote[i1][1]) > mastertime+dtimesec:
                    i1=i1-1
                if i1 != i0: # Tempo has changed. Recompute using MIDI steps
                    tickspermicrosecond=division/self.microsecondsperquarternote[i0][0]
                    secondspertick0=1./tickspermicrosecond*1e-6
                    tickspermicrosecond=division/self.microsecondsperquarternote[i1][0]
                    secondspertick1=1./tickspermicrosecond*1e-6
                    dtimesec=0.
                    for itick in range(dtime):
                        if mastertime+dtimesec <  self.microsecondsperquarternote[i1][1]:
                            dtimesec=dtimesec+secondspertick0
                        else:
                            dtimesec=dtimesec+secondspertick1


                else: # No tempo change. Proceed with value at i0            
                    tickspermicrosecond=division/self.microsecondsperquarternote[i0][0]
                    secondspertick=1./tickspermicrosecond*1e-6
                    dtimesec=dtime*secondspertick

                mastertime=mastertime+dtimesec

                if status == 0xFF: # It's a non-MIDI event, META event
                    metatype=struct.unpack('>B',self.fileobject.read(1))[0]
                    iread=iread+1
                    [l,nb,bytesread]=self.read_var_length()
                    iread=iread+nb
                    data=self.fileobject.read(l)
                    iread=iread+l
                    if metatype == 0x51: # Set tempo
                        tt=struct.unpack('>BBB',data)
                        self.microsecondsperquarternote.append([tt[0]*65536.+tt[1]*256.+tt[2],mastertime])
                        self.bpm.append([60000000. / self.microsecondsperquarternote[-1][0] * (self.den[-1][0] / self.num[-1][0]), mastertime])
                        self.num.append([self.num[-1][0], mastertime])
                        self.den.append([self.den[-1][0], mastertime])
                    if metatype == 0x58: # Time signature
                        d=struct.unpack('>BBBB',data)
                        self.num.append([float(d[0]),mastertime])
                        self.den.append([float(d[1]**2),mastertime])
                        self.microsecondsperquarternote.append([self.microsecondsperquarternote[-1][0], mastertime])
                        self.bpm.append([self.bpm[-1][0], mastertime])
                    if metatype == 0x1:
                        try:
                            data=data.decode('utf-8')
                        except:
                            data=data.decode('latin-1')
                        #print(data)
                        if data == "@KMIDI KARAOKE FILE":
                            self.karfile=True
                            self.kartrack=itrack+1
                        if self.karfile and itrack == self.kartrack:
                            if data[0] != '@':
                                if '\\' in data:
                                    self.karsyl.append('\\')
                                    self.kartimes.append(mastertime)
                                    data=re.sub('\\\\','',data)
                                if '/' in data:
                                    self.karsyl.append('/')
                                    self.kartimes.append(mastertime)
                                    data=re.sub('/','',data)
                                self.karsyl.append(data)
                                self.kartimes.append(mastertime)    
                    if metatype == 0x3: # Track name
                        self.tracknames[itrack]=data
                    if metatype == 0x2F: # End of track
                        pass 

                elif status == 0xF0 or status == 0xF7: # Now a Sysex event
                    [l,nb,bytesread]=self.read_var_length()
                    iread=iread+nb
                    data=self.fileobject.read(l)
                    iread=iread+l

                else: # MIDI messages
                    if status < 128: # Use running status instead
                        status=runningstatus
                        self.fileobject.seek(-1,1)
                        iread=iread-1
                    status1 = status / 16
                    status2 = status % 16
                    channel=status2
                    if status1 == 0b1100: # Program change
                        read=struct.unpack('>B',self.fileobject.read(1))[0]
                        currentpatch=read
                        self.patchesused.append([itrack,currentpatch,mastertime])
                        iread=iread+1
                    elif status1 == 0b1101: # After-touch
                        read=struct.unpack('>B',self.fileobject.read(1))[0]
                        iread=iread+1
                    else:
                        data1=struct.unpack('>B',self.fileobject.read(1))[0]
                        data2=struct.unpack('>B',self.fileobject.read(1))[0]
                        iread=iread+2
                    if status1 == 0b1001 and data2 > 0: # Note on event
                        self.notes.append([data1,data2,status2,currentpatch,itrack,mastertime,-1])
                        inote=len(self.notes)-1 # If it was previously on, count it off
                        while inote >= 0:
                            if self.notes[inote][0] == data1 and self.notes[inote][2] == currentpatch:
                                self.notes[inote][5] == mastertime # Time note off
                                break
                            inote=inote-1
                    elif status1 == 0b1000 or (status1 == 0b1001 and data2 == 0): # Note off event
                        inote=len(self.notes)-1
                        while inote >= 0:
                            if self.notes[inote][0] == data1 and self.notes[inote][2] == currentpatch:
                                self.notes[inote][5] == mastertime # Time note off
                                break
                            inote=inote-1
                    runningstatus=status
                # End MIDI event


        if self.closeonreturn:
            self.fileobject.close()
        return self.error
    
    def update_karaoke(self, dt):
        if not self.karfile or self.kartrack == 0 or len(self.karsyl) == 0:
            return
        if self.karidx >= len(self.karsyl)-1:
            return
        dt0=self.kartimes[self.karidx]
        while dt > dt0 and self.karidx < len(self.kartimes)-1:
            self.karidx=self.karidx+1
            dt0=self.kartimes[self.karidx]
        self.karidx=max(self.karidx-1,0)
        if self.karidx == self.karievent1[2]: # If reached the end of 3 lines,
            self.karidx=self.karidx+1 # Make sure next 3 lines are displayed
        self.karidx=min(self.karidx,len(self.kartimes)-1)
        if self.karidx > self.karievent1[2]: # Clear and load next three lines
            self.karlinea=['']*3
            self.karlineb=['']*3
            self.karievent0=[len(self.karsyl)-1]*3
            self.karievent1=[len(self.karsyl)-1]*3
            self.karievent0[0]=self.karidx            
            idx=self.karidx+1
            iline=0
            while idx <= len(self.karsyl)-1:
                if self.karsyl[idx]== '/': # Next line
                    self.karievent1[iline]=idx-1
                    iline=iline+1
                    if iline == 3:
                        break
                    self.karievent0[iline]=idx+1
                if self.karsyl[idx] == '\\': # End of three lines
                    self.karievent1[iline]=idx-1
                    if iline < 2:
                        for i in range(iline+1,3):
                            self.karievent0[i]=idx-1
                            self.karievent1[i]=idx-1
                    break
                idx=idx+1

        for iline in range(3): # Colored text
            if self.karievent0[iline] == self.karievent1[iline]:
                self.karlinea[iline]=''
                continue
            i0=self.karievent0[iline]
            i1=self.karidx
            if i1 < self.karievent0[iline]:
                self.karlinea[iline]=''
                continue
            if i1 > self.karievent1[iline]:
                i1=self.karievent1[iline]
            self.karlinea[iline]=''.join(self.karsyl[i0:i1+1])
            self.karlinea[iline]=re.sub('\\\\','',self.karlinea[iline])
            self.karlinea[iline]=re.sub('/','',self.karlinea[iline])
        for iline in range(3): # White text
            if self.karievent0[iline] == self.karievent1[iline]:
                self.karlineb[iline]=''
                continue
            i0=self.karidx+1
            if i0 < self.karievent0[iline]:
                i0=self.karievent0[iline]
            i1=self.karievent1[iline]
            if i0 > i1:
                self.karlineb[iline]=''
                continue
            if self.karievent1[iline] < i0:
                i0=self.karidx
            self.karlineb[iline]=''.join(self.karsyl[i0:i1+1])
            self.karlineb[iline]=re.sub('\\\\','',self.karlineb[iline])
            self.karlineb[iline]=re.sub('/','',self.karlineb[iline])

        # Special case for song end
        if dt >= max(self.kartimes):
            for iline in range(-2,1):
                if self.karlinea[iline] != '':
                    self.karlinea[iline]=''.join(self.karsyl[self.karievent0[iline]:])
                    self.karlinea[iline]=re.sub('\\\\','',self.karlinea[iline])
                    self.karlinea[iline]=re.sub('/','',self.karlinea[iline])
                    self.karlineb[iline]=''
                    break

        return False
