import requests
import json

from django.conf import settings

from bp.models import BP


def load_pretix_entries(start_url, callback):
    """
    Load (paginated) entries from pretix and perform callback on every entry

    :param start_url: initial URL
    :type start_url: str
    :param callback: callback function for each entry (should accept the result/entry as single argument)
    :type callback: function
    """
    url = start_url
    while True:
        # Get page
        r = requests.get(url, headers={'Authorization': f"Token {settings.PRETIX_API_TOKEN}"})

        if r.status_code != 200:
            print(f"Error: {r.status_code}")
            break

        # Load all page entries...
        j = json.loads(r.text)

        # ... loop over them...
        for result in j["results"]:
            # ... and call the callback function for each of them
            callback(result)

        # Repeat as long as there are further pages
        if j["next"] is None:
            break

        # Fix URL returned by API (since it may contain "localhost" depending on the configuration of the installation)
        url = settings.PRETIX_API_BASE_URL + j["next"].split("/api/v1/")[1]


def load_pretix_single_entry(url):
    """
    Load a single entry from the pretix API

    :param url: endpoint (single entry, e.g. order)
    :type url: str
    :return: Response describing the entry
    :rtype: Dict
    """
    r = requests.get(url, headers={'Authorization': f"Token {settings.PRETIX_API_TOKEN}"})

    if r.status_code != 200:
        raise ValueError

    return json.loads(r.text)

def get_pretix_projectinfo_url(project):
    """
    Get Pretix url to more infos on the project

    :param project: project of interest
    :type project: Project
    :return: Pretix URL
    :rtype: str
    """
    event_slug = project.bp.pretix_event_ag
    order_id = project.order_id
    return f"{settings.PRETIX_BASE_URL}control/event/{settings.PRETIX_ORGANIZER}/{event_slug}/orders/{order_id}"

def pretix_url(endpoint, event_slug):
    """
    Create Pretix API url for given endpoint and event slug

    :param endpoint: endpoint to query
    :type endpoint: str
    :param event_slug: slug of the event to query
    :type event_slug: str
    :return: API URL
    :rtype: str
    """
    return f"{settings.PRETIX_API_BASE_URL}organizers/{settings.PRETIX_API_ORGANIZER}/events/{event_slug}/{endpoint}"


def get_project_details(result):
    """
    Callback function to get project details from Pretix API answer

    :param result: raw entry
    :type result: dict
    :return: order code, project title, name and email of person offering the project
    :rtype: str, str, str, str
    """
    code = result["code"]
    details = result["positions"][0]
    name = details["attendee_name"]
    email = result["email"]
    secret = result["secret"]

    title = ""
    for qa in details["answers"]:
        # Find question for project title (and the corresponding answer)
        # TODO Make configurable
        if qa["question_identifier"] == "JGSNWU7J":
            title = qa["answer"]
            break

    return code, title, name, email, secret


def get_order_secret(order_id):
    """
    Get secret for an order identified by the given ID
    :param order_id: ID of the order
    :type order_id: str
    :return: secret of the given order
    :rtype: str
    """
    pretix_order = load_pretix_single_entry(pretix_url(f"orders/{order_id}/",BP.get_active().pretix_event_ag))
    return pretix_order["secret"]
