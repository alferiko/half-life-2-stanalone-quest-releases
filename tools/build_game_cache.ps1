[CmdletBinding()]
param(
    [string]$GameRoot,
    [string]$PortalRoot,
    [string]$Portal2Root,
    [string]$ApkPath,
    [string]$OutputRoot,
    [string]$Language = 'english',
    [switch]$Plan,
    [switch]$Interactive
)
$ErrorActionPreference = 'Stop'
$python = $null
$prefix = @()
foreach ($candidate in @(
    @{ Name = 'py'; Prefix = @('-3') },
    @{ Name = 'python'; Prefix = @() },
    @{ Name = 'python3'; Prefix = @() }
)) {
    $command = Get-Command $candidate.Name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $command) { continue }
    $probe = @($candidate.Prefix) + @('-c', 'import sys,lzma,zipfile; sys.exit(sys.version_info < (3,10))')
    & $command.Source @probe
    if ($LASTEXITCODE -eq 0) {
        $python = $command.Source
        $prefix = @($candidate.Prefix)
        break
    }
}
if ($null -eq $python) {
    Write-Error 'Python 3.10+ with standard-library LZMA is required. Install Python from python.org, then retry. No pip packages are needed.'
    exit 2
}
$arguments = $prefix + @('-B', '-X', 'utf8', (Join-Path $PSScriptRoot 'build_game_cache.py'), '--language', $Language)
foreach ($option in @(
    @{ Flag = '--hl2-root'; Value = $GameRoot },
    @{ Flag = '--portal-root'; Value = $PortalRoot },
    @{ Flag = '--portal2-root'; Value = $Portal2Root },
    @{ Flag = '--apk'; Value = $ApkPath },
    @{ Flag = '--output-root'; Value = $OutputRoot }
)) {
    if (-not [string]::IsNullOrWhiteSpace($option.Value)) { $arguments += @($option.Flag, $option.Value) }
}
if ($Plan) { $arguments += '--plan' }
if ($Interactive) { $arguments += '--interactive' }
& $python @arguments
exit $LASTEXITCODE
