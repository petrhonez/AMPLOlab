[Setup]
AppName=AMPLOlab
AppVersion=1.0
DefaultDirName={autopf}\AMPLOlab
DefaultGroupName=AMPLOlab
OutputDir=dist
OutputBaseFilename=AMPLOlab_Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; The executable and all other application files
Source: "dist\AMPLOlab\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Font installation
Source: "CascadiaCode.ttf"; DestDir: "{autofonts}"; FontInstall: "Cascadia Code"

[Icons]
Name: "{group}\AMPLOlab"; Filename: "{app}\AMPLOlab.exe"
Name: "{autodesktop}\AMPLOlab"; Filename: "{app}\AMPLOlab.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\AMPLOlab.exe"; Description: "{cm:LaunchProgram,AMPLOlab}"; Flags: nowait postinstall skipifsilent
