class EasyEasyAttributionMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        subid = (
            request.GET.get("ee_click_id")
            or request.GET.get("subid")
        )

        if subid and not request.session.get("easyeasy_subid"):
            request.session["easyeasy_subid"] = subid

        return self.get_response(request)