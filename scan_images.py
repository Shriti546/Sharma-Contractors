import os
import re
from collections import defaultdict

images_dir = 'images'
files = os.listdir(images_dir)

# Pattern to match "Project Name (number).ext" or "Project Name(number).ext"
# We'll use a regex that looks for an optional space, opening parenthesis, digits, closing parenthesis, and extension.
pattern = re.compile(r'^(.*?)\s*\(\s*(\d+)\s*\)\.[a-zA-Z0-9]+$')

projects = defaultdict(list)
unmatched = []

for f in files:
    match = pattern.match(f)
    if match:
        proj_name = match.group(1).strip()
        # Some are named L&T and some L&t, standardize to title case for grouping but keep original names for paths?
        # Actually let's just group by lowercase to merge them, but display original case
        key = proj_name.lower()
        projects[key].append((int(match.group(2)), f, proj_name))
    else:
        unmatched.append(f)

# Sort groups
for key in projects:
    projects[key].sort(key=lambda x: x[0])

# Print output
for key, items in projects.items():
    proj_display_name = items[0][2] # Use the original case of the first item
    print(f"Project: {proj_display_name}")
    
    # Try to find (1) for cover, else use the first one
    cover = None
    gallery = []
    
    for idx, filename, _ in items:
        if idx == 1 and not cover:
            cover = filename
        else:
            gallery.append(filename)
            
    if not cover and items:
        cover = items[0][1]
        gallery = [x[1] for x in items[1:]]
        
    print(f"* Cover: {cover}")
    print(f"* Gallery: {', '.join(gallery)}")
    print()

if unmatched:
    print("Unmatched files (not following the pattern):")
    print(", ".join(unmatched))
