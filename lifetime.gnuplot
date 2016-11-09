#!/nashome/m/mibass/bin/bin/gnuplot

set terminal pdf enhanced dashed
#set term svg enhanced mouse size 600,400

set xdata time
set timefmt "%s"
set format x "%m/%d/%Y \n%H:%M:%S"
set datafile separator "|"
set xtics rotate by -45
set rmargin 6
points="30"

set xlabel "Time" font ",17"
set ylabel "Q_C/Q_A" font ",17"
gid="2"
set output 'QCQA_50tracks.pdf'
set yrange [0:1.5]

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

set label 1 "11 ms" tc "orange" font "arialbold,16" right at graph 0.95, first QAQCMINOR - 0.06
set arrow 1 from graph 0,first QAQCMINOR to graph 1,first QAQCMINOR lt 2 lc "orange" lw 3 nohead
set label 2 "3 ms" tc "red" font "arialbold,16" right at graph 0.95, first QAQCMAJOR - 0.06
set arrow 2 from graph 0,first QAQCMAJOR to graph 1,first QAQCMAJOR lt 2 lc "red" lw 3 nohead
set grid back lt 3  lc "#DDDDDD" lw 0.1

plot '< sqlite3 lifetime.sqlite "SELECT '.avgtimestr.',QCQA,'.startstr.','.endstr.',QCQA-QCQA_er,QCQA+QCQA_er,QC,QC_err,QA,QA_err from ltdata where groupid='.gid.' order by start desc limit '.points.';"' \
  using 1:2:3:4:5:6 with xyerrorbars pt 7 ps 0.2 lw 3 notitle,\
  '< sqlite3 lifetime.sqlite "SELECT '.avgtimestr.',QCQA,start,end,QCQA-QCQA_er,QCQA+QCQA_er from ltdata where groupid='.gid.' order by start desc limit 1;"' \
  u 1:2:(sprintf("   <-%.03f", $2)) w labels rotate offset char 0,2 tc "red" notitle




gid='3'
set output 'QCQA_100tracks.pdf'
replot

gid='4'
set output 'QCQA_300tracks.pdf'
replot


set yrange [190:230]
set ylabel "Q [ADC]" font ",17"
gid="2"
set output 'QCandQA_50tracks.pdf'
plot '< sqlite3 lifetime.sqlite "SELECT '.avgtimestr.',QC,'.startstr.','.endstr.',QC-QC_err,QC+QC_err from ltdata where groupid='.gid.' order by start desc limit '.points.';"' \
using 1:2:3:4:5:6 with xyerrorbars lt 1 pt 7 ps 0.2 lw 3 lc 'red' title 'QC',\
'< sqlite3 lifetime.sqlite "SELECT '.avgtimestr.',QA,'.startstr.','.endstr.',QA-QA_err,QA+QA_err from ltdata where groupid='.gid.' order by start desc limit '.points.';"' \
using 1:2:3:4:5:6 with xyerrorbars lt 1 pt 7 ps 0.2  lw 3 lc 'blue' title 'QA'

gid='3'
set output 'QCandQA_100tracks.pdf'
replot

gid='4'
set output 'QCandQA_300tracks.pdf'
replot
