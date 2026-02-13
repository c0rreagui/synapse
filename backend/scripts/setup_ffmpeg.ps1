# PowerShell Script to Setup FFmpeg Locally
$ErrorActionPreference = "Stop"

$BaseDir = Resolve-Path ".."
$BinDir = "$BaseDir\bin"
$ZipPath = "$BaseDir\ffmpeg.zip"
$ExtractPath = "$BaseDir\ffmpeg_temp"

# Create bin directory
if (-not (Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir | Out-Null
    Write-Host "Created $BinDir"
}

# Check if ffmpeg.exe exists
if (Test-Path "$BinDir\ffmpeg.exe") {
    Write-Host "FFmpeg already installed in $BinDir"
    exit 0
}

# Download FFmpeg (Essentials Build)
$Url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
Write-Host "Downloading FFmpeg from $Url..."
Invoke-WebRequest -Uri $Url -OutFile $ZipPath

# Extract
Write-Host "Extracting..."
Expand-Archive -Path $ZipPath -DestinationPath $ExtractPath -Force

# Find ffmpeg.exe and move
$FFmpegExe = Get-ChildItem -Path $ExtractPath -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
if ($FFmpegExe) {
    Move-Item -Path $FFmpegExe.FullName -Destination "$BinDir\ffmpeg.exe" -Force
    Write-Host "Installed FFmpeg to $BinDir\ffmpeg.exe"
} else {
    Write-Error "Could not find ffmpeg.exe in downloaded zip"
}

# Find ffprobe.exe and move
$FFprobeExe = Get-ChildItem -Path $ExtractPath -Recurse -Filter "ffprobe.exe" | Select-Object -First 1
if ($FFprobeExe) {
    Move-Item -Path $FFprobeExe.FullName -Destination "$BinDir\ffprobe.exe" -Force
    Write-Host "Installed FFprobe to $BinDir\ffprobe.exe"
}

# Cleanup
Remove-Item -Path $ZipPath -Force
Remove-Item -Path $ExtractPath -Recurse -Force

Write-Host "FFmpeg setup complete."
