Simple utility script to import txt based playlist to google music based on https://github.com/simon-weber/gmusicapi
Reason - creating playlist using Google Music UI is not convenient

## Install
```
Unzip gmusic_import_txt_playlist.zip
pip install -r requirements.txt
```

## Usage

gmusic_import_txt_playlist [Path to text file containing desired playlist]

## Options

### -h, --help
Display help message

### -v,--verbose
Enable verbose output

### -e,--email
Specify Google e-mail as an argument

### -t,--target-playlist-name
Name of playlsit you want to change/replace

### -f,--format
Fix format for parsing lines in txt file. {Artist}, {Album}, {Song} variables could be used. By default the following formats are checked.
```
{Artist} - {Album}
{Artist} - {Song}
{Album}
{Song}
{Artist}
```

If several formats could apply you will be explicitly asked.

### --matching-style
Possible options:

  1. substring  - line may contain only substring of variable format

  2. exact_match - exact match required

## Details

If several songs match the requested line they will be sorted in order of (artist name, album year, track number).

If playlist with requested name already exists you will be asked to specify what action (overwrite/append/cancel) with it explicitly.
