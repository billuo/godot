extends RefCounted

func iterate(obj: Object) -> void:
	for child in obj:
		print(child)

func test() -> void:
	var node := Node.new()
	iterate(node)
	node.free()
