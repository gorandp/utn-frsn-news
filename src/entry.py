from workers import Response, WorkerEntrypoint


def get_hello_message():
    return "Hello World!"


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return Response(get_hello_message())
