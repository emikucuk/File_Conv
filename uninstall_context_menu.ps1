#Requires -Version 5.1
<#
.SYNOPSIS
  Explorer sag tik menusunden "Formata donustur" kaydini kaldirir (HKCU).
  TinyPNG (TinyPNGCompress) kayitlarina dokunmaz.
#>
$ErrorActionPreference = "Stop"

$extensions = @(".png", ".jpg", ".jpeg", ".webp")
$verbName = "ImageFormatConvert"
$storeNames = @("fileconv.ToPng", "fileconv.ToJpeg", "fileconv.ToWebp")
$storeRoot = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell"

foreach ($ext in $extensions) {
    $base = "HKCU:\Software\Classes\SystemFileAssociations\$ext\shell\$verbName"
    if (Test-Path -LiteralPath $base) {
        Remove-Item -LiteralPath $base -Recurse -Force
        Write-Host "Kaldirildi: $ext"
    }
    else {
        Write-Host "Yok (atlandi): $ext"
    }
}

foreach ($name in $storeNames) {
    $path = Join-Path $storeRoot $name
    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path -Recurse -Force
        Write-Host "CommandStore kaldirildi: $name"
    }
}

Write-Host ""
Write-Host "Kaldirma tamamlandi."
