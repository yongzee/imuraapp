import logging
import requests

from django.conf import settings
from django.db import transaction
from allauth.account.signals import user_signed_up

logger = logging.getLogger(__name__)


def send_easyeasy_signup(user_id, subid):

    url = "https://api.easyeasy.ng/api/conversion"

    payload = {
        "subid": subid,
        "event": "signup",
        "order_id": f"imura-registration-{user_id}"
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=15
        )

        result = response.json()

        if response.status_code == 200 and result.get("status") == "success":
            logger.info(
                "EasyEasy signup recorded for user %s",
                user_id
            )
        else:
            logger.warning(
                "EasyEasy signup requires review: %s",
                result
            )

    except Exception:
        logger.exception(
            "EasyEasy signup delivery failed for user %s",
            user_id
        )


def track_new_signup(request, user, **kwargs):

    subid = request.session.get("easyeasy_subid")

    if not subid:
        return

    transaction.on_commit(
        lambda: send_easyeasy_signup(user.pk, subid)
    )


user_signed_up.connect(
    track_new_signup,
    dispatch_uid="imura_easyeasy_signup_tracking"
)