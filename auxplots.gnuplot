#!/nashome/m/mibass/bin/bin/gnuplot

set terminal pdf enhanced dashed
#set term svg enhanced mouse size 600,400

set xdata time
set timefmt "%s"
set format x "%m/%d/%Y \n%H:%M:%S"
set datafile separator "|"
set xtics rotate by -45
set rmargin 6
points="50"

set xlabel "Time" font ",17"
gid="2"

#set yrange [0:1.5]

avgtimestr="(start+end)/2 -3600*5"
startstr="start-3600*5"
endstr="end-3600*5"

TIMEOFFSET=946684800
#set xrange [(system("date -d 'now' +%s")-3600*72-TIMEOFFSET):(system("date -d 'now' +%s")-TIMEOFFSET+3600*5)]


gettime(d)=system(sprintf(" date -u -d @%d +%I:%m ",d))
qaqcerr(qa,qae,qc,qce,qaqc)=qaqc*sqrt((qae/qa)**2 + (qce/qc)**2)
#qaqcerr(qa,qae,qc,qce,qaqc)=sqrt((qae)**2 + (qce)**2)

QAQCMINOR=0.82
QAQCMAJOR=0.48

set output 'ntracks.pdf'
set ylabel "#Tracks Ratio" font ",17"
plot '< sqlite3 lifetime.sqlite "SELECT '.avgtimestr.','.startstr.','.endstr.', sumntracks, sumntrackscross, sumntrackssel from ltdata where groupid='.gid.' order by start desc limit '.points.';"' \
  using 1:($4/$5):2:3 with xerrorbars pt 7 ps 0.2 lw 3 ti "#Tracks/#CrossingTrack",\
  '' using 1:($4/$6):2:3 with xerrorbars pt 7 ps 0.2 lw 3 lc "red" ti "#Tracks/#SelCrossingTrack" 


set output 'tracklengths.pdf'
set ylabel "Mean Track Length [cm]" font ",17"
plot '< sqlite3 lifetime.sqlite "SELECT '.avgtimestr.','.startstr.','.endstr.', avgtrklen, IFNULL(rmstrklen,0) from ltdata where groupid='.gid.' order by start desc limit '.points.';"' \
  using 1:4:2:3:($4+$5):($4-$5) with xyerrorbars pt 7 ps 0.2 lw 3 noti
