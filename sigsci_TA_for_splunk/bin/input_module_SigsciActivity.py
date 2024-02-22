# encoding = utf-8
from timeit import default_timer as timer
import json
import time
from datetime import datetime
from sigsci_helper import get_from_and_until_times, Config, get_results, get_until_time

"""
    IMPORTANT
    Edit only the validate_input and collect_events functions.
    Do not edit any other part in this file.
    This file is generated only once when creating the modular input.
"""


# def use_single_instance_mode():
#     return True


def validate_input(helper, definition):
    # Read Timeout passed to send_http_request. Type: float.
    # https://docs.splunk.com/Documentation/AddonBuilder/4.1.4/UserGuide/PythonHelperFunctions
    # We do this per input module as splunk provides no way to validate global configuration arguments :')
    request_timeout = definition.parameters.get("request_timeout", None)
    if request_timeout is None:
        raise ValueError("Request timeout configuration is missing")
    try:
        request_timeout = float(request_timeout)
    except ValueError:
        raise ValueError(f"Invalid request timeout value: {request_timeout}")
    if request_timeout > 300.0 or request_timeout <= 0:
        raise ValueError(f"Request timeout must be between 0 and 300 seconds, got {request_timeout}")

    # Read Timeout passed to send_http_request. Type: float.
    read_timeout = definition.parameters.get("read_timeout", None)
    if read_timeout is None:
        raise ValueError("Read timeout configuration is missing")
    try:
        read_timeout = float(read_timeout)
    except ValueError:
        raise ValueError(f"Invalid read timeout value: {read_timeout}")
    if read_timeout > 300.0 or read_timeout <= 0:
        raise ValueError(f"Read timeout must be between 0 and 300 seconds, got {read_timeout}")
    # Catchup Opts
    twenty_hour_catchup = definition.parameters.get('twenty_hour_catchup', None)
    disable_catchup = definition.parameters.get('disable_catchup', None)
    if twenty_hour_catchup and disable_catchup is True:
        raise ValueError(f"Catch up values are mutually exclusive")
    pass


def collect_events(helper, ew):
    start = timer()
    loglevel = helper.get_log_level()
    helper.set_log_level(loglevel)
    # Proxy setting configuration
    # proxy_settings = helper.get_proxy()
    global_email = helper.get_global_setting("email")
    global_api_token = helper.get_global_setting("api_token")
    global_corp_api_name = helper.get_global_setting("corp_api_name")
    api_host = "https://dashboard.signalsciences.net"
    helper.log_info("email: %s" % global_email)
    helper.log_info("corp: %s" % global_corp_api_name)
    
    # Request / Read Timeouts
    request_timeout = float(helper.get_arg("request_timeout"))
    read_timeout = float(helper.get_arg('read_timeout'))
    helper.log_info(f"request configuration is: request:{request_timeout}, read: {read_timeout}")
    
    # CatchUp Config Declaration
    twenty_hour_catchup = helper.get_arg('twenty_hour_catchup')
    helper.log_info(f"twenty four hour catchup is: {twenty_hour_catchup}")
    
    disable_catchup = helper.get_arg('disable_catchup')
    helper.log_info(f"disable catchup is: {disable_catchup}")

    def pull_events(delta, key=None):
        last_run_until = helper.get_check_point("activity_last_until_time")
        helper.log_info(f"last_run_until: {last_run_until}")
        if last_run_until is None:
            (until_time, from_time) = get_from_and_until_times(
                helper, delta, five_min_offset=False
            )
        else:
            (until_time, from_time) = get_until_time(
                helper, last_run_until, delta, twenty_hour_catchup=twenty_hour_catchup, catchup_disabled=disable_catchup, five_min_offset=False
            )
        if from_time is None:
            helper.log_info(f"{last_run_until} >= current now time, skipping run")
            return
        if from_time >= until_time:
            helper.save_check_point("activity_last_until_time", from_time)
            helper.log_info(
                f"from_time {from_time} >= until_time {until_time}, skipping run"
            )
            return
        helper.save_check_point("activity_last_until_time", until_time)

        helper.log_info(f"Start Period: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(from_time))}")
        helper.log_info(f"End Period: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(until_time))}")

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
        url = (
            f"{api_host}/api/v0/corps/{global_corp_api_name}"
            f"/activity?"
            f"from={from_time}&until={until_time}"
        )
        config = Config(
            url=url,
            api_host=api_host,
            from_time=from_time,
            until_time=until_time,
            global_email=global_email,
            global_corp_api_name=global_corp_api_name,
            current_site="",
            request_timeout=request_timeout,
            read_timeout=read_timeout,
        )
        config.headers = {
            "Content-type": "application/json",
            "x-api-user": global_email,
            "x-api-token": global_api_token,
            "User-Agent": config.user_agent_string,
        }
        helper.log_info("Pulling results from Corp Activity API")
        all_events = get_results("Activity Events", helper, config)
        total_requests = len(all_events)
        helper.log_info("Total Corp Activity Pulled: %s" % total_requests)
        write_start = timer()
        for current_event in all_events:
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
                    data=current_event,
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
                    data=current_event,
                )

            try:
                ew.write_event(event)
            except Exception as e:
                raise e
        write_end = timer()
        write_time = write_end - write_start
        write_time_result = round(write_time, 2)
        helper.log_info(f"Total Corp Activity Output Time: {write_time_result} seconds")

    # If multiple inputs configured it creates an array of values and the
    # script only gets called once per Input configuration
    time_deltas = helper.get_arg("interval")
    helper.log_info(f"interval: {time_deltas}")
    if type(time_deltas) is dict:
        helper.log_info("run_type: Sequential")
        for active_input in time_deltas:
            time_delta = time_deltas[active_input]
            time_delta = int(time_delta)
            helper.log_info("time_delta: %s" % time_delta)
            pull_events(delta=time_delta, key=active_input)
    else:
        helper.log_info("Run Type: Concurrent")
        helper.log_info("time_delta: %s" % time_deltas)
        pull_events(delta=int(time_deltas))
    helper.log_info("Finished Pulling Corp Activity")
    end = timer()
    total_time = end - start
    time_result = round(total_time, 2)
    helper.log_info(f"Total Script Time: {time_result} seconds")
