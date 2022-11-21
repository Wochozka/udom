#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Version 0.0.1-alpha

udom - Uninstallview DOkuwiki Migrate - transform text files exported from UninstallView (Win, native encoding utf-16) to dokuwiki file structure and syntax.

"""

import sys
import argparse
import os
import semantic_version
import datetime

version = semantic_version.Version('0.0.1-alpha')

global args
global epilog
epilog = "Example:\n\n\t$ python3 udom.py -d [path_to_dir] \n\nCopyright (c) 2022, Wochozka, info@wochozka.cz"

def dokuFileName(fname):
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_-."
    diac = {"ě":"e", "š":"s", "č":"c", "ř":"r", "ž":"z", "ý":"y", "á":"a",
            "í":"i", "é":"e", "ú":"u", "ů":"u", "ť":"t", "ň":"n", "ô":"o",
            "ĺ":"l", "ľ":"l", "ŕ":"r", "ď":"d", "ć":"c"}
    fname = fname.lower()
    undName = ""
    for char in fname:
        if char in diac:
            char = diac[char]
            undName = undName + char
        else:
            undName = undName + char
    dokuname = ""            
    for char in undName:
        if char in allowed:
            dokuname = dokuname + char
        else:
            if dokuname[-1] != "_":
                dokuname = dokuname + "_"
    while dokuname.endswith("_"):
        dokuname = dokuname[:-1]
    return dokuname

def readSingleComp(source_file):
    """
    This method open file defined in argument as [source_file]

    Returns:
        type: list
        content: dictionaries
    """
    if (args.verbose > 0):
        print("[Reading source file]")
    lines = []
    computer = {}
    software = []
    try:
        with open(source_file, "r", encoding="utf-16") as sf:
            for line in sf:
                line = line.replace("\n","")
                lines.append(line)   
    except:
        print("Error with open file in encoding utf-16")
    
    #fill objects info dictionaries and field
    readingObject = False
    for line in lines:
        line = line.strip()
        if line != '':
            if "===" in line:
                if readingObject:
                    software.append(computer.copy())
                    readingObject = False
                else:
                    readingObject = True
            else:
                thisLine = line.split(":")
                if readingObject:
                    computer[thisLine[0].strip()] = thisLine[1].strip()
    return software

def extractSWNames(sourceFiles):
    names = []
    for sourceFile in sourceFiles:
        allSWfromAllFiles = readSingleComp(sourceFile)
        for allSWfromOne in allSWfromAllFiles:
            names.append(allSWfromOne["Display Name"])
    names = list(dict.fromkeys(names))
    names.sort()
    return names
            
def generateDokuSitesComputers(dicRoomStructure, sourceDir):
    rooms = list(dicRoomStructure.keys())
    for room in rooms:
        path = f"./inventura/computers/{room}"
        os.mkdir(path)
        comps = dicRoomStructure[room]
        for comp in comps:
            sourceFile = os.path.join(sourceDir,room,comp)
            allSoftware = readSingleComp(sourceFile)
            swNames = []
            for software in allSoftware:
                swNames.append(software["Display Name"])
                fcomp = dokuFileName(comp)
                fileName = os.path.join(path,f"{fcomp}")
                with open(fileName, "w", encoding="utf-8") as cmp:
                    compName = comp[:-4]
                    cmp.write(f"====== {room} : {compName} ======\n\n")
                    for sw in swNames:
                        fname = dokuFileName(sw)
                        cmp.write(f"| [[..:..:software:{fname}|{sw}]] |\n")       

def generateDokuSitesSoftware(swNames, allSoftware):  
    for swName in swNames:
        fname = dokuFileName(swName)
        fname = f"inventura/software/{fname}.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(f"====== {swName} ======\n\n")
            f.write("[[?do=backlink]]\n\n")
            sw = allSoftware[swName]
            keys = sw.keys()
            for key in keys:
                val = sw[key]
                f.write(f"| {key} | {val} |\n")

def generateStarts(dicRoomComps, swNames):
    #generate inventura/start.txt
    with open("inventura/start.txt", "w", encoding="utf-8") as invs:
        now = datetime.datetime.today().strftime('%d. %m. %Y')
        #invs.write("====== Inventarizace PC a SW k {0} ======\n\n".format(now))
        invs.write(f"====== Inventarizace PC a SW k {now} ======\n\n")
        invs.write("[[.computers:|Počítače]]\n\n")
        invs.write("[[.software:|Software]]")
    
    #generate inventura/computers/start.txt
    with open("inventura/computers/start.txt", "w", encoding="utf-8") as cmps:
        cmps.write("====== Počítače ======\n\n")
        for room in dicRoomComps:
            cmps.write(f"===== {room} =====\n\n")
            cmps.write("^ Počítač ^\n")
            for comp in dicRoomComps[room]:
                cmps.write(f"| [[.{room}:{comp[:-4]}|{comp[:-4]}]] |\n")
            cmps.write("\n")
    
    #generate inventura/software/start.txt
    with open("inventura/software/start.txt", "w", encoding="utf-8") as sws:
        sws.write("====== Software ======\n\n")
        for swName in swNames:
            sws.write(f"| [[.{swName}|{swName}]] |\n")
        sws.write("\n")

def readInputData(source):
    dictRoomsComps = {}
    pathsToFiles = []
    allSoftwareMash = []
    allSoftware = {}
    dirs = os.listdir(source)
    for dir in dirs:
        path = os.path.join(source, dir)
        try:
            files = os.listdir(path)
        except:
            pass
        dictRoomsComps[dir] = []
        for file in files:
            dictRoomsComps[dir].append(file)
            pathsToFiles.append(os.path.join(source,dir,file))
    for file in pathsToFiles:
        allSoftwareMash.append(readSingleComp(file))
    for comp in allSoftwareMash:
        for sw in comp:
            swName = sw["Display Name"]
            allSoftware[swName] = sw

    return dictRoomsComps, pathsToFiles, allSoftware
    
def generateDirStructure():
    if(args.merge):
        #check if exist current tree and if is convenient
        if os.path.exists("./inventura") and os.path.exists("./inventura/computers") and os.path.exists("./inventura/software"):
            pass
        else:
            print("Cannot merge current structure. Remove current structure and run again without -m parameter or repair.")
            print(
                "./inventura - ", os.path.exists("./inventura"),
                "\n./inventura/computers - ", os.path.exists("./inventura/computers"), 
                "\n./inventura/software - ", os.path.exists("./inventrua/software")
            )
            sys.exit(1)
    else:
        try:
            os.mkdir("./inventura")
            os.mkdir("./inventura/computers")
            os.mkdir("./inventura/software")
        except:
            print("Can not create a directory structure. Check if does not exist already or permissions.")
            sys.exit(1)

def main():

    if(args.file):
        allSoftware = readSingleComp(args.file)
        swNames = []
        for software in allSoftware:
            swNames.append(software["Display Name"])
            fcomp = dokuFileName(args.file)
            if(args.target):
                fileName = os.path.join(path,f"{fcomp}")
                with open(fileName, "w", encoding="utf-8") as cmp:
                    compName = args.file[:-4]
                    cmp.write(f"====== {room} : {compName} ======\n\n")
                    for sw in swNames:
                        fname = dokuFileName(sw)
                        cmp.write(f"| [[..:..:software:{fname}|{sw}]] |\n")
            else:
                compName = str(args.file)[:-4]
                print(f"====== {compName} ======\n\n")
                for sw in swNames:
                    fname = dokuFileName(sw)
                    print(f"| [[..:..:software:{fname}|{sw}]] |\n")
                    
    if(args.dir):
        dictRoomsComps, sourceFiles, allSoftware = readInputData(args.dir)
        swNames = extractSWNames(sourceFiles)
        generateDirStructure()
        generateStarts(dictRoomsComps, swNames)
        generateDokuSitesSoftware(swNames, allSoftware)
        generateDokuSitesComputers(dictRoomsComps, args.dir)
        
    sys.exit()

def check_version():
    if sys.version_info < (3,5,0):
        sys.exit("You need python 3.5 or later to run this script.\n")

def init_args():
    p = argparse.ArgumentParser(prog="udom", description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter, epilog=epilog)

    fileOrDir = p.add_mutually_exclusive_group(required=True)
    fileOrDir.add_argument("-d", "--dir", help="process all txt files in path")
    fileOrDir.add_argument("-f", "--file", default=True, help="process single txt file to stdout")

    p.add_argument("-m", "--merge", action="store_true", help="merge with current structure (or create new (owerwrite current)")
    p.add_argument("-t", "--target", action="store_true", help="define target file (only with -f)")
    p.add_argument("-V", "--version", action="store_true", help="return version and exit")
    p.add_argument("-v", "--verbose", type=int, choices=[0,1,2], default=0, help="increase output verbosity (default: 0 - quiet)")


    return(p.parse_args())

def process_args():
    if (args.version):
        print(version)
        sys.exit()

if __name__ == "__main__":
    check_version()
    args = init_args()
    process_args()
    main()
