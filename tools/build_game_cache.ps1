[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$GameRoot,

    [Parameter(Mandatory = $false)]
    [string]$OutputRoot,

    [Parameter(Mandatory = $false)]
    [string]$PortalRoot
)

$ErrorActionPreference = 'Stop'
$PortVersion = '0.985'
$ReleaseRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$OverlayRoot = Join-Path $ReleaseRoot 'vr_game_resources'
$OverlaySrceng = Join-Path $OverlayRoot 'srceng'
$OverlayManifest = Join-Path $OverlayRoot 'MANIFEST.sha256'

function Resolve-HL2Root {
    param([Parameter(Mandatory = $true)][string]$Candidate)

    $expanded = [Environment]::ExpandEnvironmentVariables($Candidate.Trim().Trim('"'))
    if ([string]::IsNullOrWhiteSpace($expanded)) {
        throw 'The Portal path is empty.'
    }
    if ([string]::IsNullOrWhiteSpace($expanded)) {
        throw 'The Half-Life 2 path is empty.'
    }

    $resolved = [IO.Path]::GetFullPath($expanded)
    if ((Test-Path -LiteralPath (Join-Path $resolved 'hl2\gameinfo.txt') -PathType Leaf) -and
        (Test-Path -LiteralPath (Join-Path $resolved 'platform') -PathType Container)) {
        return $resolved.TrimEnd('\')
    }

    if ((Split-Path -Leaf $resolved) -ieq 'hl2' -and
        (Test-Path -LiteralPath (Join-Path $resolved 'gameinfo.txt') -PathType Leaf)) {
        $parent = Split-Path -Parent $resolved
        if (Test-Path -LiteralPath (Join-Path $parent 'platform') -PathType Container) {
            return $parent.TrimEnd('\')
        }
    }

    throw "Not a Half-Life 2 root: $resolved`nExpected hl2\gameinfo.txt and platform\."
}

function Resolve-PortalRoot {
    param([Parameter(Mandatory = $true)][string]$Candidate)

    $expanded = [Environment]::ExpandEnvironmentVariables($Candidate.Trim().Trim('"'))
    $resolved = [IO.Path]::GetFullPath($expanded)
    if ((Test-Path -LiteralPath (Join-Path $resolved 'portal\gameinfo.txt') -PathType Leaf) -and
        (Test-Path -LiteralPath (Join-Path $resolved 'hl2') -PathType Container) -and
        (Test-Path -LiteralPath (Join-Path $resolved 'platform') -PathType Container)) {
        return $resolved.TrimEnd('\')
    }
    throw "Not a Portal root: $resolved`nExpected portal\gameinfo.txt, hl2 and platform."
}

function Invoke-RobocopyPackage {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [Parameter(Mandatory = $true)][string[]]$ExcludedDirectories
    )

    $arguments = @(
        $Source,
        $Destination,
        '/E',
        '/COPY:DAT',
        '/DCOPY:DAT',
        '/R:2',
        '/W:1',
        '/XJ',
        '/NFL',
        '/NDL',
        '/NP',
        '/XF', '*.dll', '*.exe', '*.pdb', '*.dmp', '*.mdmp', '*.log',
        'config.cfg', 'video.txt', 'videodefaults.txt', 'voice_ban.dt'
    )

    if ($ExcludedDirectories.Count -gt 0) {
        $arguments += '/XD'
        $arguments += $ExcludedDirectories
    }

    & robocopy.exe @arguments
    $code = $LASTEXITCODE
    if ($code -gt 7) {
        throw "robocopy failed for $Source (exit code $code)."
    }
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)

    $stream = [IO.File]::OpenRead($Path)
    try {
        $sha256 = [Security.Cryptography.SHA256]::Create()
        try {
            return ([BitConverter]::ToString($sha256.ComputeHash($stream))).Replace('-', '')
        }
        finally {
            $sha256.Dispose()
        }
    }
    finally {
        $stream.Dispose()
    }
}

function Test-OverlayManifest {
    if (-not (Test-Path -LiteralPath $OverlaySrceng -PathType Container)) {
        throw "VR resource directory is missing: $OverlaySrceng"
    }
    if (-not (Test-Path -LiteralPath $OverlayManifest -PathType Leaf)) {
        throw "VR resource checksum manifest is missing: $OverlayManifest"
    }

    $verified = 0
    foreach ($line in [IO.File]::ReadAllLines($OverlayManifest)) {
        $trimmed = $line.Trim()
        if ($trimmed.Length -eq 0 -or $trimmed.StartsWith('#')) {
            continue
        }
        if ($trimmed -notmatch '^([0-9A-Fa-f]{64})\s{2}(.+)$') {
            throw "Invalid VR resource manifest line: $line"
        }

        $expected = $Matches[1]
        $relative = $Matches[2].Replace('/', '\')
        $path = Join-Path $OverlayRoot $relative
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "VR resource is missing: $relative"
        }
        $actual = Get-Sha256 -Path $path
        if ($actual -ine $expected) {
            throw "VR resource checksum mismatch: $relative"
        }
        $verified++
    }

    if ($verified -eq 0) {
        throw 'The VR resource manifest contains no files.'
    }
    Write-Host "Verified VR resources: $verified files" -ForegroundColor Green
}

function Enable-VRSupport {
    param([Parameter(Mandatory = $true)][string]$GameInfo)

    $text = [IO.File]::ReadAllText($GameInfo)
    if ($text -match '(?im)^\s*supportsvr\s+') {
        $text = [Text.RegularExpressions.Regex]::Replace(
            $text,
            '(?im)^(\s*supportsvr\s+).*$',
            '${1}1',
            1
        )
    }
    else {
        $match = [Text.RegularExpressions.Regex]::Match(
            $text,
            '(?im)^(\s*)type\s+singleplayer_only\s*$'
        )
        if (-not $match.Success) {
            throw "Cannot add supportsvr to $GameInfo"
        }
        $newline = if ($text.Contains("`r`n")) { "`r`n" } else { "`n" }
        $replacement = $match.Value + $newline + $match.Groups[1].Value + "supportsvr`t1"
        $text = $text.Substring(0, $match.Index) + $replacement +
            $text.Substring($match.Index + $match.Length)
    }

    [IO.File]::WriteAllText($GameInfo, $text, [Text.UTF8Encoding]::new($false))
}

function Set-PortalGameInfo {
    param([Parameter(Mandatory = $true)][string]$GameInfo)

    $text = @'
"GameInfo"
{
    game "Portal"
    title "Portal"
    type singleplayer_only
    nodifficulty 1
    hasportals 1
    supportsvr 1
    FileSystem
    {
        SteamAppId 400
        SearchPaths
        {
            game+mod "portal/custom/*"
            game "hl2/custom/*"
            game+mod "portal/portal_sound_vo_russian.vpk"
            game+mod "portal/portal_sound_vo_english.vpk"
            game+mod "portal/portal_pak.vpk"
            game "portal_hl2/hl2_textures.vpk"
            game "portal_hl2/hl2_sound_vo_russian.vpk"
            game "portal_hl2/hl2_sound_vo_english.vpk"
            game "portal_hl2/hl2_sound_misc.vpk"
            game "portal_hl2/hl2_misc.vpk"
            platform "portal_platform/platform_misc.vpk"
            mod+mod_write+default_write_path "|gameinfo_path|."
            game+game_write "portal"
            gamebin "portal/bin"
            game "portal_hl2"
            game "hl2"
            platform "portal_platform"
            platform "platform"
        }
    }
}
'@
    [IO.File]::WriteAllText($GameInfo, $text + "`n", [Text.UTF8Encoding]::new($false))
}

try {
    Write-Host 'Half-Life 2 VR Standalone 0.985' -ForegroundColor Yellow
    Write-Host 'The sources must be legal Half-Life 2 and optional Portal installations.'
    Write-Host ''

    if ([string]::IsNullOrWhiteSpace($GameRoot)) {
        $GameRoot = Read-Host 'Enter the Half-Life 2 root path (the folder containing hl2 and platform)'
    }
    $GameRoot = Resolve-HL2Root -Candidate $GameRoot

    if ([string]::IsNullOrWhiteSpace($PortalRoot)) {
        $autoPortal = Join-Path (Split-Path -Parent $GameRoot) 'Portal'
        if (Test-Path -LiteralPath (Join-Path $autoPortal 'portal\gameinfo.txt') -PathType Leaf) {
            $PortalRoot = $autoPortal
            Write-Host "Portal found automatically: $PortalRoot"
        }
        else {
            $PortalRoot = Read-Host 'Enter the Portal root path, or leave blank to build without Portal 1'
        }
    }
    if (-not [string]::IsNullOrWhiteSpace($PortalRoot)) {
        $PortalRoot = Resolve-PortalRoot -Candidate $PortalRoot
    }

    if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
        $OutputRoot = Join-Path $ReleaseRoot 'game_cache'
    }
    $OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
    $SrcengRoot = Join-Path $OutputRoot 'srceng'

    if ($OutputRoot -eq $GameRoot -or $OutputRoot.StartsWith($GameRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or
        (-not [string]::IsNullOrWhiteSpace($PortalRoot) -and
         ($OutputRoot -eq $PortalRoot -or $OutputRoot.StartsWith($PortalRoot + '\', [StringComparison]::OrdinalIgnoreCase)))) {
        throw 'The output cache must not be inside a game installation.'
    }
    if ((Split-Path -Leaf $SrcengRoot) -ine 'srceng' -or
        (Split-Path -Parent $SrcengRoot) -ine $OutputRoot) {
        throw "Unsafe generated-cache path: $SrcengRoot"
    }

    Test-OverlayManifest

    if (Test-Path -LiteralPath $SrcengRoot) {
        $answer = Read-Host "The existing cache will be replaced: $SrcengRoot`nContinue? [y/N]"
        if ($answer -notmatch '^(?i:y|yes)$') {
            Write-Host 'Cancelled.'
            exit 1
        }
        Remove-Item -LiteralPath $SrcengRoot -Recurse -Force
    }

    New-Item -ItemType Directory -Path $SrcengRoot -Force | Out-Null
    Write-Host "Source: $GameRoot"
    Write-Host "Output: $SrcengRoot"
    Write-Host 'Copying Half-Life 2 files...'

    $platformSource = Join-Path $GameRoot 'platform'
    $commonExcluded = @('bin', 'download', 'downloads', 'logs', 'save', 'screenshots')
    $platformExcluded = @($commonExcluded | ForEach-Object { Join-Path $platformSource $_ })
    $campaignNames = [ordered]@{
        hl2 = 'Half-Life 2'
        lostcoast = 'Lost Coast'
        episodic = 'Episode One'
        ep2 = 'Episode Two'
    }
    $copiedCampaigns = [Collections.Generic.List[string]]::new()

    foreach ($campaign in $campaignNames.GetEnumerator()) {
        $gameSource = Join-Path $GameRoot $campaign.Key
        $gameInfo = Join-Path $gameSource 'gameinfo.txt'
        if (-not (Test-Path -LiteralPath $gameInfo -PathType Leaf)) {
            if ($campaign.Key -eq 'hl2') {
                throw "Required Half-Life 2 gameinfo is missing: $gameInfo"
            }
            Write-Host ("Skipping {0}: {1}\gameinfo.txt was not found." -f `
                $campaign.Value, $campaign.Key) -ForegroundColor DarkYellow
            continue
        }

        Write-Host ("Copying {0}..." -f $campaign.Value)
        $excluded = @($commonExcluded | ForEach-Object { Join-Path $gameSource $_ })
        $excluded += (Join-Path $gameSource 'custom')
        Invoke-RobocopyPackage -Source $gameSource `
            -Destination (Join-Path $SrcengRoot $campaign.Key) `
            -ExcludedDirectories $excluded
        $copiedCampaigns.Add($campaign.Key)
    }
    Invoke-RobocopyPackage -Source $platformSource -Destination (Join-Path $SrcengRoot 'platform') -ExcludedDirectories $platformExcluded

    if (-not [string]::IsNullOrWhiteSpace($PortalRoot)) {
        Write-Host 'Copying Portal 1 into the shared cache...'
        foreach ($mapping in @(
            @{ Source = 'portal'; Destination = 'portal' },
            @{ Source = 'hl2'; Destination = 'portal_hl2' },
            @{ Source = 'platform'; Destination = 'portal_platform' }
        )) {
            $portalSource = Join-Path $PortalRoot $mapping.Source
            $excluded = @($commonExcluded | ForEach-Object { Join-Path $portalSource $_ })
            if ($mapping.Source -ne 'platform') { $excluded += (Join-Path $portalSource 'custom') }
            Invoke-RobocopyPackage -Source $portalSource `
                -Destination (Join-Path $SrcengRoot $mapping.Destination) `
                -ExcludedDirectories $excluded
        }
        Set-PortalGameInfo -GameInfo (Join-Path $SrcengRoot 'portal\gameinfo.txt')
        $copiedCampaigns.Add('portal')
    }

    Write-Host 'Applying HL2Q3VR resources...'
    Copy-Item -Path (Join-Path $OverlaySrceng '*') -Destination $SrcengRoot -Recurse -Force
    foreach ($campaign in $copiedCampaigns) {
        Enable-VRSupport -GameInfo (Join-Path $SrcengRoot "$campaign\gameinfo.txt")
    }

    $files = Get-ChildItem -LiteralPath $SrcengRoot -Recurse -File
    $manifest = [ordered]@{
        format = 2
        port = 'HL2Q3VR'
        port_version = $PortVersion
        campaigns = @($copiedCampaigns)
        lost_coast_supported = $true
        episodes_supported = $true
        portal_supported = $copiedCampaigns.Contains('portal')
        generated_utc = [DateTime]::UtcNow.ToString('o')
        source_folder_name = Split-Path -Leaf $GameRoot
        file_count = @($files).Count
        size_bytes = ($files | Measure-Object -Property Length -Sum).Sum
        headset_destination = '/sdcard/srceng'
    }
    $manifestPath = Join-Path $OutputRoot 'hl2q3vr-cache.json'
    [IO.File]::WriteAllText(
        $manifestPath,
        (($manifest | ConvertTo-Json -Depth 4) + "`n"),
        [Text.UTF8Encoding]::new($false)
    )

    Write-Host ''
    Write-Host "Cache ready: $SrcengRoot" -ForegroundColor Green
    Write-Host 'Quest destination: /sdcard/srceng'
    exit 0
}
catch {
    Write-Host ''
    Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red
    exit 2
}
