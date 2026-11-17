
class RestHelper:

    def __init__(self, request_context):
        self.request_context = request_context

    def execute(self, method, endpoint, **kwargs):

        method = method.upper().strip()

        if method == "GET":
            return self.request_context.get(endpoint, **kwargs)

        elif method == "POST":
            return self.request_context.post(endpoint, **kwargs)

        elif method == "PUT":
            return self.request_context.put(endpoint, **kwargs)

        elif method == "PATCH":
            return self.request_context.patch(endpoint, **kwargs)

        elif method == "DELETE":
            return self.request_context.delete(endpoint, **kwargs)

        else:
            raise ValueError(
                f"Unsupported HTTP Method: {method}"
            )
