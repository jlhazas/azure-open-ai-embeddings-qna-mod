import json
import re

# Regular expression to detect section headings with the pattern 1, 1.2, 1.2.1, etc.
section_re = re.compile(r'^(\b\d+(?:\.\d+)*\b\.*\s[a-zA-Z]+)')

# Sections that we don't want to process
section_to_exclude = ['footnote', 'pageHeader', 'pageFooter', 'pageNumber']

# Function to determine if a line or paragraph is the title of a section or not
def is_heading(content):
    # If the line matches the regular expression, then the match is returned
    coincidence = re.match(section_re, content)
    if coincidence:
        return coincidence.groups(0)
    return None

# Recursive function to build the tree structure of the sections
def recursive_tree(num_list, section_title, dict):
    if len(num_list) == 0:
        # if there is no more numbers in the list, we are at the right section. Return dict
        return dict
    else:
        if num_list[0] in dict.keys():
            # The section number is already in the dictionary, move to the next level in the hierarchy
            recursive_tree(num_list[1:], section_title, dict[num_list[0]]['subsections'])
        else:
            # The section number is not in the dictionary, create a new section and move to the next level
            new_section = {}
            new_section['title'] = section_title
            # Initialize an empty list to store content (text paragraphs) of the section
            new_section['content'] = []
            # Initialize an empty dictionary to store subsections
            new_section['subsections'] = {}
            # Add the new section to the dictionary
            dict[num_list[0]] = new_section
            # continue with subsections
            recursive_tree(num_list[1:], section_title, new_section['subsections'])

# Recursive function to insert content into the corresponding section
def recursive_insert_content(num_list, content, dict):
    if len(num_list) == 1:
        # We have reached the appropriate section to insert the content
        dict[num_list[0]]['content'].append(content) # Append the content to the 'content' list of the section
        return
    else:
        # Traverse down the hierarchy to find the appropriate section for insertion
        next_dict = dict[num_list[0]]['subsections']
        # Get the dictionary of the next subsection level 
        return recursive_insert_content(num_list[1:], content, next_dict)

# Process the document data to create a tree structure of sections
def process_doc(data):
    # Create an empty dictionary to store the hierarchical tree structure
    file_tree = {} 
    # Initialize a list to keep track of the current section number
    current_section = [] 

    for i, element in enumerate(data):
        content = element['content']
        if content and element['role'] not in section_to_exclude:
            result = is_heading(content)
            if result:
                # If the current line is a section heading
                section_all = result[0]
                section_parts = section_all.split(" ")
                # Extract the section number
                section_num = section_parts[0] 
                # Set the content as the section title
                section_title = content
                # Convert the section number into a list of integers
                section_nums = [int(x) for x in section_num.split(".") if x != '']
                # Update the current_section list
                current_section = section_nums 
                # Build the tree structure using the section number and title
                recursive_tree(section_nums, section_title, file_tree)
            elif current_section != [] and element['role'] == None:
                # If the current line is a regular content line, and there's a current section to insert the content
                recursive_insert_content(current_section, content, file_tree) # Insert the content into the appropriate section in the tree
    return file_tree

# Function to split content into chunks based on the specified chunk size and tolerance
def split_chunks(content, title, chunk_size, tolerance=30):
    chunk = title
    chunks = []
    for c in content:
        if len(c) > tolerance:
            if len(chunk) + len(c) <= chunk_size:
                chunk += '\n' + c
            else:
                chunks.append(chunk)
                chunk = title
                chunk += '\n' + c
    chunks.append(chunk)
    return chunks

# Convert the tree structure of sections into chunks of specified size
def tree_to_chunks(dictionary, chunk_size):
    # Initialize a stack to traverse the tree structure
    stack = [(dictionary, list(dictionary.keys()))] 
    chunks = []
    
    while stack:
        # Get the current level from the stack
        current_dict, keys = stack[-1]  
        # If there are no more sub-levels in the current level, remove it from the stack
        if not keys:  
            stack.pop()
            continue
        # Get the next sub-level to process
        current_key = keys.pop(0) 
        # Get the dictionary corresponding to the sub-level
        current_dict = current_dict[current_key]  
        if current_dict['content']:
            # Split the content of the current section into chunks
            new_chunks = split_chunks(current_dict['content'], current_dict['title'], chunk_size) 
            chunks += new_chunks    
        # Add the next sub-level to the stack
        if current_dict['subsections']:
            stack.append((current_dict['subsections'], list(current_dict['subsections'].keys())))
    
    return chunks







