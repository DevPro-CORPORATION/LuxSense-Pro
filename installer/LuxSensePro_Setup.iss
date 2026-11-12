; LuxSense Pro — Inno Setup 6 Script
; Builds production Windows installer for LuxSense Pro with update & bootstrapper support

#define MyAppName "LuxSense Pro"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "DevPro-CORP"
#define MyAppURL "https://devpro-corporation.github.io/luxsense-pro/"
#define MyAppExeName "LuxSensePro.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{E8B291A4-7D68-4F15-B621-3D5F9A1054C1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}docs/faq.html
AppUpdatesURL={#MyAppURL}#downloads
DefaultDirName={autopf}\DevPro\{#MyAppName}
DefaultGroupName=DevPro\{#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=..\dist_installer
OutputBaseFilename=LuxSense-Pro-Setup-v{#MyAppVersion}
SetupIconFile=..\my_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
CloseApplicationsFilter=*.exe
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\updater.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\my_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\firmware\LuxSense_Arduino\LuxSense_Arduino.ino"; DestDir: "{app}\firmware"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\my_icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\my_icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// User settings and SQLite measurements are stored in APPDATA and are preserved during updates and uninstalls.
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
