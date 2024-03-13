# encoding = utf-8
from timeit import default_timer as timer
import time
from datetime import datetime, timezone, timedelta
from sigsci_helper import get_from_and_until_times, Config, get_results, get_until_time, validate_timeouts

"""
    IMPORTANT
    Edit only the validate_input and collect_events functions.
    Do not edit any other part in this file.
    This file is generated only once when creating the modular input.
"""

# def use_single_instance_mode():
#     return True

def validate_input(helper,definition):
    request_limit = int(definition.parameters.get("request_limit", None))
    if request_limit is None or request_limit == "":
        raise ValueError('The request limit cannot be blank')
    if request_limit <= 0:
        raise ValueError('The request limit cannot be 0')
    if request_limit > 1000:
        raise ValueError('Request Limit cannot be greater than 1000')

    # Read Timeout passed to send_http_request. Type: float.
    # https://docs.splunk.com/Documentation/AddonBuilder/4.1.4/UserGuide/PythonHelperFunctions
    # We do this per input module as splunk provides no way to validate global configuration arguments :')
    request_timeout = definition.parameters.get("request_timeout", None)
    read_timeout = definition.parameters.get("read_timeout", None)
    validate_timeouts(request_timeout, read_timeout)

    twenty_hour_catchup = definition.parameters.get('twenty_hour_catchup', None)
    disable_catchup = definition.parameters.get('disable_catchup', None)
    if twenty_hour_catchup and disable_catchup is True:
        raise ValueError(f"Catch up values are mutually exclusive")

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
    helper.set_log_level(loglevel)
    # Proxy setting configuration
    # proxy_settings = helper.get_proxy()
    api_host = "https://dashboard.signalsciences.net"
    global_email = helper.get_global_setting("email")
    global_api_token = helper.get_global_setting("api_token")
    global_corp_api_name = helper.get_global_setting("corp_api_name")
    helper.log_info("email: %s" % global_email)
    helper.log_info("corp: %s" % global_corp_api_name)
    
    # Request / Read Timeouts
    request_timeout = float(helper.get_arg("request_timeout"))
    read_timeout = float(helper.get_arg('read_timeout'))
    helper.log_info(f"request configuration is: request:{request_timeout}, read: {read_timeout}")

    # Config declaration.
    twenty_hour_catchup = helper.get_arg('twenty_hour_catchup')
    helper.log_info(f"twenty four hour catchup is: {twenty_hour_catchup}")

    disable_catchup = helper.get_arg('disable_catchup')
    helper.log_info(f"disable catchup is: {disable_catchup}")

    attack_and_anomaly_signals_only = helper.get_arg('attack_and_anomaly_signals_only')
    helper.log_info(f"attack signals only is: {attack_and_anomaly_signals_only}")

    def pull_requests(helper, current_site, delta, key=None):
        site_name = current_site
        last_name = f"requests_last_until_time_{current_site}"
        last_run_until = helper.get_check_point(last_name)
        request_limit = helper.get_arg('request_limit')
        helper.log_info(f"request limit: {request_limit}")

        if last_run_until is None:
            helper.log_info("no last_run_time found in checkpoint state")
            helper.log_debug("get_from_until")
            until_time, from_time = get_from_and_until_times(
                helper, delta, five_min_offset=True
            )
        else:
            helper.log_info(f"last_run_until found in state: {last_run_until}")
            helper.log_debug("get_until")
            until_time, from_time = get_until_time(
                helper, last_run_until, delta, twenty_hour_catchup, disable_catchup, five_min_offset=True
            )

        if from_time is None:
            helper.log_info(f"{last_run_until} >= current now time, skipping run")
            return

        if from_time >= until_time:
            helper.save_check_point(last_name, from_time)
            helper.log_info(
                f"from_time {from_time} >= until_time {until_time}, skipping run"
            )
            return

        helper.log_info("SiteName: %s" % site_name)
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
            f"/sites/{site_name}/feed/requests"
            f"?limit={request_limit}"
            f"&from={from_time}&until={until_time}"
        )
        if attack_and_anomaly_signals_only:
            attack_signals = [
                "USERAGENT",
                "AWS-SSRF",
                "BACKDOOR",
                "CMDEXE",
                "SQLI",
                "TRAVERSAL",
                "XSS",
                "XXE"
            ]
            anomaly_signals = [
                "2FA-DISABLED", "2FA-CHANGED", "ABNORMALPATH", "ADDRESS-CHANGED", "ALLOWED",
                "BHH", "BLOCKED", "BODY-PARSER-EVASION", "CODEINJECTION", "COMPRESSED",
                "CC-VAL-ATTEMPT", "CC-VAL-FAILURE", "CC-VAL-SUCCESS", "CVE-2017-5638",
                "CVE-2017-7269", "CVE-2017-9805", "CVE-2018-11776", "CVE-2018-15961",
                "CVE-2018-9206", "CVE-2019-0192", "CVE-2019-0193", "CVE-2019-0232",
                "CVE-2019-11580", "CVE-2019-14234", "CVE-2019-16759", "CVE-2019-2725",
                "CVE-2019-3396", "CVE-2019-3398", "CVE-2019-5418", "CVE-2019-6340",
                "CVE-2019-8394", "CVE-2019-8451", "CVE-2021-26084", "CVE-2021-26855",
                "CVE-2021-40438", "CVE-2021-44228", "CVE-2021-44228-STRICT",
                "CVE-2022-22963", "CVE-2022-22965", "CVE-2022-26134", "CVE-2022-42889",
                "CVE-2023-34362", "CVE-2023-38218", "DATACENTER", "DOUBLEENCODING",
                "EMAIL-CHANGED", "EMAIL-VALIDATION", "FORCEFULBROWSING", "GC-VAL-ATTEMPT",
                "GC-VAL-FAILURE", "GC-VAL-SUCCESS", "GRAPHQL-API", "GRAPHQL-DUPLICATE-VARIABLES",
                "GRAPHQL-IDE", "GRAPHQL-INTROSPECTION", "GRAPHQL-DEPTH",
                "GRAPHQL-MISSING-REQUIRED-OPERATION-NAME",
                "GRAPHQL-UNDEFINED-VARIABLES", "HTTP403", "HTTP404", "HTTP429",
                "HTTP4XX", "HTTP500", "HTTP503", "HTTP5XX", "IMPOSTOR", "INFO-VIEWED",
                "INSECURE-AUTH", "NOTUTF8", "INVITE-FAILURE", "INVITE-ATTEMPT",
                "INVITE-SUCCESS", "JSON-ERROR", "KBA-CHANGED", "LOGINATTEMPT",
                "LOGINDISCOVERY", "LOGINFAILURE", "LOGINSUCCESS", "MALFORMED-DATA",
                "SANS", "MESSAGE-SENT", "NO-CONTENT-TYPE", "NOUA", "NULLBYTE",
                "OOB-DOMAIN", "PW-CHANGED", "PW-RESET-ATTEMPT", "PW-RESET-FAILURE",
                "PW-RESET-SUCCESS", "PRIVATEFILE", "rate-limit", "REGATTEMPT", "REGFAILURE",
                "REGSUCCESS", "RSRC-ID-ENUM-ATTEMPT", "RSRC-ID-ENUM-FAILURE",
                "RSRC-ID-ENUM-SUCCESS", "RESPONSESPLIT", "SCANNER", "SIGSCI-IP",
                "TORNODE", "WRONG-API-CLIENT", "USER-ID-ENUM-ATTEMPT",
                "USER-ID-ENUM-FAILURE", "USER-ID-ENUM-SUCCESS", "WEAKTLS", "XML-ERROR"
            ]
            attack_tags = ",".join(attack_signals)
            anomaly_tags = ",".join(anomaly_signals)
            url = f"{url}&tags={attack_tags},{anomaly_tags}"
        config = Config(
            url=url,
            api_host=api_host,
            from_time=from_time,
            until_time=until_time,
            global_email=global_email,
            global_corp_api_name=global_corp_api_name,
            current_site=current_site,
            request_timeout=request_timeout,
            read_timeout=read_timeout,
        )
        config.headers = {
            "Content-type": "application/json",
            "x-api-user": global_email,
            "x-api-token": global_api_token,
            "User-Agent": config.user_agent_string,
        }

        all_requests = get_results("Requests", helper, config)

        total_requests = len(all_requests)
        helper.log_info("Total Requests Pulled: %s" % total_requests)
        if total_requests == 0:
            helper.save_check_point(last_name, until_time)
            helper.log_info(
                f"No events to write, saving checkpoint to value:{until_time}"
            )
        write_start = timer()
        event_count = 0
        for current_event in all_requests:
            if key is None:
                source_type = helper.get_sourcetype()
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
                event = helper.new_event(
                    source=single_name,
                    index=current_index,
                    sourcetype=source_type,
                    data=current_event,
                )

            try:
                ew.write_event(event)
                event_count += 1  # increment the count for successful events to not spam debug.
            except Exception as e:
                helper.log_error(f"error writing event: {e}")
                helper.log_error(event)
                raise e
        if event_count != 0:  # We save the checkpoint earlier on 0 events.
            helper.log_info(f"{event_count} events written, saving checkpoint: {until_time}")
            helper.save_check_point(last_name, until_time)
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
        for active_input, site in all_sites.items():
            time_delta = int(time_deltas[active_input])
            helper.log_info("site: %s" % site)
            pull_requests(helper, key=active_input, current_site=site, delta=time_delta)
            helper.log_info("Finished Pulling Requests for %s" % site)
    else:
        helper.log_info("Run Type: Concurrent")
        site = helper.get_arg("site_api_name")
        helper.log_info("site: %s" % site)
        pull_requests(helper, current_site=site, delta=int(time_deltas))
        helper.log_info("Finished Pulling Requests for %s" % site)
    end = timer()
    total_time = end - start
    time_result = round(total_time, 2)
    helper.log_info("Total Script Time: %s seconds" % time_result)