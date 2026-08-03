#Requires -Version 5.1
<#
.SYNOPSIS
  Explorer sag tik menusune "Formata donustur" ekler (HKCU).
  Tek ust madde; tiklaninca secim penceresi acilir.
#>
$ErrorActionPreference = "Stop"

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$batPath = Join-Path $projectDir "convert.bat"

if (-not (Test-Path -LiteralPath $batPath)) {
    Write-Error "convert.bat bulunamadi: $batPath"
}

function T([int[]]$codes) {
    -join ($codes | ForEach-Object { [char]$_ })
}

# Formata dönüştür
$menuLabel = "Formata d" + (T 0x00F6) + "n" + (T 0x00FC,0x015F) + "t" + (T 0x00FC) + "r"
$extensions = @(".png", ".jpg", ".jpeg", ".webp", ".avif")
$verbName = "ImageFormatConvert"
$command = "`"$batPath`" `"%1`""

# Eski CommandStore kalintilarini temizle
$storeRoot = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell"
foreach ($name in @("fileconv.ToPng", "fileconv.ToJpeg", "fileconv.ToWebp")) {
    $path = Join-Path $storeRoot $name
    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path -Recurse -Force
    }
}

foreach ($ext in $extensions) {
    $base = "HKCU:\Software\Classes\SystemFileAssociations\$ext\shell\$verbName"

    if (Test-Path -LiteralPath $base) {
        Remove-Item -LiteralPath $base -Recurse -Force
    }

    $cmdKey = Join-Path $base "command"
    New-Item -Path $base -Force | Out-Null
    New-Item -Path $cmdKey -Force | Out-Null

    Set-ItemProperty -Path $base -Name "(default)" -Value $menuLabel
    Set-ItemProperty -Path $base -Name "MUIVerb" -Value $menuLabel
    Set-ItemProperty -Path $base -Name "MultiSelectModel" -Value "Player"
    Set-ItemProperty -Path $cmdKey -Name "(default)" -Value $command

    Write-Host "Eklendi: $ext"
}

Write-Host ""
Write-Host "Kurulum tamamlandi. Explorer'i yeniden baslatmaniz gerekebilir."
Write-Host ("Menu metni: " + $menuLabel)
