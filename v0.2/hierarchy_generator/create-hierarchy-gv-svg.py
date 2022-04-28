#------------------------------------------------------------------------------------
# This code:
# Takes a list of directories 'use_dir' to include in the hierarchy
# 1. checks all .ath files in a directory aond its subdirectories to generate a list 
# of dependencies
# 2. Creates a .gv file which can be read by graphviz to create a dependency graph
#------------------------------------------------------------------------------------


import os
import sys
import errno
import shutil


ignore=[]  #files to ignore
use_dir=[] #main directories to include


#--------- function to strip starting sequence of chars
def strip_string(string, to_strip):
    if to_strip:
        while string.startswith(to_strip):
            string = string[len(to_strip):]
        while string.endswith(to_strip):
            string = string[:-len(to_strip)]
    return string

#--------- function to enter a \\n after every n words
def wrap_by_word(s, n):
    a = s.split()
    ret = ''
    for i in range(0, len(a), n):
        ret += ' '.join(a[i:i+n]) + '\n'

    #remove trailing \n                  
    #------------------------> Line below may cause issues    
    ret2 = ret.rstrip('\n')

    return ret2

#--------- function to get filenames to ignore from configuration
def get_ignore():
#	config_path = strip_string(os.getcwd(), "hierarchy_generator") + "\\hierarchy-config.txt"
	config_path = os.getcwd() + "\\hierarchy-config.txt"
	with open(config_path, 'r') as f:
		for line in f:
			if line.startswith("-"):
				line_data = strip_string(line, "- ")
				line_data = line_data.translate(str.maketrans('','','\"\r\n'))
				ignore.append(line_data)


#--------- function to get description from the manual description file hierarchy-config.txt
def get_manual_desc(filename):
	found = False
#	config_path = strip_string(os.getcwd(), "hierarchy_generator") + "\\hierarchy-config.txt"
	config_path = os.getcwd() + "\\hierarchy-config.txt"
	with open(config_path, 'r') as f:
		for line in f:
			if line.startswith("+"):
				line_data = strip_string(line, "+ ")
				line_contents = line_data.split(' ')
				if line_contents[0] == filename:
					found = True
					description = ' '.join(line_contents[1:]) 
					return (description.strip())
	if found == False:
		print("Did not find description for ", filename)
		return ("Details Missing")


#--------- function to get description of a given filename
def get_description(filename, description_data):
	found = False
	descr = ""
	for row in description_data:
		if (row[0] == filename):
			descr = wrap_by_word(row[1],3)
			found = True
			break
		else:
			continue
	if found:
		return (descr)
	else: # get from manual 
		return get_manual_desc(filename)



#---------  Function to fetch the dependency data and the description data
def get_dependency(walk_dir):
	#--------- stores dependency info
	dependency_data = []

	#--------- stores description of each file
	description_data = []

	for root, subdirs, files in os.walk(walk_dir):

	    for filename in files:
	        file_path = os.path.join(root, filename)

	        if filename in ignore:
	        	print("- ", filename)
	        	continue

	        if filename.endswith(".ath"):
	        	print(" +", filename)
		        with open(file_path, 'r') as f:
		            for line in f:
		            	# fetching dependency
		            	if line.startswith("load"):
		            		line_contents = (line.split('/'))
		            		dependency = (line_contents[-1])
		            		dependency = dependency.translate(str.maketrans('','','\"\r\n'))
		            		dependency_data.append([filename, dependency ])
	            		# fetching description
	            		if line.startswith("#+-"):
	            			line_contents = strip_string(line, "#+-")
	            			line_contents = line_contents.translate(str.maketrans('','','\"\r\n'))
	            			description_data.append([filename, line_contents])
	return ([dependency_data, description_data])


#---------  Function to create the .gv file
def create_gv(dependency_data, description_data, foldername):
	first_line = "digraph G {\n graph [fontname = \"CMU Serif Roman\"] \n edge [fontname = \"CMU Serif Roman\"] \n node [fontname = \"CMU Serif Roman\"]"
	last_line = " }"

	gvfilename = foldername.translate(str.maketrans('','','\"\r\n\\')) + "_hierarchy.gv"

	if not os.path.exists(gvfilename):
		with open(gvfilename, 'x') as the_file:
			the_file.write((first_line+"\n"))
			for dat in dependency_data:
				the_file.write(('\"' + get_description(dat[1],description_data) + " \\n(" + dat[1] + ")" + "\" -> \"" + get_description(dat[0],description_data) + " \\n(" + dat[0] + ")" + '\"\n'))
			the_file.write((last_line+'\n'))
	else:
		with open(gvfilename, 'w') as the_file:
			the_file.write((first_line+"\n"))
			for dat in dependency_data:
				the_file.write(('\"' + get_description(dat[1],description_data) + " \\n(" + dat[1] + ")" + "\" -> \"" + get_description(dat[0],description_data) + " \\n(" + dat[0] + ")" + '\"\n'))
			the_file.write((last_line+'\n'))



#---------  Function to create call on specified directories in use_dir
def doJob(use_dir, path):
	#variables to store root level data
	root_dependency = []
	root_description = []

	#variables to store directory level data
	dir_dependency = []
	dir_description = []	

	print("\n--Fetching data to create hierarchies--")
	# call to get individual dependencies of each dir
	for d in use_dir:
		path_name = lib_root_path + d
		local_data = get_dependency(path_name)
		dir_dependency.append(local_data[0])
		dir_description.append(local_data[1])
	print("--Fetched data to create hierarchies--\n\n")

	# add all descriptions to root-level
	for d in dir_description:
		for d2 in d:
			root_description.append(d2)

	# add all dependencies to root-level
	for d in dir_dependency:
		for d2 in d:
			root_dependency.append(d2)			

	print("--Creating hierarchy files--")		
	# call to create individual files	
	for i in range(len(use_dir)):
		create_gv(dir_dependency[i], root_description, use_dir[i])

	# call to create root file	
	create_gv(root_dependency, root_description, "root")

	# run commands to create the individual graphs and ove them
	for d in use_dir:
		comand = "dot -Tsvg " + d.translate(str.maketrans('','','\"\r\n\\')) + "_hierarchy.gv -o " + d.translate(str.maketrans('','','\"\r\n\\')) + "_hierarchy.svg"
		print ("Created svg file successfully ")
		print ("Running dot command: ", comand)
		os.system(comand)
		filenam = d.translate(str.maketrans('','','\"\r\n\\')) + "_hierarchy.svg"
		move_to = path + d 
		shutil.copy(filenam, move_to)

	# run commands to create the root graph	
	os.system("dot -Tsvg root_hierarchy.gv -o root_hierarchy.svg")
	shutil.copy('root_hierarchy.svg', path)	

	# delete created files from current directory
	test = os.listdir( os.getcwd() )

	for item in test:
	    if item.endswith(".svg"):
	        os.remove( os.path.join( os.getcwd(), item ) )	
	    if item.endswith(".gv"):
	        os.remove( os.path.join( os.getcwd(), item ) )	


lib_root_path = strip_string(os.getcwd(), "hierarchy_generator") + "\\"
 

#----------  ENTRY POINT
# populate ignore
get_ignore()


# populate use_dir
for x in os.listdir(lib_root_path):
	if (not ('.' in x)) and (not (x == "hierarchy_generator")):
		use_dir.append(x)


# send to generate the graph files
doJob(use_dir,lib_root_path)


print ("\n\n-------- Hierarchies successfully created! --------\n\n")