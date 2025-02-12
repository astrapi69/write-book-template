#!/bin/bash

# Get the current directory name
new_repo_name=$(basename "$(pwd)")

# Check if the new name is valid (you might want to add more checks)
if [[ -z "$new_repo_name" ]]; then
  echo "Error: Repository name cannot be empty."
  exit 1
fi

# Rename the directory (important: this renames the local directory)
# No need to rename as the directory already has the correct name

# Update the Git configuration (origin URL)
git remote set-url origin "https://github.com/YOUR_USERNAME/$new_repo_name.git"  # Replace YOUR_USERNAME

# Add, commit, and push the changes
git add .
git commit -m "Initial commit for $new_repo_name" # Or "Renamed repository..." if it was already initialized
git push origin main  # Or master, depending on your default branch

echo "Repository initialized/renamed to $new_repo_name and pushed to GitHub."
echo "Remember to create the repository $new_repo_name on GitHub if you haven't already!"

# Optional: Create the repository on GitHub using the GitHub CLI (gh) if installed.
# Requires the gh CLI to be installed and configured.
# gh repo create YOUR_USERNAME/$new_repo_name --private --source=. --remote=origin --description="Description of your book" # Add description as needed.
# gh repo create YOUR_USERNAME/$new_repo_name --public --source=. --remote=origin --description="Description of your book" # Use for public repo.

exit 0