import os
import shutil
import random

# get argument from command line
import sys
if len(sys.argv) != 2:
    print("Usage: python copy-n.py <number>")
    sys.exit(1)

try:
    n = int(sys.argv[1])
except ValueError:
    print("Please enter a valid number")
    sys.exit(1)

# check if the number is positive
if n < 1:
    print("Please enter a number greater than 0")
    sys.exit(1)

# Define the source and destination directories
source_dir = 'extensions/'
dest_dir = 'testset/'

# Ensure the destination directory exists
os.makedirs(dest_dir, exist_ok=True)

# Get a list of all subdirectories in the source directory
subdirs = [name for name in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, name))]

# Shuffle the list of subdirectories to ensure random selection
random.shuffle(subdirs)

# Select the first n subdirectories (or fewer if there are not that many)
subdirs_to_copy = subdirs[:n]

# Copy each selected subdirectory to the destination directory
for subdir in subdirs_to_copy:
    src_path = os.path.join(source_dir, subdir)
    dest_path = os.path.join(dest_dir, subdir)
    shutil.copytree(src_path, dest_path)

print(f"Copied {len(subdirs_to_copy)} directories from '{source_dir}' to '{dest_dir}'.")
