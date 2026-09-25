from pathlib import Path
import re
import sys
from enum import Enum
#import dbm
#import shelve
import os
from sqlitedict import SqliteDict
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.output.color_depth import ColorDepth

class Color:
	# Background: #08131a -- pc equivalent (eyeballed) = #002324
	BG = '\033[48;2;8;19;26m'
	RESET = '\033[0m'

	# Base:
	# Core text colors
	SAND = '\033[38;2;222;184;141m'       # #deb88d (Foreground/Cursor)
	CREAM = '\033[38;2;254;227;205m'      # #fee3cd
	CHARCOAL = '\033[38;2;66;75;82m'      # #424b52

	# EarthAndFire:
	# The warm accents
	TERRACOTTA = '\033[38;2;208;80;35m'   # #d05023
	MARIGOLD = '\033[38;2;251;160;47m'    # #fba02f
	MUTED_ROSE = '\033[38;2;211;134;119m' # #d38677
	PALE_PEACH = '\033[38;2;253;210;158m' # #fdd29e

	# OceanTeal:
	# The deep/vibrant blues
	DEEP_TEAL = '\033[38;2;2;123;155m'    # #027b9b
	DARK_PINE = '\033[38;2;29;72;80m'     # #1d4850
	SKY_CYAN = '\033[38;2;104;211;240m'   # #68d3f0
	CERULEAN = '\033[38;2;26;188;221m'    # #1abcdd

	# SlateAndIce:
	# The muted, atmospheric blues
	NIGHT_NAVY = '\033[38;2;23;56;76m'    # #17384c
	CADET_BLUE = '\033[38;2;80;163;181m'  # #50a3b5
	STEEL_SLATE = '\033[38;2;97;140;152m' # #618c98
	HEATHER = '\033[38;2;134;171;179m'    # #86abb3
	ICE_BLUE = '\033[38;2;187;227;238m'   # #bbe3ee

	# Ember:
	# Warm, high-contrast complements
	PEACH = '\033[38;2;255;179;128m'
	CORAL = '\033[38;2;255;107;107m'
	BURNT_ORANGE = '\033[38;2;230;126;34m'
	GOLD = '\033[38;2;241;196;15m'
	#AMBER = '\033[38;2;255;191;0m' # orig
	AMBER = '\033[38;2;255;193;0m'

	# Ice:
	# Cool, elegant colors that blend well
	SNOW = '\033[38;2;216;222;233m'
	FROST_LIGHT = '\033[38;2;136;192;208m'
	FROST_DARK = '\033[38;2;129;161;193m'
	MINT = '\033[38;2;163;190;140m'
	PALE_CYAN = '\033[38;2;152;216;216m'

	# one man show for 'foil'
	PINK_SHOCK = '\033[38;2;239;6;144m'

	# Cyberpunk:
	LASER_PINK = '\033[38;2;255;0;102m'
	#ELECTRIC_PURPLE = '\033[38;2;176;38;255m' # orig
	ELECTRIC_PURPLE = '\033[38;2;169;38;255m' # modified
	NEON_CYAN = '\033[38;2;0;255;255m'
	#NEON_PINK = '\033[38;2;255;20;147m'		# orig
	NEON_PINK = '\033[38;2;245;10;230m'		# modified
	#NEON_PINK = '\033[38;2;255;0;255m'   # magenta
	NEON_SILVER = '\033[1;38;2;200;200;200m' # orig = '\033[38;2;220;220;220m'

	# Muted:
	# Low-distraction colors for secondary text
	ASH_GRAY = '\033[38;2;108;122;137m'
	STEEL = '\033[38;2;149;165;166m'
	SAGE = '\033[38;2;135;169;156m'
	DUSK = '\033[38;2;113;104;138m'

C_RESET = Color.RESET

C_EDIT = Color.LASER_PINK #Color.NEON_PINK
C_SEARCH = Color.NEON_CYAN

C_PUNCT = Color.DARK_PINE
C_IN = Color.ICE_BLUE
C_ALERT = Color.TERRACOTTA
C_ALERT2 = Color.MUTED_ROSE
C_HL = Color.MARIGOLD
C_HL2 = Color.CORAL

C_MENU = Color.DEEP_TEAL
C_DARK = Color.CHARCOAL
C_ST = Color.SAGE #Color.FROST_DARK
C_ST2 = Color.ASH_GRAY #Color.NIGHT_NAVY
C_X = Color.NIGHT_NAVY
C_NR = Color.SAND #Color.PALE_PEACH
C_NR2 = Color.CREAM

C_FOIL = Color.PINK_SHOCK #Color.PALE_CYAN #Color.FROST_LIGHT
C_DIAM_WAVY = Color.NEON_PINK #Color.LASER_PINK
C_SPIRAL_CHECK = Color.ELECTRIC_PURPLE
C_BG = Color.AMBER #Color.MUTED_ROSE
C_PROMO = Color.NEON_SILVER

def warning_file_not_found(filename):
	print(f"\n {C_PUNCT}[{C_HL}*{C_PUNCT}]{C_HL2} Collection '{C_HL}{filename}{C_HL2}' does not exist yet")
	print(f" {C_PUNCT}[{C_HL}*{C_PUNCT}]{C_HL2} Create it by adding "
		  f"cards in {C_EDIT}Edit{C_HL2} mode{C_RESET}")
# Main
def error_bad_filename(filename):
	print(f"\n    {C_PUNCT}[{C_ALERT}!{C_PUNCT}]{C_ALERT} Bad file format"
		  f": '{C_IN}{filename}{C_ALERT}'")
	print(f"    {C_PUNCT}[{C_ALERT}!{C_PUNCT}]{C_ALERT} Expecting '{C_HL}"
		  f".sqlite{C_ALERT}' extension (or none){C_RESET}")
# Menu
def error_bad_option(mode):
	print(f"\n    {C_PUNCT}[{C_ALERT}!{C_PUNCT}]{C_ALERT} Invalid option"
		  f": '{C_IN}{mode}{C_ALERT}'. Enter a mode number"
		  f"/name.{C_RESET}\n"
		 )

'''MENU_STR = f"""
  {C_MENU} ====================
 //
||  {C_PUNCT}[{C_EDIT}1{C_PUNCT}] {C_EDIT}Edit{C_MENU}
||  {C_PUNCT}[{C_SEARCH}2{C_PUNCT}] {C_SEARCH}Search{C_MENU}
||  {C_PUNCT}[{C_MENU}3{C_PUNCT}] {C_MENU}Quit{C_MENU}
 \\\\"""
MENU_PROMPT = f"{C_MENU}   === Select a mode{C_PUNCT}: "'''

MENU_STR = f"""
{C_MENU} ┌──────────────────
{C_MENU} │  {C_PUNCT}[{C_EDIT}1{C_PUNCT}] {C_EDIT}Edit
{C_MENU} │  {C_PUNCT}[{C_SEARCH}2{C_PUNCT}] {C_SEARCH}Search
{C_MENU} │  {C_PUNCT}[{C_MENU}3{C_PUNCT}] {C_MENU}Quit
{C_MENU} └──────────────────"""
#MENU_PROMPT = f"{C_MENU}   ╰─► Select a mode{C_PUNCT}: "
MENU_PROMPT = f"{C_MENU}  ❯ Select a mode{C_PUNCT}: "

'''MENU_STR = f"""
{C_MENU} ╔════════════════════╗
{C_MENU} ║  {C_PUNCT}[{C_EDIT}1{C_PUNCT}] {C_EDIT}Edit          {C_MENU}║
{C_MENU} ║  {C_PUNCT}[{C_SEARCH}2{C_PUNCT}] {C_SEARCH}Search        {C_MENU}║
{C_MENU} ║  {C_PUNCT}[{C_MENU}3{C_PUNCT}] {C_MENU}Quit          {C_MENU}║
{C_MENU} ╚════════════════════╝"""
MENU_PROMPT = f"\n{C_MENU}  ❯ Select a mode{C_PUNCT}: "'''

GOODBYE_STR = f"\n {C_HL2}sayonara..."

def print_hello(filename, collection, total_nr_copies, nr_cards, full_playsets):
	print( f"\n {C_PUNCT}[{C_HL}{Path(filename).name}{C_PUNCT}] "
		f"---{{{C_ST2}{len(collection)}{C_X}x{C_ST2} entries{C_PUNCT}}}\n\n"
		f"   {C_MENU}Total Copies{C_PUNCT}: {C_NR}{total_nr_copies}{C_X}x\n"
		f"   {C_MENU}Unique{C_PUNCT}: {C_NR}{nr_cards}{C_X}x\n"
		f"   {C_MENU}Playsets{C_PUNCT}: {C_NR}{full_playsets}{C_X}x{C_MENU}"
		)

# Search
def error_bad_card_type(ctype):
	print(f"\n    {C_PUNCT}[{C_ALERT}!{C_PUNCT}]{C_ALERT} Invalid card type"
		  	f" ({C_HL}-t{C_ALERT}): '{C_IN}{ctype}{C_ALERT}'")
	print(f"    {C_PUNCT}[{C_ALERT}!{C_PUNCT}]{C_ALERT} Should be '{C_ALERT2}n{C_ALERT}',"
		  	f" '{C_ALERT2}m{C_ALERT}', '{C_ALERT2}j{C_ALERT}' or '{C_ALERT2}c{C_ALERT}'{C_RESET}")
def print_result(result):
	if len(result) > 0:
		print("")
	if len(result) == 1:
		print(f"{C_MENU}  Found {C_NR}1{C_MENU} card!")
	else:
		print(f"{C_MENU}  Found {C_NR}{len(result)}{C_MENU} cards!")

SEARCH_STR = (f"\n {C_PUNCT}[{C_SEARCH}*{C_PUNCT}]{C_ST2} <ENTER>{C_MENU} a blank line to go back\n"
			  f" {C_PUNCT}[{C_SEARCH}*{C_PUNCT}]{C_MENU} Enter a line as follows to {C_SEARCH}Search{C_MENU} the collection:\n\n"
			  f"    {C_PUNCT}[ [{C_HL}/{C_PUNCT}]{C_ALERT2}ID{C_PUNCT} ]  [{C_HL}-t {C_ALERT2}n{C_PUNCT}"
			  f"|{C_ALERT2}m{C_PUNCT}|{C_ALERT2}j{C_PUNCT}|{C_ALERT2}c{C_PUNCT}]  [{C_HL}-n {C_ALERT2}NAME{C_PUNCT}]  [{C_HL}-a {C_ALERT2}ART{C_PUNCT}]"
			 )
SEARCH_PROMPT = f"\n  {C_SEARCH}? "

EDIT_STR = (f"\n {C_PUNCT}[{C_EDIT}*{C_PUNCT}]{C_ST2} <ENTER>{C_MENU} a blank line to go back\n"
			f" {C_PUNCT}[{C_EDIT}*{C_PUNCT}]{C_MENU} Enter a line as follows to {C_EDIT}Edit{C_MENU} the collection:\n\n"
			f"    {C_ALERT2}ID  {C_PUNCT}[{C_ALERT2}AMOUNT{C_PUNCT}]  [{C_HL}-n {C_ALERT2}NAME{C_PUNCT}]  [{C_HL}-a {C_ALERT2}ART{C_PUNCT}]"
			f"  [{C_HL}-del{C_PUNCT}]\n\n            {C_PUNCT}({C_ALERT2}AMOUNT{C_MENU} can be negative{C_PUNCT})"
		   )
EDIT_PROMPT = f"\n  {C_EDIT}~ "

session = PromptSession()


def get_art_color(art):
	if 'foil' in art:
		return C_FOIL
	elif 'diamond' in art or 'wavy' in art:
		return C_DIAM_WAVY
	elif 'checkered' in art or 'spiral' in art:
		return C_SPIRAL_CHECK
	elif 'b&g' in art:
		return C_BG
	elif 'promo' in art:
		return C_PROMO
	return C_ST

class Type(Enum):
	NINJA	 = 1
	MISSION	 = 2
	JUTSU	 = 3
	CLIENT	 = 4
	#BAD_TYPE = 5 # a cheat to store random things

def getType(uid):
	if uid[0] == 'n':
		return Type.NINJA
	if uid[0] == 'm':
		return Type.MISSION
	if uid[0] == 'j':
		return Type.JUTSU
	if uid[0] == 'c':
		return Type.CLIENT
	return None # Type.BAD_TYPE 

class Entry:
	def __init__(self, uid, amount = 0, name = None, art = None):
		self.uid = uid
		self.amount = amount
		self.name = name
		self.art = {}
		if art != None:
			self.art[art] = amount
	def __str__(self):
		return self.str_indent()
	def str_indent(self, indent = 0):
		f_uid = f"{C_HL}{self.uid}"
		self_str = f"{f_uid:>{indent+len(C_HL)}}"
		if self.name != None:
			self_str += f"{C_PUNCT} ~ {C_ALERT}{self.name}"
		self_str += f"{C_PUNCT}:  {C_HL2}{self.amount}{C_X}x"
		if len(self.art) > 0:
			self_str += f"  {C_PUNCT}["
			for art, amount in self.art.items():
				clr_art = get_art_color(art)
				self_str += f"{C_NR2}{amount}{C_X}x {clr_art}{art}{C_PUNCT}, "
			self_str = self_str[:-2] + f"{C_PUNCT}]"
		return self_str
	def getID(self):
		return self.uid
	def update(self, amount, name, art):
		if amount != 0:
			print(f"   {C_EDIT}* {C_MENU}Amount {C_EDIT}*  {C_MENU}{self.amount}{C_X}x {C_EDIT}-> {C_HL2}{self.amount + amount}{C_X}x")
			self.amount += amount
		#assert self.amount >= 0
		if name != None:
			print(f"   {C_EDIT}*  {C_MENU}Name  {C_EDIT}*  {C_MENU}{self.name} {C_EDIT}-> {C_ALERT}{name}")
			self.name = name
		if art != None:
			if art not in self.art:
				self.art[art] = amount
				print(f"   {C_EDIT}*   {C_HL2}Art  {C_EDIT}*  {get_art_color(art)}{art}{C_PUNCT}: {C_NR2}{amount}{C_X}x")
			else:
				print(f"   {C_EDIT}*   {C_MENU}Art  {C_EDIT}*  {get_art_color(art)}{art}{C_PUNCT}: "
							f"{C_MENU}{self.art[art]}{C_X}x {C_EDIT}-> {C_NR2}{self.art[art] + amount}{C_X}x")
				self.art[art] += amount
			#assert self.art[art] >= 0
		if amount == 0 and name == None and art == None:
			print(f"   {C_EDIT}* {C_MENU}No changes {C_EDIT}*")
		return self
	def delete_art(self, art):
		if art in self.art:
			self.amount -= self.art[art]
			del self.art[art]
			print(f"   {C_EDIT}*   {C_HL2}Art  {C_EDIT}*  {C_HL2}Deleted  {get_art_color(art)}{art}  {C_PUNCT}({C_HL}{self.uid}{C_PUNCT})")
			#print(f"   {C_EDIT}* {C_HL2}Updated {C_EDIT}*  {self}")
		else:
			print(f"    {C_PUNCT}[{C_ALERT}!{C_PUNCT}]{C_ALERT} FAILED to delete!"
						f" Art '{C_IN}{art}{C_ALERT}' does not exist for '{C_IN}{self.uid}{C_ALERT}'")
		return self

def parse_edit():
	cmd = session.prompt(ANSI(EDIT_PROMPT),
						 color_depth=ColorDepth.TRUE_COLOR)
	tkns = cmd.split()
	if len(tkns) <= 0:
		return "QUIT"
	uid = tkns[0].lower()
	#if uid[0] not in ("n","m","j","c"):
	#	raise ValueError(f"!! Invalid <id> first character: '{uid[0]}'.")
	amount = 0
	name = None
	art = None
	delete = False
	if "-del" in tkns:
		delete = True
	if "-n" in tkns:
		name = tkns[tkns.index("-n") + 1].lower()
	if "-a" in tkns:
		art = tkns[tkns.index("-a") + 1].lower()
	if len(tkns) > 1:
		try:
			amount = int(tkns[1].lower())
		except:
			# print("* No amount detected. Adding 0 copies. *")
			pass
	return (uid, amount, name, art, delete)

def edit_mode(filename):
	print(EDIT_STR)
	#	  "   * <id> MUST start with 'n', 'm', 'c' or 'j'. E.g. 'm827', 'nprus001', 'jpr020', 'nps004'")
	while True:
		#try:
		edit = parse_edit()
		#except ValueError as error:
		#	print("\n    " + str(error) + " Should be 'n', 'm', 'c' or 'j'. E.g. 'm827', 'nprus001'")
		#	print(" "*80 + "^       ^")
		#	continue
		if edit == "QUIT":
			break
		uid, amount, name, art, delete = edit
		print("")
		#with shelve.open(filename, flag = 'c', protocol = 4, writeback = False) as collection:
		with SqliteDict(filename, autocommit=True, flag="c") as collection:
			if delete:
				if uid in collection:
					if art == None:
						del collection[uid]
						print(f" {C_PUNCT}[{C_HL2}DELETED{C_PUNCT}]  {C_HL}{uid}")
					else:
						collection[uid] = collection[uid].delete_art(art)
						print(f"\n {C_PUNCT}[{C_HL2}*{C_PUNCT}]  {collection[uid]}")
				else:
					print(f"    {C_PUNCT}[{C_ALERT}!{C_PUNCT}]{C_ALERT} FAILED to delete! "
								f"Card ID '{C_IN}{uid}{C_ALERT}' does not exist")
			else:
				if uid in collection:
					collection[uid] = collection[uid].update(amount, name, art)
					print(f"\n {C_PUNCT}[{C_EDIT}*{C_PUNCT}]  {collection[uid]}")
				else:
					collection[uid] = Entry(uid, amount, name, art)
					print(f" {C_PUNCT}[{C_HL2}NEW{C_PUNCT}]  {collection[uid]}")

def parse_query():
	cmd = session.prompt(ANSI(SEARCH_PROMPT),
						 color_depth=ColorDepth.TRUE_COLOR)
	tkns = cmd.split()
	if len(tkns) <= 0:
		return "QUIT"
	exact_uid = False
	uid = None
	card_type = None
	names = []
	arts = []
	if tkns[0] not in ("-t", "-n", "-a"):
		uid = tkns[0].lower()
		if uid[0] == "/":
			uid = uid[1:]
			exact_uid = True
	if "-t" in tkns:
		raw_type = tkns[tkns.index("-t") + 1].lower()
		card_type = getType(raw_type)
		if card_type == None:
			raise ValueError(raw_type)
	for i in range(len(tkns) - 1):
		tkn = tkns[i]
		arg = tkns[i+1]
		if "-n" == tkn:
			names.append(arg.lower())
		if "-a" == tkn:
			arts.append(arg.lower())
	return (uid, exact_uid, card_type, names, arts)

def query_mode(filename):
	try:
		if not os.path.exists(filename):
			raise FileNotFoundError("")
		#with shelve.open(filename, flag = 'r', protocol = 4, writeback = False) as collection:
		with SqliteDict(filename, flag="r") as collection:
			print(SEARCH_STR)
			base_indent = 4
			while True:
				try:
					query = parse_query()
				except ValueError as error:
					error_bad_card_type(error)
					continue
				if query == "QUIT":
					break
				print("")
				uid, exact_uid, card_type, names, arts = query
				if uid != None and exact_uid == True:
					if uid in collection:
						print(base_indent*" " + f"{collection[uid]}")
					else:
						print(f"    {C_PUNCT}[{C_ALERT}!{C_PUNCT}]{C_ALERT} Card ID '{C_IN}{uid}{C_ALERT}' does not exist")
				else:
					filters = []
					if uid != None and exact_uid == False:
						filters.append((uid_filter, uid))
					if card_type != None:
						filters.append((type_filter, card_type))
					if names != []:
						filters.append((name_filter, [re.compile(n, re.IGNORECASE) for n in names]))
					if arts != []:
						filters.append((art_filter, [re.compile(a, re.IGNORECASE) for a in arts]))
					result = []
					max_id_len = 4
					for card in collection.values():
						if all([f[0](card, f[1]) for f in filters]):
							result.append(card)
							card_id = card.getID()
							max_id_len = len(card_id) if len(card_id) > max_id_len else max_id_len
					result.sort(key=getID)
					for card in result:
						print(card.str_indent(max_id_len + base_indent))
					print_result(result)
	#except dbm.error:
	except FileNotFoundError:
		warning_file_not_found(filename)

def getID(card):
	return card.getID()

def getArt(art_item):
	return art_item[0]

def uid_filter(card, partial_uid):
	return re.search(partial_uid, card.getID()) != None

def type_filter(card, type):
	return getType(card.getID()) == type

def name_filter(card, names):
	if card.name == None and re.fullmatch(names[0], "mr_bojangles"): # lmao
		return True
	if card.name == None:
		return False
	for n in names:
		if re.search(n, card.name) == None:
			return False
	return True

def art_filter(card, arts):
	for art in arts:
		if any(re.search(art, a) for a in card.art.keys()):
			continue
		return False
	return True

def print_stats(filename):
	try:
		if not os.path.exists(filename):
			raise FileNotFoundError("")
		#with shelve.open(filename, flag = 'r', protocol = 4, writeback = False) as collection:
		with SqliteDict(filename, flag="r") as collection:
			arts = {}
			nr_cards = 0
			total_nr_copies = 0
			full_playsets = 0
			#good_types = (Type.NINJA, Type.MISSION, Type.JUTSU, Type.CLIENT)
			for card in collection.values():
				total_nr_copies += card.amount
				if card.amount > 0:
					nr_cards += 1
				if card.amount >= 3:
					full_playsets += 1
				individual_arts = {}
				for art in card.art.keys():
					for ind_art in art.split("/"):
						if ind_art not in individual_arts:
							individual_arts[ind_art] = 0
						individual_arts[ind_art] += card.art[art]
				for art in individual_arts:
					if art not in arts:
						arts[art] = 0
					arts[art] += individual_arts[art]
			print_hello(filename, collection, total_nr_copies, nr_cards, full_playsets)
			if len(arts) == 0:
				return
			#print(hello_str + " Versions:")
			arts_lst = []
			max_amount = 1
			#max_len_art = 1
			for art, amount in arts.items():
				arts_lst.append((art,amount))
				#if len(art) > max_len_art:
				#	max_len_art = len(art)
				if amount > max_amount:
					max_amount = amount
			max_am_width = len(str(max_amount))
			#max_width = max_len_art + max_am_width + 5 # 5 = len("x ") + space btwn cols
			arts_lst.sort(key=getArt)
			indent = 5*" "
			arts_str = ""
			max_col_widths = [0, 0, 0]
			nr_cols = len(max_col_widths)
			str_ctr = 0
			for art, amount in arts_lst:
				am = f"{amount:>{max_am_width}}"
				am_art = f"{am}x {art}"
				col_ix = str_ctr % nr_cols
				max_col_widths[col_ix] = max(max_col_widths[col_ix], len(am_art))
				str_ctr += 1
			str_ctr = 0
			for art, amount in arts_lst:
				if str_ctr % nr_cols == 0:
					arts_str += f"\n{indent}"
				am = f"{amount:>{max_am_width}}"
				clr_art = get_art_color(art)
				am_art = f"{C_NR2}{am}{C_X}x {clr_art}{art}"
				clr_pad = len(f"{C_NR2}{C_X}{clr_art}")
				col_ix = str_ctr % nr_cols
				col_width = max_col_widths[col_ix] + 4 + clr_pad
				arts_str += f"{am_art:<{col_width}}"
				#arts_str += f"{am_art:<{max_width}}"
				str_ctr += 1
				
			print(arts_str)
	#except dbm.error:
	except FileNotFoundError:
		warning_file_not_found(filename)

def main(filename):
	invalid_option = False
	print_stats(filename)
	while True:
		try:
			if not invalid_option:
				print(MENU_STR)
			invalid_option = False
			mode = session.prompt(ANSI(MENU_PROMPT),
								  color_depth=ColorDepth.TRUE_COLOR).lower().strip()
			if mode in ('1', 'e', 'edit'):
				edit_mode(filename)
			elif mode in ('2', 's', 'search'):
				query_mode(filename)
			elif mode in ("3", "q", "quit", "exit"):
				break
			else:
				error_bad_option(mode)
				invalid_option = True
		except (EOFError, KeyboardInterrupt):
			break
	print(GOODBYE_STR)

if __name__ == '__main__':
	filename = "collection"
	if len(sys.argv) >= 2:
		filename = sys.argv[1]
	if "." in filename:
		if ".sqlite" != filename[-7:]:
			error_bad_filename(filename)
			exit(1)
	else:
		filename = filename + ".sqlite"
	main(filename)