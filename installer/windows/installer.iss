; OrpheusDL-GUI Installer Script for Inno Setup
; Requires Inno Setup 6.0 or later

#define MyAppName "OrpheusDL GUI"
#include "version.iss"
#define MyAppPublisher "OrpheusDL"
#define MyAppURL "https://github.com/bascurtiz/orpheusdl-gui"
#define MyAppExeName "OrpheusDL_GUI.exe"
#define SourcePath "..\..\dist"

[Setup]

AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}

RestartApplications=no
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}

AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

OutputDir=..\..\dist
OutputBaseFilename=OrpheusDL_GUI-Setup-{#MyAppVersion}

SetupIconFile=..\..\icon.ico

Compression=lzma2
SolidCompression=yes

WizardStyle=modern
WizardImageFile=wizard_image.bmp
WizardSmallImageFile=wizard_small_image.bmp

PrivilegesRequired=lowest

AllowNoIcons=yes
DisableProgramGroupPage=yes
CloseApplications=no

UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]

Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Types]

Name: "full"; Description: "Full installation (all modules)"
Name: "compact"; Description: "Compact installation (core only)"
Name: "custom"; Description: "Custom installation"; Flags: iscustom

[Components]

Name: "main"; Description: "OrpheusDL-GUI Core (required)"; Types: full compact custom; Flags: fixed

Name: "ffmpeg"; Description: "FFmpeg (Included - Recommended for conversions)"; Types: full custom; Flags: fixed
Name: "deno"; Description: "Deno (Required for YouTube module)"; Types: full custom; Flags: fixed

Name: "modules"; Description: "Music Platform Modules"; Types: full custom
Name: "modules\applemusic"; Description: "Apple Music"; Types: full custom
Name: "modules\beatport"; Description: "Beatport"; Types: full custom
Name: "modules\beatsource"; Description: "Beatsource"; Types: full custom
Name: "modules\deezer"; Description: "Deezer"; Types: full custom
Name: "modules\qobuz"; Description: "Qobuz"; Types: full custom
Name: "modules\soundcloud"; Description: "SoundCloud"; Types: full custom
Name: "modules\spotify"; Description: "Spotify"; Types: full custom
Name: "modules\tidal"; Description: "Tidal"; Types: full custom
Name: "modules\youtube"; Description: "YouTube"; Types: full custom

[Tasks]

Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]

Source: "{#SourcePath}\{#MyAppExeName}"; DestDir: "{app}"; Components: main; Flags: ignoreversion

Source: "{#SourcePath}\config\*"; DestDir: "{app}\config"; Components: main; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

Source: "..\..\orpheus\*"; DestDir: "{app}\orpheus"; Components: main; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\..\utils\*"; DestDir: "{app}\utils"; Components: main; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\..\orpheus.py"; DestDir: "{app}"; Components: main; Flags: ignoreversion skipifsourcedoesntexist

Source: "..\..\icon.ico"; DestDir: "{app}"; Components: main; Flags: ignoreversion
Source: "..\..\icon.png"; DestDir: "{app}"; Components: main; Flags: ignoreversion

Source: "..\..\platforms\*"; DestDir: "{app}\platforms"; Components: main; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

Source: "..\..\ffmpeg.exe"; DestDir: "{app}"; Components: ffmpeg; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\..\ffprobe.exe"; DestDir: "{app}"; Components: ffmpeg; Flags: ignoreversion skipifsourcedoesntexist

Source: "..\..\deno.exe"; DestDir: "{app}"; Components: deno; Flags: ignoreversion skipifsourcedoesntexist

Source: "..\..\modules\applemusic\*"; DestDir: "{app}\modules\applemusic"; Components: modules\applemusic; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\..\modules\beatport\*"; DestDir: "{app}\modules\beatport"; Components: modules\beatport; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\..\modules\beatsource\*"; DestDir: "{app}\modules\beatsource"; Components: modules\beatsource; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\..\modules\deezer\*"; DestDir: "{app}\modules\deezer"; Components: modules\deezer; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\..\modules\qobuz\*"; DestDir: "{app}\modules\qobuz"; Components: modules\qobuz; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\..\modules\soundcloud\*"; DestDir: "{app}\modules\soundcloud"; Components: modules\soundcloud; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\..\modules\spotify\*"; DestDir: "{app}\modules\spotify"; Components: modules\spotify; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\..\modules\tidal\*"; DestDir: "{app}\modules\tidal"; Components: modules\tidal; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\..\modules\youtube\*"; DestDir: "{app}\modules\youtube"; Components: modules\youtube; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

Source: "..\..\modules\__init__.py"; DestDir: "{app}\modules"; Components: main; Flags: ignoreversion skipifsourcedoesntexist

[Icons]

Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]

Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]

Type: filesandordirs; Name: "{app}\config"
Type: filesandordirs; Name: "{app}\downloads"
Type: filesandordirs; Name: "{app}\temp"

[Code]

var
  DenoIndex: Integer;
  YouTubeIndex: Integer;

procedure ComponentsListClickCheck(Sender: TObject);
begin
  if (YouTubeIndex <> -1) and (DenoIndex <> -1) then
  begin
    if WizardForm.ComponentsList.Checked[YouTubeIndex] then
      WizardForm.ComponentsList.Checked[DenoIndex] := True
    else
      WizardForm.ComponentsList.Checked[DenoIndex] := False;
  end;
end;

procedure InitializeWizard;
var
  I: Integer;
begin
  WizardForm.WelcomeLabel2.Caption :=
    'This will install {#MyAppName} on your computer.' + #13#10 + #13#10 +
    'OrpheusDL-GUI is a graphical interface for downloading music from various platforms.' + #13#10 + #13#10 +
    'You will be able to select which music platform modules to install.';

  DenoIndex := -1;
  YouTubeIndex := -1;

  for I := 0 to WizardForm.ComponentsList.Items.Count - 1 do
  begin
    if Pos('Deno', WizardForm.ComponentsList.ItemCaption[I]) > 0 then
      DenoIndex := I;

    if Pos('YouTube', WizardForm.ComponentsList.ItemCaption[I]) > 0 then
      YouTubeIndex := I;
  end;

  if (DenoIndex <> -1) and (YouTubeIndex <> -1) then
    WizardForm.ComponentsList.OnClickCheck := @ComponentsListClickCheck;
end;