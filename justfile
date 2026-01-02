set shell := ["pwsh", "-NoLogo", "-NoProfile", "-Command"]
set lazy

export_dir := `$env:APPDATA` + "\\Godot\\export_templates\\" + `python ./just_help.py version`
common_build_args := "-j14"
windows_build_args := "platform=windows accesskit=no angle=no threads=yes"
web_build_args := "platform=web optimize=size javascript_eval=no dlink_enabled=yes"
android_build_args := "platform=android optimize=size thread=yes"

_ensure_dir path:
    New-Item -ItemType Directory -Force -Path {{ path }} | Out-Null

# Sync the fork and fast-forward the master branch without introducing merge commits.
sync:
    gh repo sync billuo/godot -b master
    git fetch origin master:master

# Create a new custom-build branch off given commit.
new_branch branch_name commit:
    @git diff --quiet --exit-code;  if ($LASTEXITCODE -ne 0) { Write-Error "Unstaged changes; commit or stash them first."; exit 1 }
    @git diff --cached --quiet --exit-code; if ($LASTEXITCODE -ne 0) { Write-Error "Staged changes; commit or stash them first."; exit 1 }
    @just sync
    git checkout -b '{{ branch_name }}'
    git rebase {{ commit }}
    git push

# Create a new bugfix branch off latest master, consisting of only one given commit.
bugfix_branch issue desc commit:
    @git diff --quiet --exit-code;  if ($LASTEXITCODE -ne 0) { Write-Error "Unstaged changes; commit or stash them first."; exit 1 }
    @git diff --cached --quiet --exit-code; if ($LASTEXITCODE -ne 0) { Write-Error "Staged changes; commit or stash them first."; exit 1 }
    @just sync
    git checkout master
    git checkout -b 'bugfix/{{ issue }}-{{ desc }}'
    git cherry-pick {{ commit }}
    git push

# Commit a fixup and squash it into <commit>.
fixup commit:
    git commit --fixup {{ commit }}
    git -c sequence.editor=true rebase -i --autosquash {{ commit }}^

build_everything:
    @just build_editor
    @just copy_editor
    @just build_export_windows
    @just copy_export_windows
    @just build_export_web
    @just copy_export_web
    @just build_export_android
    @just copy_export_android

build_editor *args:
    scons {{ common_build_args }} {{ windows_build_args }} compiledb=yes  {{ args }}
build_editor_dev *args:
    @just build_editor dev_build=yes dev_mode=yes {{ args }}
copy_editor:
    Copy-Item bin\godot.windows.editor.x86_64.console.exe C:\software\godot-custom
    Copy-Item bin\godot.windows.editor.x86_64.exe C:\software\godot-custom

build_export_windows:
    scons {{ common_build_args }} target=template_debug   {{ windows_build_args }} production=yes debug_symbols=yes
    scons {{ common_build_args }} target=template_release {{ windows_build_args }} production=yes debug_symbols=no
copy_export_windows:
    @just _ensure_dir {{ export_dir }}
    Copy-Item bin\godot.windows.template_debug.x86_64.exe   {{ export_dir }}\windows_debug_x86_64.exe
    Copy-Item bin\godot.windows.template_release.x86_64.exe {{ export_dir }}\windows_release_x86_64.exe

build_export_web:
    scons {{ common_build_args }} {{ web_build_args }} target=template_debug   lto=none debug_symbols=yes threads=yes
    scons {{ common_build_args }} {{ web_build_args }} target=template_release lto=full debug_symbols=no  threads=yes
    scons {{ common_build_args }} {{ web_build_args }} target=template_debug   lto=none debug_symbols=yes threads=no
    scons {{ common_build_args }} {{ web_build_args }} target=template_release lto=full debug_symbols=no  threads=no
copy_export_web:
    @just _ensure_dir {{ export_dir }}
    Copy-Item bin\godot.web.template_debug.wasm32.dlink.zip             {{ export_dir }}\web_dlink_debug.zip
    Copy-Item bin\godot.web.template_release.wasm32.dlink.zip           {{ export_dir }}\web_dlink_release.zip
    Copy-Item bin\godot.web.template_debug.wasm32.nothreads.dlink.zip   {{ export_dir }}\web_dlink_nothreads_debug.zip
    Copy-Item bin\godot.web.template_release.wasm32.nothreads.dlink.zip {{ export_dir }}\web_dlink_nothreads_release.zip

android_prerequisites := `python ./just_help.py extract-android-sdk-packages`
install_android_prerequisites:
    C:\dev\android-sdk\cmdline-tools\bin\sdkmanager.bat --sdk_root=C:\dev\android-sdk  {{ android_prerequisites }}

build_export_android:
    scons {{ common_build_args }} {{ android_build_args }} target=template_debug   arch=arm32 debug_symbols=yes
    scons {{ common_build_args }} {{ android_build_args }} target=template_debug   arch=arm64 debug_symbols=yes generate_android_binaries=yes
    scons {{ common_build_args }} {{ android_build_args }} target=template_release arch=arm32 debug_symbols=no
    scons {{ common_build_args }} {{ android_build_args }} target=template_release arch=arm64 debug_symbols=no  generate_android_binaries=yes

copy_export_android:
    @just _ensure_dir {{ export_dir }}
    Copy-Item bin\android_debug.apk   {{ export_dir }}
    Copy-Item bin\android_release.apk {{ export_dir }}
