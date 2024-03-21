import json, sys, os
from datetime import datetime, timedelta, timezone
from timeit import default_timer as timer
from urllib.parse import urlparse, parse_qs
import time
import requests


def validate_timeouts(request_timeout, read_timeout):
    # Read Timeout passed to send_http_request. Type: float.
    # https://docs.splunk.com/Documentation/AddonBuilder/4.1.4/UserGuide/PythonHelperFunctions
    # We do this per input module as splunk provides no way to validate global configuration arguments.
    if request_timeout is None:
        raise ValueError("Request timeout configuration is missing")
    try:
        request_timeout = float(request_timeout)
    except ValueError:
        raise ValueError(f"Invalid request timeout value: {request_timeout}")
    if request_timeout > 300.0 or request_timeout <= 0:
        raise ValueError(f"Request timeout must be between 0 and 300 seconds, got {request_timeout}")

    # Read Timeout passed to send_http_request. Type: float.
    if read_timeout is None:
        raise ValueError("Read timeout configuration is missing")
    try:
        read_timeout = float(read_timeout)
    except ValueError:
        raise ValueError(f"Invalid read timeout value: {read_timeout}")
    if read_timeout > 300.0 or read_timeout <= 0:
        raise ValueError(f"Read timeout must be between 0 and 300 seconds, got {read_timeout}")

def validate_catchup(disable_catchup, twenty_hour_catchup):
    ## definitions.parameters.get returns the defaultValue for a checkbox as a str on init with the value of `true`.
    ## We have to accomodate for when a user tries and ticks both without changing the value.
    if disable_catchup is not None:
        if disable_catchup.lower() == 'true':
            disable_catchup = 1
        else:
            disable_catchup = int(disable_catchup)
            
        if twenty_hour_catchup is not None:
            twenty_hour_catchup = int(twenty_hour_catchup)
        
        if twenty_hour_catchup and disable_catchup:
            raise ValueError("Catch up values are mutually exclusive")

def check_response(
        code,
        response_text,
        global_email,
        global_corp_api_name,
        from_time=None,
        until_time=None,
        current_site=None,
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
    if code == 414:
        base_msg["error"] = "request uri size exceeded"
        base_msg["msg"] = "request-uri-too-large"
    elif code == 500:
        base_msg["error"] = "Internal Server Error"
        base_msg["msg"] = "internal-error"
    elif code == 401:
        base_msg["error"] = (
            "Unauthorized. Incorrect credentials or lack of permissions"
        )
        base_msg["msg"] = "unauthorized"
    elif code == 429:
        base_msg["error"] = "Too Many Requests"
        base_msg["msg"] = "too-many-requests"
    elif code is not None and 400 <= code <= 599 and code not in [400, 500, 401]:
        base_msg["error"] = "Unknown Error"
        base_msg["msg"] = "other-error"
    else:
        success = True
    return success, base_msg


def get_request_data(url, method, payload, headers, request_timeout, read_timeout, helper):
    response_code = None
    response_error = "Initial error state"
    try:
        response_raw = helper.send_http_request(
            url,
            method,
            parameters=None,
            payload=payload,
            headers=headers,
            cookies=None,
            verify=True,
            cert=None,
            timeout=(request_timeout, read_timeout),
            use_proxy=True,
        )
        response_code = response_raw.status_code
        response_error = response_raw.text
        try:
            data = json.loads(response_raw.text)
        except Exception as error:
            data = {"data": []}
            helper.log_info("Unable to parse API Response")
            helper.log_error(response_error)
            helper.log_error(error)
    except Exception as error:
        data = {"data": []}
        helper.log_info("HTTP Request Failed")
        helper.log_error(error)
        response_error = "Request Failure"

    return data, response_code, response_error


def timestamp_sanitise(_time):
    return _time - _time % 60

def get_from_and_until_times(helper, delta, five_min_offset=False):
    # Get the current epoch time
    until_time = int(time.time())
    helper.log_info(f"Time Now: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(int(time.time())))}")

    # Check if five_min_offset is needed.
    if five_min_offset:
        until_time -= 5 * 60  # Subtract 5 minutes in seconds

    # Always sanitize the until_time irrespective of five_min_offset, 
    # because it makes sure the timestamp is always aligned to a whole minute boundary.
    until_time = timestamp_sanitise(until_time)

    # Get the starting time.
    from_time = until_time - delta
    
    # If five_min_offset, then sanitize from_time as well
    if five_min_offset:
        from_time = timestamp_sanitise(from_time)

    return until_time, from_time

SECONDS_IN_DAY= 24 * 60 * 60

def get_until_time(helper, from_time, delta, twenty_hour_catchup, catchup_disabled, five_min_offset=False):
    # Get current epoch time rounded down to nearest minute
    now = timestamp_sanitise(int(time.time()))
    from_time = timestamp_sanitise(from_time)
    helper.log_info(f"Time Now: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(now))}")

    if five_min_offset:
        until_time = now - 5 * 60  # Subtract 5 minutes in seconds
    else:
        until_time = now

    # Calculate the difference between now and the from_time
    time_difference = now - from_time
    
    # If catchups are disabled, don't catch up at all.
    # We evaluate by ecking if the time difference is greater than the delta added to itself.
    if catchup_disabled:
        if time_difference > delta + delta:
            helper.log_debug("Last checkpoint is greater than current delta. Not attempting to catch up and resetting from delta.")
            until_time, from_time = get_from_and_until_times(
                helper, delta, five_min_offset=True
            )
        return until_time, from_time
            
    # If the difference is more than 24 hours (in seconds).
    if time_difference > SECONDS_IN_DAY:
        helper.log_info("Last checkpoint is over 24 hours ago, due to API limitations this cannot be greater than 24 hours and must be reset.")
        if twenty_hour_catchup:
            helper.log_info("Setting from_time to 24 hours ago.")
            adjusted_from_time = now - SECONDS_IN_DAY  # Subtract 24 hours in seconds
            helper.log_info(f"Previous Run: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(from_time))}")
            helper.log_info(f"Adjusted from_time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(adjusted_from_time))}")
            return until_time, adjusted_from_time
        else:
            helper.log_info("Last checkpoint was over 24 hours ago, resetting the time from delta.")
            # Return times as if checkpoint was none.
            until_time, from_time = get_from_and_until_times(
                helper, delta, five_min_offset=True
            )
            return until_time, from_time

    return until_time, from_time

def get_results(title, helper, config):
    loop = True
    counter = 1
    method = "GET"
    payload = None
    while loop:
        pulled_events = []
        helper.log_info("Processing page %s" % counter)
        start_page = timer()

        response_result, response_code, response_error = get_request_data(
            config.url,
            method,
            payload,
            config.headers,
            config.request_timeout,
            config.read_timeout,
            helper
        )

        pulled, request_details = check_response(
            response_code,
            response_error,
            global_email=config.global_email,
            global_corp_api_name=config.global_corp_api_name,
            current_site=config.current_site,
            from_time=config.from_time,
            until_time=config.until_time,
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

        try:
            number_requests_per_page = len(response["data"])
        except KeyError:
            number_requests_per_page = 0
            helper.log_error(f"Invalid response: {response_result}")
            break
            
        helper.log_info(f"Number of {title} for Page: {number_requests_per_page}")

        for data in response["data"]:
            event_id = data["id"]
            if event_id not in config.event_ids:
                config.event_ids.append(event_id)
            else:
                continue

            if "headersOut" in data:
                headers_out = data["headersOut"]
                if headers_out is not None:
                    new_header_out = []
                    for header in headers_out:
                        header_data = {header[0]: header[1]}
                        new_header_out.append(header_data)
                    data["headersOut"] = new_header_out

            if "headersIn" in data:
                headers_in = data["headersIn"]
                if headers_in is not None:
                    new_header_in = []
                    for header in headers_in:
                        header_data = {header[0]: header[1]}
                        new_header_in.append(header_data)
                    data["headersIn"] = new_header_in

            data = json.dumps(data)
            config.events.append(data)

        next_data = response.get("next")
        if next_data is not None:
            next_url = next_data.get("uri")
        else:
            next_url = None
        if next_url == "":
            helper.log_info("Finished Page %s" % counter)
            end_page = timer()
            page_time = end_page - start_page
            page_time_result = round(page_time, 2)
            helper.log_info(f"Total Page Time: {page_time_result} seconds")
            loop = False
        elif next_url is not None:
            # The NextID is too large to put into query parameters, so extract the value and put it in a form body.
            # See: SDS-1720
            if "feed/requests" in config.url:
                # Remove any additional query parameters past the request_limit.
                # These cannot contain `?` so safe to use as a split separator.
                config.url = config.url.split('&', 1)[0]
                method = "POST"
                config.headers['content-type'] = "application/x-www-form-urlencoded"
                next_value = next_url.split('?', 1)[1] if '?' in next_url else ''
                query_dict = parse_qs(next_value)
                next_value = query_dict.get('next', [None])[0]
                payload = f"next={next_value}"
                helper.log_debug("payload: %s" % {payload})  
            else: 
                config.url = config.api_host + next_url

            helper.log_debug("next url: %s" % {config.url})
            helper.log_info("Finished Page %s" % counter)

            counter += 1
            end_page = timer()
            page_time = end_page - start_page
            page_time_result = round(page_time, 2)
            helper.log_info(f"Total Page Time: {page_time_result} seconds")
        else:
            loop = False
    return config.events


class Config:
    api_host: str
    url: str
    method: str
    headers: dict
    events: list
    from_time: str
    until_time: str
    global_email: str
    global_corp_api_name: str
    current_site: str
    user_agent_version: str
    user_agent_string: str
    event_ids: list
    request_timeout: float
    read_timeout: float

    def __init__(
            self,
            api_host=None,
            url=None,
            method=None,
            headers=None,
            from_time=None,
            until_time=None,
            global_email=None,
            global_corp_api_name=None,
            current_site=None,
            request_timeout=None,
            read_timeout=None,
    ):
        self.api_host = api_host
        self.url = url
        self.method = method
        self.headers = headers
        self.events = []
        self.from_time = from_time
        self.until_time = until_time
        self.global_email = global_email
        self.global_corp_api_name = global_corp_api_name
        self.current_site = current_site
        self.event_ids = []
        self.request_timeout = request_timeout
        self.read_timeout = read_timeout
        self.user_agent_version = "1.0.38"
        self.user_agent_string = (
            f"TA-sigsci-waf/{self.user_agent_version} "
            f"(PythonRequests {requests.__version__})"
        )
