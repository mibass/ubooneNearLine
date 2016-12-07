#!/bin/env python
import sqlite3, os, glob, ROOT, tempfile, json, datetime, time, samweb_client, sys, ifdh
from subprocess import call


dbname="lifetime.sqlite"
conn=None
#outdir="/pnfs/uboone/scratch/users/mibass/lifetime/"
outdir="/pnfs/uboone/scratch/users/uboonepro/NearLine/"

#groupDic={1:20, 2:50, 3:100} #mapping of group id's to number of tracks to require
groupDic={2:50, 3:100, 4:300}

def AddUsedFileToDB(fid,groupid,ltid):
  c = conn.cursor()
  c.execute("INSERT INTO usedFiles (groupid,fid,ltid) VALUES (%d,%d,%d)" %(groupid, fid,ltid))

def markAsUsed(groupid,fids,ltid):
  for fid in fids:
    AddUsedFileToDB(fid,groupid,ltid)

def getTimeStamps(fname):
  #pull json from adjacent fname+".json" file
  jfname=fname+".json"
  with open(jfname) as data_file:    
    data = json.load(data_file)

  dstart = datetime.datetime.strptime(data['start_time'], "%Y-%m-%dT%H:%M:%S")
  dend = datetime.datetime.strptime(data['end_time'], "%Y-%m-%dT%H:%M:%S")
  run = data['runs'][0][0]
  
  print data
  print dstart, dend, run
  print (time.mktime(dstart.timetuple()),time.mktime(dend.timetuple()))
  return dstart, dend, run

def getTimeStampFromSAM(fname):
  #pull json from adjacent fname+".json" file
  jfname=fname+".json"
  with open(jfname) as data_file:    
    data = json.load(data_file)   

  #print data
  parentfname=data['parents'][0]['file_name']
  print "Found parent filename:", parentfname
  print "Querying SAM metadata..."
  samweb = samweb_client.SAMWebClient(experiment='uboone')
  mdata=samweb.getMetadata(parentfname)
  print "Found parent start,end:", mdata['start_time'],",", mdata['end_time']
  dstart = datetime.datetime.strptime(mdata['start_time'], "%Y-%m-%dT%H:%M:%S+00:00")
  dend = datetime.datetime.strptime(mdata['end_time'], "%Y-%m-%dT%H:%M:%S+00:00")
  run = data['runs'][0][0]
  start=time.mktime(dstart.timetuple())
  end=time.mktime(dend.timetuple())
  return start, end, run
  
def getTimeStampFromTree(fname):
  f=ROOT.TFile(fname)
  print "opening file", fname
  tree=f.Get("Lifetime/Event")
  mint=1e12
  maxt=0
  run=0
  for t in tree:
    if t.evttime<mint and t.ntracks_selec>0: mint=t.evttime
    if t.evttime>maxt and t.ntracks_selec>0: maxt=t.evttime
    run=t.run
    #print t.evttime, mint, maxt, t.ntracks_selec
  return mint, maxt, run

def getEnoughFiles(groupid, ntracks):

  c = conn.cursor()
  c.execute("SELECT fid,fname,tracks from files where fid not in (SELECT fid from usedFiles where groupid=%d) order by srun,sevent;"%(groupid))
  ct=0
  rows=c.fetchall()
  ftups=[]
  print "Found %d unused files." % len(rows)
  
  for row in rows:
    #print row
    if row[2]==0: continue
    ct+=row[2]
    ftups.append((row[0],row[1]))
    if ct>=ntracks: break
  
  return ftups, ct


def getTimeStamps(fname):
	#try to get timestamp from events tree, otherwise use SAM
  start=end=run=0
  try:
    print "Getting time stamps, run number from Lifetime/Event tree..." 
    start,end,run=getTimeStampFromTree(fname)
    print "Found start=%d, end=%d, run=%d"% (start, end, run)
  except Exception,e:
    print "Getting time stamp from tree failed, using SAM.\n Error was:\n", e
    start,end,run=getTimeStampFromSAM(fname)
    
  return start, end, run 

def mergeFiles(fnames, tracks):
  tifdh=ifdh.ifdh()
  temp = tempfile.NamedTemporaryFile()
  localfnames=[]
  #merge all the filenames in ftup
  for f in fnames:
    #print f
    localf=tifdh.fetchInput(str(f))
    print "Got local location: %s" % localf
    temp.write(localf+"\n")
    localfnames.append(localf)
  temp.flush()

  print "Wrote %d filenames to %s" % (len(localfnames),temp.name)
  start1,end1, run1=getTimeStamps(localfnames[0])
  print "First file is: ", localfnames[0], start1
  start2,end2, run1=getTimeStamps(localfnames[-1])
  print "Last file is: ", localfnames[-1], end2
  print "Executing hadd..."

  thisoutdir="%s/%dtracks" % (outdir,tracks)
  if not os.path.exists(thisoutdir):
    os.mkdir(thisoutdir,0755)
      
  thisoutdir="%s/%dtracks/%d/" % (outdir,tracks,run1)
  if not os.path.exists(thisoutdir):
    os.mkdir(thisoutdir,0755)
  
  basename="MergedLifeTimeHists_%d_to_%d.root" %(int(start1),int(end2))
  outfilename=thisoutdir+basename #the ultimate file location
  tout=tempfile.mkdtemp()+"/"+basename #temporary target output root file 
  
  cmd="hadd" 
  args=" -f -k %s @%s" %(tout, temp.name)
  print "Executing: ", cmd+args
  call(cmd+args, shell=True)
  #call("wc %s"%(temp.name), shell=True)
  temp.close
  
  print "Copying %s to %s..." % (tout, outfilename)
  if os.path.isfile(outfilename):
    tifdh.rm(outfilename)
  tifdh.cp((tout,outfilename))
  #tifdh.cleanup()
  return outfilename, int(start1),int(end2), tout


def GetFieldTotal(field, intfile, total=True):
  tree=intfile.Get("Lifetime/Event")
  t=ROOT.TH1F("t","",1000,0,0)
  #exit()
  tree.Draw("%s>>t"%field,"","goff")
  if total:
    return t.GetEntries()*t.GetMean(),None #this should return the total
  else:
    return t.GetMean(),t.GetRMS() #return average

def analyzeFile(fname, disableOne=False):
  #execute the analyze lifetime script with root
  cmd="root"
  args= " -b -q 'Lifetime.C++(\"%s\")'" % (fname)
  ret=call(cmd+args, shell=True)
  print "Returned from lifetime measurement with return code:",ret
  
  #check for bat return code, exit (without commit) if non-zero
  if ret!=0:
      print "Return code !=0, aborting!"
      exit()
      
  with open(fname+".json") as data_file:
    fstr=data_file.read()
    data_file.seek(0,0)
    if any(x in fstr for x in ('inf','nan')):
      print "Invalid measurement found... skipping."
      return None
    else:
      data = json.load(data_file) 
  
  if not disableOne:
    print "Getting measurements from merged file..."
    tf=ROOT.TFile(fname)
    print "iszombie=",tf.IsZombie()
    print "isrecovered=",tf.TestBit(ROOT.TFile.kRecovered)
    data['sumntracks']=GetFieldTotal("ntracks",tf)[0]
    data['sumntrackscross']=GetFieldTotal("ntracks_cross",tf)[0]
    data['sumntrackssel']=GetFieldTotal("ntracks_selec",tf)[0]
    data['avgtrklen'], data['rmstrklen']=GetFieldTotal("trklen", tf, False)
  else:
    print "Skipping Lifetime/Event tree measurements..."
    data['sumntracks']=data['sumntrackscross']=data['sumntrackssel']=data['avgtrklen']=data['rmstrklen']=-1
  
  return data

def storeData(fname,start,end,ltdata, groupid):
  c = conn.cursor()
  if ltdata is not None:
    c.execute("INSERT INTO ltdata (ltid, groupid, fname, start, end, QA, QA_err, QC, QC_err, QCQA, QCQA_er, sumntracks, sumntrackscross, sumntrackssel, avgtrklen, rmstrklen) VALUES (NULL, %d,'%s',%d, %d, %f, %f, %f, %f, %f, %f, %d, %d, %d, %f, %f)"\
            %(groupid, fname, start, end, ltdata['QA'], ltdata['QA_err'], ltdata['QC'], ltdata['QC_err'], ltdata['QAQC'],ltdata['QAQC_err'], ltdata['sumntracks'], ltdata['sumntrackscross'], ltdata['sumntrackssel'], ltdata['avgtrklen'], ltdata['rmstrklen'] ))
  else:
    c.execute("INSERT INTO ltdata (ltid, groupid, fname, start, end) VALUES (NULL, %d, '%s', %d, %d)"\
            %(groupid, fname, start, end))
  return c.lastrowid
   

def openDB():
  global conn
  conn=sqlite3.connect(dbname)
  if not conn: 
    print "Error creating/opening database!"
    exit(1) 

def main():
  disableOne=(True if sys.argv[1]=="1" else False) # disable measurements for just 1 file to get past bad files
  openDB()
  for groupid,ntracks in groupDic.items():
    while True: #loop until there aren't enough tracks left for this group
      flist,tracks=getEnoughFiles(groupid,ntracks)
      if tracks>=ntracks and tracks>0:
        outfilename,start,end,toutfilename=mergeFiles(tuple(x[1] for x in flist),ntracks) #passing fnames
        ltdata=analyzeFile(toutfilename, disableOne)
        ltid=storeData(outfilename,start,end,ltdata, groupid)
        markAsUsed(groupid,tuple(x[0] for x in flist),ltid) #passing fids
        conn.commit()
        #remove the local temp file
        os.remove(toutfilename)
        if disableOne:
            print "Exiting due to disableOne being enabled."
            exit()
      else:
        break
  

if __name__ == "__main__":
    main()
    
  
