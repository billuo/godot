extends RefCounted

@abstract class AbstractClass:
	@abstract func do_something_plain() -> void

	func call_something_plain() -> void:
		await do_something_plain()

class Implementation extends AbstractClass:
	func do_something_plain() -> void:
		@warning_ignore("redundant_await")
		await 0

func test() -> void:
	var variant: AbstractClass = Implementation.new()
	await variant.do_something_plain()
	await variant.call_something_plain()
