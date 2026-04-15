# 从YouTube视频下载字幕 (PowerShell 版本)
# 用法: .\download_subtitles.ps1 -Url <YouTube_URL> [-OutputDir <输出目录>]
# 语言优先级：中文 > 英文 > 其他

param (
    [Parameter(Mandatory=$true)]
    [string]$Url,
    [string]$OutputDir = "."
)

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

Write-Host ">>> 检查可用字幕..." -ForegroundColor Cyan
yt-dlp --list-subs --no-download $Url

Write-Host "`n>>> 尝试下载人工字幕 (中文优先)..." -ForegroundColor Cyan

# 尝试1: 人工中文字幕
$proc = Start-Process yt-dlp -ArgumentList "--write-subs", "--sub-langs", "'zh-Hans,zh-Hant,zh,zh-CN,zh-TW'", "--sub-format", "srt", "--skip-download", "-o", "'$OutputDir/%(title)s'", "'$Url'" -Wait -PassThru -NoNewWindow
if ($proc.ExitCode -eq 0) {
    Write-Host "✅ 中文人工字幕尝试完成。" -ForegroundColor Green
}

# 尝试2: 人工英文字幕
Write-Host ">>> 尝试人工英文字幕..." -ForegroundColor Cyan
$proc = Start-Process yt-dlp -ArgumentList "--write-subs", "--sub-langs", "'en,en-US,en-GB'", "--sub-format", "srt", "--skip-download", "-o", "'$OutputDir/%(title)s'", "'$Url'" -Wait -PassThru -NoNewWindow

# 尝试3: 自动生成字幕
Write-Host ">>> 尝试自动生成字幕..." -ForegroundColor Cyan
$proc = Start-Process yt-dlp -ArgumentList "--write-auto-subs", "--sub-langs", "'zh-Hans,zh,en'", "--sub-format", "srt", "--skip-download", "-o", "'$OutputDir/%(title)s'", "'$Url'" -Wait -PassThru -NoNewWindow

Write-Host "`n>>> 检查下载结果..." -ForegroundColor Cyan
$files = Get-ChildItem -Path $OutputDir -Filter "*.srt" | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-1) }
if ($files) {
    foreach ($file in $files) {
        Write-Host "✅ 下载成功: $($file.FullName)" -ForegroundColor Green
    }
} else {
    Write-Host "❌ 未找到新下载的字幕文件。" -ForegroundColor Red
}
