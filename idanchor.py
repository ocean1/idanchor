# IDAnchor - Generates hyperlinked HTML disassembly file.
#
# Craig Heffner
# http://www.devttys0.com
# September 25, 2011

name_list = []
ida_file_name = "out.html"
html_file_name = "ida.html"
nav_file_name = "nav.html"
index_file_name = "index.html"
count = 0

# Get the area selected in the IDA screen (doesn't seem to work with 64 bit binaries?)
start_ea = SelStart()
end_ea = SelEnd()

if start_ea == BADADDR or end_ea == BADADDR:
        print "Please select an area to export!"
        exit(1)

# User must specify an output directory
ddir = AskFile(1, "*", "Select output directory:")
if ddir is None:
        print "No output directory specified! Quitting..."
        exit(1)

# All output files go into the specified directory
ida_file = "%s/%s" % (ddir, ida_file_name)
html_file = "%s/%s" % (ddir, html_file_name)
nav_file = "%s/%s" % (ddir, nav_file_name)
index_file = "%s/%s" % (ddir, index_file_name)

# Make sure the directory exists
if not os.path.exists(ddir):
        print "Creating output directory %s..." % ddir
        os.makedirs(ddir)

# Generate HTML file
print "Generating HTML file (0x%X - 0x%X)..." % (start_ea, end_ea)
n = GenerateFile(OFILE_LST, ida_file, start_ea, end_ea, GENFLG_GENHTML)

if n < 1:
        print "failed to generate HTML file %s!" % ida_file
        exit(1)
else:
        print "%d lines of HTML generated OK." % n

print "Searching for names...",

# Get a list of all known functions and append the function address and name to the name_list array
for ea in Functions():
        if ea <= end_ea:
                addr = "%8X" % ea
                name = Name(ea)
                name_list.append((addr.strip(), name))
                count += 1

# Generate the function navigation file
nfp = open(nav_file, "w")
nfp.write("<html><body>\n")
for (addr, name) in name_list:
        nfp.write('<a target="ida" href="%s#%s">%s</a><br />\n' % (html_file_name, addr, name))
nfp.write("</body></html>")
nfp.close()

# Generate the main index file
hfp = open(index_file, "w")
hfp.write('<html><frameset cols="20%%,80%%"><frame src="nav.html" /><frame name="ida" src="ida.html" /></frameset></html>')
hfp.close()

# Loop through the entire selected area looking for named offsets that we don't already know about
ea = start_ea
while ea < end_ea:

        try:
                # Only process code areas. If we hit a non-code area, stop searching for names.
                if GetSegmentAttr(ea, SEGATTR_TYPE) != 0x02:
                        break
        except:
                pass

        # Check if this offset has a name; if so, add its name and address to name_list.
        name = Name(ea)
        if name and name not in name_list:
                addr = ("%X" % ea).strip()
                name_list.append((addr, name))
                Jump(ea)
                count += 1
        ea += 1

# Record where we stopped; we'll need this later
end_code_ea = ea

print "found %d names." % count

print "Adding hyperlinks to HTML file...",

ifp = open(ida_file, "r")
ofp = open(html_file, "w")
inbody = False

# When parsing the HTML, names may be bracketed by these characters
prefixes = [' ', '>', '(']
postfixes = ['\r', '\n', ' ', '+', '<']

for line in ifp.readlines():

        if line.startswith("<body"):
                #line = "%s<pre>" % line
                inbody = True
        elif "</body>" in line:
                #line = line.replace("</body>", "</pre></body>")
                inbody = False
        elif inbody:
                try:
                        # Parse out the address of this line
                        laddr = line.split('.')[1].split(':')[1].split(' ')[0]
                        saddr = laddr.lstrip('0').strip()
                        try:
                                # Make sure we parsed a valid ea, else skip this part
                                tea = int(saddr, 16)
                                if tea >= start_ea and tea <= end_ea:
                                        # Mark each line with its address
                                        line = line.replace('<span', '<span id="%s"' % saddr, 1)
                        except:
                                pass
                except:
                        pass

                # Find all references to all names in this line and wrap the name with a hyperlink to the named line
                for (addr, name) in name_list:

                        # Don't hyperlink names outside of the program's code area (externs, etc)
                        if name in line and int(addr, 16) <= end_code_ea:
                                for prefix in prefixes:
                                        for postfix in postfixes:
                                                search = '%s%s%s' % (prefix, name, postfix)
                                                replace = '%s<a href="#%s">%s</a>%s' % (prefix, addr.strip(), name, postfix)
                                                line = line.replace(search, replace)
                
        ofp.write(line)

ifp.close()
ofp.close()
os.remove(ida_file)

print "Done."
