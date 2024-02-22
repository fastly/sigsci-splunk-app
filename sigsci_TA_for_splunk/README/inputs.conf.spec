[SigsciRequests://<name>]
site_api_name = This is the API Name of the site to pull request data from. This should not be a URL.
request_limit = The amount of request objects returned in the array. Default: 100. Max:1000
disable_catchup = Disables catch-up behavior. Request feed will always be ingested from now and the delta (and offset). We recommend keeping this as checked for request feeds with large amounts of requests.
twenty_hour_catchup = In the event the last time stored is >24hours the TA will try can try and catch-up from exactly 24 hours ago, otherwise resets to now - delta. Disable catchup must be false in order to work.
attack_and_anomaly_signals_only = Only retrieves requests that contain attack or anomaly signals. Please evaluate your signal configuration if there are overly inclusive signals creating excessive requests.
request_timeout = Configures Request Timeout for HTTP operations. Consider increasing if on a slow connection or pagination batches are large.
read_timeout = Configures Read Timeout for HTTP operations. Consider increasing if on a slow connection or pagination batches are large.

[SigsciActivity://<name>]
disable_catchup = 
twenty_hour_catchup = 
request_timeout = Configures Request Timeout for HTTP operations. Consider increasing if on a slow connection or pagination batches are large.
read_timeout = Configures Read Timeout for HTTP operations. Consider increasing if on a slow connection or pagination batches are large.

[SigsciEvent://<name>]
site_api_name = This is the Site API Name. It should not be a URL.
disable_catchup = Time is always set based from now - delta (Interval). Recommended to be True. Default: True.
twenty_hour_catchup = If last stored timestamp was over 24 hours, resets to exactly 24 hours ago instead to meet API limitations.
request_timeout = Configures Request Timeout for HTTP operations. Consider increasing if on a slow connection or pagination batches are large.
read_timeout = Configured Read Timeout for HTTP operations. Consider increasing if on a slow connection or pagination batches are large.