# ubooneNearLine

The uboon NearLine processing monitors the output of POMS nearling processing, tracks any new files that are found, and 

File descriptions:

Tracker.py:
  Looks for new files in the appropriate folder. Counts the number of crossing tracks in each new file found and inserts them into a table in the lifetime.sqlite database.
  
Analyzer.py:
  Groups together multiple files until enough tracks are found (50, 100, or 300), merges the files, and runs the Lifetime.C anaysis module on the result. The output of the analysis is stored in the lifetime database (purity, uncertainty, number of tracks, etc.). The files that are used for each grouping (50,100,300 tracks) are marked as used in a used files table in the database.
  
lifetime.gnuplot:
  Generates plots based on entries in the lifetime database.
  
ECLAPI.py, ecl_post.py:
  Posts the output plots to the ECL.
  
runs.sh:
  The script that gets run by the cronjob that calls the scripts in the appropriate sequence.
