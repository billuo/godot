$ErrorActionPreference = "Stop"

# [string[]] $CommonArgs = "use_llvm=yes", "CC=clang", "CXX=clang++", "-j 28"
[string[]] $CommonArgs = "-j 28", "compiledb=no"

# For web, aim to minimize binary size above everything else.
[string[]] $WebTemplateArgs = "optimize=size", "debug_symbols=no", "thread=yes"
# $WebTemplateArgs += "module_text_server_adv_enabled=no", "module_text_server_fb_enabled=yes"

$TemplateOutDir = "$env:APPDATA/godot/export_templates/4.3.dev"

git checkout custom-build
git pull

scons $CommonArgs compiledb=yes

# templates
scons target=template_debug $CommonArgs
scons target=template_release $CommonArgs
Copy-Item bin\godot.windows.template_debug.x86_64.exe $TemplateOutDir\windows_debug_x86_64.exe -Force
Copy-Item bin\godot.windows.template_release.x86_64.exe $TemplateOutDir\windows_release_x86_64.exe -Force

scons platform=web target=template_debug $CommonArgs $WebTemplateArgs disable_3d=yes lto=thin
scons platform=web target=template_release $CommonArgs $WebTemplateArgs disable_3d=yes lto=thin
Copy-Item bin\godot.web.template_debug.wasm32.zip $TemplateOutDir\web_debug-no3d.zip -Force
Copy-Item bin\godot.web.template_release.wasm32.zip $TemplateOutDir\web_release-no3d.zip -Force

scons platform=web target=template_debug $CommonArgs $WebTemplateArgs lto=thin
scons platform=web target=template_release $CommonArgs $WebTemplateArgs lto=thin
Copy-Item bin\godot.web.template_debug.wasm32.zip $TemplateOutDir\web_debug.zip -Force
Copy-Item bin\godot.web.template_release.wasm32.zip $TemplateOutDir\web_release.zip -Force

scons platform=android target=template_debug arch=arm32 $CommonArgs
scons platform=android target=template_debug arch=arm64 $CommonArgs
scons platform=android target=template_release arch=arm32 $CommonArgs
scons platform=android target=template_release arch=arm64 $CommonArgs
Set-Location platform/android/java
.\gradlew generateGodotTemplates
Set-Location ../../..
Copy-Item bin\android_debug.apk $TemplateOutDir\ -Force
Copy-Item bin\android_release.apk $TemplateOutDir\ -Force
