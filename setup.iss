; Hiandco Tech ERP - Inno Setup Script
; Bu dosya profesyonel bir Windows kurulum sihirbazı oluşturur

[Setup]
; Uygulama bilgileri
AppId={{B7A3F2E1-4D5C-6E8F-9A1B-2C3D4E5F6A7B}
AppName=Hiandco Tech ERP
AppVersion=1.0.0
AppVerName=Hiandco Tech ERP 1.0.0
AppPublisher=Hiandco Tech
AppPublisherURL=https://hiandco.tr
DefaultDirName={autopf}\HiandcoTechERP
DefaultGroupName=Hiandco Tech ERP
DisableProgramGroupPage=yes

; Çıkış dosyası
OutputDir=installer_output
OutputBaseFilename=HiandcoTechERP_Setup_v1.0.0
SetupIconFile=assets\favicon.ico

; Sıkıştırma
Compression=lzma2/ultra64
SolidCompression=yes

; Minimum Windows 10
MinVersion=10.0

; Yönetici hakları gerektirme (kullanıcı klasörüne kurulabilir)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Görsel ayarlar
WizardStyle=modern
WizardSizePercent=110

; Uninstall bilgileri
UninstallDisplayIcon={app}\HiandcoTechERP.exe
UninstallDisplayName=Hiandco Tech ERP

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstüne kısayol oluştur"; GroupDescription: "Ek simgeler:"; Flags: checkedonce

[Files]
; Ana exe ve tüm dosyalar
Source: "dist\HiandcoTechERP\HiandcoTechERP.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\HiandcoTechERP\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Masaüstü kısayolu
Name: "{autodesktop}\Hiandco Tech ERP"; Filename: "{app}\HiandcoTechERP.exe"; Tasks: desktopicon
; Başlat menüsü
Name: "{group}\Hiandco Tech ERP"; Filename: "{app}\HiandcoTechERP.exe"
Name: "{group}\Hiandco Tech ERP Kaldır"; Filename: "{uninstallexe}"

[Run]
; Kurulum sonrası uygulamayı başlat seçeneği
Filename: "{app}\HiandcoTechERP.exe"; Description: "Hiandco Tech ERP'yi şimdi başlat"; Flags: nowait postinstall skipifsilent shellexec
