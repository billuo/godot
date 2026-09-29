extends RefCounted

# A method with a body is a coroutine when the body contains `await`, so the annotation
# must not make an ordinary method report a `MISSING_AWAIT` warning when it isn't awaited.
@async func annotated() -> void:
	pass

func plain() -> void:
	pass

func test() -> void:
	await annotated()
	annotated()
	@warning_ignore("redundant_await")
	await plain()
