#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Class and methods to convert video for the fuze
"""
import os, tempfile, shutil, sys, commands, unicodedata
from subprocess import check_call, call
from PyQt4.QtCore import QT_TR_NOOP,SIGNAL,QObject,QString,QVariant
from vthumb import *

class Fuze( ):
    def __init__(self, GUI = None):
        self.GUI = GUI
        self.CWD = os.getcwd()
####################################################################
        self.mencoderpass1 = "mencoder -ffourcc DX50 -ofps 20 -vf pp=li,expand=:::::224/176,scale=224:176,harddup     -ovc lavc -lavcopts vcodec=mpeg4:vbitrate=683:vmax_b_frames=0:keyint=15:turbo:vpass=1 -srate 44100 -af resample=44100:0:1,format=s16le -oac mp3lame -lameopts cbr:br=128"

        self.mencoderpass2 = "mencoder -ffourcc DX50 -ofps 20 -vf pp=li,expand=:::::224/176,scale=224:176,harddup     -ovc lavc -lavcopts vcodec=mpeg4:vbitrate=683:vmax_b_frames=0:keyint=15:vpass=2 -srate 44100 -af resample=44100:0:1,format=s16le -oac mp3lame -lameopts cbr:br=128"
####################################################################
        if self.GUI != None:
            self.qobject = QObject()
            self.qobject.connect(self.qobject, SIGNAL("stop"),GUI.WAIT)
            self.qobject.connect(self.qobject, SIGNAL("working"),GUI.Status)
            self.qobject.connect(self.qobject, SIGNAL("Exception"),GUI.ErrorDiag)
            self.qobject.connect(self.qobject, SIGNAL("itemDone"),GUI.DelItem)
            self.qobject.connect(self.qobject, SIGNAL("finished"),GUI.getReady)
            self.LoadSettings()
        self.xterm = None
	self.AMGPrefix = tempfile.gettempdir()
        if os.name == 'nt':
            self.FFMPEG = os.path.join(self.CWD, "ffmpeg.exe")
            self.mencoderpass1 = self.mencoderpass1.replace("mencoder",os.path.join(self.CWD, "mencoder.exe"))
            self.mencoderpass2 = self.mencoderpass2.replace("mencoder",os.path.join(self.CWD, "mencoder.exe"))
        else:
            self.FFMPEG = "ffmpeg"
            if os.name == 'posix' and self.GUI != None:
                termloc = commands.getstatusoutput("which xterm")
                if termloc[0] == 0:
                    self.xterm = termloc[1]
                else:
                    print "xterm not found"
                print self.xterm
            else:
                if self.GUI != None:
                    print "No terminal emulator available"

    def LoadSettings(self):
        self.mencoderpass1 = str(self.GUI.settings.value("mencoderpass1", QVariant(self.mencoderpass1)).toString())
        self.mencoderpass2 = str(self.GUI.settings.value("mencoderpass2", QVariant(self.mencoderpass2)).toString())


    def convert(self,args, FINALPREFIX =  None):
        os.chdir(self.AMGPrefix)
        tempfiles = {}
        if self.GUI != None:
            self.qobject.emit(SIGNAL("stop"),self.GUI.Video)
        for argument in args:
            if os.path.isfile(argument):
                if os.name == 'nt':
                    OUTPUT = os.path.join(self.AMGPrefix,os.path.splitext(os.path.basename(argument))[0] + ".temp.avi")#.encode("ascii", "ignore")
                else:
                    OUTPUT = unicodedata.normalize('NFKD',os.path.join(self.AMGPrefix,os.path.splitext(os.path.basename(argument))[0] + ".temp.avi")).encode("ascii", "ignore")
                try:
                    print "Calling mencoder #1"
                    mencoderpass1 = str(self.mencoderpass1)
                    if self.GUI != None:
                        self.qobject.emit(SIGNAL("working"),"Using mencoder on " + argument + "...")
                        if self.xterm != None:
                            mencoderpass1 = self.xterm + " -e " + mencoderpass1
                    mencoderpass1 = mencoderpass1.split()
                    mencoderpass1.append(argument)
                    mencoderpass1.append("-o")
                    mencoderpass1.append(OUTPUT)
                    check_call(mencoderpass1)
                except Exception, e:
                    print e
                    if self.GUI != None:
                        self.qobject.emit(SIGNAL("Exception"),e)
                    continue
                try:
                    print "Calling mencoder #2"
                    mencoderpass2 = str(self.mencoderpass2)
                    if self.GUI != None:
                        self.qobject.emit(SIGNAL("working"),"Using mencoder on " + argument + " (pass 2)...")
                        if self.xterm != None:
                            mencoderpass2 = self.xterm + " -e " + mencoderpass2
                    mencoderpass2 = mencoderpass2.split()
                    mencoderpass2.append(argument)
                    mencoderpass2.append("-o")
                    mencoderpass2.append(OUTPUT)
                    check_call(mencoderpass2)
                    tempfiles[OUTPUT] = argument
                except Exception, e:
                    print e
                    if self.GUI != None:
                        self.qobject.emit(SIGNAL("Exception"),e)
                    continue
            else:
                print "\'" + argument + "\'" + ": file not found"

        print "temporary files are: "
        print tempfiles
    
        for file in tempfiles.keys():
            if FINALPREFIX == None:
                FINAL = os.path.splitext(tempfiles[file])[0] + "_fuze.avi"
            else:
                FINAL = os.path.join(FINALPREFIX,os.path.splitext(os.path.basename(tempfiles[file]))[0]) + "_fuze.avi"
            try:
                    fuzemux = "fuzemux"
                    if self.GUI != None:
                        self.qobject.emit(SIGNAL("working"),"Using command:" + fuzemux)
                        if self.xterm != None:
                            fuzemux = self.xterm + " -e " + fuzemux
	            fuzemux=fuzemux.split() 
                    fuzemux.append(file)
                    fuzemux.append(os.path.join(self.AMGPrefix,"final.avi"))
                    print "Calling fuzemux"
                    check_call(fuzemux)
            except Exception, e:
                print e
                if self.GUI != None:
                    self.qobject.emit(SIGNAL("Exception"),e)
                os.remove(os.path.join(self.AMGPrefix,"final.avi"))
                continue
            print "Moving " + os.path.join(self.AMGPrefix,"final.avi") + " to " + FINAL + " and cleaning temporary files"
            print FINAL
            try:
                try:
                    if self.GUI != None:
                        self.qobject.emit(SIGNAL("working"),"Creating video thumbnail")
                    print "Creating video thumbnail"
                    os.chdir(os.path.split(FINAL)[0])
                    find_thumb(os.path.join(self.AMGPrefix,"final.avi"), os.path.splitext(os.path.basename(FINAL))[0], 100, [], True, False, self.FFMPEG)
                except Exception, e:
                    print e
                    raise e
                    if self.GUI != None:
                        self.qobject.emit(SIGNAL("Exception"),e)
                shutil.move(os.path.join(self.AMGPrefix,"final.avi"),FINAL)
                os.chdir(self.CWD)
                os.chdir(self.CWD)
                if self.GUI != None:
                    self.qobject.emit(SIGNAL("itemDone"),tempfiles[file])
                os.remove(file)
            except Exception, e:
                print e
                print  "Ooops not moving final video"
                if self.GUI != None:
                    self.qobject.emit(SIGNAL("Exception"),e)
        if self.GUI != None:
            self.qobject.emit(SIGNAL("finished"),self.GUI.Video)

if __name__ == "__main__":
    if sys.argv[1:] == [] :
        print """Usage:
        python fuze.py INPUTVIDEO1 INPUTVIDEO2 ..."""
        exit(1)
    Fuze().convert(sys.argv[1:])

