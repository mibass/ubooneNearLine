#!/bin/env python
import sqlite3, os, glob, ROOT, fnmatch



dbname="lifetime.sqlite"
searchPath="/pnfs/uboone/persistent/uboonepro/electron_lifetime_test/v05_08_00_04/"
fileSearchString="SwizRecoLifetime_hist_*.root"
conn=None

def createdb():
  if os.path.isfile(dbname):
    print "DB exists! Delete it first if you want to recreate it."
    exit(1)
  conn=sqlite3.connect(dbname)
  
  if not conn: 
    print "Error creating/opening database!"
    exit(1)
  c = conn.cursor()
  
  c.execute("CREATE TABLE files(fid INTEGER PRIMARY KEY,fname TEXT, tracks INT, srun INT, ssubrun INT, sevent INT)")
  c.execute("CREATE TABLE usedFiles(groupid INT, fid INT, ltid INT)")
  c.execute("CREATE TABLE ltdata(ltid INTEGER PRIMARY KEY, groupid INT, fname TEXT, start INT, end INT, QA REAL, QA_err REAL, QC REAL, QC_err REAL, QCQA REAL, QCQA_er REAL, sumntracks INT, sumntrackscross INT, sumntrackssel INT, avgtrklen REAL, rmstrklen REAL)")
  conn.commit()
  conn.close()
  
def fileInDB(fname):
  c = conn.cursor()
  c.execute('SELECT COUNT(*) from files where fname="%s";'%(fname))
  return False if c.fetchall()[0][0]==0 else True

def deleteMeasurement(ltid,fname):
  #delete measurement files
  for f in glob.glob(fname+"*"): #to get the json
    os.remove(f)
  #delete relevant database entries
  c=conn.cursor()
  c.execute("delete from ltdata where ltid=%d;"%(ltid))
  c.execute("delete from usedFiles where ltid=%d;"%(ltid))


def AddFileToDB(fname,tracks,srun,ssubrun,sevent):
  c = conn.cursor()
  #before adding a new file, check to see if there are already subsequent runs in lt measurements, if so, delete the measurements to regroup/reanalyze
  c.execute("SELECT DISTINCT ltdata.ltid, ltdata.fname FROM ltdata INNER JOIN usedFiles ON ltdata.ltid=usedFiles.ltid INNER JOIN files ON usedFiles.fid = files.fid WHERE files.srun=%d AND files.ssubrun>=%d" \
            % (srun,ssubrun))
  rows=c.fetchall()
  for row in rows:
      deleteMeasurement(row[0],row[1])
  
  #now add the new file
  c.execute("INSERT INTO files (fid,fname, tracks, srun, ssubrun, sevent) VALUES (NULL,'%s',%d,%d,%d,%d)" %(fname, tracks, srun, ssubrun, sevent))

def getStats(fname):
  #open root file, count number of select tracks in Lifetime/Events
  try:
    f=ROOT.TFile(fname)
    tree=f.Get("Lifetime/Event")
    t=ROOT.TH1F("t","",1000,0,0)
    tree.Draw("ntracks_selec>>t","ntracks_selec>0","goff")
    tracks=int(t.GetEntries()*t.GetMean()) #this should return the total number of tracks, even with multiple per event
    startrun=int(tree.GetMinimum("run"))
    startsubrun=int(tree.GetMinimum("subrun"))
    startevent=int(tree.GetMinimum("event"))
    f.Close()
    return  {'tracks': tracks, 'startnum': startrun, 'startsubrun': startsubrun, 'startevent': startevent}
  except Exception as e:
    print "Exception while getting stats for file:",fname
    print "Exception was ",e
    print "Skipping file and marking as empty!"
    return  {'tracks': 0, 'startnum': -1, 'startsubrun': -1, 'startevent': -1}

def getNewFiles():
  skipcount=0
  #for filename in sorted(glob.iglob(searchPath+'/**/'+fileSearchString,recursive=True), key=os.path.getmtime):
  for root, dirnames, filenames in os.walk(searchPath):
    for filename in fnmatch.filter(filenames, fileSearchString):
      filepath=os.path.join(root, filename)
      print(filepath)
      if not fileInDB(filepath):
        stats=getStats(filepath)
        AddFileToDB(filepath, stats['tracks'], stats['startnum'], stats['startsubrun'], stats['startevent'])
      else:
        print "\t skipped...|"
        skipcount+=1
        if skipcount>200: 
          print "Skipped 200 files... not checking anymore (assumes newest directories returned first!)."
          return

def openDB():
  global conn
  conn=sqlite3.connect(dbname)
  if not conn: 
    print "Error creating/opening database!"
    exit(1) 

def main():
  if not os.path.isfile(dbname): createdb()
  openDB()
  getNewFiles()
  conn.commit()
  
  

if __name__ == "__main__":
    main()
    
  
