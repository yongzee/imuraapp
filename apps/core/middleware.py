class EasyEasyAttributionMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Capture the original referral ID (first touch).
        subid = (
            request.GET.get("ee_click_id")
            or request.GET.get("subid")
        )

        if subid and not request.session.get("easyeasy_subid"):
            request.session["easyeasy_subid"] = subid.strip()[:255]

        # Make the pending signup available to the next page.
        pending_signup = request.session.get(
            "easyeasy_signup_pending"
        )

        if pending_signup:
            request.easyeasy_signup_pending = pending_signup

        response = self.get_response(request)

        # Clear the flag after the destination page successfully loads.
        if pending_signup and response.status_code == 200:
            request.session.pop("easyeasy_signup_pending", None)

        return response