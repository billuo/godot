extends RefCounted

@abstract class AbstractClass:
	@abstract @async func do_something_async() -> void

	func call_something_async() -> void:
		await do_something_async()

class Implementation extends AbstractClass:
	func do_something_async() -> void:
		@warning_ignore("redundant_await")
		await 0

func test() -> void:
	var variant: AbstractClass = Implementation.new()
	await variant.do_something_async()
	await variant.call_something_async()
