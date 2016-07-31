Simple utility script to import txt based playlist to google music based on https://github.com/simon-weber/gmusicapi

Usage:
pip install -r requirements.txt (once)
gmusic_import_txt_playlist [path-to-text-file]

Possible options:

-h,--help - help

-v,--verbose - verbose output

-t,--target-playlist-name - target playlist name on google music

-f,--format - format for parsing lines in txt file. {Artist}, {Album}, {Song} variables could be used. By default several common formats are tried.

--matching-style - substring or exact_match. in substring mode script is satisfied if you input only substring of {Artist}, {Album}, etc. In exact_match exact match is required.
