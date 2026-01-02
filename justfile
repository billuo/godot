set shell := ["powershell.exe", "-c"]

build_editor:
	scons -j14 compiledb=yes

build_export_web:
	scons -j14 target=template_debug   platform=web optimize=size lto=none debug_symbols=yes javascript_eval=no     dlink_enabled=yes threads=yes
	scons -j14 target=template_release platform=web optimize=size lto=full debug_symbols=no  javascript_eval=no     dlink_enabled=yes threads=yes
	scons -j14 target=template_debug   platform=web optimize=size lto=none debug_symbols=yes javascript_eval=no     dlink_enabled=yes threads=no
	scons -j14 target=template_release platform=web optimize=size lto=full debug_symbols=no  javascript_eval=no     dlink_enabled=yes threads=no

build_export_windows:
	scons -j14 target=template_debug platform=windows production=yes threads=yes debug_symbols=yes
	scons -j14 target=template_release platform=windows production=yes threads=yes debug_symbols=no

build_export_android version:
	scons -j14 target=template_debug   platform=android arch=arm32 generate_android_binaries=no  optimize=size thread=yes debug_symbols=yes
	scons -j14 target=template_debug   platform=android arch=arm64 generate_android_binaries=yes optimize=size thread=yes debug_symbols=yes
	cp bin\android_debug.apk $env:APPDATA\Godot\export_templates\{{version}}
	scons -j14 target=template_release platform=android arch=arm32 generate_android_binaries=no  optimize=size thread=yes debug_symbols=no
	scons -j14 target=template_release platform=android arch=arm64 generate_android_binaries=yes optimize=size thread=yes debug_symbols=no
	cp bin\android_release.apk $env:APPDATA\Godot\export_templates\{{version}}

copy_editor:
	cp bin\godot.windows.editor.x86_64.console.exe C:\software\godot-custom
	cp bin\godot.windows.editor.x86_64.exe C:\software\godot-custom

copy_export version:
	cp bin\godot.web.template_debug.wasm32.dlink.zip $env:APPDATA\Godot\export_templates\{{version}}\web_dlink_debug.zip
	cp bin\godot.web.template_release.wasm32.dlink.zip $env:APPDATA\Godot\export_templates\{{version}}\web_dlink_release.zip
	cp bin\godot.web.template_debug.wasm32.nothreads.dlink.zip $env:APPDATA\Godot\export_templates\{{version}}\web_dlink_nothreads_debug.zip
	cp bin\godot.web.template_release.wasm32.nothreads.dlink.zip $env:APPDATA\Godot\export_templates\{{version}}\web_dlink_nothreads_release.zip
	cp bin\godot.windows.template_debug.x86_64.exe $env:APPDATA\Godot\export_templates\{{version}}\windows_debug_x86_64.exe
	cp bin\godot.windows.template_release.x86_64.exe $env:APPDATA\Godot\export_templates\{{version}}\windows_release_x86_64.exe
