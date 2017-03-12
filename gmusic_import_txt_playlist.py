import gmusicapi
import getpass
import sys
import os
import argparse
import collections
from parse import *
from enum import Enum

class Action(Enum):
	new = 0
	overwrite = 1
	append = 2

class MatchingStyle(Enum):
	substring = 0
	exact_match = 1

albumInfoCache = dict ()
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-v', '--verbose', action="store_true", dest="verbose", help="Verbose output", default=False)
parser.add_argument('-e', '--email', action="store", dest="email", help="User e-mail (otherwise asked)")
parser.add_argument('-t', '--target_playlist_name', action="store", dest="playlist_name", help="Name of target playlist")
parser.add_argument('--matching_style', action="store", dest="matching_style", help="Matching style for song/album/artist names (possible values: {})".format ([e.name for e in MatchingStyle]), default="substring")
formats = ['{Artist} - {Album}', '{Artist} - {Song}', '{Album}', '{Song}', '{Artist}']
parser.add_argument('-f', '--format', action="store", dest="fixed_format", help="Fix format for playlist items. You may use variables {{Artist}}, {{Album}}, {{Song}}. By default the following formats are checked: {}".format (formats))
parser.add_argument('input_file', action="store", nargs=argparse.REMAINDER, help='text file path containing your playlist')
options = parser.parse_args()
client = gmusicapi.clients.Mobileclient ()
email = options.email
if not email:
	email = input("Google E-mail:")

pass_from_env = ''
if 'GMUSIC_PASSWD' in os.environ:
	pass_from_env = os.environ['GMUSIC_PASSWD']
if pass_from_env:
	passwd = pass_from_env
else:
	passwd = getpass.getpass("Password:")
if not client.login(email, passwd, gmusicapi.clients.Mobileclient.FROM_MAC_ADDRESS):
	sys.exit ("Login Failed.\nIf you use 2 step authentication you may need to generate app specific password on https://security.google.com/settings/security/apppasswords. If you don't want to remember it you may store password in GMUSIC_PASSWD environment variable, but don't forget to close terminal after usage")

playlist_name = options.playlist_name
if not playlist_name:
	playlist_name = input("Target Playlist Name:")

matching_style = MatchingStyle.substring

for e in MatchingStyle:
	if e.name == options.matching_style:
		matching_style = e

def print_verbose (str):
	if options.verbose:
		print (str)

class ErrorExit(Exception):
    pass

def exit_with_error (str):
	print (str)
	raise ErrorExit ()

try: # to logout in any case
	print_verbose ('Authentication successful')

	playlists = client.get_all_playlists ()
	songs = client.get_all_songs ()
	collision_count = 0
	collided_id = None
	further_action = Action.new
	for playlist in playlists:
		if playlist['name'] == playlist_name:
			collision_count += 1
			collided_id = playlist['id']
	if collision_count == 1:
		action = input ('Unique playlist with name "' + playlist_name + '" already exists.\nPlease choose subsequent action - overwrite(o)/append(a)/new(n):')
		if action[0] == 'o':
			further_action = Action.overwrite
		elif action[0] == 'a':
			further_action = Action.append
		elif action[0] == 'n':
			further_action = Action.new
		else:
			exit_with_error ('Incorrect action was selected')
		print ('The following action was selected: ' + further_action.name)
	elif collision_count > 1:
		print ('Warning: several playlists exist with the name "' + playlist_name + '". Continuing with creation of another one.')

	def getSongYear (song):
		song_name = ' - '.join ([song['artist'], song['album'], song['title']])
		if 'year' in song:
			print_verbose ('Year for {0} is {1}'.format (song_name, song['year']))
			return song['year']

		albumId = song['albumId']
		global albumIInfoCache
		if not albumId in albumInfoCache:
			print_verbose ('Loading info for album with id {0}'.format (albumId))
			try:
				albumInfoCache[albumId] = client.get_album_info (albumId, False)
			except:
				print ('Song year could not be determined for {0}'.format (song_name))
				return 1970
		return albumInfoCache[albumId]['year']

	def checkMatch (matchingThis, againstThis):
		if matching_style == MatchingStyle.exact_match:
			return matchingThis.lower () == againstThis.lower ()
		elif matching_style == MatchingStyle.substring:
			return matchingThis.lower () in againstThis.lower ()
		else:
			return False

	def findByInfo (info):
		tuple_list = []
		for song in songs:
			matched = True
			if 'Song' in info and not checkMatch (info['Song'], song['title']):
				matched = False
			if 'Album' in info and not checkMatch (info['Album'], song['album']):
				matched = False
			if 'Artist' in info and not checkMatch (info['Artist'], song['artist']):
				matched = False
			if matched:
				print_verbose ('Matched: ' + ' - '.join ([song['artist'], song['album'], song['title']]))
				tuple_list.append ((getSongYear (song), song['album'], song['discNumber'], song['trackNumber'], song['id']))
		tuple_list.sort ()
		return [i[-1] for i in tuple_list]

	id_list = []
	try:
		with open(options.input_file[0], 'r') as f:
			for line in f:
				line = line.strip()
				if not line: # skip empty lines
					continue

				def exit_when_line_not_parsable ():
					exit_with_error ('Line "{}" was not parsed successfuly (maybe songs/albums are missing or format is wrong)'.format (line))

				print_verbose ('Resolving format for ' + line)
				matched = False
				if options.fixed_format:
					res = parse(options.fixed_format, line)
					if res:
						matched_ids = findByInfo (res.named)
						if matched_ids:
							id_list.extend (matched_ids)
							matched = True
					if not matched:
						exit_when_line_not_parsable ()
				else:
					formatResults = collections.OrderedDict ()
					for format in formats:
						print_verbose ('Starting matching for format ' + format)
						res = parse(format, line)
						print_verbose ('Parse Results: ' + str (res))
						if res:
							l = findByInfo (res.named)
							if l:
								formatResults[format] = l
							if format in formatResults:
								print_verbose ('Found match for format ' + format)
					if len (formatResults) > 1:
						print ('Several formats were matched for line "{}":'.format (line))
						for i, format in enumerate(formatResults.keys ()):
							print (str (i + 1) + ' - ' + format)
						res = input ('Choose Desired (1-{}):'.format (len (formatResults)))
						try:
							int_res = int (res)
							if (int_res > len (formatResults)) or (int_res < 0):
								raise IOError ()
							print (list (formatResults.keys ())[int_res - 1] + ' was chosen.')
							id_list.extend (list (formatResults.values ())[int_res - 1])
						except IOError as e:
							exit_with_error ('Wrong Input')
					elif len (formatResults) == 1:
						print_verbose ('Format resolved to: ' + next (iter (formatResults.keys())))
						id_list.extend (next (iter (formatResults.values())))
					else:
						exit_when_line_not_parsable ()
	except (IOError, OSError) as e:
		exit_with_error ('Input file {} cannot be opened'.format (options.input_file[0]))

	if collided_id:
		if further_action == Action.overwrite:
			print_verbose ('Cleanup before overwrite')
			for playlist_content in client.get_all_user_playlist_contents ():
				if playlist_content['id'] == collided_id:
					entry_ids = []
					for playlist_entry in playlist_content['tracks']:
						entry_ids.append (playlist_entry['id'])
					client.remove_entries_from_playlist(entry_ids)
	target_id = collided_id

	if further_action == Action.new:
		print_verbose ('Creating New Playlist')
		target_id = client.create_playlist (playlist_name)

	print_verbose ('Adding to playlist')
	client.add_songs_to_playlist (target_id, id_list)
	print ('Success!')
except ErrorExit as e:
	print ('Script terminated due to errors.')
finally:
	print_verbose ('Logging Out')
	client.logout()
