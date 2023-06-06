import json
from datetime import datetime, timedelta
import calendar
from timeit import default_timer as timer
import time
import requests


def check_response(
        code,
        response_text,
        global_email,
        global_corp_api_name,
        from_time=None,
        until_time=None,
        current_site=None
):
    success = False
    base_msg = {
        "from": from_time,
        "until": until_time,
        "global_email": global_email,
        "global_corp_api_name": global_corp_api_name,
        "response_text": response_text,
        "status_code": code,
    }
    if current_site is not None:
        base_msg["current_site"] = current_site
    if code == 400:
        if "Rate limit exceeded" in response_text:
            base_msg["msg"] = "rate-limit"
        else:
            base_msg["error"] = "BAD API Request"
            base_msg["msg"] = "bad-request"
    elif code == 500:
        base_msg["error"] = "Internal Server Error"
        base_msg["msg"] = "internal-error"
    elif code == 401:
        base_msg["error"] = "Unauthorized. Incorrect credentials or lack " \
                            "of permissions"
        base_msg["msg"] = "unauthorized"
    elif 400 <= code <= 599 and code != 400 and code != 500 and code != 401:
        base_msg["error"] = "Unknown Error"
        base_msg["msg"] = "other-error"
    else:
        success = True
    return success, base_msg


def get_request_data(url, headers, helper):
    method = "GET"
    try:
        response_raw = helper.send_http_request(
            url,
            method,
            parameters=None,
            payload=None,
            headers=headers,
            cookies=None,
            verify=True,
            cert=None,
            timeout=None,
            use_proxy=True
        )
        response_code = response_raw.status_code
        response_error = response_raw.text
        try:
            data = json.loads(response_raw.text)
        except Exception as error:
            data = {
                "data": []
            }
            helper.log_info("Unable to parse API Response")
            helper.log_error(response_error)
            helper.log_error(error)
    except Exception as error:
        data = {
            "data": []
        }
        helper.log_info("Unable to parse API Response")
        helper.log_error(error)
        response_code = 500
        response_error = "Unable to parse API Response"

    return data, response_code, response_error


def get_from_and_until_times(delta, five_min_offset=False):
    if five_min_offset:
        until_time = datetime.utcnow() - timedelta(minutes=5)
    else:
        until_time = datetime.utcnow()

    from_time = until_time - timedelta(seconds=delta)
    if five_min_offset:
        until_time = until_time.replace(second=0)
        from_time = from_time.replace(second=0)
    until_time = calendar.timegm(until_time.utctimetuple())
    from_time = calendar.timegm(from_time.utctimetuple())
    from_time_friendly = datetime.fromtimestamp(from_time)
    until_time_friendly = datetime.fromtimestamp(until_time)
    return until_time, from_time, from_time_friendly, until_time_friendly


def get_until_time(from_time, delta, five_min_offset=False):
    if five_min_offset:
        current_time_offset = datetime.utcnow() - timedelta(minutes=5)
        current_time_offset = current_time_offset.replace(second=0)
    else:
        current_time_offset = datetime.utcnow()
    current_time_offset = calendar.timegm(current_time_offset.utctimetuple())
    new_until_time = from_time + delta
    if from_time > current_time_offset:
        from_time = None
        until_time = current_time_offset
    else:
        if new_until_time > current_time_offset or current_time_offset > new_until_time:
            until_time = current_time_offset
        else:
            until_time = new_until_time
    if from_time is not None and until_time is not None:
        from_time_friendly = datetime.fromtimestamp(from_time)
        until_time_friendly = datetime.fromtimestamp(until_time)
    else:
        from_time_friendly = None
        until_time_friendly = None
    return until_time, from_time, from_time_friendly, until_time_friendly


def get_results(title, helper, config):
    loop = True
    counter = 1
    while loop:
        pulled_events = []
        helper.log_info("Processing page %s" % counter)
        start_page = timer()
        response_result, response_code, response_error = \
            get_request_data(config.url, config.headers, helper)

        pulled, request_details = check_response(
            response_code,
            response_error,
            global_email=config.global_email,
            global_corp_api_name=config.global_corp_api_name,
            current_site=config.current_site,
            from_time=config.from_time,
            until_time=config.until_time
        )

        if not pulled and request_details["msg"] != "rate-limit":
            helper.log_error("Failed to pull results")
            helper.log_error(request_details)
            exit()
        if not pulled and request_details["msg"] == "rate-limit":
            helper.log_error("Rate Limit hit")
            helper.log_error("Retrying in 10 seconds")
            time.sleep(10)
            break
        else:
            response = response_result

        number_requests_per_page = len(response['data'])
        helper.log_info(
            f"Number of {title} for Page: {number_requests_per_page}"
        )

        for request in response['data']:
            data = json.dumps(request)
            data = json.loads(data)
            event_id = data["id"]
            if event_id not in config.event_ids:
                config.event_ids.append(event_id)
            else:
                continue
            headers_out = data.get('headersOut', []) 
            headers_in = data.get('headersIn', [])


            if headers_out is not None:
                new_header_out = []
                for header in headers_out:
                    header_data = {
                        header[0]: header[1]
                    }
                    new_header_out.append(header_data)

                data['headersOut'] = new_header_out

            if headers_in is not None:
                new_header_in = []
                for header in headers_in:
                    header_data = {
                        header[0]: header[1]
                    }
                    new_header_in.append(header_data)
                data['headersIn'] = new_header_in

            data = json.dumps(data)
            config.events.append(data)
        next_data = response.get("next")
        if next_data is not None:
            next_url = next_data.get("uri")
        else:
            next_url = None
        if next_url == '':
            helper.log_info("Finished Page %s" % counter)
            end_page = timer()
            page_time = end_page - start_page
            page_time_result = round(page_time, 2)
            helper.log_info(
                f"Total Page Time: {page_time_result} seconds"
            )
            loop = False
        elif next_url is not None:
            config.url = config.api_host + next_url
            helper.log_info("Finished Page %s" % counter)
            counter += 1
            end_page = timer()
            page_time = end_page - start_page
            page_time_result = round(page_time, 2)
            helper.log_info(
                f"Total Page Time: {page_time_result} seconds"
            )
        else:
            loop = False
    return config.events


class Config:
    api_host: str
    url: str
    headers: dict
    events: dict
    from_time: str
    until_time: str
    global_email: str
    global_corp_api_name: str
    current_site: str
    user_agent_version: str
    user_agent_string: str
    event_ids: list

    def __init__(
            self,
            api_host=None,
            url=None,
            headers=None,
            from_time=None,
            until_time=None,
            global_email=None,
            global_corp_api_name=None,
            current_site=None,
    ):
        self.api_host = api_host
        self.url = url
        self.headers = headers
        self.events = []
        self.from_time = from_time
        self.until_time = until_time
        self.global_email = global_email
        self.global_corp_api_name = global_corp_api_name
        self.current_site = current_site
        self.event_ids = []
        self.user_agent_version = "1.0.33"
        self.user_agent_string = (
            f"TA-sigsci-waf/{self.user_agent_version} "
            f"(PythonRequests {requests.__version__})"
        )

