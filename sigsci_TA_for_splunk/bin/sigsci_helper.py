import json


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


