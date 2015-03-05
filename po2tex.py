#!/usr/bin/python3
import sys
import time
from enum import Enum

class PoType(Enum):
	unknown     = 0
	part        = 1
	section     = 2
	quote       = 3
	chapter     = 4
	description = 5
	normal      = 6
	footnote    = 7
	hline       = 8


def html2latex(line):
	line = line.replace("\\\"", "\"")
	line = line.replace("%", "\\%")
	line = line.replace("$", "\\$")
	line = line.replace("&", "\\&")
	line = line.replace("#", "\\#")
	line = line.replace("é", "\\'e")

	while True:
		footnotestart = line.find("<a class=\"sdfootnote")
		footnoteend = line.find("</a>",footnotestart)
		if footnotestart == -1 or footnoteend == -1:
			break
		str = line[:footnotestart]
		footnotestart = line.find(">", footnotestart)
		str = str + line[footnotestart+1:footnoteend]
		str = str + line[footnoteend+4:]
		#print("%% %s" % (str))
		line = str

	line = line.replace("_", "\\_")
	line = line.replace("<em>", "\\textit{")
	line = line.replace("<i>", "\\textit{")
	line = line.replace("</em>", "}")
	line = line.replace("</i>", "}")

	line = line.replace("<font size=\"1\">", " {\\footnotesize ")
	line = line.replace("</font>", "}")


	line = line.replace("<strong>", "\\textbf{")
	line = line.replace("</strong>", "}")

	supstr = "<sup>"
	slashsupstr = "</sup>"

	while line.find("<sup>") != -1 and line.rfind("</sup>") != -1:
		supidx = line.find(supstr)
		str = line[:supidx] + "\\textsuperscript{" + line[supidx+len(supstr):]
		line = str

		supidx = line.rfind(slashsupstr)
		str = line[:supidx] + "}" + line[supidx+len(slashsupstr):]
		#print(str)
		line = str

	line = line.replace("<sup>", "")
	line = line.replace("</sup>", "")

	#line = line.replace("<sup>", "\\textsuperscript{")
	#line = line.replace("</sup>", "}")


	line = line.replace("</a><font size=\"1\">", "}</a><font size=\"1\">")
	line = line.replace("<br />", "\\newline ")

	line = line.replace("·", "$\\cdot$") # Hack - why are bullets in html
	line = line.replace("●", "$\\bullet$") # Hack - why are bullets in html

	line = line.replace("…", "''")
	line = line.replace("\"", "''")

	return line

class PoString():
	def __init__(self, filename, msgid, msgstr):
		self.filename = filename
		self.msgid = msgid
		self.msgstr = msgstr
		self.type = PoType.unknown

	def getID(self):
		return self.msgid

	def getStr(self):
		return self.msgstr

	def setID(self, msgid):
		self.msgid = msgid

	def setStr(self, msgstr):
		self.msgstr = msgstr

	def getFilename(self):
		return self.filename

	def getType(self):
		return self.type

	def setType(self, type):
		self.type = type

	def toLatex(self):
		rawtext = self.msgstr
		if len(rawtext) == 0:
			rawtext = self.msgid
		latex = html2latex(rawtext)

		#if len(latex) == 0:
			#return None

		if self.type == PoType.part:
			return "\\part{%s}\n" % (latex)

		if self.type == PoType.footnote:
			return "{%s}\n" % (latex)


		if self.type == PoType.section:
			return "\n\section{%s}" % (latex)

		if self.type == PoType.chapter:
			return "\n\chapter{%s}" % (latex)

		if self.type == PoType.quote:
			return "\n\\begin{center}\\parbox{15cm}{\\Large %s}\end{center}" % (latex)

		if self.type == PoType.hline:
			return "\n\n\\hrulefill\n\n"

		if self.type == PoType.normal:
			return latex
		return None



def process_tzmd(postrings):
	last_type = PoType.unknown
	current_file = ""
	index = 0
	while index < len(postrings):
		po = postrings[index]

		# First entry is junk in all files
		if current_file != po.getFilename():
			current_file = po.getFilename()
			last_type = PoType.unknown
			index = index + 1
			continue

		# Assume that the block is the same type as the previous
		if po.getType() == PoType.unknown:
			po.setType(last_type)

		if last_type == PoType.unknown:
			print("%% Entry is unknown - setting is to chapter")
			po.setType(PoType.chapter)

		if last_type == PoType.part:
			#It's only a quote of most letters are lowercase
			orig = po.getID()
			lower = orig.lower()
			diffs = 0
			idx = 0
			while idx < len(orig):
				if orig[idx] != lower[idx]:
					diffs = diffs + 1
				idx = idx + 1

			if diffs > 0.23*len(orig):
				po.setType(PoType.chapter)
			else:
				po.setType(PoType.quote)

		if last_type == PoType.chapter:
			po.setType(PoType.normal)

		if last_type == PoType.quote:
			if len(po.getID()) < 32:
				po.setType(PoType.chapter)
			else:
				po.setType(PoType.normal)

		if last_type == PoType.section:
			po.setType(PoType.normal)

		if last_type == PoType.description:
			po.setType(PoType.normal)

		if last_type == PoType.normal or last_type == PoType.footnote:
			if len(po.getID()) < 32:
				str = po.getID()
				if str.rfind(":") == len(str)-1:
					po.setType(PoType.description)
				else:
					po.setType(PoType.section)

		if po.getID().find("PART ") == 0:
			po.setType(PoType.part)

			# check if we need to split the part in part and chapter
			rawtext = po.getID()
			trtext = po.getStr()
			if rawtext.rfind(">") > -1:
				rawpartname    = rawtext[:rawtext.find("<")]
				rawchaptername = rawtext[rawtext.rfind(">")+1:]
				trpartname    = trtext[:trtext.find("<")]
				trchaptername = trtext[trtext.rfind(">")+1:]
				po.setID(rawpartname)
				po.setStr(trpartname)
				newpo = PoString(filename,rawchaptername, trchaptername)
				#print("%% Inserting chapter at index %d" % (index+1))
				postrings.insert(index,newpo)

		if po.getID().find("sdfootnotesym") != -1:
			po.setType(PoType.footnote)
			if last_type != PoType.footnote:
				print("%% HLINE")
				newpo = PoString(filename,"", "")
				newpo.setType(PoType.hline)
				postrings.insert(index,newpo)


		#print( "%s - %s:   %s" % (po.getFilename(), po.getType(), po.getID()))
		print("%% %s" % (po.getType()))

		index = index + 1
		last_type = po.getType()


def toLatex(postrings):
	for po in postrings:
		latex = po.toLatex()
		if latex != None:
			print( latex )
			print("")


postrings = []

unknown_ctx = 0
msgid_ctx = 0
msgstr_ctx  = 1

running_msgid = ""
running_msgstr = ""
context = unknown_ctx

first = True
for filename in sys.argv:
	if first:
		first = False
		continue

	#print( filename )

	f = open(filename, "r")

	for line in f:
		line = line.strip()
		if line.find("#") == 0:
			continue

		valid_line = False
		if line.find("msgid ") == 0:
			if context == msgstr_ctx:
				postrings.append( PoString(filename, running_msgid, running_msgstr) )
			context = msgid_ctx
			running_msgid = ""
			valid_line = True

		if line.find("msgstr ") == 0:
			context = msgstr_ctx
			running_msgstr = ""
			valid_line = True

		if line.find("\"") == 0:
			valid_line = True

		if not valid_line:
			continue

		first_quote  = line.find("\"")+1
		last_quote = line.rfind("\"")
		str = line[first_quote:last_quote]
		#print( line )

		if context == msgid_ctx:
			running_msgid += str

		if context == msgstr_ctx:
			running_msgstr += str
			#print( str )
			#print ( running_msgstr)

	f.close()
	if context == msgstr_ctx:
		postrings.append( PoString(filename, running_msgid, running_msgstr) )
	context = unknown_ctx

#time.sleep(10)

process_tzmd(postrings)

#print( "Number of strings: %d" % (len(postrings)))

do_latex = True
if do_latex:
	print ( "\\documentclass[a4paper,oneside,onecolumn,final]{report}\n"
	"\\usepackage{cmap}\n"
	"\\usepackage[utf8]{inputenc}\n"
	"\\usepackage[T1]{fontenc}\n"
	"\\usepackage[danish]{babel}\n"
	"\\usepackage{amsmath}\n"
	"\\usepackage{amssymb,amsfonts,textcomp}\n"
	"\\usepackage{ae,aecompl}\n"
	"\\usepackage[margin=2cm]{geometry}\n"
	"\\usepackage{parskip}\n"
	"\\usepackage[hidelinks]{hyperref}\n")

	print("\\usepackage{titlesec}\n"
	"\\titleclass{\part}{top}"
	"\\titleformat{\\part}[display]"
	"{\\normalfont\\huge\\bfseries}{}{0pt}{\Huge}")

	print("\\begin{document}\n")

	print( "\\tableofcontents\n")
	print( "\\clearpage\n")

	toLatex(postrings)

	print( "\n\end{document}" )