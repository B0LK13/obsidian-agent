# 

A comprehensive Rainmeter configuration that transforms your Windows desktop into a unified **NEXUS PRIME Operations Center**, perfectly synchronized with your PowerShell, ZSH, and CMD terminal configurations.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    TBA SINGULARITY OS RAINMETER SUITE                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │   SYSTEM    │ │   NETWORK   │ │   THREAT    │ │  SERVICES   │ │   CLOCK   │ │
│  │    GRID     │ │   OPSEC     │ │   INTEL     │ │   MATRIX    │ │   PANEL   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │    DISK     │ │    GPU      │ │   PROCESS   │ │   WEATHER   │ │  SPOTIFY  │ │
│  │   STORAGE   │ │   MONITOR   │ │   SCANNER   │ │    INTEL    │ │  CONTROL  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
├─────────────────────────────────────────────────────────────────────────────────┤
│                         @Resources (Shared Assets)                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │  Variables  │ │   Styles    │ │   Scripts   │ │    Fonts    │               │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘               │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
Documents\Rainmeter\Skins\TheBlackAgency\
├── @Resources\
│   ├── Variables.inc
│   ├── Styles.inc
│   ├── Scripts\
│   │   ├── ThreatFeed.lua
│   │   ├── ServiceMonitor.lua
│   │   └── SystemInfo.lua
│   ├── Fonts\
│   │   └── (JetBrains Mono, etc.)
│   └── Images\
│       ├── logo.png
│       └── icons\
├── System\
│   └── System.ini
├── Network\
│   └── Network.ini
├── ThreatIntel\
│   └── ThreatIntel.ini
├── Services\
│   └── Services.ini
├── Clock\
│   └── Clock.ini
├── Disk\
│   └── Disk.ini
├── GPU\
│   └── GPU.ini
├── Process\
│   └── Process.ini
├── Weather\
│   └── Weather.ini
├── Spotify\
│   └── Spotify.ini
├── Visualizer\
│   └── Visualizer.ini
└── Launcher\
    └── Launcher.ini
```

---

## 1. Core Variables: `@Resources\Variables.inc`

```ini
[Variables]
; ╔════════════════════════════════════════════════════════════════════════════╗
; ║  TBA SINGULARITY OS — CORE VARIABLES V10                                   ║
; ║  Synchronized with PowerShell/ZSH/CMD Terminal Configurations              ║
; ╚════════════════════════════════════════════════════════════════════════════╝

; ══════════════════════════════════════════════════════════════════════════════
; COLOR PALETTE (TBA-NEXUS-PRIME)
; ══════════════════════════════════════════════════════════════════════════════

; Primary Colors
ColorVirtuRed=255,23,68
ColorVoidBlack=10,10,12
ColorNexusCyan=0,229,255

; Secondary Colors
ColorCarbon=18,19,23
ColorSteel=104,110,120
ColorChrome=176,180,186
ColorGhost=230,230,230

; Accent Colors
ColorWarning=255,214,0
ColorSuccess=0,230,118
ColorError=255,23,68
ColorInfo=41,121,255
ColorMagenta=213,0,249

; Background Colors (with alpha)
ColorBgVoid=10,10,12,230
ColorBgCarbon=18,19,23,220
ColorBgPanel=15,15,18,240
ColorBgHover=30,30,35,250

; Gradient Colors
ColorGradientStart=255,23,68
ColorGradientMid=213,0,249
ColorGradientEnd=0,229,255

; ══════════════════════════════════════════════════════════════════════════════
; TYPOGRAPHY
; ══════════════════════════════════════════════════════════════════════════════

; Primary Font (Install JetBrains Mono or CaskaydiaCove NF)
FontFace=JetBrains Mono
FontFaceAlt=Consolas
FontFaceMono=CaskaydiaCove Nerd Font

; Font Sizes
FontSizeXL=16
FontSizeLG=12
FontSizeMD=10
FontSizeSM=9
FontSizeXS=8

; Font Weights
FontWeightBold=600
FontWeightNormal=400
FontWeightLight=300

; ══════════════════════════════════════════════════════════════════════════════
; DIMENSIONS & SPACING
; ══════════════════════════════════════════════════════════════════════════════

; Module Widths
WidthSmall=200
WidthMedium=280
WidthLarge=350
WidthXL=450

; Heights
BarHeight=4
BarHeightMedium=6
BarHeightLarge=8
GraphHeight=40
GraphHeightLarge=60

; Spacing
PaddingXS=5
PaddingSM=8
PaddingMD=12
PaddingLG=16
PaddingXL=20

; Margins
MarginSM=5
MarginMD=10
MarginLG=15

; Border
BorderRadius=3
BorderWidth=1

; ══════════════════════════════════════════════════════════════════════════════
; ANIMATION & TIMING
; ══════════════════════════════════════════════════════════════════════════════

UpdateRateFast=500
UpdateRateNormal=1000
UpdateRateSlow=5000
UpdateRateVerySlow=60000

FadeInDuration=150
FadeOutDuration=100

; ══════════════════════════════════════════════════════════════════════════════
; NETWORK & API CONFIGURATION
; ══════════════════════════════════════════════════════════════════════════════

; External IP Services (fallback chain)
IPServicePrimary=https://api.ipify.org
IPServiceSecondary=https://ifconfig.me/ip
IPServiceTertiary=https://checkip.amazonaws.com

; Weather API (OpenWeatherMap - get free key at openweathermap.org)
WeatherAPIKey=YOUR_API_KEY_HERE
WeatherCity=Amsterdam
WeatherUnits=metric

; Threat Intelligence Feeds
ThreatFeedHackerNews=https://feeds.feedburner.com/TheHackersNews
ThreatFeedCVE=https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml
ThreatFeedBleeping=https://www.bleepingcomputer.com/feed/

; ══════════════════════════════════════════════════════════════════════════════
; SERVICE MONITORING
; ══════════════════════════════════════════════════════════════════════════════

; Local Services
OllamaHost=localhost
OllamaPort=11434

DockerProcess=com.docker.backend.exe
WSLProcess=wsl.exe

; ══════════════════════════════════════════════════════════════════════════════
; DISPLAY SETTINGS
; ══════════════════════════════════════════════════════════════════════════════

; Monitor (for multi-monitor setups)
; 0 = Primary, 1 = Secondary, etc.
TargetMonitor=0

; Skin Position (percentage from edge)
PositionX=@0
PositionY=100

; Scale Factor (for HiDPI displays)
; 1.0 = 100%, 1.25 = 125%, 1.5 = 150%, 2.0 = 200%
ScaleFactor=1.0

; ══════════════════════════════════════════════════════════════════════════════
; BEHAVIOR FLAGS
; ══════════════════════════════════════════════════════════════════════════════

; Hide when fullscreen app detected (1 = yes, 0 = no)
HideOnFullscreen=1

; Auto-hide IP address (1 = masked by default)
MaskIPAddress=1

; Enable glitch effects (1 = yes, 0 = no)
EnableGlitchFX=1

; Threat feed auto-scroll (1 = yes, 0 = no)
ThreatAutoScroll=1
```

---

## 2. Shared Styles: `@Resources\Styles.inc`

```ini
; ╔════════════════════════════════════════════════════════════════════════════╗
; ║  TBA SINGULARITY OS — SHARED STYLES V10                                    ║
; ╚════════════════════════════════════════════════════════════════════════════╝

; ══════════════════════════════════════════════════════════════════════════════
; TEXT STYLES
; ══════════════════════════════════════════════════════════════════════════════

[StyleTextBase]
FontFace=#FontFace#
FontSize=#FontSizeMD#
FontColor=#ColorGhost#
AntiAlias=1
ClipString=1

[StyleTextTitle]
FontFace=#FontFace#
FontSize=#FontSizeLG#
FontColor=#ColorVirtuRed#
FontWeight=#FontWeightBold#
AntiAlias=1
StringCase=Upper

[StyleTextHeader]
FontFace=#FontFace#
FontSize=#FontSizeMD#
FontColor=#ColorVirtuRed#
FontWeight=#FontWeightBold#
AntiAlias=1

[StyleTextLabel]
FontFace=#FontFace#
FontSize=#FontSizeXS#
FontColor=#ColorSteel#
StringCase=Upper
AntiAlias=1

[StyleTextValue]
FontFace=#FontFace#
FontSize=#FontSizeMD#
FontColor=#ColorGhost#
AntiAlias=1

[StyleTextValueLarge]
FontFace=#FontFace#
FontSize=#FontSizeLG#
FontColor=#ColorGhost#
FontWeight=#FontWeightBold#
AntiAlias=1

[StyleTextHighlight]
FontFace=#FontFace#
FontSize=#FontSizeMD#
FontColor=#ColorNexusCyan#
AntiAlias=1

[StyleTextWarning]
FontFace=#FontFace#
FontSize=#FontSizeMD#
FontColor=#ColorWarning#
AntiAlias=1

[StyleTextSuccess]
FontFace=#FontFace#
FontSize=#FontSizeMD#
FontColor=#ColorSuccess#
AntiAlias=1

[StyleTextError]
FontFace=#FontFace#
FontSize=#FontSizeMD#
FontColor=#ColorError#
AntiAlias=1

[StyleTextMuted]
FontFace=#FontFace#
FontSize=#FontSizeXS#
FontColor=#ColorSteel#
AntiAlias=1

; ══════════════════════════════════════════════════════════════════════════════
; BAR STYLES
; ══════════════════════════════════════════════════════════════════════════════

[StyleBarBase]
BarColor=#ColorVirtuRed#
SolidColor=#ColorCarbon#
BarOrientation=Horizontal
H=#BarHeight#

[StyleBarCyan]
BarColor=#ColorNexusCyan#
SolidColor=#ColorCarbon#
BarOrientation=Horizontal
H=#BarHeight#

[StyleBarSuccess]
BarColor=#ColorSuccess#
SolidColor=#ColorCarbon#
BarOrientation=Horizontal
H=#BarHeight#

[StyleBarWarning]
BarColor=#ColorWarning#
SolidColor=#ColorCarbon#
BarOrientation=Horizontal
H=#BarHeight#

; ══════════════════════════════════════════════════════════════════════════════
; HISTOGRAM STYLES
; ══════════════════════════════════════════════════════════════════════════════

[StyleHistogramRed]
PrimaryColor=#ColorVirtuRed#
SecondaryColor=#ColorVirtuRed#,80
SolidColor=#ColorCarbon#
AntiAlias=1
H=#GraphHeight#

[StyleHistogramCyan]
PrimaryColor=#ColorNexusCyan#
SecondaryColor=#ColorNexusCyan#,80
SolidColor=#ColorCarbon#
AntiAlias=1
H=#GraphHeight#

[StyleHistogramGreen]
PrimaryColor=#ColorSuccess#
SecondaryColor=#ColorSuccess#,80
SolidColor=#ColorCarbon#
AntiAlias=1
H=#GraphHeight#

[StyleHistogramMagenta]
PrimaryColor=#ColorMagenta#
SecondaryColor=#ColorMagenta#,80
SolidColor=#ColorCarbon#
AntiAlias=1
H=#GraphHeight#

; ══════════════════════════════════════════════════════════════════════════════
; SHAPE STYLES (Borders, Lines, Panels)
; ══════════════════════════════════════════════════════════════════════════════

[StyleLineTop]
Shape=Rectangle 0,0,(#WidthMedium#),2 | Fill Color #ColorVirtuRed# | StrokeWidth 0

[StyleLineBottom]
Shape=Rectangle 0,0,(#WidthMedium#),2 | Fill Color #ColorVirtuRed# | StrokeWidth 0

[StyleLineSeparator]
Shape=Rectangle 0,0,(#WidthMedium#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,100 | StrokeWidth 0

[StylePanel]
Shape=Rectangle 0,0,(#WidthMedium#),(#Height#),#BorderRadius# | Fill Color #ColorBgPanel# | Stroke Color #ColorSteel#,50 | StrokeWidth 1

; ══════════════════════════════════════════════════════════════════════════════
; INTERACTIVE STYLES
; ══════════════════════════════════════════════════════════════════════════════

[StyleButtonBase]
FontFace=#FontFace#
FontSize=#FontSizeSM#
FontColor=#ColorGhost#
SolidColor=#ColorCarbon#
AntiAlias=1
Padding=#PaddingSM#,#PaddingXS#,#PaddingSM#,#PaddingXS#
MouseOverAction=[!SetOption #CURRENTSECTION# SolidColor "#ColorBgHover#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
MouseLeaveAction=[!SetOption #CURRENTSECTION# SolidColor "#ColorCarbon#"][!UpdateMeter #CURRENTSECTION#][!Redraw]

[StyleButtonAccent]
FontFace=#FontFace#
FontSize=#FontSizeSM#
FontColor=#ColorVoidBlack#
SolidColor=#ColorVirtuRed#
AntiAlias=1
Padding=#PaddingSM#,#PaddingXS#,#PaddingSM#,#PaddingXS#
MouseOverAction=[!SetOption #CURRENTSECTION# SolidColor "#ColorNexusCyan#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
MouseLeaveAction=[!SetOption #CURRENTSECTION# SolidColor "#ColorVirtuRed#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
```

---

## 3. Enhanced System Module: `System\System.ini`

```ini
[Rainmeter]
Update=#UpdateRateNormal#
AccurateText=1
BackgroundMode=2
SolidColor=#ColorBgPanel#
DynamicWindowSize=1

[Metadata]
Name=TBA System Grid
Author=The Black Agency
Version=10.0
License=MIT

; ── INCLUDES ──
@Include=#@#Variables.inc
@Include2=#@#Styles.inc

; ══════════════════════════════════════════════════════════════════════════════
; FULLSCREEN DETECTION
; ══════════════════════════════════════════════════════════════════════════════

[MeasureFullScreen]
Measure=Plugin
Plugin=IsFullScreen
IfCondition=(MeasureFullScreen = 1) && (#HideOnFullscreen# = 1)
IfTrueAction=[!FadeDuration 100][!Hide]
IfFalseAction=[!FadeDuration 150][!Show]

; ══════════════════════════════════════════════════════════════════════════════
; SYSTEM MEASURES
; ══════════════════════════════════════════════════════════════════════════════

; ── CPU ──
[MeasureCPU]
Measure=CPU
Processor=0

[MeasureCPU1]
Measure=CPU
Processor=1

[MeasureCPU2]
Measure=CPU
Processor=2

[MeasureCPU3]
Measure=CPU
Processor=3

[MeasureCPU4]
Measure=CPU
Processor=4

[MeasureCPUTemp]
Measure=Plugin
Plugin=CoreTemp
CoreTempType=Temperature
CoreTempIndex=0
Substitute="":"N/A"

[MeasureCPUFreq]
Measure=Registry
RegHKey=HKEY_LOCAL_MACHINE
RegKey=HARDWARE\DESCRIPTION\System\CentralProcessor\0
RegValue=~MHz

; ── MEMORY ──
[MeasureRAM]
Measure=PhysicalMemory

[MeasureRAMUsed]
Measure=PhysicalMemory
InvertMeasure=0

[MeasureRAMTotal]
Measure=PhysicalMemory
Total=1

[MeasureRAMUsedGB]
Measure=Calc
Formula=MeasureRAMUsed / 1073741824
MinValue=0
MaxValue=([MeasureRAMTotal] / 1073741824)
DynamicVariables=1

[MeasureRAMTotalGB]
Measure=Calc
Formula=MeasureRAMTotal / 1073741824
DynamicVariables=1

; ── SWAP ──
[MeasureSWAP]
Measure=SwapMemory

[MeasureSWAPUsed]
Measure=SwapMemory
InvertMeasure=0

[MeasureSWAPTotal]
Measure=SwapMemory
Total=1

; ── UPTIME ──
[MeasureUptime]
Measure=Uptime
Format="%4!i!d %3!i!h %2!i!m"

; ── SYSTEM INFO ──
[MeasureOSVersion]
Measure=Registry
RegHKey=HKEY_LOCAL_MACHINE
RegKey=SOFTWARE\Microsoft\Windows NT\CurrentVersion
RegValue=ProductName

[MeasureOSBuild]
Measure=Registry
RegHKey=HKEY_LOCAL_MACHINE
RegKey=SOFTWARE\Microsoft\Windows NT\CurrentVersion
RegValue=CurrentBuild

; ══════════════════════════════════════════════════════════════════════════════
; VISUAL METERS
; ══════════════════════════════════════════════════════════════════════════════

; ── HEADER DECORATION ──
[MeterTopLine]
Meter=Shape
Shape=Rectangle 0,0,#WidthMedium#,3 | Fill Color #ColorVirtuRed# | StrokeWidth 0

[MeterTitle]
Meter=String
MeterStyle=StyleTextHeader
Text="╔══[ SYSTEM_TELEMETRY ]══╗"
X=#PaddingMD#
Y=8

[MeterSubtitle]
Meter=String
MeterStyle=StyleTextMuted
Text="NEXUS PRIME // HARDWARE MONITOR"
X=#PaddingMD#
Y=2R

; ── SEPARATOR ──
[MeterSep1]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthMedium#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,60 | StrokeWidth 0
Y=8R

; ══════════════════════════════════════════════════════════════════════════════
; CPU SECTION
; ══════════════════════════════════════════════════════════════════════════════

[MeterCPULabel]
Meter=String
MeterStyle=StyleTextLabel
Text="CPU_CORE_LOAD"
X=#PaddingMD#
Y=10R

[MeterCPUValue]
Meter=String
MeterStyle=StyleTextValueLarge
MeasureName=MeasureCPU
Text="%1%"
X=(#WidthMedium#-#PaddingMD#)
Y=0r
StringAlign=Right

[MeterCPUGraph]
Meter=Histogram
MeasureName=MeasureCPU
MeasureName2=MeasureCPU1
MeterStyle=StyleHistogramRed
X=#PaddingMD#
Y=5R
W=(#WidthMedium#-#PaddingMD#*2)
H=#GraphHeight#

; CPU Cores Mini-Bars
[MeterCPUCoreLabel]
Meter=String
MeterStyle=StyleTextMuted
Text="CORE DISTRIBUTION"
X=#PaddingMD#
Y=5R

[MeterCPUCore1]
Meter=Bar
MeasureName=MeasureCPU1
MeterStyle=StyleBarBase
X=#PaddingMD#
Y=3R
W=((#WidthMedium#-#PaddingMD#*2-15)/4)

[MeterCPUCore2]
Meter=Bar
MeasureName=MeasureCPU2
MeterStyle=StyleBarCyan
X=5R
Y=0r
W=((#WidthMedium#-#PaddingMD#*2-15)/4)

[MeterCPUCore3]
Meter=Bar
MeasureName=MeasureCPU3
MeterStyle=StyleBarBase
X=5R
Y=0r
W=((#WidthMedium#-#PaddingMD#*2-15)/4)

[MeterCPUCore4]
Meter=Bar
MeasureName=MeasureCPU4
MeterStyle=StyleBarCyan
X=5R
Y=0r
W=((#WidthMedium#-#PaddingMD#*2-15)/4)

; CPU Info Line
[MeterCPUInfo]
Meter=String
MeterStyle=StyleTextMuted
MeasureName=MeasureCPUFreq
MeasureName2=MeasureCPUTemp
Text="FREQ: %1 MHz │ TEMP: %2°C"
X=#PaddingMD#
Y=8R

; ── SEPARATOR ──
[MeterSep2]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthMedium#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,60 | StrokeWidth 0
Y=10R

; ══════════════════════════════════════════════════════════════════════════════
; MEMORY SECTION
; ══════════════════════════════════════════════════════════════════════════════

[MeterRAMLabel]
Meter=String
MeterStyle=StyleTextLabel
Text="MEMORY_ALLOCATION"
X=#PaddingMD#
Y=10R

[MeterRAMValue]
Meter=String
MeterStyle=StyleTextValueLarge
MeasureName=MeasureRAM
Text="%1%"
Percentual=1
X=(#WidthMedium#-#PaddingMD#)
Y=0r
StringAlign=Right

[MeterRAMGraph]
Meter=Histogram
MeasureName=MeasureRAM
MeterStyle=StyleHistogramCyan
X=#PaddingMD#
Y=5R
W=(#WidthMedium#-#PaddingMD#*2)
H=#GraphHeight#

[MeterRAMInfo]
Meter=String
MeterStyle=StyleTextMuted
MeasureName=MeasureRAMUsedGB
MeasureName2=MeasureRAMTotalGB
Text="USED: %1 GB / %2 GB"
NumOfDecimals=1
X=#PaddingMD#
Y=5R
DynamicVariables=1

; ── SEPARATOR ──
[MeterSep3]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthMedium#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,60 | StrokeWidth 0
Y=10R

; ══════════════════════════════════════════════════════════════════════════════
; SWAP SECTION
; ══════════════════════════════════════════════════════════════════════════════

[MeterSWAPLabel]
Meter=String
MeterStyle=StyleTextLabel
Text="SWAP_PARTITION"
X=#PaddingMD#
Y=10R

[MeterSWAPValue]
Meter=String
MeterStyle=StyleTextValue
MeasureName=MeasureSWAP
Text="%1%"
Percentual=1
X=(#WidthMedium#-#PaddingMD#)
Y=0r
StringAlign=Right

[MeterSWAPBar]
Meter=Bar
MeasureName=MeasureSWAP
MeterStyle=StyleBarWarning
X=#PaddingMD#
Y=5R
W=(#WidthMedium#-#PaddingMD#*2)
H=#BarHeightMedium#

; ── SEPARATOR ──
[MeterSep4]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthMedium#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,60 | StrokeWidth 0
Y=12R

; ══════════════════════════════════════════════════════════════════════════════
; SYSTEM INFO SECTION
; ══════════════════════════════════════════════════════════════════════════════

[MeterUptimeLabel]
Meter=String
MeterStyle=StyleTextLabel
Text="SYSTEM_UPTIME"
X=#PaddingMD#
Y=10R

[MeterUptimeValue]
Meter=String
MeterStyle=StyleTextHighlight
MeasureName=MeasureUptime
X=(#WidthMedium#-#PaddingMD#)
Y=0r
StringAlign=Right

[MeterOSLabel]
Meter=String
MeterStyle=StyleTextMuted
MeasureName=MeasureOSVersion
MeasureName2=MeasureOSBuild
Text="%1 (Build %2)"
X=#PaddingMD#
Y=5R
W=(#WidthMedium#-#PaddingMD#*2)
ClipString=2

; ── FOOTER ──
[MeterBottomLine]
Meter=Shape
Shape=Rectangle 0,0,#WidthMedium#,3 | Fill Color #ColorVirtuRed# | StrokeWidth 0
Y=12R
```

---

## 4. Enhanced Network Module: `Network\Network.ini`

```ini
[Rainmeter]
Update=#UpdateRateNormal#
AccurateText=1
BackgroundMode=2
SolidColor=#ColorBgPanel#
DynamicWindowSize=1

[Metadata]
Name=TBA Network OPSEC
Author=The Black Agency
Version=10.0

@Include=#@#Variables.inc
@Include2=#@#Styles.inc

; ══════════════════════════════════════════════════════════════════════════════
; FULLSCREEN DETECTION
; ══════════════════════════════════════════════════════════════════════════════

[MeasureFullScreen]
Measure=Plugin
Plugin=IsFullScreen
IfCondition=(MeasureFullScreen = 1) && (#HideOnFullscreen# = 1)
IfTrueAction=[!FadeDuration 100][!Hide]
IfFalseAction=[!FadeDuration 150][!Show]

; ══════════════════════════════════════════════════════════════════════════════
; NETWORK MEASURES
; ══════════════════════════════════════════════════════════════════════════════

; ── BANDWIDTH ──
[MeasureNetIn]
Measure=NetIn
Interface=Best
UseBits=1

[MeasureNetOut]
Measure=NetOut
Interface=Best
UseBits=1

[MeasureNetInMax]
Measure=Calc
Formula=MeasureNetIn
MinValue=0
MaxValue=1000000000

[MeasureNetOutMax]
Measure=Calc
Formula=MeasureNetOut
MinValue=0
MaxValue=1000000000

; ── TOTAL TRAFFIC (Session) ──
[MeasureNetInTotal]
Measure=NetIn
Interface=Best
Cumulative=1

[MeasureNetOutTotal]
Measure=NetOut
Interface=Best
Cumulative=1

; ── EXTERNAL IP ──
[MeasureWANIP]
Measure=WebParser
URL=#IPServicePrimary#
RegExp=(.*)
UpdateRate=3600
FinishAction=[!EnableMeasure MeasureWANIPBackup]
OnConnectErrorAction=[!EnableMeasure MeasureWANIPBackup]

[MeasureWANIPBackup]
Measure=WebParser
URL=#IPServiceSecondary#
RegExp=(.*)
UpdateRate=3600
Disabled=1

; ── LOCAL IP ──
[MeasureLANIP]
Measure=Plugin
Plugin=SysInfo
SysInfoType=IP_ADDRESS
SysInfoData=Best

; ── ADAPTER INFO ──
[MeasureAdapterName]
Measure=Plugin
Plugin=SysInfo
SysInfoType=ADAPTER_DESCRIPTION
SysInfoData=Best

; ── PING/LATENCY ──
[MeasurePing]
Measure=Plugin
Plugin=PingPlugin
DestAddress=8.8.8.8
UpdateRate=5
Timeout=2000
Substitute="":"---"

; ══════════════════════════════════════════════════════════════════════════════
; IP MASKING LOGIC
; ══════════════════════════════════════════════════════════════════════════════

[MeasureIPMasked]
Measure=Calc
IfCondition=#MaskIPAddress# = 1
IfTrueAction=[!SetOption MeterIPValue Text "***.***.***.***"]
IfFalseAction=[!SetOption MeterIPValue Text "[MeasureWANIP]"]
DynamicVariables=1

; ══════════════════════════════════════════════════════════════════════════════
; VISUAL METERS
; ══════════════════════════════════════════════════════════════════════════════

; ── HEADER ──
[MeterTopLine]
Meter=Shape
Shape=Rectangle 0,0,#WidthMedium#,3 | Fill Color #ColorNexusCyan# | StrokeWidth 0

[MeterTitle]
Meter=String
MeterStyle=StyleTextHeader
FontColor=#ColorNexusCyan#
Text="╔══[ NET_UPLINK ]══╗"
X=#PaddingMD#
Y=8

[MeterSubtitle]
Meter=String
MeterStyle=StyleTextMuted
Text="OPSEC MONITOR // TRAFFIC ANALYSIS"
X=#PaddingMD#
Y=2R

; ── SEPARATOR ──
[MeterSep1]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthMedium#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,60 | StrokeWidth 0
Y=8R

; ══════════════════════════════════════════════════════════════════════════════
; DOWNLOAD SECTION
; ══════════════════════════════════════════════════════════════════════════════

[MeterDLLabel]
Meter=String
MeterStyle=StyleTextLabel
Text="▼ INBOUND_TRAFFIC"
X=#PaddingMD#
Y=10R

[MeterDLValue]
Meter=String
MeterStyle=StyleTextHighlight
MeasureName=MeasureNetIn
Text="%1b/s"
AutoScale=1
NumOfDecimals=1
X=(#WidthMedium#-#PaddingMD#)
Y=0r
StringAlign=Right

[MeterDLGraph]
Meter=Histogram
MeasureName=MeasureNetIn
MeterStyle=StyleHistogramCyan
Flip=0
X=#PaddingMD#
Y=5R
W=(#WidthMedium#-#PaddingMD#*2)
H=#GraphHeight#

; ══════════════════════════════════════════════════════════════════════════════
; UPLOAD SECTION
; ══════════════════════════════════════════════════════════════════════════════

[MeterULLabel]
Meter=String
MeterStyle=StyleTextLabel
Text="▲ OUTBOUND_TRAFFIC"
X=#PaddingMD#
Y=8R

[MeterULValue]
Meter=String
MeterStyle=StyleTextError
MeasureName=MeasureNetOut
Text="%1b/s"
AutoScale=1
NumOfDecimals=1
X=(#WidthMedium#-#PaddingMD#)
Y=0r
StringAlign=Right

[MeterULGraph]
Meter=Histogram
MeasureName=MeasureNetOut
MeterStyle=StyleHistogramRed
X=#PaddingMD#
Y=5R
W=(#WidthMedium#-#PaddingMD#*2)
H=#GraphHeight#

; ── SEPARATOR ──
[MeterSep2]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthMedium#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,60 | StrokeWidth 0
Y=10R

; ══════════════════════════════════════════════════════════════════════════════
; SESSION STATS
; ══════════════════════════════════════════════════════════════════════════════

[MeterSessionLabel]
Meter=String
MeterStyle=StyleTextLabel
Text="SESSION_TRANSFER"
X=#PaddingMD#
Y=10R

[MeterSessionIn]
Meter=String
MeterStyle=StyleTextMuted
MeasureName=MeasureNetInTotal
Text="▼ %1B"
AutoScale=1
NumOfDecimals=2
X=#PaddingMD#
Y=3R

[MeterSessionOut]
Meter=String
MeterStyle=StyleTextMuted
MeasureName=MeasureNetOutTotal
Text="▲ %1B"
AutoScale=1
NumOfDecimals=2
X=(#WidthMedium#/2)
Y=0r

; ── SEPARATOR ──
[MeterSep3]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthMedium#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,60 | StrokeWidth 0
Y=10R

; ══════════════════════════════════════════════════════════════════════════════
; IP & LATENCY SECTION
; ══════════════════════════════════════════════════════════════════════════════

[MeterIPSection]
Meter=String
MeterStyle=StyleTextLabel
Text="NETWORK_IDENTITY"
X=#PaddingMD#
Y=10R

; External IP (Hover to reveal)
[MeterIPLabel]
Meter=String
MeterStyle=StyleTextMuted
Text="EXT_IP ::"
X=#PaddingMD#
Y=5R

[MeterIPValue]
Meter=String
MeterStyle=StyleTextValue
Text="***.***.***.***"
X=70
Y=0r
MouseOverAction=[!SetOption MeterIPValue Text "[MeasureWANIP]"][!SetOption MeterIPValue FontColor "#ColorWarning#"][!UpdateMeter MeterIPValue][!Redraw]
MouseLeaveAction=[!SetOption MeterIPValue Text "***.***.***.***"][!SetOption MeterIPValue FontColor "#ColorGhost#"][!UpdateMeter MeterIPValue][!Redraw]
LeftMouseUpAction=[!SetClip "[MeasureWANIP]"]
ToolTipText="Click to copy IP to clipboard"
DynamicVariables=1

; Local IP
[MeterLANLabel]
Meter=String
MeterStyle=StyleTextMuted
Text="LAN_IP ::"
X=#PaddingMD#
Y=3R

[MeterLANValue]
Meter=String
MeterStyle=StyleTextValue
MeasureName=MeasureLANIP
X=70
Y=0r

; Latency
[MeterPingLabel]
Meter=String
MeterStyle=StyleTextMuted
Text="LATENCY ::"
X=#PaddingMD#
Y=3R

[MeterPingValue]
Meter=String
MeterStyle=StyleTextValue
MeasureName=MeasurePing
Text="%1 ms"
X=70
Y=0r
DynamicVariables=1

; ── ADAPTER INFO ──
[MeterAdapterInfo]
Meter=String
MeterStyle=StyleTextMuted
MeasureName=MeasureAdapterName
Text="%1"
X=#PaddingMD#
Y=8R
W=(#WidthMedium#-#PaddingMD#*2)
ClipString=2

; ── FOOTER ──
[MeterBottomLine]
Meter=Shape
Shape=Rectangle 0,0,#WidthMedium#,3 | Fill Color #ColorNexusCyan# | StrokeWidth 0
Y=10R
```

---

## 5. Threat Intelligence Module: `ThreatIntel\ThreatIntel.ini`

```ini
[Rainmeter]
Update=#UpdateRateSlow#
AccurateText=1
BackgroundMode=2
SolidColor=#ColorBgPanel#
DynamicWindowSize=1

[Metadata]
Name=TBA Threat Intelligence
Author=The Black Agency
Version=10.0

@Include=#@#Variables.inc
@Include2=#@#Styles.inc

; ══════════════════════════════════════════════════════════════════════════════
; FULLSCREEN DETECTION
; ══════════════════════════════════════════════════════════════════════════════

[MeasureFullScreen]
Measure=Plugin
Plugin=IsFullScreen
IfCondition=(MeasureFullScreen = 1) && (#HideOnFullscreen# = 1)
IfTrueAction=[!FadeDuration 100][!Hide]
IfFalseAction=[!FadeDuration 150][!Show]

; ══════════════════════════════════════════════════════════════════════════════
; RSS FEED MEASURES — THE HACKER NEWS
; ══════════════════════════════════════════════════════════════════════════════

[MeasureTHN]
Measure=WebParser
URL=#ThreatFeedHackerNews#
RegExp=(?siU)<item>.*<title>(.*)</title>.*<link>(.*)</link>.*<pubDate>(.*)</pubDate>.*</item>.*<item>.*<title>(.*)</title>.*<link>(.*)</link>.*<pubDate>(.*)</pubDate>.*</item>.*<item>.*<title>(.*)</title>.*<link>(.*)</link>.*<pubDate>(.*)</pubDate>.*</item>.*<item>.*<title>(.*)</title>.*<link>(.*)</link>.*<pubDate>(.*)</pubDate>.*</item>.*<item>.*<title>(.*)</title>.*<link>(.*)</link>.*<pubDate>(.*)</pubDate>.*</item>
UpdateRate=900
LogSubstringErrors=0
DecodeCharacterReference=1

; Article 1
[MeasureTHNTitle1]
Measure=WebParser
URL=[MeasureTHN]
StringIndex=1
Substitute="":"Loading..."

[MeasureTHNLink1]
Measure=WebParser
URL=[MeasureTHN]
StringIndex=2

[MeasureTHNDate1]
Measure=WebParser
URL=[MeasureTHN]
StringIndex=3

; Article 2
[MeasureTHNTitle2]
Measure=WebParser
URL=[MeasureTHN]
StringIndex=4

[MeasureTHNLink2]
Measure=WebParser
URL=[MeasureTHN]
StringIndex=5

; Article 3
[MeasureTHNTitle3]
Measure=WebParser
URL=[MeasureTHN]
StringIndex=7

[MeasureTHNLink3]
Measure=WebParser
URL=[MeasureTHN]
StringIndex=8

; Article 4
[MeasureTHNTitle4]
Measure=WebParser
URL=[MeasureTHN]
StringIndex=10

[MeasureTHNLink4]
Measure=WebParser
URL=[MeasureTHN]
StringIndex=11

; Article 5
[MeasureTHNTitle5]
Measure=WebParser
URL=[MeasureTHN]
StringIndex=13

[MeasureTHNLink5]
Measure=WebParser
URL=[MeasureTHN]
StringIndex=14

; ══════════════════════════════════════════════════════════════════════════════
; BLEEPING COMPUTER FEED
; ══════════════════════════════════════════════════════════════════════════════

[MeasureBC]
Measure=WebParser
URL=#ThreatFeedBleeping#
RegExp=(?siU)<item>.*<title>(.*)</title>.*<link>(.*)</link>.*</item>.*<item>.*<title>(.*)</title>.*<link>(.*)</link>.*</item>.*<item>.*<title>(.*)</title>.*<link>(.*)</link>.*</item>
UpdateRate=900
LogSubstringErrors=0
DecodeCharacterReference=1

[MeasureBCTitle1]
Measure=WebParser
URL=[MeasureBC]
StringIndex=1
Substitute="":"Loading..."

[MeasureBCLink1]
Measure=WebParser
URL=[MeasureBC]
StringIndex=2

[MeasureBCTitle2]
Measure=WebParser
URL=[MeasureBC]
StringIndex=3

[MeasureBCLink2]
Measure=WebParser
URL=[MeasureBC]
StringIndex=4

[MeasureBCTitle3]
Measure=WebParser
URL=[MeasureBC]
StringIndex=5

[MeasureBCLink3]
Measure=WebParser
URL=[MeasureBC]
StringIndex=6

; ══════════════════════════════════════════════════════════════════════════════
; AUTO-SCROLL MECHANISM
; ══════════════════════════════════════════════════════════════════════════════

[MeasureScrollCounter]
Measure=Calc
Formula=(MeasureScrollCounter % 8) + 1
UpdateDivider=10
DynamicVariables=1

; ══════════════════════════════════════════════════════════════════════════════
; VISUAL METERS
; ══════════════════════════════════════════════════════════════════════════════

; ── HEADER ──
[MeterTopLine]
Meter=Shape
Shape=Rectangle 0,0,#WidthLarge#,3 | Fill Color #ColorError# | StrokeWidth 0

[MeterTitle]
Meter=String
MeterStyle=StyleTextHeader
FontColor=#ColorError#
Text="╔══[ THREAT_INTELLIGENCE ]══╗"
X=#PaddingMD#
Y=8

[MeterSubtitle]
Meter=String
MeterStyle=StyleTextMuted
Text="LIVE CYBERSECURITY FEED // AUTO-REFRESH 15M"
X=#PaddingMD#
Y=2R

; Status indicator
[MeterLiveIndicator]
Meter=String
FontFace=#FontFace#
FontSize=#FontSizeXS#
FontColor=#ColorSuccess#
Text="● LIVE"
X=(#WidthLarge#-#PaddingMD#)
Y=-12r
StringAlign=Right
AntiAlias=1

; ── SEPARATOR ──
[MeterSep1]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthLarge#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,60 | StrokeWidth 0
Y=10R

; ══════════════════════════════════════════════════════════════════════════════
; THE HACKER NEWS SECTION
; ══════════════════════════════════════════════════════════════════════════════

[MeterTHNHeader]
Meter=String
MeterStyle=StyleTextLabel
Text="■ THE HACKER NEWS"
FontColor=#ColorWarning#
X=#PaddingMD#
Y=10R

; Article 1
[MeterTHN1]
Meter=String
MeterStyle=StyleTextBase
FontSize=#FontSizeSM#
MeasureName=MeasureTHNTitle1
X=#PaddingMD#
Y=8R
W=(#WidthLarge#-#PaddingMD#*2)
ClipString=2
LeftMouseUpAction=["[MeasureTHNLink1]"]
MouseOverAction=[!SetOption #CURRENTSECTION# FontColor "#ColorNexusCyan#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
MouseLeaveAction=[!SetOption #CURRENTSECTION# FontColor "#ColorGhost#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
ToolTipText="Click to open article"
DynamicVariables=1

; Article 2
[MeterTHN2]
Meter=String
MeterStyle=StyleTextBase
FontSize=#FontSizeSM#
MeasureName=MeasureTHNTitle2
X=#PaddingMD#
Y=3R
W=(#WidthLarge#-#PaddingMD#*2)
ClipString=2
LeftMouseUpAction=["[MeasureTHNLink2]"]
MouseOverAction=[!SetOption #CURRENTSECTION# FontColor "#ColorNexusCyan#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
MouseLeaveAction=[!SetOption #CURRENTSECTION# FontColor "#ColorGhost#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
DynamicVariables=1

; Article 3
[MeterTHN3]
Meter=String
MeterStyle=StyleTextBase
FontSize=#FontSizeSM#
MeasureName=MeasureTHNTitle3
X=#PaddingMD#
Y=3R
W=(#WidthLarge#-#PaddingMD#*2)
ClipString=2
LeftMouseUpAction=["[MeasureTHNLink3]"]
MouseOverAction=[!SetOption #CURRENTSECTION# FontColor "#ColorNexusCyan#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
MouseLeaveAction=[!SetOption #CURRENTSECTION# FontColor "#ColorGhost#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
DynamicVariables=1

; Article 4
[MeterTHN4]
Meter=String
MeterStyle=StyleTextBase
FontSize=#FontSizeSM#
MeasureName=MeasureTHNTitle4
X=#PaddingMD#
Y=3R
W=(#WidthLarge#-#PaddingMD#*2)
ClipString=2
LeftMouseUpAction=["[MeasureTHNLink4]"]
MouseOverAction=[!SetOption #CURRENTSECTION# FontColor "#ColorNexusCyan#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
MouseLeaveAction=[!SetOption #CURRENTSECTION# FontColor "#ColorGhost#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
DynamicVariables=1

; Article 5
[MeterTHN5]
Meter=String
MeterStyle=StyleTextBase
FontSize=#FontSizeSM#
MeasureName=MeasureTHNTitle5
X=#PaddingMD#
Y=3R
W=(#WidthLarge#-#PaddingMD#*2)
ClipString=2
LeftMouseUpAction=["[MeasureTHNLink5]"]
MouseOverAction=[!SetOption #CURRENTSECTION# FontColor "#ColorNexusCyan#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
MouseLeaveAction=[!SetOption #CURRENTSECTION# FontColor "#ColorGhost#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
DynamicVariables=1

; ── SEPARATOR ──
[MeterSep2]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthLarge#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,60 | StrokeWidth 0
Y=12R

; ══════════════════════════════════════════════════════════════════════════════
; BLEEPING COMPUTER SECTION
; ══════════════════════════════════════════════════════════════════════════════

[MeterBCHeader]
Meter=String
MeterStyle=StyleTextLabel
Text="■ BLEEPING COMPUTER"
FontColor=#ColorMagenta#
X=#PaddingMD#
Y=10R

; BC Article 1
[MeterBC1]
Meter=String
MeterStyle=StyleTextBase
FontSize=#FontSizeSM#
MeasureName=MeasureBCTitle1
X=#PaddingMD#
Y=8R
W=(#WidthLarge#-#PaddingMD#*2)
ClipString=2
LeftMouseUpAction=["[MeasureBCLink1]"]
MouseOverAction=[!SetOption #CURRENTSECTION# FontColor "#ColorNexusCyan#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
MouseLeaveAction=[!SetOption #CURRENTSECTION# FontColor "#ColorGhost#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
DynamicVariables=1

; BC Article 2
[MeterBC2]
Meter=String
MeterStyle=StyleTextBase
FontSize=#FontSizeSM#
MeasureName=MeasureBCTitle2
X=#PaddingMD#
Y=3R
W=(#WidthLarge#-#PaddingMD#*2)
ClipString=2
LeftMouseUpAction=["[MeasureBCLink2]"]
MouseOverAction=[!SetOption #CURRENTSECTION# FontColor "#ColorNexusCyan#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
MouseLeaveAction=[!SetOption #CURRENTSECTION# FontColor "#ColorGhost#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
DynamicVariables=1

; BC Article 3
[MeterBC3]
Meter=String
MeterStyle=StyleTextBase
FontSize=#FontSizeSM#
MeasureName=MeasureBCTitle3
X=#PaddingMD#
Y=3R
W=(#WidthLarge#-#PaddingMD#*2)
ClipString=2
LeftMouseUpAction=["[MeasureBCLink3]"]
MouseOverAction=[!SetOption #CURRENTSECTION# FontColor "#ColorNexusCyan#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
MouseLeaveAction=[!SetOption #CURRENTSECTION# FontColor "#ColorGhost#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
DynamicVariables=1

; ── SEPARATOR ──
[MeterSep3]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthLarge#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,60 | StrokeWidth 0
Y=12R

; ══════════════════════════════════════════════════════════════════════════════
; REFRESH CONTROLS
; ══════════════════════════════════════════════════════════════════════════════

[MeterRefreshBtn]
Meter=String
MeterStyle=StyleButtonBase
Text="↻ REFRESH FEEDS"
X=#PaddingMD#
Y=10R
LeftMouseUpAction=[!CommandMeasure MeasureTHN Update][!CommandMeasure MeasureBC Update][!UpdateMeter *][!Redraw]

[MeterOpenTHN]
Meter=String
MeterStyle=StyleTextMuted
Text="[OPEN THN]"
X=130
Y=0r
LeftMouseUpAction=["https://thehackernews.com"]
MouseOverAction=[!SetOption #CURRENTSECTION# FontColor "#ColorNexusCyan#"][!UpdateMeter #CURRENTSECTION#][!Redraw]
MouseLeaveAction=[!SetOption #CURRENTSECTION# FontColor "#ColorSteel#"][!UpdateMeter #CURRENTSECTION#][!Redraw]

[MeterLastUpdate]
Meter=String
MeterStyle=StyleTextMuted
FontSize=7
Text="Last update: [*MeasureTHN:Timestamp*]"
X=(#WidthLarge#-#PaddingMD#)
Y=0r
StringAlign=Right
DynamicVariables=1

; ── FOOTER ──
[MeterBottomLine]
Meter=Shape
Shape=Rectangle 0,0,#WidthLarge#,3 | Fill Color #ColorError# | StrokeWidth 0
Y=12R
```

---

## 6. Services Matrix Module: `Services\Services.ini`

```ini
[Rainmeter]
Update=#UpdateRateSlow#
AccurateText=1
BackgroundMode=2
SolidColor=#ColorBgPanel#
DynamicWindowSize=1

[Metadata]
Name=TBA Services Matrix
Author=The Black Agency
Version=10.0

@Include=#@#Variables.inc
@Include2=#@#Styles.inc

; ══════════════════════════════════════════════════════════════════════════════
; SERVICE DETECTION MEASURES
; ══════════════════════════════════════════════════════════════════════════════

; ── OLLAMA (Neural Link) ──
[MeasureOllama]
Measure=Plugin
Plugin=WebParser
URL=http://#OllamaHost#:#OllamaPort#/api/tags
RegExp=(.*)
UpdateRate=30
FinishAction=[!SetVariable OllamaStatus "1"][!UpdateMeasure MeasureOllamaCalc]
OnConnectErrorAction=[!SetVariable OllamaStatus "0"][!UpdateMeasure MeasureOllamaCalc]

[MeasureOllamaCalc]
Measure=Calc
Formula=#OllamaStatus#
IfCondition=MeasureOllamaCalc = 1
IfTrueAction=[!SetOption MeterOllamaStatus FontColor "#ColorSuccess#"][!SetOption MeterOllamaStatus Text "● ONLINE"]
IfFalseAction=[!SetOption MeterOllamaStatus FontColor "#ColorSteel#"][!SetOption MeterOllamaStatus Text "○ OFFLINE"]
DynamicVariables=1

; ── DOCKER ──
[MeasureDocker]
Measure=Plugin
Plugin=Process
ProcessName=#DockerProcess#
IfCondition=MeasureDocker = -1
IfTrueAction=[!SetOption MeterDockerStatus FontColor "#ColorSteel#"][!SetOption MeterDockerStatus Text "○ OFFLINE"]
IfFalseAction=[!SetOption MeterDockerStatus FontColor "#ColorSuccess#"][!SetOption MeterDockerStatus Text "● ONLINE"]

; ── WSL ──
[MeasureWSL]
Measure=Plugin
Plugin=Process
ProcessName=#WSLProcess#
IfCondition=MeasureWSL = -1
IfTrueAction=[!SetOption MeterWSLStatus FontColor "#ColorSteel#"][!SetOption MeterWSLStatus Text "○ OFFLINE"]
IfFalseAction=[!SetOption MeterWSLStatus FontColor "#ColorSuccess#"][!SetOption MeterWSLStatus Text "● ONLINE"]

; ── Windows Defender ──
[MeasureDefender]
Measure=Plugin
Plugin=Process
ProcessName=MsMpEng.exe
IfCondition=MeasureDefender = -1
IfTrueAction=[!SetOption MeterDefenderStatus FontColor "#ColorError#"][!SetOption MeterDefenderStatus Text "⚠ DISABLED"]
IfFalseAction=[!SetOption MeterDefenderStatus FontColor "#ColorSuccess#"][!SetOption MeterDefenderStatus Text "● ACTIVE"]

; ── SSH Agent ──
[MeasureSSHAgent]
Measure=Plugin
Plugin=Process
ProcessName=ssh-agent.exe
IfCondition=MeasureSSHAgent = -1
IfTrueAction=[!SetOption MeterSSHStatus FontColor "#ColorSteel#"][!SetOption MeterSSHStatus Text "○ OFFLINE"]
IfFalseAction=[!SetOption MeterSSHStatus FontColor "#ColorSuccess#"][!SetOption MeterSSHStatus Text "● RUNNING"]

; ── Git ──
[MeasureGit]
Measure=Plugin
Plugin=RunCommand
Program=where
Parameter=git
State=Hide
OutputType=ANSI
FinishAction=[!SetOption MeterGitStatus FontColor "#ColorSuccess#"][!SetOption MeterGitStatus Text "● INSTALLED"]
OnFinishAction=[!UpdateMeasure MeasureGit]
IfMatch=^$
IfMatchAction=[!SetOption MeterGitStatus FontColor "#ColorSteel#"][!SetOption MeterGitStatus Text "○ NOT FOUND"]

; ── Node.js ──
[MeasureNode]
Measure=Plugin
Plugin=RunCommand
Program=node
Parameter=--version
State=Hide
OutputType=ANSI
Substitute="v":"","#CRLF#":""
FinishAction=[!UpdateMeterGroup NodeMeters]

; ── Python ──
[MeasurePython]
Measure=Plugin
Plugin=RunCommand
Program=python
Parameter=--version
State=Hide
OutputType=ANSI
Substitute="Python ":"","#CRLF#":""
FinishAction=[!UpdateMeterGroup PythonMeters]

; ══════════════════════════════════════════════════════════════════════════════
; VISUAL METERS
; ══════════════════════════════════════════════════════════════════════════════

; ── HEADER ──
[MeterTopLine]
Meter=Shape
Shape=Rectangle 0,0,#WidthMedium#,3 | Fill Color #ColorMagenta# | StrokeWidth 0

[MeterTitle]
Meter=String
MeterStyle=StyleTextHeader
FontColor=#ColorMagenta#
Text="╔══[ SERVICE_MATRIX ]══╗"
X=#PaddingMD#
Y=8

[MeterSubtitle]
Meter=String
MeterStyle=StyleTextMuted
Text="RUNTIME MONITOR // LIVE STATUS"
X=#PaddingMD#
Y=2R

; ── SEPARATOR ──
[MeterSep1]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthMedium#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,60 | StrokeWidth 0
Y=8R

; ══════════════════════════════════════════════════════════════════════════════
; AI / ML SERVICES
; ══════════════════════════════════════════════════════════════════════════════

[MeterAIHeader]
Meter=String
MeterStyle=StyleTextLabel
Text="■ AI_SERVICES"
X=#PaddingMD#
Y=10R

; Ollama
[MeterOllamaLabel]
Meter=String
MeterStyle=StyleTextBase
Text="NEURAL_LINK (Ollama)"
X=#PaddingMD#
Y=5R

[MeterOllamaStatus]
Meter=String
MeterStyle=StyleTextBase
Text="○ CHECKING..."
FontColor=#ColorSteel#
X=(#WidthMedium#-#PaddingMD#)
Y=0r
StringAlign=Right

; ── SEPARATOR ──
[MeterSep2]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthMedium#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,40 | StrokeWidth 0
Y=10R

; ══════════════════════════════════════════════════════════════════════════════
; CONTAINER / VM SERVICES
; ══════════════════════════════════════════════════════════════════════════════

[MeterContainerHeader]
Meter=String
MeterStyle=StyleTextLabel
Text="■ CONTAINER_GRID"
X=#PaddingMD#
Y=10R

; Docker
[MeterDockerLabel]
Meter=String
MeterStyle=StyleTextBase
Text="DOCKER_ENGINE"
X=#PaddingMD#
Y=5R

[MeterDockerStatus]
Meter=String
MeterStyle=StyleTextBase
Text="○ CHECKING..."
FontColor=#ColorSteel#
X=(#WidthMedium#-#PaddingMD#)
Y=0r
StringAlign=Right

; WSL
[MeterWSLLabel]
Meter=String
MeterStyle=StyleTextBase
Text="WSL_SUBSYSTEM"
X=#PaddingMD#
Y=3R

[MeterWSLStatus]
Meter=String
MeterStyle=StyleTextBase
Text="○ CHECKING..."
FontColor=#ColorSteel#
X=(#WidthMedium#-#PaddingMD#)
Y=0r
StringAlign=Right

; ── SEPARATOR ──
[MeterSep3]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthMedium#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,40 | StrokeWidth 0
Y=10R

; ══════════════════════════════════════════════════════════════════════════════
; SECURITY SERVICES
; ══════════════════════════════════════════════════════════════════════════════

[MeterSecurityHeader]
Meter=String
MeterStyle=StyleTextLabel
Text="■ SECURITY_LAYER"
X=#PaddingMD#
Y=10R

; Defender
[MeterDefenderLabel]
Meter=String
MeterStyle=StyleTextBase
Text="WINDOWS_DEFENDER"
X=#PaddingMD#
Y=5R

[MeterDefenderStatus]
Meter=String
MeterStyle=StyleTextBase
Text="○ CHECKING..."
FontColor=#ColorSteel#
X=(#WidthMedium#-#PaddingMD#)
Y=0r
StringAlign=Right

; SSH Agent
[MeterSSHLabel]
Meter=String
MeterStyle=StyleTextBase
Text="SSH_AGENT"
X=#PaddingMD#
Y=3R

[MeterSSHStatus]
Meter=String
MeterStyle=StyleTextBase
Text="○ CHECKING..."
FontColor=#ColorSteel#
X=(#WidthMedium#-#PaddingMD#)
Y=0r
StringAlign=Right

; ── SEPARATOR ──
[MeterSep4]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthMedium#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,40 | StrokeWidth 0
Y=10R

; ══════════════════════════════════════════════════════════════════════════════
; DEV TOOLS
; ══════════════════════════════════════════════════════════════════════════════

[MeterDevHeader]
Meter=String
MeterStyle=StyleTextLabel
Text="■ DEV_RUNTIMES"
X=#PaddingMD#
Y=10R

; Git
[MeterGitLabel]
Meter=String
MeterStyle=StyleTextBase
Text="GIT"
X=#PaddingMD#
Y=5R

[MeterGitStatus]
Meter=String
MeterStyle=StyleTextBase
Text="○ CHECKING..."
FontColor=#ColorSteel#
X=(#WidthMedium#-#PaddingMD#)
Y=0r
StringAlign=Right

; Node.js
[MeterNodeLabel]
Meter=String
MeterStyle=StyleTextBase
Text="NODE.JS"
X=#PaddingMD#
Y=3R

[MeterNodeStatus]
Meter=String
MeterStyle=StyleTextBase
MeasureName=MeasureNode
Text="v%1"
FontColor=#ColorSuccess#
X=(#WidthMedium#-#PaddingMD#)
Y=0r
StringAlign=Right
Substitute="":"○ NOT FOUND"
Group=NodeMeters

; Python
[MeterPythonLabel]
Meter=String
MeterStyle=StyleTextBase
Text="PYTHON"
X=#PaddingMD#
Y=3R

[MeterPythonStatus]
Meter=String
MeterStyle=StyleTextBase
MeasureName=MeasurePython
Text="v%1"
FontColor=#ColorSuccess#
X=(#WidthMedium#-#PaddingMD#)
Y=0r
StringAlign=Right
Substitute="":"○ NOT FOUND"
Group=PythonMeters

; ── FOOTER ──
[MeterBottomLine]
Meter=Shape
Shape=Rectangle 0,0,#WidthMedium#,3 | Fill Color #ColorMagenta# | StrokeWidth 0
Y=15R
```

---

## 7. Clock Panel: `Clock\Clock.ini`

```ini
[Rainmeter]
Update=1000
AccurateText=1
BackgroundMode=2
SolidColor=#ColorBgPanel#
DynamicWindowSize=1

[Metadata]
Name=TBA Clock Panel
Author=The Black Agency
Version=10.0

@Include=#@#Variables.inc
@Include2=#@#Styles.inc

; ══════════════════════════════════════════════════════════════════════════════
; TIME MEASURES
; ══════════════════════════════════════════════════════════════════════════════

[MeasureTime]
Measure=Time
Format=%H:%M:%S

[MeasureTimeHour]
Measure=Time
Format=%H

[MeasureTimeMin]
Measure=Time
Format=%M

[MeasureTimeSec]
Measure=Time
Format=%S

[MeasureDate]
Measure=Time
Format=%Y-%m-%d

[MeasureDayName]
Measure=Time
Format=%A

[MeasureWeek]
Measure=Time
Format=%V

[MeasureUTC]
Measure=Time
TimeZone=0
Format=%H:%M UTC

; ══════════════════════════════════════════════════════════════════════════════
; VISUAL METERS
; ══════════════════════════════════════════════════════════════════════════════

; ── HEADER ──
[MeterTopLine]
Meter=Shape
Shape=Rectangle 0,0,#WidthSmall#,3 | Fill Color #ColorVirtuRed# | StrokeWidth 0

[MeterTitle]
Meter=String
MeterStyle=StyleTextLabel
Text="CHRONO_SYNC"
X=#PaddingMD#
Y=8

; ── MAIN TIME ──
[MeterTimeDisplay]
Meter=String
FontFace=#FontFaceMono#
FontSize=32
FontColor=#ColorVirtuRed#
FontWeight=600
MeasureName=MeasureTime
X=(#WidthSmall#/2)
Y=8R
StringAlign=Center
AntiAlias=1

; ── DATE ──
[MeterDateDisplay]
Meter=String
MeterStyle=StyleTextValue
MeasureName=MeasureDate
X=(#WidthSmall#/2)
Y=5R
StringAlign=Center

[MeterDayDisplay]
Meter=String
MeterStyle=StyleTextMuted
MeasureName=MeasureDayName
Text="%1 // WEEK [MeasureWeek]"
X=(#WidthSmall#/2)
Y=2R
StringAlign=Center
DynamicVariables=1

; ── SEPARATOR ──
[MeterSep1]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthSmall#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,60 | StrokeWidth 0
Y=10R

; ── UTC TIME ──
[MeterUTCLabel]
Meter=String
MeterStyle=StyleTextLabel
Text="UTC_REFERENCE"
X=#PaddingMD#
Y=8R

[MeterUTCValue]
Meter=String
MeterStyle=StyleTextHighlight
MeasureName=MeasureUTC
X=(#WidthSmall#-#PaddingMD#)
Y=0r
StringAlign=Right

; ── FOOTER ──
[MeterBottomLine]
Meter=Shape
Shape=Rectangle 0,0,#WidthSmall#,3 | Fill Color #ColorVirtuRed# | StrokeWidth 0
Y=12R
```

---

## 8. Disk Storage Module: `Disk\Disk.ini`

```ini
[Rainmeter]
Update=5000
AccurateText=1
BackgroundMode=2
SolidColor=#ColorBgPanel#
DynamicWindowSize=1

[Metadata]
Name=TBA Disk Storage
Author=The Black Agency
Version=10.0

@Include=#@#Variables.inc
@Include2=#@#Styles.inc

; ══════════════════════════════════════════════════════════════════════════════
; DISK MEASURES
; ══════════════════════════════════════════════════════════════════════════════

; Drive C:
[MeasureDiskC]
Measure=FreeDiskSpace
Drive=C:
InvertMeasure=1

[MeasureDiskCTotal]
Measure=FreeDiskSpace
Drive=C:
Total=1

[MeasureDiskCFree]
Measure=FreeDiskSpace
Drive=C:

[MeasureDiskCPercent]
Measure=Calc
Formula=(MeasureDiskC / MeasureDiskCTotal) * 100

; Drive D: (if exists)
[MeasureDiskD]
Measure=FreeDiskSpace
Drive=D:
InvertMeasure=1
IgnoreRemovable=0

[MeasureDiskDTotal]
Measure=FreeDiskSpace
Drive=D:
Total=1
IgnoreRemovable=0

[MeasureDiskDFree]
Measure=FreeDiskSpace
Drive=D:
IgnoreRemovable=0

[MeasureDiskDPercent]
Measure=Calc
Formula=(MeasureDiskD / MeasureDiskDTotal) * 100
IfCondition=MeasureDiskDTotal = 0
IfTrueAction=[!HideMeterGroup DriveD]
IfFalseAction=[!ShowMeterGroup DriveD]

; Disk Activity
[MeasureDiskRead]
Measure=Plugin
Plugin=PerfMon
PerfMonObject=PhysicalDisk
PerfMonCounter=Disk Read Bytes/sec
PerfMonInstance=0 C:

[MeasureDiskWrite]
Measure=Plugin
Plugin=PerfMon
PerfMonObject=PhysicalDisk
PerfMonCounter=Disk Write Bytes/sec
PerfMonInstance=0 C:

; ══════════════════════════════════════════════════════════════════════════════
; VISUAL METERS
; ══════════════════════════════════════════════════════════════════════════════

; ── HEADER ──
[MeterTopLine]
Meter=Shape
Shape=Rectangle 0,0,#WidthMedium#,3 | Fill Color #ColorWarning# | StrokeWidth 0

[MeterTitle]
Meter=String
MeterStyle=StyleTextHeader
FontColor=#ColorWarning#
Text="╔══[ DISK_STORAGE ]══╗"
X=#PaddingMD#
Y=8

[MeterSubtitle]
Meter=String
MeterStyle=StyleTextMuted
Text="PARTITION MONITOR // I/O ANALYSIS"
X=#PaddingMD#
Y=2R

; ── SEPARATOR ──
[MeterSep1]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthMedium#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,60 | StrokeWidth 0
Y=8R

; ══════════════════════════════════════════════════════════════════════════════
; DRIVE C: SECTION
; ══════════════════════════════════════════════════════════════════════════════

[MeterDriveCLabel]
Meter=String
MeterStyle=StyleTextLabel
Text="■ DRIVE C: (SYSTEM)"
X=#PaddingMD#
Y=10R

[MeterDriveCPercent]
Meter=String
MeterStyle=StyleTextValueLarge
MeasureName=MeasureDiskCPercent
Text="%1%"
NumOfDecimals=0
X=(#WidthMedium#-#PaddingMD#)
Y=0r
StringAlign=Right

[MeterDriveCBar]
Meter=Bar
MeasureName=MeasureDiskC
MeterStyle=StyleBarWarning
X=#PaddingMD#
Y=5R
W=(#WidthMedium#-#PaddingMD#*2)
H=#BarHeightMedium#
DynamicVariables=1

[MeterDriveCInfo]
Meter=String
MeterStyle=StyleTextMuted
MeasureName=MeasureDiskCFree
MeasureName2=MeasureDiskCTotal
Text="FREE: %1B / %2B"
AutoScale=1
NumOfDecimals=1
X=#PaddingMD#
Y=5R

; ══════════════════════════════════════════════════════════════════════════════
; DRIVE D: SECTION (Conditional)
; ══════════════════════════════════════════════════════════════════════════════

[MeterSep2]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthMedium#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,40 | StrokeWidth 0
Y=10R
Group=DriveD

[MeterDriveDLabel]
Meter=String
MeterStyle=StyleTextLabel
Text="■ DRIVE D: (DATA)"
X=#PaddingMD#
Y=10R
Group=DriveD

[MeterDriveDPercent]
Meter=String
MeterStyle=StyleTextValueLarge
MeasureName=MeasureDiskDPercent
Text="%1%"
NumOfDecimals=0
X=(#WidthMedium#-#PaddingMD#)
Y=0r
StringAlign=Right
Group=DriveD

[MeterDriveDBar]
Meter=Bar
MeasureName=MeasureDiskD
MeterStyle=StyleBarCyan
X=#PaddingMD#
Y=5R
W=(#WidthMedium#-#PaddingMD#*2)
H=#BarHeightMedium#
Group=DriveD

[MeterDriveDInfo]
Meter=String
MeterStyle=StyleTextMuted
MeasureName=MeasureDiskDFree
MeasureName2=MeasureDiskDTotal
Text="FREE: %1B / %2B"
AutoScale=1
NumOfDecimals=1
X=#PaddingMD#
Y=5R
Group=DriveD

; ══════════════════════════════════════════════════════════════════════════════
; DISK I/O SECTION
; ══════════════════════════════════════════════════════════════════════════════

[MeterSep3]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthMedium#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,60 | StrokeWidth 0
Y=12R

[MeterIOLabel]
Meter=String
MeterStyle=StyleTextLabel
Text="DISK_IO_ACTIVITY"
X=#PaddingMD#
Y=10R

[MeterReadLabel]
Meter=String
MeterStyle=StyleTextMuted
Text="READ:"
X=#PaddingMD#
Y=5R

[MeterReadValue]
Meter=String
MeterStyle=StyleTextHighlight
MeasureName=MeasureDiskRead
Text="%1B/s"
AutoScale=1
NumOfDecimals=1
X=50
Y=0r

[MeterWriteLabel]
Meter=String
MeterStyle=StyleTextMuted
Text="WRITE:"
X=(#WidthMedium#/2)
Y=0r

[MeterWriteValue]
Meter=String
MeterStyle=StyleTextError
MeasureName=MeasureDiskWrite
Text="%1B/s"
AutoScale=1
NumOfDecimals=1
X=45R
Y=0r

; ── FOOTER ──
[MeterBottomLine]
Meter=Shape
Shape=Rectangle 0,0,#WidthMedium#,3 | Fill Color #ColorWarning# | StrokeWidth 0
Y=12R
```

---

## 9. GPU Monitor (NVIDIA): `GPU\GPU.ini`

```ini
[Rainmeter]
Update=1000
AccurateText=1
BackgroundMode=2
SolidColor=#ColorBgPanel#
DynamicWindowSize=1

[Metadata]
Name=TBA GPU Monitor
Author=The Black Agency
Version=10.0
Information=Requires NVIDIA GPU with nvidia-smi

@Include=#@#Variables.inc
@Include2=#@#Styles.inc

; ══════════════════════════════════════════════════════════════════════════════
; GPU MEASURES (NVIDIA)
; ══════════════════════════════════════════════════════════════════════════════

[MeasureGPUName]
Measure=Plugin
Plugin=RunCommand
Program=nvidia-smi
Parameter=--query-gpu=name --format=csv,noheader,nounits
State=Hide
UpdateDivider=60
Substitute="#CRLF#":""

[MeasureGPUUsage]
Measure=Plugin
Plugin=RunCommand
Program=nvidia-smi
Parameter=--query-gpu=utilization.gpu --format=csv,noheader,nounits
State=Hide
Substitute="#CRLF#":"","%":""

[MeasureGPUMemUsed]
Measure=Plugin
Plugin=RunCommand
Program=nvidia-smi
Parameter=--query-gpu=memory.used --format=csv,noheader,nounits
State=Hide
Substitute="#CRLF#":"","MiB":""

[MeasureGPUMemTotal]
Measure=Plugin
Plugin=RunCommand
Program=nvidia-smi
Parameter=--query-gpu=memory.total --format=csv,noheader,nounits
State=Hide
UpdateDivider=60
Substitute="#CRLF#":"","MiB":""

[MeasureGPUTemp]
Measure=Plugin
Plugin=RunCommand
Program=nvidia-smi
Parameter=--query-gpu=temperature.gpu --format=csv,noheader,nounits
State=Hide
Substitute="#CRLF#":""

[MeasureGPUFan]
Measure=Plugin
Plugin=RunCommand
Program=nvidia-smi
Parameter=--query-gpu=fan.speed --format=csv,noheader,nounits
State=Hide
Substitute="#CRLF#":"","%":"","[Not Supported]":"N/A"

[MeasureGPUPower]
Measure=Plugin
Plugin=RunCommand
Program=nvidia-smi
Parameter=--query-gpu=power.draw --format=csv,noheader,nounits
State=Hide
Substitute="#CRLF#":"","W":""

; Calculated measures
[MeasureGPUMemPercent]
Measure=Calc
Formula=(MeasureGPUMemUsed / MeasureGPUMemTotal) * 100
DynamicVariables=1

[MeasureGPUUsageCalc]
Measure=Calc
Formula=MeasureGPUUsage
MinValue=0
MaxValue=100
DynamicVariables=1

; ══════════════════════════════════════════════════════════════════════════════
; VISUAL METERS
; ══════════════════════════════════════════════════════════════════════════════

; ── HEADER ──
[MeterTopLine]
Meter=Shape
Shape=Rectangle 0,0,#WidthMedium#,3 | Fill Color #ColorSuccess# | StrokeWidth 0

[MeterTitle]
Meter=String
MeterStyle=StyleTextHeader
FontColor=#ColorSuccess#
Text="╔══[ GPU_COMPUTE ]══╗"
X=#PaddingMD#
Y=8

[MeterGPUName]
Meter=String
MeterStyle=StyleTextMuted
MeasureName=MeasureGPUName
X=#PaddingMD#
Y=2R
W=(#WidthMedium#-#PaddingMD#*2)
ClipString=2

; ── SEPARATOR ──
[MeterSep1]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthMedium#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,60 | StrokeWidth 0
Y=8R

; ══════════════════════════════════════════════════════════════════════════════
; GPU USAGE SECTION
; ══════════════════════════════════════════════════════════════════════════════

[MeterGPUUsageLabel]
Meter=String
MeterStyle=StyleTextLabel
Text="GPU_UTILIZATION"
X=#PaddingMD#
Y=10R

[MeterGPUUsageValue]
Meter=String
MeterStyle=StyleTextValueLarge
MeasureName=MeasureGPUUsage
Text="%1%"
X=(#WidthMedium#-#PaddingMD#)
Y=0r
StringAlign=Right
DynamicVariables=1

[MeterGPUUsageGraph]
Meter=Histogram
MeasureName=MeasureGPUUsageCalc
MeterStyle=StyleHistogramGreen
X=#PaddingMD#
Y=5R
W=(#WidthMedium#-#PaddingMD#*2)
H=#GraphHeight#

; ══════════════════════════════════════════════════════════════════════════════
; VRAM SECTION
; ══════════════════════════════════════════════════════════════════════════════

[MeterVRAMLabel]
Meter=String
MeterStyle=StyleTextLabel
Text="VRAM_ALLOCATION"
X=#PaddingMD#
Y=8R

[MeterVRAMValue]
Meter=String
MeterStyle=StyleTextValue
MeasureName=MeasureGPUMemPercent
Text="%1%"
NumOfDecimals=0
X=(#WidthMedium#-#PaddingMD#)
Y=0r
StringAlign=Right
DynamicVariables=1

[MeterVRAMBar]
Meter=Bar
MeasureName=MeasureGPUMemPercent
MeterStyle=StyleBarCyan
X=#PaddingMD#
Y=5R
W=(#WidthMedium#-#PaddingMD#*2)
H=#BarHeightMedium#
DynamicVariables=1

[MeterVRAMInfo]
Meter=String
MeterStyle=StyleTextMuted
MeasureName=MeasureGPUMemUsed
MeasureName2=MeasureGPUMemTotal
Text="%1 MB / %2 MB"
X=#PaddingMD#
Y=5R
DynamicVariables=1

; ── SEPARATOR ──
[MeterSep2]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthMedium#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,60 | StrokeWidth 0
Y=10R

; ══════════════════════════════════════════════════════════════════════════════
; THERMAL / POWER SECTION
; ══════════════════════════════════════════════════════════════════════════════

[MeterThermalLabel]
Meter=String
MeterStyle=StyleTextLabel
Text="THERMAL_STATUS"
X=#PaddingMD#
Y=10R

; Temperature
[MeterTempLabel]
Meter=String
MeterStyle=StyleTextMuted
Text="TEMP:"
X=#PaddingMD#
Y=5R

[MeterTempValue]
Meter=String
MeterStyle=StyleTextValue
MeasureName=MeasureGPUTemp
Text="%1°C"
X=50
Y=0r
DynamicVariables=1

; Fan Speed
[MeterFanLabel]
Meter=String
MeterStyle=StyleTextMuted
Text="FAN:"
X=(#WidthMedium#/2)
Y=0r

[MeterFanValue]
Meter=String
MeterStyle=StyleTextValue
MeasureName=MeasureGPUFan
Text="%1%"
X=35R
Y=0r
DynamicVariables=1

; Power Draw
[MeterPowerLabel]
Meter=String
MeterStyle=StyleTextMuted
Text="POWER:"
X=#PaddingMD#
Y=3R

[MeterPowerValue]
Meter=String
MeterStyle=StyleTextWarning
MeasureName=MeasureGPUPower
Text="%1 W"
X=55
Y=0r
DynamicVariables=1

; ── FOOTER ──
[MeterBottomLine]
Meter=Shape
Shape=Rectangle 0,0,#WidthMedium#,3 | Fill Color #ColorSuccess# | StrokeWidth 0
Y=12R
```

---

## 10. Quick Launcher: `Launcher\Launcher.ini`

```ini
[Rainmeter]
Update=1000
AccurateText=1
BackgroundMode=2
SolidColor=#ColorBgPanel#
DynamicWindowSize=1

[Metadata]
Name=TBA Quick Launcher
Author=The Black Agency
Version=10.0

@Include=#@#Variables.inc
@Include2=#@#Styles.inc

; ══════════════════════════════════════════════════════════════════════════════
; VISUAL METERS
; ══════════════════════════════════════════════════════════════════════════════

; ── HEADER ──
[MeterTopLine]
Meter=Shape
Shape=Rectangle 0,0,#WidthSmall#,3 | Fill Color #ColorVirtuRed# | StrokeWidth 0

[MeterTitle]
Meter=String
MeterStyle=StyleTextHeader
Text="╔══[ QUICK_LAUNCH ]══╗"
X=#PaddingMD#
Y=8

; ── SEPARATOR ──
[MeterSep1]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthSmall#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,60 | StrokeWidth 0
Y=8R

; ══════════════════════════════════════════════════════════════════════════════
; TERMINAL LAUNCHERS
; ══════════════════════════════════════════════════════════════════════════════

[MeterTermHeader]
Meter=String
MeterStyle=StyleTextLabel
Text="■ TERMINALS"
X=#PaddingMD#
Y=10R

[MeterLaunchWT]
Meter=String
MeterStyle=StyleButtonBase
Text="⚡ Windows Terminal"
X=#PaddingMD#
Y=5R
W=(#WidthSmall#-#PaddingMD#*2)
LeftMouseUpAction=["wt.exe"]
ToolTipText="Launch Windows Terminal"

[MeterLaunchPwsh]
Meter=String
MeterStyle=StyleButtonBase
Text="💠 PowerShell 7"
X=#PaddingMD#
Y=3R
W=(#WidthSmall#-#PaddingMD#*2)
LeftMouseUpAction=["pwsh.exe"]
ToolTipText="Launch PowerShell 7"

[MeterLaunchWSL]
Meter=String
MeterStyle=StyleButtonBase
Text="🐧 WSL (Ubuntu)"
X=#PaddingMD#
Y=3R
W=(#WidthSmall#-#PaddingMD#*2)
LeftMouseUpAction=["wsl.exe"]
ToolTipText="Launch WSL"

; ── SEPARATOR ──
[MeterSep2]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthSmall#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,40 | StrokeWidth 0
Y=8R

; ══════════════════════════════════════════════════════════════════════════════
; DEVELOPMENT TOOLS
; ══════════════════════════════════════════════════════════════════════════════

[MeterDevHeader]
Meter=String
MeterStyle=StyleTextLabel
Text="■ DEV_TOOLS"
X=#PaddingMD#
Y=10R

[MeterLaunchVSCode]
Meter=String
MeterStyle=StyleButtonBase
Text="📝 VS Code"
X=#PaddingMD#
Y=5R
W=(#WidthSmall#-#PaddingMD#*2)
LeftMouseUpAction=["code"]
ToolTipText="Launch Visual Studio Code"

[MeterLaunchDocker]
Meter=String
MeterStyle=StyleButtonBase
Text="🐳 Docker Desktop"
X=#PaddingMD#
Y=3R
W=(#WidthSmall#-#PaddingMD#*2)
LeftMouseUpAction=["C:\Program Files\Docker\Docker\Docker Desktop.exe"]
ToolTipText="Launch Docker Desktop"

[MeterLaunchPostman]
Meter=String
MeterStyle=StyleButtonBase
Text="📮 Postman"
X=#PaddingMD#
Y=3R
W=(#WidthSmall#-#PaddingMD#*2)
LeftMouseUpAction=["#PROGRAMFILES#\Postman\Postman.exe"]
ToolTipText="Launch Postman"

; ── SEPARATOR ──
[MeterSep3]
Meter=Shape
Shape=Rectangle #PaddingMD#,0,(#WidthSmall#-#PaddingMD#*2),1 | Fill Color #ColorSteel#,40 | StrokeWidth 0
Y=8R

; ══════════════════════════════════════════════════════════════════════════════
; UTILITIES
; ══════════════════════════════════════════════════════════════════════════════

[MeterUtilHeader]
Meter=String
MeterStyle=StyleTextLabel
Text="■ UTILITIES"
X=#PaddingMD#
Y=10R

[MeterLaunchTaskMgr]
Meter=String
MeterStyle=StyleButtonBase
Text="📊 Task Manager"
X=#PaddingMD#
Y=5R
W=(#WidthSmall#-#PaddingMD#*2)
LeftMouseUpAction=["taskmgr.exe"]
ToolTipText="Launch Task Manager"

[MeterLaunchSettings]
Meter=String
MeterStyle=StyleButtonBase
Text="⚙️ Settings"
X=#PaddingMD#
Y=3R
W=(#WidthSmall#-#PaddingMD#*2)
LeftMouseUpAction=["ms-settings:"]
ToolTipText="Open Windows Settings"

[MeterLaunchExplorer]
Meter=String
MeterStyle=StyleButtonBase
Text="📁 File Explorer"
X=#PaddingMD#
Y=3R
W=(#WidthSmall#-#PaddingMD#*2)
LeftMouseUpAction=["explorer.exe"]
ToolTipText="Open File Explorer"

; ── FOOTER ──
[MeterBottomLine]
Meter=Shape
Shape=Rectangle 0,0,#WidthSmall#,3 | Fill Color #ColorVirtuRed# | StrokeWidth 0
Y=12R
```

---

## Installation & Layout Script

Save as `Install-TBARainmeter.ps1`:

```powershell
#Requires -RunAsAdministrator
# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  TBA SINGULARITY OS — RAINMETER INSTALLER                                  ║
# ╚════════════════════════════════════════════════════════════════════════════╝

$ErrorActionPreference = "Stop"

Write-Host @"
╔════════════════════════════════════════════════════════════════════════════╗
║  TBA SINGULARITY OS // RAINMETER SUITE INSTALLER                           ║
╚════════════════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Red

# Paths
$rainmeterPath = "$env:USERPROFILE\Documents\Rainmeter\Skins\TheBlackAgency"
$directories = @(
    "$rainmeterPath\@Resources",
    "$rainmeterPath\@Resources\Scripts",
    "$rainmeterPath\@Resources\Images",
    "$rainmeterPath\@Resources\Fonts",
    "$rainmeterPath\System",
    "$rainmeterPath\Network",
    "$rainmeterPath\ThreatIntel",
    "$rainmeterPath\Services",
    "$rainmeterPath\Clock",
    "$rainmeterPath\Disk",
    "$rainmeterPath\GPU",
    "$rainmeterPath\Launcher"
)

Write-Host "[1/3] Creating directory structure..." -ForegroundColor Cyan

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    Write-Host "  ✓ $dir" -ForegroundColor Gray
}

Write-Host "[2/3] Installing JetBrains Mono font..." -ForegroundColor Cyan

# Download and install JetBrains Mono if not present
$fontName = "JetBrains Mono"
$fonts = (New-Object -ComObject Shell.Application).Namespace(0x14)
$installedFonts = $fonts.Items() | ForEach-Object { $_.Name }

if ($installedFonts -notcontains "JetBrains Mono Regular") {
    Write-Host "  Downloading JetBrains Mono..." -ForegroundColor Yellow
    $fontUrl = "https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip"
    $fontZip = "$env:TEMP\JetBrainsMono.zip"
    $fontExtract = "$env:TEMP\JetBrainsMono"
    
    try {
        Invoke-WebRequest -Uri $fontUrl -OutFile $fontZip
        Expand-Archive -Path $fontZip -DestinationPath $fontExtract -Force
        
        $fontFiles = Get-ChildItem -Path "$fontExtract\fonts\ttf" -Filter "*.ttf"
        foreach ($font in $fontFiles) {
            Copy-Item $font.FullName "C:\Windows\Fonts\" -Force
        }
        
        Write-Host "  ✓ JetBrains Mono installed" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠ Could not install font automatically. Please install JetBrains Mono manually." -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✓ JetBrains Mono already installed" -ForegroundColor Green
}

Write-Host "[3/3] Configuration complete!" -ForegroundColor Cyan

Write-Host @"

╔════════════════════════════════════════════════════════════════════════════╗
║  INSTALLATION COMPLETE                                                     ║
╠════════════════════════════════════════════════════════════════════════════╣
║  Skin directory: $rainmeterPath
║                                                                            ║
║  Next steps:                                                               ║
║  1. Copy the .ini files to their respective folders                        ║
║  2. Copy Variables.inc and Styles.inc to @Resources                        ║
║  3. Open Rainmeter -> Manage -> Refresh All                                ║
║  4. Load skins: Right-click skin -> Load                                   ║
║                                                                            ║
║  Recommended layout (right side of screen):                                ║
║  ┌────────────────┐                                                        ║
║  │     Clock      │ <- Top right corner                                    ║
║  ├────────────────┤                                                        ║
║  │    System      │                                                        ║
║  ├────────────────┤                                                        ║
║  │    Network     │                                                        ║
║  ├────────────────┤                                                        ║
║  │   Services     │                                                        ║
║  ├────────────────┤                                                        ║
║  │  ThreatIntel   │                                                        ║
║  └────────────────┘                                                        ║
╚════════════════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Green
```

---

## Layout Configuration: `Rainmeter.ini` Settings

Add to your `%APPDATA%\Rainmeter\Rainmeter.ini`:

```ini
[TheBlackAgency\Clock]
Active=1
WindowX=(#SCREENAREAWIDTH#-220)
WindowY=20
SavePosition=1
AlwaysOnTop=1
Draggable=1
SnapEdges=1
ClickThrough=0
KeepOnScreen=1

[TheBlackAgency\System]
Active=1
WindowX=(#SCREENAREAWIDTH#-300)
WindowY=150
SavePosition=1
AlwaysOnTop=1

[TheBlackAgency\Network]
Active=1
WindowX=(#SCREENAREAWIDTH#-300)
WindowY=420
SavePosition=1
AlwaysOnTop=1

[TheBlackAgency\Services]
Active=1
WindowX=(#SCREENAREAWIDTH#-300)
WindowY=680
SavePosition=1
AlwaysOnTop=1

[TheBlackAgency\ThreatIntel]
Active=1
WindowX=(#SCREENAREAWIDTH#-370)
WindowY=950
SavePosition=1
AlwaysOnTop=1

[TheBlackAgency\Launcher]
Active=1
WindowX=(#SCREENAREAWIDTH#-220)
WindowY=(#SCREENAREAHEIGHT#-350)
SavePosition=1
AlwaysOnTop=1
```

---

## Summary

<details>
<summary><strong>📦 Included Modules</strong></summary>

| Module | Description | Update Rate |
|--------|-------------|-------------|
| **System** | CPU, RAM, SWAP with histograms | 1s |
| **Network** | Traffic graphs, IP masking, latency | 1s |
| **ThreatIntel** | Live RSS feeds from security sources | 15m |
| **Services** | Docker, WSL, Ollama, Defender status | 5s |
| **Clock** | Time, date, UTC reference | 1s |
| **Disk** | Storage usage, I/O activity | 5s |
| **GPU** | NVIDIA GPU monitoring | 1s |
| **Launcher** | Quick access buttons | Static |

</details>

<details>
<summary><strong>🎨 Color Synchronization</strong></summary>

All colors match the terminal configurations:

| Color | Hex | Usage |
|-------|-----|-------|
| Virtu Red | `#FF1744` | Primary accent, headers |
| Void Black | `#0A0A0C` | Backgrounds |
| Nexus Cyan | `#00E5FF` | Secondary accent, network |
| Warning | `#FFD600` | Alerts, disk usage |
| Success | `#00E676` | Online status, GPU |
| Error | `#FF1744` | Offline status, threats |

</details>

<details>
<summary><strong>⚡ Features</strong></summary>

- **Auto-hide on fullscreen** apps/games
- **IP address masking** (hover to reveal)
- **Click-to-copy** IP address
- **Live threat feeds** with clickable links
- **Service auto-detection** for Docker, WSL, Ollama
- **NVIDIA GPU support** via nvidia-smi
- **HiDPI scaling** support
- **Low resource usage** optimized update rates

</details>