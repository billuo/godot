/**************************************************************************/
/*  test_canvas_item.cpp                                                  */
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

#include "tests/test_macros.h"

TEST_FORCE_LINK(test_canvas_item)

#include "scene/2d/node_2d.h"
#include "scene/2d/sprite_2d.h"
#include "scene/main/scene_tree.h"
#include "scene/main/window.h"
#include "scene/resources/material.h"
#include "tests/signal_watcher.h"

namespace TestCanvasItem {

static Sprite2D *make_sprite(Node *p_parent) {
	Sprite2D *sprite = memnew(Sprite2D);
	p_parent->add_child(sprite);
	return sprite;
}

static Ref<ShaderMaterial> make_material() {
	Ref<ShaderMaterial> material;
	material.instantiate();
	return material;
}

TEST_CASE("[SceneTree][CanvasItem] Instance shader parameters are refreshed when material changes") {
	Sprite2D *item = memnew(Sprite2D);
	Ref<ShaderMaterial> material = make_material();
	Ref<ShaderMaterial> other_material = make_material();

	SIGNAL_WATCH(item, CoreStringName(property_list_changed));

	Array empty_args = { {} };

	SUBCASE("Assigning a material") {
		item->set_material(material);
		SIGNAL_CHECK("property_list_changed", empty_args);
	}

	SUBCASE("Clearing the material") {
		item->set_material(material);
		SIGNAL_DISCARD("property_list_changed");

		item->set_material(Ref<Material>());
		SIGNAL_CHECK("property_list_changed", empty_args);

		material->notify_property_list_changed();
		SIGNAL_CHECK_FALSE("property_list_changed");
	}

	SUBCASE("Editing the material") {
		item->set_material(material);
		SIGNAL_DISCARD("property_list_changed");
		material->notify_property_list_changed();
		SIGNAL_CHECK("property_list_changed", empty_args);
	}

	SUBCASE("Replacing the material") {
		item->set_material(material);
		SIGNAL_DISCARD("property_list_changed");

		item->set_material(other_material);
		SIGNAL_CHECK("property_list_changed", empty_args);

		// The replaced material must not be tracked anymore...
		material->notify_property_list_changed();
		SIGNAL_CHECK_FALSE("property_list_changed");

		// ...and the new one must be.
		other_material->notify_property_list_changed();
		SIGNAL_CHECK("property_list_changed", empty_args);
	}

	SUBCASE("Assigning the same material again") {
		item->set_material(material);
		item->set_material(material);
		SIGNAL_DISCARD("property_list_changed");

		// Must not be connected twice.
		material->notify_property_list_changed();
		SIGNAL_CHECK("property_list_changed", empty_args);
	}

	SUBCASE("Switching to/from the parent material") {
		item->set_use_parent_material(true);
		SIGNAL_CHECK("property_list_changed", empty_args);

		item->set_use_parent_material(false);
		SIGNAL_CHECK("property_list_changed", empty_args);

		item->set_use_parent_material(false);
		SIGNAL_CHECK("property_list_changed", empty_args);
	}

	SIGNAL_UNWATCH(item, CoreStringName(property_list_changed));
	memdelete(item);
}

TEST_CASE("[SceneTree][CanvasItem] Instance shader parameters are refreshed when children use the parent material") {
	Window *root = SceneTree::get_singleton()->get_root();
	Sprite2D *parent = make_sprite(root);
	Sprite2D *child = make_sprite(parent);
	Sprite2D *grandchild = make_sprite(child);
	Ref<ShaderMaterial> material = make_material();

	parent->set_material(material);
	child->set_use_parent_material(true);
	grandchild->set_use_parent_material(true);

	Array empty_args = { {} };

	SUBCASE("Child") {
		SIGNAL_WATCH(child, CoreStringName(property_list_changed));
		material->notify_property_list_changed();
		SIGNAL_CHECK("property_list_changed", empty_args);
		SIGNAL_UNWATCH(child, CoreStringName(property_list_changed));
	}

	SUBCASE("Grandchild") {
		SIGNAL_WATCH(grandchild, CoreStringName(property_list_changed));
		material->notify_property_list_changed();
		SIGNAL_CHECK("property_list_changed", empty_args);
		SIGNAL_UNWATCH(grandchild, CoreStringName(property_list_changed));
	}

	SUBCASE("Child, after the parent material was replaced") {
		SIGNAL_WATCH(child, CoreStringName(property_list_changed));
		parent->set_material(make_material());
		SIGNAL_CHECK("property_list_changed", empty_args);
		SIGNAL_UNWATCH(child, CoreStringName(property_list_changed));
	}

	SUBCASE("Grandchild, after its parent stopped using the parent material") {
		SIGNAL_WATCH(grandchild, CoreStringName(property_list_changed));
		child->set_use_parent_material(false);
		SIGNAL_CHECK("property_list_changed", empty_args);
		material->notify_property_list_changed();
		SIGNAL_CHECK_FALSE("property_list_changed");
		SIGNAL_UNWATCH(grandchild, CoreStringName(property_list_changed));
	}

	SUBCASE("Items reparented to another item") {
		Sprite2D *other = make_sprite(root);
		Array two_empty_args = { {}, {} };
		SIGNAL_WATCH(child, CoreStringName(property_list_changed));
		SIGNAL_WATCH(grandchild, CoreStringName(property_list_changed));
		child->reparent(other);
		SIGNAL_CHECK("property_list_changed", two_empty_args);
		SIGNAL_UNWATCH(child, CoreStringName(property_list_changed));
		SIGNAL_UNWATCH(grandchild, CoreStringName(property_list_changed));
		memdelete(other);
	}

	memdelete(parent);
}

TEST_CASE("[SceneTree][CanvasItem] Instance shader parameters are refreshed when children use the parent material and have their own materials") {
	Window *root = SceneTree::get_singleton()->get_root();
	Sprite2D *parent = make_sprite(root);
	Sprite2D *child = make_sprite(parent);
	Sprite2D *top_level_child = make_sprite(parent);
	Node2D *node2d = memnew(Node2D);
	parent->add_child(node2d);
	Sprite2D *child_of_node2d = make_sprite(node2d);
	Ref<ShaderMaterial> material = make_material();
	Ref<ShaderMaterial> child_material = make_material();
	Ref<ShaderMaterial> top_level_material = make_material();
	Ref<ShaderMaterial> node2d_child_material = make_material();

	parent->set_material(material);
	child->set_material(child_material);
	child->set_use_parent_material(true);
	top_level_child->set_material(top_level_material);
	top_level_child->set_use_parent_material(true);
	top_level_child->set_as_top_level(true);
	child_of_node2d->set_material(node2d_child_material);
	child_of_node2d->set_use_parent_material(true);

	Array empty_args = { {} };

	SUBCASE("Child using the parent material") {
		SIGNAL_WATCH(child, CoreStringName(property_list_changed));

		// The own material is ignored...
		child_material->notify_property_list_changed();
		SIGNAL_CHECK_FALSE("property_list_changed");

		// ...and the inherited one is used instead.
		material->notify_property_list_changed();
		SIGNAL_CHECK("property_list_changed", empty_args);

		SIGNAL_UNWATCH(child, CoreStringName(property_list_changed));
	}

	SUBCASE("Top level child") {
		SIGNAL_WATCH(top_level_child, CoreStringName(property_list_changed));

		// A top level item ignores its parent...
		material->notify_property_list_changed();
		SIGNAL_CHECK_FALSE("property_list_changed");

		// ...and falls back to its own material.
		top_level_material->notify_property_list_changed();
		SIGNAL_CHECK("property_list_changed", empty_args);

		SIGNAL_UNWATCH(top_level_child, CoreStringName(property_list_changed));
	}

	SUBCASE("Child of a parent that isn't a canvas item") {
		SIGNAL_WATCH(child_of_node2d, CoreStringName(property_list_changed));
		material->notify_property_list_changed();
		SIGNAL_CHECK_FALSE("property_list_changed");
		SIGNAL_UNWATCH(child_of_node2d, CoreStringName(property_list_changed));
	}

	memdelete(parent);
}

TEST_CASE("[SceneTree][CanvasItem] Instance shader parameters are refreshed when using parent material and top_level changes") {
	Window *root = SceneTree::get_singleton()->get_root();

	Sprite2D *parent = make_sprite(root);
	Sprite2D *child = make_sprite(parent);
	Sprite2D *grandchild = make_sprite(child);
	Ref<ShaderMaterial> material = make_material();

	parent->set_material(material);
	child->set_use_parent_material(true);
	grandchild->set_use_parent_material(true);

	Array empty_args = { {} };

	SUBCASE("Child switched to top level") {
		SIGNAL_WATCH(child, CoreStringName(property_list_changed));
		child->set_as_top_level(true);
		SIGNAL_CHECK("property_list_changed", empty_args);
		SIGNAL_UNWATCH(child, CoreStringName(property_list_changed));
	}

	SUBCASE("Child switched back from top level") {
		child->set_as_top_level(true);
		SIGNAL_WATCH(child, CoreStringName(property_list_changed));
		child->set_as_top_level(false);
		SIGNAL_CHECK("property_list_changed", empty_args);
		SIGNAL_UNWATCH(child, CoreStringName(property_list_changed));
	}

	SUBCASE("Grandchild of a child switched to top level") {
		SIGNAL_WATCH(grandchild, CoreStringName(property_list_changed));
		child->set_as_top_level(true);
		SIGNAL_CHECK("property_list_changed", empty_args);
		SIGNAL_UNWATCH(grandchild, CoreStringName(property_list_changed));
	}

	SUBCASE("Child already at the same top level state") {
		SIGNAL_WATCH(child, CoreStringName(property_list_changed));
		child->set_as_top_level(false);
		SIGNAL_CHECK_FALSE("property_list_changed");
		SIGNAL_UNWATCH(child, CoreStringName(property_list_changed));
	}

	memdelete(parent);
}

} // namespace TestCanvasItem
