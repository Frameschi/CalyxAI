; Installer script for Calyx AI
; Copyright (c) 2025 ARCROSS

!macro preInit
    SetRegView 64
    WriteRegExpandStr HKLM "${INSTALL_REGISTRY_KEY}" InstallLocation "$INSTDIR"
    WriteRegExpandStr HKCU "${INSTALL_REGISTRY_KEY}" InstallLocation "$INSTDIR"
    SetRegView 32
    WriteRegExpandStr HKLM "${INSTALL_REGISTRY_KEY}" InstallLocation "$INSTDIR"
    WriteRegExpandStr HKCU "${INSTALL_REGISTRY_KEY}" InstallLocation "$INSTDIR"
!macroend

; Custom installer pages
!macro customInstall
    ; Create desktop shortcut with custom icon
    CreateShortCut "$DESKTOP\Calyx AI.lnk" "$INSTDIR\Calyx AI.exe" "" "$INSTDIR\resources\logo.png"
    
    ; Create start menu entries
    CreateDirectory "$SMPROGRAMS\ARCROSS"
    CreateShortCut "$SMPROGRAMS\ARCROSS\Calyx AI.lnk" "$INSTDIR\Calyx AI.exe" "" "$INSTDIR\resources\logo.png"
    CreateShortCut "$SMPROGRAMS\ARCROSS\Uninstall Calyx AI.lnk" "$INSTDIR\Uninstall Calyx AI.exe"
!macroend

; Custom uninstaller
!macro customUnInstall
    Delete "$DESKTOP\Calyx AI.lnk"
    Delete "$SMPROGRAMS\ARCROSS\Calyx AI.lnk"
    Delete "$SMPROGRAMS\ARCROSS\Uninstall Calyx AI.lnk"
    RMDir "$SMPROGRAMS\ARCROSS"
!macroend
