po2tex
======

TZM uses pootle for book translations. It work alright, but to get an overview
of the complete translation things tend to get annoying.

So this python script will process the book and create tex out of it.

Usage
-----

Basic usage is somthing like this 

	$ ./po2tex.py da/tzmd_1-* da/tzmd_2-* da/tzmd_3-* da/tzmd_4-* > tzmd.tex 
	$ latexmk -pdf tzmd.tex

It of cause requires that you have the po files, but hopefully that will solve
itself over time when we at some point get some kind of access to the current
po files through some read-only interface.
