# PowerShell script to remove sensitive files from the working tree.
# Run from repository root. This only removes files from the index and commits the change.

Write-Output "Removing sensitive/tracked generated files from the index..."

# Remove .env
try { git rm --cached .env -f 2>$null; Write-Output "Removed .env" } catch { Write-Output ".env not tracked or already removed" }

# Remove .venv
try { git rm --cached -r .venv -f 2>$null; Write-Output "Removed .venv" } catch { Write-Output ".venv not tracked or already removed" }

# Remove staticfiles
try { git rm --cached -r staticfiles -f 2>$null; Write-Output "Removed staticfiles" } catch { Write-Output "staticfiles not tracked or already removed" }

# Remove logs
try { git rm --cached server.log server_error.log -f 2>$null; Write-Output "Removed logs" } catch { Write-Output "Logs not tracked or already removed" }

Write-Output "`nCommitting removals (local only)..."
git commit -m "chore: remove sensitive and generated files from repository"

Write-Output "`nNEXT (manual): To completely purge these files from git history, use git-filter-repo:"
Write-Output "  pip install git-filter-repo"
Write-Output "  git filter-repo --path .env --path staticfiles --path server.log --path server_error.log --invert-paths"
Write-Output "  git push --force"
Write-Output "`nAfter history rewrite: inform collaborators to re-clone. Rotate secrets immediately."