# A static function cannot contain `await`, so it cannot be a coroutine.
# `@async` is rejected to avoid marking a function as a coroutine that never is one.
class SomeClass:
	@async static func some_method() -> void:
		pass
