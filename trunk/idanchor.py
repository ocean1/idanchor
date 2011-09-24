#!/usr/bin/env python

import os

class IDAnchor:

	SUBDELIM = "S U B R O U T I N E"
	XREF_MARKER = "<span style=\"color:navy\">"
	SUBNAME_MARKER = "<span style=\"color:navy\">:"
	INDEX = '<html><frameset cols="20%%,80%%"><frame src="nav.html" /><frame name="ida" src="ida.html" /></frameset></html>'

	def __init__(self, infile, outdir):
		self.xrefs = []
		self.functions = []
		self.outdir = outdir
		self.html = open(infile).read().split('\n')

	def PatchAll(self):
		self.PatchXRefs()
		self.PatchFunctions()

	def PatchXRefs(self):
		self.FindXRefs()
		self.LinkXRefs()
		self.MarkXRefs()
		return len(self.xrefs)

	def PatchFunctions(self):
		self.FindFunctions()
		self.LinkFunctions()
		self.MarkFunctions()
		return len(self.functions)

	def FindFunctions(self):
		sub = 0
		num = 0

		for line in self.html:

			if not sub and self.SUBDELIM in line:
				sub = True
			elif self.SUBNAME_MARKER in line:
				name = line.split('</span>')[1].split('<span')[0]
				self.functions.append((num, name))
			elif sub > 10:
				sub = 0
			else:
				sub+=1

			num+=1

		return num

	def FindXRefs(self):
		num = 0

		for line in self.html:
			
			if line.startswith('.') and '# CODE XREF:' in line:
				name = line.split(self.XREF_MARKER)[1].split(':')[0]
				self.xrefs.append((num, name))

			num += 1

		return num

	def Mark(self, info):
		count = 0

                for (line, name) in info:
                        self.html[line] = self.html[line].replace('<span', '<span id="%s"' % name)
                        count += 1

                return count

	def MarkFunctions(self):
		return self.Mark(self.functions)

	def MarkXRefs(self):
		return self.Mark(self.xrefs)

	def Link(self, info):
		prefixes = [' ', '>']
		postfixes = ['\r', '\n', ' ', '+', '<']

		for i in range(0, len(self.html)):
			for (line, name) in info:
				if name in self.html[i]:
					for prefix in prefixes:
						for postfix in postfixes:
							search = '%s%s%s' % (prefix, name, postfix)
							replace = '%s<a href="#%s">%s</a>%s' % (prefix, name, name, postfix)

							self.html[i] = self.html[i].replace(search, replace)
		return

	def LinkFunctions(self):
		return self.Link(self.functions)

	def LinkXRefs(self):
		return self.Link(self.xrefs)

	def Save(self):
		os.mkdir(self.outdir)
		os.chdir(self.outdir)

		self.WriteToFile()
		self.GenNavBar()
		self.GenIndexPage()

	def WriteToFile(self):
		fp = open("ida.html", "w")

		for line in self.html:
			fp.write("%s\n" % line)

		fp.close()

	def GenNavBar(self):
		names = []

		fp = open("nav.html", "w")		
		fp.write("<html><body>")

		for (line, name) in self.functions:
			names.append(name)
		names.sort()

		for name in names:
			fp.write('<a target="ida" href="ida.html#%s">%s</a><br />' % (name, name))

		fp.write("</body></html>")
		fp.close()

	def GenIndexPage(self):
		fp = open("index.html", "w")
		fp.write(self.INDEX)
		fp.close()


if __name__ == "__main__":

	import sys

	if len(sys.argv) != 3:
		print ""
		print "Usage: %s <IDA html file> <output directory>" % sys.argv[0]
		print ""
		print "Example: %s idafile.html out" % sys.argv[0]
		print ""
		sys.exit(1)
	
	target = sys.argv[1]
	outdir = sys.argv[2]

	try:
		a = IDAnchor(target, outdir)
		print "Processing %s; this could take a while..." % target

		xc = a.PatchXRefs()
		fc = a.PatchFunctions()
		a.Save()

		print "Processed %d functions and %d code xrefs. Data saved to %s." % (fc, xc, outdir)
	except Exception, e:
		print "ERROR:", e

