match-archive-tools
===================

Some python scripts to make archiving FRC webcasts easier

Getting Started
---------------

Clone this repository, download the proper dependencies (python, ffmpeg), and create a Google API project to use, and you should be good to go! For more detailed instructions, see [this page in the wiki](https://github.com/plnyyanks/match-archive-tools/wiki/Getting-Started)

Command Documentation
---------------------
Because command line arguments are fun!

### playlist_split.py
Since different playlists have different naming schemes for their uploads, you will have to parse out the match type and number from the video title (this is done in the method process_titles). You have to assign the variables matchType and matchNum to the proper values, where matchType is of the list {q,qf1,qf2,qf3,qf4,sf1,sf2,f1} and matchNum is the match number in that set.
* --playlist <YouTube Playlist ID>
    * This is the string of text in the playlist's URL after list=. For example, the ID for [this playlist](http://www.youtube.com/playlist?list=PLIOXQWvJmRQbcqD9iqYDA2Ib1ivFLWq7Y) is PLIOXQWvJmRQbcqD9iqYDA2Ib1ivFLWq7Y
    * This is the playlist whose videos the script will iterate through and parse to generate the TBA match key
* --key <TBA Event Key>
    * This is the event key that The Blue Alliance used to index FRC events. On the TBA page for the event, the key is found after /event/ in the URL. For example, the key for [http://www.thebluealliance.com/event/2014ctgro](this event) is 2014ctgro. 
The script will output a CSV file in the same directory as the script that you can open up, and copy/paste the data into the TBA [Archival Spreadsheet](https://docs.google.com/spreadsheet/ccc?key=0ApRO2Yzh2z01dExFZEdieV9WdTJsZ25HSWI3VUxsWGc#gid=1)
    
### match_split.py
* -f, --file <path/to/video/file>
    * Path to the video file to be processed and split up
* -t, --tiles <path/to/csv/file>
    * Path to a CSV file that contains the following columns: [tba_matchKey](http://www.thebluealliance.com/record) (see "After the Event Section"), Start time of match in video (HH:mm:ss)
    * The file must contain one row per match you want split out
* -p, --playlist <YouTube Playlist ID>
    * This is the string of text in the playlist's URL after list=. For example, the ID for [this playlist](http://www.youtube.com/playlist?list=PLIOXQWvJmRQbcqD9iqYDA2Ib1ivFLWq7Y) is PLIOXQWvJmRQbcqD9iqYDA2Ib1ivFLWq7Y
    * This is the playlist that uploaded videos will be added to
    * You will have to create the playlist manually and copy down the ID

The script will output a CSV file in the same directory as the script that you can open up, and copy/paste the data into the TBA [Archival Spreadsheet](https://docs.google.com/spreadsheet/ccc?key=0ApRO2Yzh2z01dExFZEdieV9WdTJsZ25HSWI3VUxsWGc#gid=1)

Obtaining Video
---------------
The match_split script assumes that its video input is one big chunck of video consisting of multiple matches over lots of time. You can record the video yourself, or record webcasts you're watching using [livestreamer](http://livestreamer.readthedocs.org/en/latest/). Remember to use the -o option to write the video to a file.
