# encoding = utf-8

import time
from datetime import datetime, timedelta
from timeit import default_timer as timer
import requests
import calendar
import json
from sigsci_helper import check_response, get_request_data

'''
    IMPORTANT
    Edit only the validate_input and collect_events functions.
    Do not edit any other part in this file.
    This file is generated only once when creating the modular input.
'''


# def use_single_instance_mode():
#     return True


def validate_input(helper, definition):
    # This example accesses the modular input variable
    time_delta = definition.parameters.get('time_delta', None)
    if time_delta is None or time_delta == "":
        msg = "The frequency can not be empty"
        raise ValueError(
            "InvalidFrequency",
            msg
        )
    else:
        try:
            int(time_delta)
        except Exception as error:
            msg = "Time delta must be an integer"
            raise ValueError(
                "InvalidFrequency",
                msg
            )
    pass


def collect_events(helper, ew):
    start = timer()
    # loglevel = helper.get_log_level()
    # Proxy setting configuration
    # proxy_settings = helper.get_proxy()
    global_email = helper.get_global_setting("email")
    global_api_token = helper.get_global_setting("api_token")
    global_corp_api_name = helper.get_global_setting("corp_api_name")
    api_host = 'https://dashboard.signalsciences.net'
    helper.log_info("email: %s" % global_email)
    helper.log_info("corp: %s" % global_corp_api_name)
    python_requests_version = requests.__version__
    user_agent_version = "1.0.26"
    user_agent_string = (
        f"TA-sigssci-waf/{user_agent_version} "
        f"(PythonRequests {python_requests_version})"
    )

    def pull_events(delta, key=None):
        until_time = datetime.utcnow()
        until_time = until_time.replace(second=0, microsecond=0)
        from_time = until_time - timedelta(seconds=delta)
        until_time = calendar.timegm(until_time.utctimetuple())
        from_time = calendar.timegm(from_time.utctimetuple())
        from_time_friendly = datetime.fromtimestamp(from_time)
        until_time_friendly = datetime.fromtimestamp(until_time)

        helper.log_info(f"Start Period: {from_time_friendly}")
        helper.log_info(f"End Period: {until_time_friendly}")

        input_name = helper.get_input_stanza_names()
        single_name = ""

        if type(input_name) is dict and input_name > 1:
            helper.log_info("Multi instance mode")
            for current_name in input_name:
                single_name = current_name
        else:
            helper.log_info("Single instance mode")
            helper.log_info("Inputs: %s" % input_name)
            helper.log_info("Inputs Num: %s" % len(input_name))
            single_name = input_name
            helper.log_info(f"single_name: {single_name}")

        # Loop across all the data and output it in one big JSON object
        headers = {
            'Content-type': 'application/json',
            'x-api-user': global_email,
            'x-api-token': global_api_token,
            'User-Agent': user_agent_string
        }

        url = (
            f"{api_host}/api/v0/corps/{global_corp_api_name}"
            f"/activity?"
            f"from={from_time}&until={until_time}"
        )
        loop = True

        counter = 1
        helper.log_info("Pulling results from Corp Activity API")
        all_events = []
        while loop:
            helper.log_info("Processing page %s" % counter)
            start_page = timer()
            response_result, response_code, response_error = \
                get_request_data(url, headers, helper)

            pulled, request_details = check_response(
                response_code,
                response_error,
                global_email=global_email,
                global_corp_api_name=global_corp_api_name,
                from_time=from_time,
                until_time=until_time
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
                f"Number of Requests for Page: {number_requests_per_page}"
            )
            for request in response["data"]:
                data = json.dumps(request)
                data = json.loads(data)
                all_events.append(data)

            if "next" in response and "uri" in response['next']:
                next_url = response['next']['uri']
                if next_url == '':
                    helper.log_info("Finished Page %s" % counter)
                    counter += 1
                    end_page = timer()
                    page_time = end_page - start_page
                    page_time_result = round(page_time, 2)
                    helper.log_info(
                        f"Total Page Time: {page_time_result} seconds"
                    )
                    loop = False
                else:
                    url = api_host + next_url
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

        total_requests = len(all_events)
        helper.log_info("Total Corp Activity Pulled: %s" % total_requests)
        write_start = timer()
        for current_event in all_events:
            # helper.log_debug(current_event)
            # helper.log_info(f"data={event_data}")
            current_event = json.dumps(current_event)
            if key is None:
                source_type = helper.get_sourcetype()
                helper.log_info("Concurrent Mode")
                source_type_info = type(source_type)
                active_index = helper.get_output_index()
                index_info = type(active_index)
                single_name_info = type(single_name)
                current_event_info = type(current_event)
                helper.log_info(f"source_type: {source_type}")
                helper.log_info(f"source_type_info: {source_type_info}")
                helper.log_info(f"index: {active_index}")
                helper.log_info(f"index_info: {index_info}")
                helper.log_info(f"single_name: {single_name}")
                helper.log_info(f"single_name_info: {single_name_info}")
                helper.log_info(f"current_event: {current_event}")
                helper.log_info(f"current_event_info: {current_event_info}")
                event = helper.new_event(
                    source=single_name,
                    index=helper.get_output_index(),
                    sourcetype=source_type,
                    data=current_event
                )
            else:
                indexes = helper.get_output_index()
                current_index = indexes[key]
                types = helper.get_sourcetype()
                source_type = types[key]
                single_name = single_name[0]
                helper.log_info("Sequential Mode")
                helper.log_info(f"source_type: {source_type}")
                helper.log_info(f"index: {current_index}")
                helper.log_info(f"single_name: {single_name}")
                helper.log_info(f"current_event: {current_event}")
                event = helper.new_event(
                    source=single_name,
                    index=current_index,
                    sourcetype=source_type,
                    data=current_event
                )

            try:
                ew.write_event(event)
            except Exception as e:
                raise e
        write_end = timer()
        write_time = write_end - write_start
        write_time_result = round(write_time, 2)
        helper.log_info(
            f"Total Corp Activity Output Time: {write_time_result} seconds"
        )

    # If multiple inputs configured it creates an array of values and the
    # script only gets called once per Input configuration
    time_deltas = helper.get_arg('time_delta')
    if type(time_deltas) is dict:
        helper.log_info("run_type: Sequential")
        for active_input in time_deltas:
            time_delta = time_deltas[active_input]
            time_delta = int(time_delta)
            helper.log_info("time_delta: %s" % time_delta)
            pull_events(
                delta=time_delta,
                key=active_input
            )
    else:
        helper.log_info("Run Type: Concurrent")
        helper.log_info("time_delta: %s" % time_deltas)
        pull_events(
            delta=int(time_deltas)
        )
    helper.log_info("Finished Pulling Corp Activity")
    end = timer()
    total_time = end - start
    time_result = round(total_time, 2)
    helper.log_info(f"Total Script Time: {time_result} seconds")
