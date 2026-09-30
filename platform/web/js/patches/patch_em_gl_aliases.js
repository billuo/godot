/**************************************************************************/
/*  patch_em_gl_aliases.js                                                */
/**************************************************************************/
/*                         This file is part of:                          */
/*                             GODOT ENGINE                               */
/*                        https://godotengine.org                         */
/**************************************************************************/
/* Copyright (c) 2014-present Godot Engine contributors (see AUTHORS.md). */
/* Copyright (c) 2007-2014 Juan Linietsky, Ariel Manzur.                  */
/*                                                                        */
/* Permission is hereby granted, free of charge, to any person obtaining  */
/* a copy of this software and associated documentation files (the        */
/* "Software"), to deal in the Software without restriction, including    */
/* without limitation the rights to use, copy, modify, merge, publish,    */
/* distribute, sublicense, and/or sell copies of the Software, and to     */
/* permit persons to whom the Software is furnished to do so, subject to  */
/* the following conditions:                                              */
/*                                                                        */
/* The above copyright notice and this permission notice shall be         */
/* included in all copies or substantial portions of the Software.        */
/*                                                                        */
/* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,        */
/* EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF     */
/* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. */
/* IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY   */
/* CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,   */
/* TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE      */
/* SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                 */
/**************************************************************************/

// Emscripten defines the GL functions as `glFoo`, renames them to
// `emscripten_glFoo`, and keeps `glFoo` as an alias of it (see
// `recordGLProcAddressGet` in Emscripten's libwebgl.js). Aliases that point at
// another GL function, such as `glGetVertexAttribIuiv`, end up as
// `emscripten_glGetVertexAttribIuiv` pointing at `glGetVertexAttribIiv`.
//
// With threads and an offscreen framebuffer enabled, Emscripten links the
// pthread GL shims (system/lib/gl/webgl1.c and webgl2.c) into the module, which
// exports the `glFoo` symbols. Emscripten treats an alias whose target is a wasm
// export as a "native alias": it skips the declaration and binds the symbol only
// after the wasm module has been instantiated. That breaks the startup twice:
// - the emitted signature assignment (`_emscripten_glFoo.sig = "..."`) has no
//   value to attach to, so the module throws while it is being created;
// - the shims import `emscripten_glFoo`, which is still undefined when the
//   module is instantiated, so the imports fail with "function import requires
//   a callable".
//
// Point those aliases at the renamed JS implementation instead, which is what
// Emscripten resolves them to when the shims aren't linked. The shims proxy the
// GL calls to the main thread before calling these functions, so this doesn't
// change which thread runs the WebGL calls.
//
// Emscripten 6.0.1 is affected. Remove this once Emscripten defines the symbol
// before building the wasm import object.
for (const [name, target] of Object.entries(LibraryManager.library)) {
	if (!name.startsWith('emscripten_gl') || typeof target != 'string' || !target.startsWith('gl')) {
		continue;
	}
	const implementation = `emscripten_${target}`;
	if (implementation in LibraryManager.library) {
		LibraryManager.library[name] = implementation;
	}
}
