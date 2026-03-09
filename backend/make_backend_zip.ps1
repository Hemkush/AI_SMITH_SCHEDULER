# PowerShell script to create a deployable ZIP for Elastic Beanstalk
# Run from inside the backend folder:
#   ./make_backend_zip.ps1

$zipName = "backend-app.zip"
$cwd = Get-Location
Write-Host "Creating $zipName from $cwd"

# Remove existing zip if present
if (Test-Path $zipName) { Remove-Item $zipName -Force }

# Patterns to exclude (can include wildcards like *.pyc)
$exclude = @('venv','__pycache__','*.pyc','.git','backend-app.zip')

# Collect all files recursively
$allFiles = Get-ChildItem -Recurse -File

# Filter files using safe -like wildcard matching instead of -match (regex)
$includeFiles = @()
foreach ($f in $allFiles) {
    $path = $f.FullName
    $name = $f.Name
    $skip = $false
    foreach ($pattern in $exclude) {
        if ($pattern -like '*[*?]*') {
            # pattern contains wildcard: compare against file name and full path
            if ($name -like $pattern -or $path -like $pattern) { $skip = $true; break }
        } else {
            # no wildcard: check if pattern appears in the path or equals the file/dir name
            if ($path -like "*$pattern*" -or $name -eq $pattern) { $skip = $true; break }
        }
    }
    if (-not $skip) { $includeFiles += $path }
}

if ($includeFiles.Count -eq 0) {
    Write-Error "No files found to zip. Ensure you run this script from the backend folder."
    exit 1
}

# Create ZIP using Compress-Archive with explicit file list (avoids including excluded files)
try {
    Compress-Archive -Path $includeFiles -DestinationPath $zipName -Force
    Write-Host "Created $zipName with $($includeFiles.Count) files"
} catch {
    Write-Error "Failed to create ZIP: $_"
    exit 1
}
