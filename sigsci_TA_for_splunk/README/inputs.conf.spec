[SigsciEvent://<name>]
site_api_name = This is the Site API Name. It should not be a URL.
disable_catchup = Disables catch-up behavior. Events will always be ingested from now minus the delta (including an offset for the requests feed). Recommended to be left true. Default: True.
twenty_hour_catchup = In the event the last time stored is >24Hours the TA will try and catch-up from exactly 24 hours ago, otherwise resets to now minus the delta. 'Disable Catchup' must be False in order to work.
request_timeout = Configures Request Timeout for HTTP operations. Consider increasing if on a slow connection or pagination batches are large.
read_timeout = Configured Read Timeout for HTTP operations. Consider increasing if on a slow connection or pagination batches are large.

[SigsciActivity://<name>]
disable_catchup = Disables catch-up behavior. Events will always be ingested from now minus the delta (including an offset for the requests feed). Recommended to be left true. Default: True.
twenty_hour_catchup = In the event the last time stored is >24Hours the TA will try and catch-up from exactly 24 hours ago, otherwise resets to now minus the delta. 'Disable Catchup' must be false in order to work.
request_timeout = Configures Request Timeout for HTTP operations. Consider increasing if on a slow connection or pagination batches are large.
read_timeout = Configures Read Timeout for HTTP operations. Consider increasing if on a slow connection or pagination batches are large.

[SigsciRequests://<name>]
site_api_name = This is the API Name of the site to pull request data from. This should not be a URL.
request_limit = The amount of request objects returned in the array. Default: 100. Max:1000
disable_catchup = Disables catch-up behavior. Events will always be ingested from now minus the delta (including an offset for the requests feed). Recommended to be left true. Default: True.
twenty_hour_catchup = In the event the last time stored is >24hours the TA will try can try and catch-up from exactly 24 hours ago, otherwise resets to now minus the delta. 'Disable Catchup' must be False in order to work.
attack_and_anomaly_signals_only = Only retrieves requests that contain attack or anomaly signals. Please evaluate your signal configuration if there are overly inclusive signals creating excessive requests.
request_timeout = Configures Request Timeout for HTTP operations. Consider increasing if on a slow connection or pagination batches are large.
read_timeout = Configures Read Timeout for HTTP operations. Consider increasing if on a slow connection or pagination batches are large.