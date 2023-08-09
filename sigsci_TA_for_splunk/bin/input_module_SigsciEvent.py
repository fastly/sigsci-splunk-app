# encoding = utf-8
from timeit import default_timer as timer
import requests
import json
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
    # This example accesses the modular input variable
    site_name = definition.parameters.get("site_api_name", None)
    if site_name is None or site_name == "":
        msg = "The site_name can not be empty"
        raise ValueError("InvalidSiteName", msg)
    elif "http" in site_name:
        msg = (
            "The site name is not the full URL it should be the ",
            "API Name of the site like 'my_example_site'",
        )
        raise ValueError("InvalidSiteName", msg)
    elif " " in site_name:
        msg = (
            "The site name should be the API Name of the site like ",
            "not the Display Name. Example would be 'my_site_name' instead of ",
            "My Site Name",
        )
        raise ValueError("InvalidSiteName", msg)
    pass


def collect_events(helper, ew):
    start = timer()
    loglevel = helper.get_log_level()
    # Proxy setting configuration
    # proxy_settings = helper.get_proxy()
    global_email = helper.get_global_setting("email")
    global_api_token = helper.get_global_setting("api_token")
    global_corp_api_name = helper.get_global_setting("corp_api_name")
    api_host = "https://dashboard.signalsciences.net"
    helper.log_info("email: %s" % global_email)
    helper.log_info("corp: %s" % global_corp_api_name)

    def pull_events(current_site, delta, key=None):
        site_name = current_site
        last_name = f"events_last_until_time_{current_site}"
        last_run_until = helper.get_check_point(last_name)
        helper.log_info(f"last_run_until: {last_run_until}")
        if last_run_until is None:
            (until_time, from_time) = get_from_and_until_times(
                delta, five_min_offset=False
            )
        else:
            (until_time, from_time) = get_until_time(
                last_run_until, delta, five_min_offset=False
            )
        if from_time is None or from_time > until_time:
            helper.log_info(f"{from_time} >= current now time, skipping run")
            return
        if from_time >= until_time:
            helper.save_check_point(last_name, from_time)
            helper.log_info(
                f"from_time {from_time} >= until_time {until_time}, skipping run"
            )
            return
        helper.save_check_point(last_name, until_time)
        helper.log_info("SiteName: %s" % site_name)

        helper.log_info(f"Start Period: {datetime.fromtimestamp(from_time)}")
        helper.log_info(f"End Period: {datetime.fromtimestamp(until_time)}")

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
            f"/sites/{site_name}/activity?"
            f"from={from_time}&until={until_time}"
        )
        helper.log_info("Pulling results from Events API")
        config = Config(
            url=url,
            api_host=api_host,
            from_time=from_time,
            until_time=until_time,
            global_email=global_email,
            global_corp_api_name=global_corp_api_name,
            current_site=current_site,
        )
        config.headers = {
            "Content-type": "application/json",
            "x-api-user": global_email,
            "x-api-token": global_api_token,
            "User-Agent": config.user_agent_string,
        }
        all_events = get_results("Events", helper, config)
        total_requests = len(all_events)
        helper.log_info("Total Events Pulled: %s" % total_requests)
        write_start = timer()
        for current_event in all_events:
            helper.log_debug(current_event)
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
        helper.log_info("Total Event Output Time: %s seconds" % write_time_result)

    # If multiple inputs configured it creates an array of values and the
    # script only gets called once per Input configuration

    all_sites = helper.get_arg("site_api_name")
    time_deltas = helper.get_arg("interval")
    helper.log_info(f"interval: {time_deltas}")
    if type(all_sites) is dict:
        helper.log_info("run_type: Sequential")
        for active_input in all_sites:
            site = all_sites[active_input]
            current_delta = int(time_deltas[active_input])
            helper.log_info("site: %s" % site)
            pull_events(key=active_input, current_site=site, delta=current_delta)
            helper.log_info("Finished Pulling Events for %s" % site)
    else:
        helper.log_info("Run Type: Concurrent")
        site = helper.get_arg("site_api_name")
        helper.log_info("site: %s" % site)
        pull_events(current_site=site, delta=int(time_deltas))
        helper.log_info("Finished Pulling Events for %s" % site)
    end = timer()
    total_time = end - start
    time_result = round(total_time, 2)
    helper.log_info("Total Script Time: %s seconds" % time_result)
