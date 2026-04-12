"""
Clean DQL Examples - Extracted from production dashboards.
Total examples: 7725
"""

DASHBOARD_EXAMPLES = [

    # === AWS ===
    {
        "nl": "Show average read latency over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter'],
        "dql": """timeseries x = avg(cloud.aws.rds.ReadLatency.By.DBInstanceIdentifier), 
            filter:{in(aws.account.id, array($AccountId)) AND 
                    in(aws.region, array($Region)) AND
                    (in(dt.smartscape_source.id, iCollectArray(toSmartscapeId(array($InstanceId)[]))) OR 
                      matchesValue($InstanceId, "ALL"))}
| fieldsAdd avgLat = arrayAvg(x)""",
    },
    {
        "nl": "Show average write latency over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter'],
        "dql": """timeseries x = avg(cloud.aws.rds.WriteLatency.By.DBInstanceIdentifier), 
            filter:{in(aws.account.id, array($AccountId)) AND 
                    in(aws.region, array($Region)) AND
                    (in(dt.smartscape_source.id, iCollectArray(toSmartscapeId(array($InstanceId)[]))) OR 
                      matchesValue($InstanceId, "ALL"))}
| fieldsAdd avgLat = arrayAvg(x)""",
    },
    {
        "nl": "Show average network receive throughput over time",
        "intent": "host_network",
        "expected_contains": ['timeseries', 'avg(', 'filter'],
        "dql": """timeseries x = avg(cloud.aws.rds.NetworkReceiveThroughput.By.DBInstanceIdentifier), 
            filter:{in(aws.account.id, array($AccountId)) AND 
                    in(aws.region, array($Region)) AND
                    (in(dt.smartscape_source.id, iCollectArray(toSmartscapeId(array($InstanceId)[]))) OR 
                      matchesValue($InstanceId, "ALL"))}
| fieldsAdd AvgThr = arrayAvg(x)""",
    },
    {
        "nl": "Show average network transmit throughput over time",
        "intent": "host_network",
        "expected_contains": ['timeseries', 'avg(', 'filter'],
        "dql": """timeseries x = avg(cloud.aws.rds.NetworkTransmitThroughput.By.DBInstanceIdentifier), 
            filter:{in(aws.account.id, array($AccountId)) AND 
                    in(aws.region, array($Region)) AND
                    (in(dt.smartscape_source.id, iCollectArray(toSmartscapeId(array($InstanceId)[]))) OR 
                      matchesValue($InstanceId, "ALL"))}
| fieldsAdd AvgThr = arrayAvg(x)""",
    },
    {
        "nl": "Show mean invocation latency per function per region over time",
        "intent": "aws_bedrock",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries { avg(cloud.aws.bedrock.invocationLatencyByAccountIdRegion), value.A = avg(cloud.aws.bedrock.invocationLatencyByAccountIdRegion, scalar: true) }, interval: 1h, by: { aws.region }, filter: { matchesValue(aws.account.id, { "<account-id>", "<account-id>", "<account-id>" }) }""",
    },
    {
        "nl": "Show sum of invocations per function per region over time",
        "intent": "aws_lambda",
        "expected_contains": ['timeseries', 'sum(', 'avg(', 'filter', 'by'],
        "dql": """timeseries { sum(cloud.aws.lambda.invocationsByAccountIdFunctionNameRegion), value.A = avg(cloud.aws.lambda.invocationsByAccountIdFunctionNameRegion, scalar: true) }, by: { aws.region, aws.account.id, functionname }, filter: {  in (aws.account.id, array("<account-id>","<account-id>" ,"<account-id>") ) }""",
    },
    {
        "nl": "Show mean of input token per function per region over time",
        "intent": "aws_bedrock",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries { avg(cloud.aws.bedrock.inputTokenCountByAccountIdRegion), value.A = avg(cloud.aws.bedrock.inputTokenCountByAccountIdRegion, scalar: true) }, interval: 1h, by: { aws.region }, filter: { matchesValue(aws.account.id, { "<account-id>", "<account-id>", "<account-id>" }) }""",
    },
    {
        "nl": "Show average duration of response per function per region over time",
        "intent": "aws_lambda",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries { avg(cloud.aws.lambda.durationByAccountIdFunctionNameRegionResource), value.A = avg(cloud.aws.lambda.durationByAccountIdFunctionNameRegionResource, scalar: true) }, interval: 1h, by: { aws.region, functionname }, filter: { matchesValue(aws.account.id, { "<account-id>", "<account-id>", "<account-id>" }) }""",
    },
    {
        "nl": "Show sum of errors per function per region over time",
        "intent": "aws_lambda",
        "expected_contains": ['timeseries', 'sum(', 'avg(', 'filter', 'by'],
        "dql": """timeseries { sum(cloud.aws.lambda.errorsByAccountIdFunctionNameRegionResource), value.A = avg(cloud.aws.lambda.errorsByAccountIdFunctionNameRegionResource, scalar: true) }, interval: 30m, by: { aws.region, functionname }, filter: { matchesValue(aws.account.id, { "<account-id>", "<account-id>", "<account-id>" }) }""",
    },
    {
        "nl": "Show engine cpu utilization over time",
        "intent": "host_cpu",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries { avg(cloud.aws.eccustom.engine_cpuutilization), value.A = avg(cloud.aws.eccustom.engine_cpuutilization, scalar: true) }, by: { dt.entity.custom_device }, filter: { matchesValue(dt.source_entity.type, "cloud:aws:elasticachecustom") AND matchesValue(entityAttr(dt.entity.custom_device, "entity.name"), { $Instance }) }
| fieldsAdd dt.entity.custom_device.name = entityName(dt.entity.custom_device)
| limit 20""",
    },
    {
        "nl": "Show swap usage over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries { avg(cloud.aws.eccustom.swap_usage), value.A = avg(cloud.aws.eccustom.swap_usage, scalar: true) }, by: { dt.entity.custom_device }, filter: { matchesValue(dt.source_entity.type, "cloud:aws:elasticachecustom") AND matchesValue(entityAttr(dt.entity.custom_device, "entity.name"), { $Instance }) }
| fieldsAdd dt.entity.custom_device.name = entityName(dt.entity.custom_device)
| limit 20""",
    },
    {
        "nl": "Show freeable memory over time",
        "intent": "host_memory",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries { avg(cloud.aws.eccustom.freeable_memory), value.A = avg(cloud.aws.eccustom.freeable_memory, scalar: true) }, by: { dt.entity.custom_device }, filter: { matchesValue(dt.source_entity.type, "cloud:aws:elasticachecustom") AND matchesValue(entityAttr(dt.entity.custom_device, "entity.name"), { $Instance }) }
| fieldsAdd dt.entity.custom_device.name = entityName(dt.entity.custom_device)
| limit 20""",
    },
    {
        "nl": "Show network bytes in over time",
        "intent": "host_network",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries { avg(cloud.aws.eccustom.network_bytes_in_sum), value.A = avg(cloud.aws.eccustom.network_bytes_in_sum, scalar: true) }, by: { dt.entity.custom_device }, filter: { matchesValue(dt.source_entity.type, "cloud:aws:elasticachecustom") AND matchesValue(entityAttr(dt.entity.custom_device, "entity.name"), { $Instance }) }
| fieldsAdd dt.entity.custom_device.name = entityName(dt.entity.custom_device)
| limit 20""",
    },
    {
        "nl": "Show network bytes out over time",
        "intent": "host_network",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries { avg(cloud.aws.eccustom.network_bytes_out_sum), value.A = avg(cloud.aws.eccustom.network_bytes_out_sum, scalar: true) }, by: { dt.entity.custom_device }, filter: { matchesValue(dt.source_entity.type, "cloud:aws:elasticachecustom") AND matchesValue(entityAttr(dt.entity.custom_device, "entity.name"), { $Instance }) }
| fieldsAdd dt.entity.custom_device.name = entityName(dt.entity.custom_device)
| limit 20""",
    },
    {
        "nl": "Show current connections over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries { avg(cloud.aws.eccustom.curr_connections), value.A = avg(cloud.aws.eccustom.curr_connections, scalar: true) }, by: { dt.entity.custom_device }, filter: { matchesValue(dt.source_entity.type, "cloud:aws:elasticachecustom") AND matchesValue(entityAttr(dt.entity.custom_device, "entity.name"), { $Instance }) }
| fieldsAdd dt.entity.custom_device.name = entityName(dt.entity.custom_device)
| limit 20""",
    },
    {
        "nl": "Show network bandwidth out allowance exceeded over time",
        "intent": "host_network",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries { avg(cloud.aws.eccustom.network_bandwidth_out_allowance_exceeded_sum), value.A = avg(cloud.aws.eccustom.network_bandwidth_out_allowance_exceeded_sum, scalar: true) }, by: { dt.entity.custom_device }, filter: { matchesValue(dt.source_entity.type, "cloud:aws:elasticachecustom") AND matchesValue(entityAttr(dt.entity.custom_device, "entity.name"), { $Instance }) }
| fieldsAdd dt.entity.custom_device.name = entityName(dt.entity.custom_device)
| limit 20""",
    },
    {
        "nl": "Show replication bytes over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries { avg(cloud.aws.eccustom.replication_bytes), value.A = avg(cloud.aws.eccustom.replication_bytes, scalar: true) }, by: { dt.entity.custom_device }, filter: { matchesValue(dt.source_entity.type, "cloud:aws:elasticachecustom") AND matchesValue(entityAttr(dt.entity.custom_device, "entity.name"), { $Instance }) }
| fieldsAdd dt.entity.custom_device.name = entityName(dt.entity.custom_device)
| limit 20""",
    },
    {
        "nl": "Show evictions over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries { avg(cloud.aws.eccustom.evictions_sum), value.A = avg(cloud.aws.eccustom.evictions_sum, scalar: true) }, by: { dt.entity.custom_device }, filter: { matchesValue(dt.source_entity.type, "cloud:aws:elasticachecustom") AND matchesValue(entityAttr(dt.entity.custom_device, "entity.name"), { $Instance }) }
| fieldsAdd dt.entity.custom_device.name = entityName(dt.entity.custom_device)
| limit 20""",
    },
    {
        "nl": "Show cache hit ratio over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries avg(cloud.aws.eccustom.cache_hits_sum), by: { dt.entity.custom_device }, filter: { matchesValue(entityAttr(dt.entity.custom_device, "entity.name"), { $Instance }) AND matchesValue(dt.source_entity.type, "cloud:aws:elasticachecustom") }
| fieldsAdd dt.entity.custom_device.name = entityName(dt.entity.custom_device)
| limit 20
| join [
    timeseries avg(cloud.aws.eccustom.cache_misses_sum),
    by: { dt.entity.custom_device },
    filter: { matchesValue(entityAttr(dt.entity.custom_device, "entity.name"), { $Instance }) AND matchesValue(dt.source_entity.type, "cloud:aws:elasticachecustom") }
    | fieldsAdd dt.entity.custom_device.name = entityName(dt.entity.custom_device)
    | limit 20
  ], on: { dt.entity.custom_device }, fields: { `avg(cloud.aws.eccustom.cache_misses_sum)` }
| fieldsAdd CacheHitRatio = `avg(cloud.aws.eccustom.cache_hits_sum)`[]/(`avg(cloud.aws.eccustom.cache_hits_sum)`[]+`avg(cloud.aws.eccustom.cache_misses_sum)`[])*100
| fieldsRemove `avg(cloud.aws.eccustom.cache_hits_sum)`, `avg(cloud.aws.eccustom.cache_misses_sum)`""",
    },
    {
        "nl": "Show redis traffic out [aws] over time",
        "intent": "host_network",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries network_bytes_out = max(cloud.aws.eccustom.network_bytes_out_sum, rate: 1s),
by: { dt.entity.custom_device },
filter: {
contains(entityName(dt.entity.custom_device), "apigw")
AND not contains(entityName(dt.entity.custom_device), "private")
}
| sort arraySum(network_bytes_out) desc
| fieldsAdd entityName(dt.entity.custom_device)
| fieldsRemove dt.entity.custom_device
| sort network_bytes_out desc
| parse dt.entity.custom_device.name, """ "dtp-" LD:installation "-apigw-" INT:instance """
| fieldsAdd label = concat(installation, "-", instance)
| limit toLong($MetricsLimit)""",
    },
    {
        "nl": "Show redis network bandwidth out exceeded [aws] over time",
        "intent": "host_network",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries network_bandwidth_out_allowance_exceeded = sum(cloud.aws.eccustom.network_bandwidth_out_allowance_exceeded_sum, rate: 1s),
by: { dt.entity.custom_device },
filter: {
contains(entityName(dt.entity.custom_device), "apigw")
AND not contains(entityName(dt.entity.custom_device), "private")
}
| sort arraySum(network_bandwidth_out_allowance_exceeded) desc
| fieldsAdd entityName(dt.entity.custom_device)
| fieldsRemove dt.entity.custom_device
| sort network_bandwidth_out_allowance_exceeded desc
| parse dt.entity.custom_device.name, """ "dtp-" LD:installation "-apigw-" INT:instance """
| fieldsAdd label = concat(installation, "-", instance)
| limit toLong($MetricsLimit)""",
    },
    {
        "nl": "Show response time "execute-non-billable-spans-dql" over time",
        "intent": "service_latency",
        "expected_contains": ['fetch spans', 'timeseries', 'avg(', 'percentile', 'filter'],
        "dql": """fetch spans, samplingRatio:1
//| filter span.name == "app function:api/execute-non-billable-spans-dql"
| filter span.name == "Runtime AWS Lambda event handler"
| filter dt.app.function == "/api/execute-non-billable-spans-dql"
| makeTimeseries { 
    avg=avg(duration)
    //,p50=percentile(duration, 50)
    //,p90=percentile(duration, 90)
    ,p99=percentile(duration, 99)
    //,max=max(duration)
}""",
    },
    {
        "nl": "Show slowest "execute-non-billable-spans-dql"",
        "intent": "service_latency",
        "expected_contains": ['fetch spans', 'filter'],
        "dql": """fetch spans, samplingRatio:100
//| filter span.name == "app function:api/execute-non-billable-spans-dql"
| filter span.name == "Runtime AWS Lambda event handler"
| filter dt.app.function == "/api/execute-non-billable-spans-dql"
| fields start_time, end_time, duration, trace.id

| sort duration desc
| limit 10""",
    },
    {
        "nl": "Show metric processor errors over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'sum(', 'by'],
        "dql": """timeseries failure_count = sum(dt.service.request.failure_count, scalar: true), by: { dt.entity.service}
| fieldsAdd entityName(dt.entity.service)
| limit 100""",
    },
    {
        "nl": "Show metric processor errors over time over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'sum(', 'by'],
        "dql": """timeseries { failure_count = sum(dt.service.request.failure_count), count = sum(dt.service.request.count) }, by: { dt.entity.service }, union: true
| fieldsAdd entityName(dt.entity.service)
| fieldsAdd failure_percent = failure_count[] * 100 / count[]
| fieldsRemove failure_count, count""",
    },
    {
        "nl": "Show lambda invocations over time",
        "intent": "aws_lambda",
        "expected_contains": ['timeseries', 'sum(', 'by'],
        "dql": """timeseries invocations_sum = sum(cloud.aws.lambda.invocations_sum), by: { dt.entity.custom_device }
| fieldsAdd entityName(dt.entity.custom_device)
| limit 20""",
    },
    {
        "nl": "Show lambda duration avg over time",
        "intent": "aws_lambda",
        "expected_contains": ['timeseries', 'avg(', 'by'],
        "dql": """timeseries duration = avg(dt.cloud.aws.lambda.duration), by: { dt.entity.aws_lambda_function }
| fieldsAdd entityName(dt.entity.aws_lambda_function)
| sort arrayAvg(duration) desc
| append [ timeseries duration = avg(cloud.aws.lambda.duration), by: { dt.entity.custom_device }
         | fieldsAdd entityName(dt.entity.custom_device) ]
| limit 20""",
    },
    {
        "nl": "Show mint lines invalid over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'by'],
        "dql": """timeseries mint_lines_invalid_sum_by_region_dynatrace_tenant_url_function_name = sum(cloud.aws.dt_metrics_streaming.mint_lines_invalid_sum_by_region_dynatrace_tenant_url_function_name), by: { function_name }
| sort arraySum(mint_lines_invalid_sum_by_region_dynatrace_tenant_url_function_name) desc
| limit 20""",
    },
    {
        "nl": "Show mint lines ingested over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'by'],
        "dql": """timeseries mint_lines_ingested_sum_by_region_dynatrace_tenant_url_function_name = sum(cloud.aws.dt_metrics_streaming.mint_lines_ingested_sum_by_region_dynatrace_tenant_url_function_name), by: { function_name }
| sort arraySum(mint_lines_ingested_sum_by_region_dynatrace_tenant_url_function_name) desc
| limit 20""",
    },
    {
        "nl": "Show dynatrace requests count over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'sum(', 'by'],
        "dql": """timeseries dynatrace_requests_count_sum_by_region_dynatrace_tenant_url_function_name = sum(cloud.aws.dt_metrics_streaming.dynatrace_requests_count_sum_by_region_dynatrace_tenant_url_function_name), by: { function_name }
| sort arraySum(dynatrace_requests_count_sum_by_region_dynatrace_tenant_url_function_name) desc
| limit 20""",
    },

    # === AZURE ===
    {
        "nl": "Show tenant - local dev over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'by'],
        "dql": """timeseries CREATE_DEFAULT = sum(platform.settings.service.api.localdevmode.create_schema_default.count), by:{ dt.tenant.uuid }
| fieldsAdd CREATE_DEFAULT = arraySum(CREATE_DEFAULT)
| append [timeseries VALIDATE_MOCK_DATA = sum(platform.settings.service.api.localdevmode.validate_mock_data.count), by:{ dt.tenant.uuid }
         | fieldsAdd VALIDATE_MOCK_DATA = arraySum(VALIDATE_MOCK_DATA)]
| append [timeseries VALIDATE_SCHEMA = sum(platform.settings.service.api.localdevmode.validate_schema.count), by:{ dt.tenant.uuid }
         | fieldsAdd VALIDATE_SCHEMA = arraySum(VALIDATE_SCHEMA)]
| summarize { CREATE_DEFAULT = takeAny(CREATE_DEFAULT), VALIDATE_MOCK_DATA = takeAny(VALIDATE_MOCK_DATA), VALIDATE_SCHEMA = takeAny(VALIDATE_SCHEMA) }, 
  by: { dt.tenant.uuid }
| sort { VALIDATE_SCHEMA desc, VALIDATE_MOCK_DATA desc, CREATE_DEFAULT desc }""",
    },
    {
        "nl": "Show redis traffic out [azure] over time",
        "intent": "host_network",
        "expected_contains": ['timeseries', 'filter', 'by'],
        "dql": """timeseries network_bytes_out = max(dt.cloud.azure.redis.cache.read, rate:1s),
by: { dt.entity.azure_redis_cache},
filter: {
contains(entityName(dt.entity.azure_redis_cache), "apigw")
AND not contains(entityName(dt.entity.azure_redis_cache), "private")
}

| fieldsAdd entityName = entityName(dt.entity.azure_redis_cache)
| sort dt.entity.azure_redis_cache desc
| parse entityName, """ "dtp-" LD:installation "-apigw""""
| limit toLong($MetricsLimit)""",
    },
    {
        "nl": "Show invocations per minute, azure openai over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries invocations = sum(copilot.worker.llm_invocations), 
interval: 1m,
by: {skill}
| filter in(skill, $skill)
| summarize `invocations` = sum(invocations[]), by:{timeframe, interval, skill}""",
    },
    {
        "nl": "Show percentage of failed service requests, azure openai over time",
        "intent": "service_entity",
        "expected_contains": ['fetch dt.entity.service', 'timeseries', 'sum(', 'avg(', 'filter', 'by'],
        "dql": """timeseries {total=sum(dt.service.request.count), failures=sum(dt.service.request.failure_count) }, by: { dt.entity.service }
| lookup [
 fetch dt.entity.service 
 | filter contains(entity.name, "openai.azure.com")
 | fieldsAdd entity.name 
 | fieldsAdd id
] , prefix: "ent.", sourceField:dt.entity.service, lookupField: id
| filter isNotNull(ent.id)
| fieldsAdd sliArray = 100 * (failures[]/total[])
| fields sli = arrayAvg(sliArray)""",
    },
    {
        "nl": "Show maximum invocations per minute, azure openai over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries invocations = sum(copilot.worker.llm_invocations), 
interval: 1m,
by: {skill}
| filter in(skill, $skill)
| summarize invocations1 = sum(invocations[]), by:{timeframe, interval, skill}
| fields skill, invocations1
| fields skill, `#invocations`=arrayMax(invocations1)
////| summarize `invocations2` = max(invocations[]), by:{skill}""",
    },
    {
        "nl": "Count of azure cost plotted, split by subscription",
        "intent": "events",
        "expected_contains": ['fetch events', 'sum(', 'filter', 'by'],
        "dql": """fetch events, from: now()-1095d
| filter dt.system.bucket == "custom_sen_critical_events_finops_final_nonprod"
AND event.type == "BillingDataAggregate"
AND event.provider == "rnd.data.preaggregation.workflow"
| filter dt_CloudProvider == "Microsoft"

| filter in(dt_Capability,$Capability)

| filter in(SubAccountName, $AzureSubscription)

| filter substring(dt_UsageDay, to:7) >= $from AND
substring(dt_UsageDay, to:7) <= $to

| fieldsAdd usageDayTs = toTimestamp(concat(replaceString(dt_UsageDay, ".", "-"), "T00:00:00Z"))
| summarize {cost_per_capability = sum(EffectiveCost)},by:{SubAccountName, dt_UsageDay = bin(usageDayTs,24h)}""",
    },
    {
        "nl": "Count of azure cost plotted, split by capability",
        "intent": "events",
        "expected_contains": ['fetch events', 'sum(', 'filter', 'by'],
        "dql": """fetch events, from: now()-1095d
| filter dt.system.bucket == "custom_sen_critical_events_finops_final_nonprod"
AND event.type == "BillingDataAggregate"
AND event.provider == "rnd.data.preaggregation.workflow"
| filter dt_CloudProvider == "Microsoft"

| filter in(dt_Capability,$Capability)

| filter in(SubAccountName, $AzureSubscription)

| filter substring(dt_UsageDay, to:7) >= $from AND
substring(dt_UsageDay, to:7) <= $to

| fieldsAdd usageDayTs = toTimestamp(concat(replaceString(dt_UsageDay, ".", "-"), "T00:00:00Z"))
| summarize {cost_per_capability = sum(EffectiveCost)},by:{dt_Capability, dt_UsageDay = bin(usageDayTs,24h)}""",
    },
    {
        "nl": "Count of azure cost total daily",
        "intent": "events",
        "expected_contains": ['fetch events', 'sum(', 'filter', 'by'],
        "dql": """fetch events, from: now()-1095d
| filter dt.system.bucket == "custom_sen_critical_events_finops_final_nonprod"
AND event.type == "BillingDataAggregate"
AND event.provider == "rnd.data.preaggregation.workflow"
| filter dt_CloudProvider == "Microsoft"

| filter in(dt_Capability,$Capability)

| filter in(SubAccountName, $AzureSubscription)

| filter substring(dt_UsageDay, to:7) >= $from AND
substring(dt_UsageDay, to:7) <= $to

| summarize {daily_cost = sum(EffectiveCost)},by:{dt_UsageDay = substring(dt_UsageDay, to:7)}
| sort dt_UsageDay""",
    },
    {
        "nl": "Count of azure cost",
        "intent": "events",
        "expected_contains": ['fetch events', 'sum(', 'filter'],
        "dql": """fetch events, from: now()-1095d
| filter dt.system.bucket == "custom_sen_critical_events_finops_final_nonprod"
AND event.type == "BillingDataAggregate"
AND event.provider == "rnd.data.preaggregation.workflow"
| filter dt_CloudProvider == "Microsoft"

| filter in(dt_Capability,$Capability)

| filter in(SubAccountName, $AzureSubscription)

| filter substring(dt_UsageDay, to:7) >= $from AND
substring(dt_UsageDay, to:7) <= $to

| summarize {cost = sum(EffectiveCost)}""",
    },
    {
        "nl": "Count of azure cost split by account",
        "intent": "events",
        "expected_contains": ['fetch events', 'sum(', 'filter', 'by'],
        "dql": """fetch events, from: now()-1095d
| filter dt.system.bucket == "custom_sen_critical_events_finops_final_nonprod"
AND event.type == "BillingDataAggregate"
AND event.provider == "rnd.data.preaggregation.workflow"
| filter dt_CloudProvider == "Microsoft"

| filter in(dt_Capability,$Capability)

| filter in(SubAccountName, $AzureSubscription)

| filter substring(dt_UsageDay, to:7) >= $from AND
substring(dt_UsageDay, to:7) <= $to

| summarize {cost = sum(EffectiveCost)},by:{SubAccountName}
| sort cost desc""",
    },
    {
        "nl": "Count of azure cost total plotted",
        "intent": "events",
        "expected_contains": ['fetch events', 'sum(', 'filter', 'by'],
        "dql": """fetch events, from: now()-1095d
| filter dt.system.bucket == "custom_sen_critical_events_finops_final_nonprod"
AND event.type == "BillingDataAggregate"
AND event.provider == "rnd.data.preaggregation.workflow"
| filter dt_CloudProvider == "Microsoft"

| filter in(dt_Capability,$Capability)

| filter in(SubAccountName, $AzureSubscription)

| filter substring(dt_UsageDay, to:7) >= $from AND
substring(dt_UsageDay, to:7) <= $to

| fieldsAdd usageDayTs = toTimestamp(concat(replaceString(dt_UsageDay, ".", "-"), "T00:00:00Z"))
| summarize {daily_cost = sum(EffectiveCost)},by:{dt_UsageDay = bin(usageDayTs,24h)}""",
    },
    {
        "nl": "Show heap used over time",
        "intent": "host_memory",
        "expected_contains": ['timeseries', 'filter', 'by'],
        "dql": """timeseries used = max(dt.runtime.jvm.memory_pool.used), by: { dt.entity.process_group_instance }, filter: { in(dt.entity.process_group_instance, classicEntitySelector("type(\"PROCESS_GROUP_INSTANCE\"),tag(\"Dtp_Platform-Services_Hub_Channels\")")) }
| fieldsAdd entityName(dt.entity.process_group_instance)
| fieldsRemove dt.entity.process_group_instance""",
    },
    {
        "nl": "Show heap committed over time",
        "intent": "host_memory",
        "expected_contains": ['timeseries', 'filter', 'by'],
        "dql": """timeseries committed = max(dt.runtime.jvm.memory_pool.committed), by: { dt.entity.process_group_instance }, filter: { in(dt.entity.process_group_instance, classicEntitySelector("type(\"PROCESS_GROUP_INSTANCE\"),tag(\"Dtp_Platform-Services_Hub_Channels\")")) }
| fieldsAdd entityName(dt.entity.process_group_instance)
| fieldsRemove dt.entity.process_group_instance""",
    },
    {
        "nl": "Show connected clients per instance over time",
        "intent": "azure_metrics",
        "expected_contains": ['timeseries', 'filter', 'by'],
        "dql": """timeseries clients = max(cloud.azure.microsoft_cache.redisenterprise.connectedclients),
                     by:{azure.resource.name, azure.subscription, azure.location, azure.resource.group, dt.smartscape_source.id},
                     filter:{in(azure.subscription, array($Subscription)) AND
                             in(azure.location, array($Location)) AND
                             in(azure.resource.group, array($ResourceGroup)) }
| sort ArrayMax(clients) desc
| limit toLong($Limit)""",
    },
    {
        "nl": "Count of storage accounts",
        "intent": "azure_entity",
        "expected_contains": ['fetch dt.entity.azure_storage_account', 'count()', 'filter', 'by'],
        "dql": """fetch dt.entity.azure_storage_account | fieldsAdd  azure.resource.type = "Storage Accounts"
| append [ fetch dt.entity.custom_device | filter entity.type == "cloud:azure:storage:storageaccounts" | fieldsAdd  azure.resource.type = "Storage Accounts"]
| append [ fetch dt.entity.custom_device | filter entity.type == "cloud:azure:classic_storage_account" | fieldsAdd  azure.resource.type = "Classic Storage Accounts"]
| summarize count= count(), by: {azure.resource.type}""",
    },
    {
        "nl": "Count of network devices",
        "intent": "azure_entity",
        "expected_contains": ['fetch dt.entity.azure_application_gateway', 'count()', 'filter', 'by'],
        "dql": """fetch dt.entity.azure_application_gateway | fieldsAdd  azure.resource.type = "Application Gateway"
| append [ fetch dt.entity.azure_api_management_service | fieldsAdd azure.resource.type = "API Management"]
| append [ fetch dt.entity.custom_device | filter entity.type == "cloud:azure:network:applicationgateways" | fieldsAdd  azure.resource.type = "Application Gateway"]
| append [ fetch dt.entity.custom_device | filter entity.type == "cloud:azure:network:azurefirewalls" | fieldsAdd  azure.resource.type = "Azure Firewall"]
| append [ fetch dt.entity.custom_device | filter entity.type == "cloud:azure:network:dnszones" | fieldsAdd  azure.resource.type = "DNS Zone"]
| append [ fetch dt.entity.custom_device | filter entity.type == "cloud:azure:network:expressroutecircuits" | fieldsAdd  azure.resource.type = "ExpressRoute Circuit"]
| append [ fetch dt.entity.custom_device | filter entity.type == "cloud:azure:frontdoor" | fieldsAdd  azure.resource.type = "Front Door (classic)"]
| append [ fetch dt.entity.custom_device | filter entity.type == "cloud:azure:network:loadbalancers:basic" | fieldsAdd  azure.resource.type = "Basic Load Balancer"]
| append [ fetch dt.entity.custom_device | filter entity.type == "cloud:azure:network:loadbalancers:gateway" | fieldsAdd  azure.resource.type = "Gateway Load Balancer"]
| append [ fetch dt.entity.custom_device | filter entity.type == "cloud:azure:network:loadbalancers:standard" | fieldsAdd  azure.resource.type = "Standard Load Balancer"]
| append [ fetch dt.entity.custom_device | filter entity.type == "cloud:azure:network:privatednszones" | fieldsAdd  azure.resource.type = "Private DNS Zone"]
| append [ fetch dt.entity.custom_device | filter entity.type == "cloud:azure:network:publicipAddress" | fieldsAdd  azure.resource.type = "Public IP Address"]
| append [ fetch dt.entity.custom_device | filter entity.type == "cloud:azure:traffic_manager_profile" | fieldsAdd  azure.resource.type = "Traffic Manager Profile"]
| append [ fetch dt.entity.custom_device | filter entity.type == "cloud:azure:virtual_network_gateway" | fieldsAdd  azure.resource.type = "Virtual Network Gateway"]
| summarize count= count(), by: {azure.resource.type}""",
    },
    {
        "nl": "Count of azure marketplace cost split by publisher",
        "intent": "events",
        "expected_contains": ['fetch events', 'sum(', 'filter', 'by'],
        "dql": """fetch events
| filter in(dt.system.bucket, { "custom_sen_critical_events_finops_draft_nonprod", "custom_sen_critical_events_finops_draft_prod", "custom_sen_critical_events_finops_final_nonprod", "custom_sen_critical_events_finops_final_prod" })
| filter event.provider == "Microsoft"
  AND in(event.type, { "BillingDraft", "BillingFinal" })

| filter in(SubAccountName, $MicrosoftAccount)
| filterOut in(lower(ChargeCategory), { "credit", "tax", "refund", "adjustment" })

| filter x_PublisherCategory == "Vendor"

| filter ChargePeriodStart >= toTimestamp($dt_timeframe_from) AND
ChargePeriodStart <= toTimestamp($dt_timeframe_to)

| summarize {cost = sum(EffectiveCost)}, by: {PublisherName}
| sort cost desc""",
    },
    {
        "nl": "Count of azure marketplace cost split by subscription",
        "intent": "events",
        "expected_contains": ['fetch events', 'sum(', 'filter', 'by'],
        "dql": """fetch events
| filter in(dt.system.bucket, { "custom_sen_critical_events_finops_draft_nonprod", "custom_sen_critical_events_finops_draft_prod", "custom_sen_critical_events_finops_final_nonprod", "custom_sen_critical_events_finops_final_prod" })
| filter event.provider == "Microsoft"
  AND in(event.type, { "BillingDraft", "BillingFinal" })

| filter in(SubAccountName, $MicrosoftAccount)
| filterOut in(lower(ChargeCategory), { "credit", "tax", "refund", "adjustment" })

| filter x_PublisherCategory == "Vendor"

| filter ChargePeriodStart >= toTimestamp($dt_timeframe_from) AND
ChargePeriodStart <= toTimestamp($dt_timeframe_to)

| summarize {cost = sum(EffectiveCost)}, by: {SubAccountName}
| sort cost desc""",
    },
    {
        "nl": "Count of azure marketplace cost",
        "intent": "events",
        "expected_contains": ['fetch events', 'sum(', 'filter'],
        "dql": """fetch events
| filter in(dt.system.bucket, { "custom_sen_critical_events_finops_draft_nonprod", "custom_sen_critical_events_finops_draft_prod", "custom_sen_critical_events_finops_final_nonprod", "custom_sen_critical_events_finops_final_prod" })
| filter event.provider == "Microsoft"
  AND in(event.type, { "BillingDraft", "BillingFinal" })

| filter in(SubAccountName, $MicrosoftAccount)
| filterOut in(lower(ChargeCategory), { "credit", "tax", "refund", "adjustment" })

| filter x_PublisherCategory == "Vendor"

| filter ChargePeriodStart >= toTimestamp($dt_timeframe_from) AND
ChargePeriodStart <= toTimestamp($dt_timeframe_to)

| summarize {cost = sum(EffectiveCost)}""",
    },
    {
        "nl": "Count of azure marketplace cost by day",
        "intent": "events",
        "expected_contains": ['fetch events', 'sum(', 'filter', 'by'],
        "dql": """fetch events
| filter in(dt.system.bucket, { "custom_sen_critical_events_finops_draft_nonprod", "custom_sen_critical_events_finops_draft_prod", "custom_sen_critical_events_finops_final_nonprod", "custom_sen_critical_events_finops_final_prod" })
| filter event.provider == "Microsoft"
  AND in(event.type, { "BillingDraft", "BillingFinal" })

| filter in(SubAccountName, $MicrosoftAccount)
| filterOut in(lower(ChargeCategory), { "credit", "tax", "refund", "adjustment" })

| filter x_PublisherCategory == "Vendor"

| filter ChargePeriodStart >= toTimestamp($dt_timeframe_from) AND
ChargePeriodStart <= toTimestamp($dt_timeframe_to)

| summarize {cost = sum(EffectiveCost)}, by: { UsageDay = bin(ChargePeriodStart,24h) }""",
    },
    {
        "nl": "Count of azure marketplace cost by month",
        "intent": "events",
        "expected_contains": ['fetch events', 'sum(', 'filter', 'by'],
        "dql": """fetch events
| filter in(dt.system.bucket, { "custom_sen_critical_events_finops_draft_nonprod", "custom_sen_critical_events_finops_draft_prod", "custom_sen_critical_events_finops_final_nonprod", "custom_sen_critical_events_finops_final_prod" })
| filter event.provider == "Microsoft"
  AND in(event.type, { "BillingDraft", "BillingFinal" })

| filter in(SubAccountName, $MicrosoftAccount)
| filterOut in(lower(ChargeCategory), { "credit", "tax", "refund", "adjustment" })

| filter x_PublisherCategory == "Vendor"

| filter ChargePeriodStart >= toTimestamp($dt_timeframe_from) AND
ChargePeriodStart <= toTimestamp($dt_timeframe_to)

| summarize {cost = sum(EffectiveCost)}, by: {Month = formatTimestamp(ChargePeriodStart, format:"yyyy-MM")}""",
    },
    {
        "nl": "Count of azure latest marketplace cost split by day, account and publisher",
        "intent": "events",
        "expected_contains": ['fetch events', 'sum(', 'filter', 'by'],
        "dql": """fetch events
| filter in(dt.system.bucket, { "custom_sen_critical_events_finops_draft_nonprod", "custom_sen_critical_events_finops_draft_prod", "custom_sen_critical_events_finops_final_nonprod", "custom_sen_critical_events_finops_final_prod" })
| filter event.provider == "Microsoft"
  AND in(event.type, { "BillingDraft", "BillingFinal" })

| filter in(SubAccountName, $MicrosoftAccount)
| filterOut in(lower(ChargeCategory), { "credit", "tax", "refund", "adjustment" })

| filter x_PublisherCategory == "Vendor"

| filter ChargePeriodStart >= toTimestamp($dt_timeframe_from) AND
ChargePeriodStart <= toTimestamp($dt_timeframe_to)

| summarize {cost = sum(EffectiveCost)}, by: {day = bin(ChargePeriodStart,24h), SubAccountName, PublisherName}
| sort cost desc""",
    },
    {
        "nl": "Show azure access tokens rotation executions chart over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'filter'],
        "dql": """timeseries filter:dt.entity.service == "SERVICE-7A98C174A87251DF", max_response_time = max(dt.service.request.response_time)""",
    },
    {
        "nl": "Show available memory over time",
        "intent": "host_memory",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries availMemB = avg(cloud.azure.microsoft_compute.virtualmachinescalesets.AvailableMemoryBytes), 
by:{azure.resource.name, azure.subscription, azure.location, azure.resource.group, dt.smartscape_source.id},
filter:{
	in(azure.subscription, array($Subscription)) AND 
	in(azure.location, array($Location)) AND 
	in(azure.resource.group, array($ResourceGroup))}
| sort arrayAvg(availMemB) desc
| limit toLong($Limit)""",
    },
    {
        "nl": "Show cpu credits consumed over time",
        "intent": "host_cpu",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries creditsUsed = avg(cloud.azure.microsoft_compute.virtualmachines.CPUCreditsConsumed), 
by:{azure.resource.name, azure.subscription, azure.location, azure.resource.group, dt.smartscape_source.id},
filter:{
	in(azure.subscription, array($Subscription)) AND 
	in(azure.location, array($Location)) AND 
	in(azure.resource.group, array($ResourceGroup))}
| sort arrayAvg(creditsUsed) desc
| limit toLong($Limit)""",
    },
    {
        "nl": "Show cpu credits remaining over time",
        "intent": "host_cpu",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries creditsLeft = avg(cloud.azure.microsoft_compute.virtualmachines.CPUCreditsRemaining), 
by:{azure.resource.name, azure.subscription, azure.location, azure.resource.group, dt.smartscape_source.id},
filter:{
	in(azure.subscription, array($Subscription)) AND 
	in(azure.location, array($Location)) AND 
	in(azure.resource.group, array($ResourceGroup))}
| sort arrayAvg(creditsLeft) desc
| limit toLong($Limit)""",
    },
    {
        "nl": "Show inbound vs outbound flows over time",
        "intent": "azure_metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries {inFlows = avg(cloud.azure.microsoft_compute.virtualmachines.InboundFlows), outFlows = avg(cloud.azure.microsoft_compute.virtualmachines.OutboundFlows)}, 
by:{azure.resource.name, azure.subscription, azure.location, azure.resource.group, dt.smartscape_source.id},
filter:{
	in(azure.subscription, array($Subscription)) AND 
	in(azure.location, array($Location)) AND 
	in(azure.resource.group, array($ResourceGroup))}
| fieldsAdd inFlowsLast = arrayLast(inFlows)
| fieldsAdd outFlowsLast = arrayLast(outFlows)
| sort inFlowsLast + outFlowsLast desc
| limit toLong($Limit)""",
    },
    {
        "nl": "Show cpu utilization rate for 10 instances with highest usage over time",
        "intent": "host_cpu",
        "expected_contains": ['timeseries', 'filter', 'by'],
        "dql": """timeseries max = max(cloud.azure.microsoft_compute.virtualmachines.PercentageCPU), 
  filter:{
	in(azure.subscription, array($Subscription)) AND 
	in(azure.location, array($Location)) AND 
	in(azure.resource.group, array($ResourceGroup))},
  by:{azure.resource.name, azure.subscription, azure.location, azure.resource.group, dt.smartscape_source.id}
| fieldsadd lastMaxCPU=toLong(arrayLast(max)) 
| fields azure.resource.name, lastMaxCPU
| sort lastMaxCPU desc
| limit toLong($Limit)""",
    },
    {
        "nl": "Show total network in over time",
        "intent": "host_network",
        "expected_contains": ['timeseries', 'sum(', 'filter'],
        "dql": """timeseries NetworkInput = sum(cloud.azure.microsoft_compute.virtualmachines.NetworkInTotal), 
filter:{
	in(azure.subscription, array($Subscription)) AND 
	in(azure.location, array($Location)) AND 
	in(azure.resource.group, array($ResourceGroup))}
| fieldsAdd groupSum = arraySum(NetworkInput)
| summarize TotalNetworkInput = sum(groupSum)""",
    },
    {
        "nl": "Show total network out over time",
        "intent": "host_network",
        "expected_contains": ['timeseries', 'sum(', 'filter'],
        "dql": """timeseries NetworkOutput = sum(cloud.azure.microsoft_compute.virtualmachines.NetworkOutTotal),
filter:{
	in(azure.subscription, array($Subscription)) AND 
	in(azure.location, array($Location)) AND 
	in(azure.resource.group, array($ResourceGroup))}
| fieldsAdd groupSum = arraySum(NetworkOutput)
| summarize TotalNetworkOutput = sum(groupSum)""",
    },

    # === EVENTS ===
    {
        "nl": "Count of median chat response generation walltime: slowest 3 tenants",
        "intent": "events",
        "expected_contains": ['filter', 'by'],
        "dql": """fetch bizevents 
| filter event.type == "GenAI Skill Invocation"
| filter contains(skill, "chat")
| filter status == "SUCCESSFUL"
| fieldsAdd execution_duration_s = execution_duration_ms / 1000
| summarize median_s = median(execution_duration_s), by:{tenant_id}
| sort median_s desc
| limit 3""",
    },
    {
        "nl": "Count of mean chat response generation walltime: fastest 3 tenants",
        "intent": "events",
        "expected_contains": ['filter', 'by'],
        "dql": """fetch bizevents 
| filter event.type == "GenAI Skill Invocation"
| filter contains(skill, "chat")
| filter status == "SUCCESSFUL"
| fieldsAdd execution_duration_s = execution_duration_ms / 1000
| summarize median_s = median(execution_duration_s), by:{tenant_id}
| sort median_s asc
| limit 3""",
    },
    {
        "nl": "Show feedback",
        "intent": "events",
        "expected_contains": ['filter'],
        "dql": """fetch bizevents
| filter event.type == "Davis CoPilot Feedback"
//| filter event.category == "Notebooks NL to DQL feedback"
| fieldsAdd skill = event.category
| fieldsAdd skill = replaceString(event.category, "Notebooks NL to DQL feedback", "nl2dql")
| fieldsAdd skill = replaceString(skill, "Davis CoPilot feedback", "recommender")
| filter in(skill, array($skill)) 
| fields timestamp, skill, type=feedback.type, category=feedback.category, text=feedback.text, user_query=arrayRemoveNulls(array(user_query,user_prompt)), response=arrayRemoveNulls(array(generated_dql,query_explanation,copilot_response))
| sort timestamp""",
    },
    {
        "nl": "Count of positive/negative nl2dql feedback",
        "intent": "events",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """fetch bizevents
| filter event.type == "Davis CoPilot Feedback"
| filter event.category == "Notebooks NL to DQL feedback"
| summarize count(), by:{feedback.type}""",
    },
    {
        "nl": "Count of nl2dql feedback categories",
        "intent": "events",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """fetch bizevents
| filter event.type == "Davis CoPilot Feedback"
| filter event.category == "Notebooks NL to DQL feedback"
| filter feedback.type == "negative"
| summarize count(), by:{feedback.category}""",
    },
    {
        "nl": "Count of positive/negative recommender feedback",
        "intent": "events",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """fetch bizevents
| filter event.type == "Davis CoPilot Feedback"
| filter event.category == "Davis CoPilot feedback"
| summarize count(), by:{feedback.type}""",
    },
    {
        "nl": "Count of recommender feedback categories",
        "intent": "events",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """fetch bizevents
| filter event.type == "Davis CoPilot Feedback"
| filter event.category == "Davis CoPilot feedback"
| filter feedback.type == "negative"
| summarize count(), by:{feedback.category}""",
    },
    {
        "nl": "Count of total alerts count:",
        "intent": "events",
        "expected_contains": ['fetch events', 'count()', 'filter'],
        "dql": """fetch events, from: bin(now(),1h)-duration(toLong($Since_Days), "d"), to: now()
| filter event.owner == "team-colipri" and event.name=="lima-usage-anomaly-detection"
| summarize alerts=count()""",
    },
    {
        "nl": "Show alert details",
        "intent": "events",
        "expected_contains": ['fetch events', 'filter'],
        "dql": """fetch events, from: bin(now(),1h)-duration(toLong($Since_Days), "d"), to: now()
| filter event.owner == "team-colipri" and event.name=="lima-usage-anomaly-detection"
| fieldsKeep timestamp, event.description, event.details, event.scenario""",
    },
    {
        "nl": "Count of last week",
        "intent": "query",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """fetch user.events
| filter matchesValue(page.url.full, "*settings/openpipeline*") or matchesValue(page.title, "*OpenPipeline*")
| parse `view.url.domain`, """ALNUM "--" ALNUM:tenant LD"""
| summarize by:{tenant}, count()
| summarize count()""",
    },
    {
        "nl": "Show test runs / sdlc events",
        "intent": "data_record",
        "expected_contains": [],
        "dql": """data record(
test1 =1,
test2 =2,
test3 =4)""",
    },
    {
        "nl": "Count of how often is the srg triggered - total",
        "intent": "events",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """fetch bizevents
| filter guardian.name == "Juno App Production Go"
| filter event.type == "guardian.validation.finished"
| summarize total = count(), by:{event.type}""",
    },
    {
        "nl": "Count of srg calculation - validation status",
        "intent": "events",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """fetch bizevents
| filter guardian.name == "Juno App Production Go"
| filter event.type == "guardian.validation.finished"
| summarize result = count(), by:{validation.status}""",
    },
    {
        "nl": "Count of srg calculation - aggregated objective results",
        "intent": "events",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """fetch bizevents
| filter guardian.name == "Juno App Production Go"
| filter event.type == "guardian.validation.finished"
| parse validation.summary, "JSON:json"
| fieldsFlatten json
| fieldsAdd temp1 = concat("Pass: ", " ", json.pass)
| fieldsAdd temp2 = concat("Fail: ", " ", json.fail)
| fieldsAdd status = concat(temp1, " ", temp2)
| fieldsRemove temp1, temp2
| summarize results = count(), by:{status}""",
    },
    {
        "nl": "Count of different controls - trigger-type",
        "intent": "events",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """fetch bizevents
| filter guardian.name == "Juno App Production Go"
| filter event.type == "guardian.validation.finished"
| fieldsAdd trigger_type = if(isNull(validation.workflow.trigger_type), "Null", else: validation.workflow.trigger_type)
| summarize result = count(), by:{trigger_type}""",
    },
    {
        "nl": "Count of page views per smartscape",
        "intent": "query",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """fetch user.events
| filter characteristics.classifier == "navigation"
| filter startsWith(page.name, "/ui/smartscape/")
| fieldsAdd smartscape_view = replaceString(page.name, "/ui/smartscape/", "")
| fieldsAdd smartscape_view = if(startsWith(smartscape_view, "problem/subscape/"), "problem/subscape", else:smartscape_view)
| summarize count = count(), by:{smartscape_view}
| sort count desc""",
    },
    {
        "nl": "Count of interactions breakdown",
        "intent": "query",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """fetch user.events, bucket:{"default_user_events"}
| filter in(ui_element.features, "Graph tooltip")
| filter interaction.name == "click"
| summarize count(), by:{ui_element.custom_name}
| sort `count()` desc""",
    },
    {
        "nl": "Count of intents with unsupported entity types",
        "intent": "query",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """fetch user.events, bucket:{"default_user_events"}
| filter ui_element.custom_name == "Entity not found message"
| fieldsKeep ui_element.properties
| expand ui_element.properties
| filter startsWith(ui_element.properties, "entityId:")
| parse ui_element.properties, "'entityId:' LD:type '-'"
| summarize count(), by:{type}
| sort `count()` desc""",
    },
    {
        "nl": "Count of interactions per view",
        "intent": "query",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """fetch user.events, bucket:{"default_user_events"}
| filter interaction.name == "click"
| filter in(ui_element.features, "Graph tooltip")
| fieldsAdd view.name = replaceString(view.name, "/ui/smartscape/", "")
| fieldsAdd view.name = if(startsWith(view.name, "problem/subscape/"), "problem/subscape", else: view.name)
| summarize count(), by:{view.name}
| sort `count()` desc""",
    },
    {
        "nl": "Count of copy interaction breakdown",
        "intent": "query",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """fetch user.events
| filter ui_element.custom_name == "Copy tooltip property"
| filter in(ui_element.features, "Graph tooltip")
| fieldsKeep ui_element.properties
| expand ui_element.properties
| filter startsWith(ui_element.properties, "fieldLabel:")
| parse ui_element.properties, "'fieldLabel:' LD:label"
| summarize count = count(), by:{label}
| sort count desc""",
    },
    {
        "nl": "Count of timed out pages",
        "intent": "events",
        "expected_contains": ['count()', 'filter'],
        "dql": """fetch bizevents
  | FILTER `event.provider` == $SalesforceTenant
  | FILTER like(event.type,"salesforce.LightningUriEvent%")
  | FILTER isNotNull(`QueriedEntities`)
  | FILTER `Operation` == "Read"
  | SUMMARIZE {
      AllPages=ToDouble(Count()),
      TimedOutPages=ToDouble(CountIf(`EffectivePageTime` == 0))
  }
  | fieldsAdd percent=TimedOutPages/AllPages*100""",
    },
    {
        "nl": "Count of adoption by queried entity",
        "intent": "events",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """fetch bizevents
  | FILTER `event.provider` == $SalesforceTenant
  | FILTER like(event.type,"salesforce.ListViewEvent%") 
      OR like(event.type,"salesforce.ReportEvent%") 
      OR like(event.type,"salesforce.LightningUriEvent%") 
      OR like(event.type,"salesforce.UriEvent%")
  | FIELDS {`QueriedEntities`, alias:queriedEntities}, {event.type, alias:eventType}, `Name`
  | FIELDSADD name = if(eventType == "salesforce.ListViewEvent", `Name`, else: queriedEntities)
  | FILTER isNotNull(name)
  | SUMMARIZE quantity = toDouble(count()), by:{name}
  | SORT quantity desc
  | LIMIT 10""",
    },
    {
        "nl": "Count of adoption by event type",
        "intent": "events",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """fetch bizevents
  | FILTER `event.provider` == $SalesforceTenant
  | FILTER like(event.type,"salesforce.ListViewEvent%")
    OR like(event.type,"salesforce.ReportEvent%")
    OR like(event.type,"salesforce.LightningUriEvent%")
    OR like(event.type,"salesforce.UriEvent%")
  | SUMMARIZE quantity = toDouble(count()), by:{event.type}
  | SORT quantity desc
  | LIMIT 10""",
    },
    {
        "nl": "Count of detected anomalies",
        "intent": "events",
        "expected_contains": ['count()', 'filter'],
        "dql": """fetch bizevents
    | FILTER `event.provider` == $SalesforceTenant
    | FILTER `event.type` == "salesforce.ApiAnomalyEvent" OR `event.type` == "salesforce.ReportAnomalyEvent" OR `event.type` == "salesforce.SessionHijackingEvent"
    | summarize Count()""",
    },
    {
        "nl": "Show last event ingest",
        "intent": "events",
        "expected_contains": ['filter'],
        "dql": """fetch bizevents
| FILTER `event.provider` == $SalesforceTenant
| sort timestamp desc
| limit 1
| fields timestamp""",
    },
    {
        "nl": "Count of app rule violations",
        "intent": "events",
        "expected_contains": ['fetch events', 'count()', 'filter'],
        "dql": """fetch events
| filter event.kind == "DAVIS_EVENT"
| filter event.type == "CUSTOM_INFO"
| filter source == "app-security-policies-check"
| filter isNotNull(appId)
| filter appId == $app
| filter $assetVersion == "summary" OR appVersion == $assetVersion
| sort timestamp desc
| dedup {appId, ruleId}
| summarize count()""",
    },
    {
        "nl": "Count of affected apps",
        "intent": "events",
        "expected_contains": ['fetch events', 'count()', 'filter'],
        "dql": """fetch events
| filter event.kind == "DAVIS_EVENT"
| filter event.type == "CUSTOM_INFO"
| filter source == "app-security-policies-check"
| filter isNotNull(appId)
| filter appId == $app
| filter $assetVersion == "summary" OR appVersion == $assetVersion
| sort timestamp desc
| dedup {appId}
| summarize count()""",
    },
    {
        "nl": "Show operator invocation events",
        "intent": "events",
        "expected_contains": ['filter'],
        "dql": """fetch bizevents
| filter event.type == "GenAI Skill Invocation"
| filter skill == "operator"
| filter isNull(platform) or matchesValue(platform, $Platform)
| filter matchesValue(tenant_id, $Tenant)
| fieldsAdd user_input_redacted = lower(replacePattern(substring(user_input, to: 60), "[^0-9a-zA-Z ]", ""))
| filter isNull(status) or matchesValue(status, $Status)
| filter matchesValue(user_input_redacted, $Question)
| sort timestamp asc
| fieldsKeep timestamp, user_input, tenant_id, user_email, server_version, platform, client_id,  user_input, response,status, failure_reason, failure_message""",
    },
    {
        "nl": "Show behavioral events",
        "intent": "events",
        "expected_contains": ['fetch events', 'filter'],
        "dql": """fetch events
| filter event.type == "behavioral"
| filter bhv.platform == "3g"
| filter in(bhv.app.id, $AppId)
| fields appId=bhv.app.id, timestamp, id = event.id, name = bhv.name, app_version = bhv.app.version, tenant = bhv.tenant.uuid, user_domain = splitString(bhv.user.id, "@")[1], bhv.custom.recordCount, bhv.custom.timeframeInDays
| sort timestamp desc""",
    },
    {
        "nl": "Show user type test",
        "intent": "events",
        "expected_contains": ['fetch events', 'filter'],
        "dql": """fetch events
| filter 113000046@bancobcr.com""",
    },

    # === GRAIL ===
    {
        "nl": "Show duplicates",
        "intent": "data_record",
        "expected_contains": [],
        "dql": """data record()
| fieldsAdd duplicates=splitString(splitString($incidents, "|")[6], ",")""",
    },
    {
        "nl": "Show description",
        "intent": "data_record",
        "expected_contains": [],
        "dql": """data record()
| fieldsAdd ID=splitString($incidents, "|")[4]
| fieldsAdd description=splitString($incidents, "|")[7]
| fieldsAdd detail=splitString($incidents, "|")[5]""",
    },

    # === HOSTS ===
    {
        "nl": "Show producer record error rate over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter'],
        "dql": """timeseries {
  Avg=avg(deus.dpsIngest.kafka.producer.record.error.rate)
  }, 
filter: {
dt.host_group.id == $host_group
AND startsWith(client.id, "dps-ingest-durability-ingestor")
}""",
    },
    {
        "nl": "Show producer request latency [timer, avg, max] over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter'],
        "dql": """timeseries {
  Avg=avg(deus.dpsIngest.kafka.producer.request.latency.avg)
  }, 
filter: {
dt.host_group.id == $host_group
AND startsWith(client.id, "dps-ingest-durability-ingestor")
}""",
    },
    {
        "nl": "Show producer request throttling time over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter'],
        "dql": """timeseries {
  Avg=avg(deus.dpsIngest.kafka.producer.produce.throttle.time.avg)
  }, 
filter: {
dt.host_group.id == $host_group
AND startsWith(client.id, "dps-ingest-durability-ingestor")
}""",
    },
    {
        "nl": "Show producer in-flight requests over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter'],
        "dql": """timeseries {
  Avg=avg(deus.dpsIngest.kafka.producer.requests.in.flight)
  }, 
filter: {
dt.host_group.id == $host_group
AND startsWith(client.id, "dps-ingest-durability-ingestor")
}""",
    },
    {
        "nl": "Show bulks deduplicated over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries sum(deus.dpsIngest.nobex.ingest.bulks_deduplicated),
by: { source, retry_number, dt.host_group.id },
filter: {in(array($host_group), dt.host_group.id)}""",
    },
    {
        "nl": "Show bulk deduplication registration/query duration over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries {
  registration=avg(deus.dpsIngest.bulk.deduplication.registration.duration),
  query=avg(deus.dpsIngest.bulk.deduplication.query.duration)
},
by: { success, dt.host_group.id },
filter: {in(array($host_group), dt.host_group.id)}""",
    },
    {
        "nl": "Show bulk cache size over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'filter', 'by'],
        "dql": """timeseries max(deus.dpsIngest.bulk.deduplication.cache.size),
by: { success, dt.host_group.id },
filter: {in(array($host_group), dt.host_group.id)}""",
    },
    {
        "nl": "Show cached tenant ids over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'filter', 'by'],
        "dql": """timeseries max=max(deus.dpsIngest.tenant_registry.tenant_ids),
by: { dt.host_group.id },
filter: {in(array($host_group), dt.host_group.id)}""",
    },
    {
        "nl": "Show registry updates over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'filter', 'by'],
        "dql": """timeseries max(deus.dpsIngest.tenant_registry.updates),
by: { dt.host_group.id },
filter: {in(array($host_group), dt.host_group.id)}""",
    },
    {
        "nl": "Show registry misses over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries sum=sum(deus.dpsIngest.tenant_registry.misses),
by: { dt.host_group.id },
filter: {in(array($host_group), dt.host_group.id)}""",
    },
    {
        "nl": "Show retry header values seen over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries sum(deus.dpsIngest.nobex.ingest.retry_header.count),
by: { source, retry_number, dt.host_group.id },
filter: {in(array($host_group), dt.host_group.id)}""",
    },
    {
        "nl": "Count of distribution of various known owner tags on all hosts",
        "intent": "host_entity",
        "expected_contains": ['fetch dt.entity.host', 'count()'],
        "dql": """fetch dt.entity.host, from: -10m  
  | fields id, tags
  
 | summarize {
   total = count(),
   owner_teams = countif (iAny(matchesPhrase(tags[], "owner\\: team-") or matchesPhrase(tags[], "owner\\:team-"))),
   aws_owner = countif (iAny(matchesPhrase(tags[], "[AWS]Owner:"))),
   dt_owner_team = countif (iAny(matchesPhrase(tags[], "dt_owner_team:"))),
   dt_owner_email = countif (iAny(matchesPhrase(tags[], "dt_owner_email:"))),
   dt_owner_capability = countif (iAny(matchesPhrase(tags[], "dt_owner_capability:"))),   
   sec_owner = countif (iAny(matchesPhrase(tags[], "sec_owner_iam"))),
   created_by = countif (iAny(matchesPhrase(tags[], "ACE\\:CREATED-BY"))),
   azure_updated_by = countif (iAny(matchesPhrase(tags[], "[Azure]ACE\\:UPDATED-BY")))
 }""",
    },
    {
        "nl": "Show loopback api errors over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'by'],
        "dql": """timeseries {
  avg=avg(remote_isfm.pipeline.loopback.errors.count)
}, 
by: { dt.host_group.id, dt.system.bucket, dt.pipeline.loopback.source }""",
    },
    {
        "nl": "Show worker poll duration over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'by'],
        "dql": """timeseries {
  max=max(remote_isfm.pipeline.loopback.worker.poll_time)
},
by: { dt.host_group.id }""",
    },
    {
        "nl": "Show batch processing duration over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'by'],
        "dql": """timeseries {
  avg=avg(remote_isfm.pipeline.loopback.worker.batch_execution_time)
},
by: { loopback.type, dt.host_group.id }""",
    },
    {
        "nl": "Show batches processed over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'by'],
        "dql": """timeseries {
  sum=sum(remote_isfm.pipeline.loopback.worker.batches_processed.count)
},
by: { loopback.type, dt.host_group.id }""",
    },
    {
        "nl": "Show bytes processed over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'by'],
        "dql": """timeseries {
  avg=avg(remote_isfm.pipeline.loopback.worker.uncompressed_bytes_processed)
},
by: { loopback.type, dt.host_group.id }""",
    },
    {
        "nl": "Show queue consumed bytes over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'by'],
        "dql": """timeseries {
  bytes=max(remote_isfm.pipeline.loopback.queue.bytes_used)
},
by: { dt.host_group.id }""",
    },
    {
        "nl": "Show queue accepted over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries {
  sum=sum(remote_isfm.pipeline.loopback.queue.backpressure_counts.count)
},
filter: { 
//dt.backpressure.reason != "REJECTED" 
loopback.type == "sfm_metrics"
},
by: { loopback.type, dt.host_group.id }""",
    },
    {
        "nl": "Show queue rejections over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries {
  sum=sum(remote_isfm.pipeline.loopback.queue.backpressure_counts.count)
},
filter: { dt.backpressure.reason != "ACCEPTED" },
by: { loopback.type, dt.backpressure.reason, dt.host_group.id }""",
    },
    {
        "nl": "Show disk read over time",
        "intent": "host_disk",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries readBytes = sum(cloud.azure.microsoft_compute.virtualmachines.DiskReadBytes),
by:{azure.resource.name, azure.subscription, azure.location, azure.resource.group, dt.smartscape_source.id},
filter:{
	in(azure.subscription, array($Subscription)) AND 
	in(azure.location, array($Location)) AND 
	in(azure.resource.group, array($ResourceGroup))}
| sort arraySum(readBytes) desc
| limit toLong($Limit)""",
    },
    {
        "nl": "Show disk i/o operations/sec over time",
        "intent": "host_disk",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries {readOps = avg(cloud.azure.microsoft_compute.virtualmachines.DiskReadOperations_Sec), 
            writeOps = avg(cloud.azure.microsoft_compute.virtualmachines.DiskWriteOperations_Sec)}, 
by:{azure.resource.name, azure.subscription, azure.location, azure.resource.group, dt.smartscape_source.id},
filter:{
	in(azure.subscription, array($Subscription)) AND 
	in(azure.location, array($Location)) AND 
	in(azure.resource.group, array($ResourceGroup))}
| sort arrayAvg(readOps) + arrayAvg(writeOps) desc
| limit toLong($Limit)""",
    },
    {
        "nl": "Show disk write over time",
        "intent": "host_disk",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries writeBytes = sum(cloud.azure.microsoft_compute.virtualmachines.DiskWriteBytes),
by:{azure.resource.name, azure.subscription, azure.location, azure.resource.group, dt.smartscape_source.id},
filter:{
	in(azure.subscription, array($Subscription)) AND 
	in(azure.location, array($Location)) AND 
	in(azure.resource.group, array($ResourceGroup))}
| sort arraySum(writeBytes) desc
| limit toLong($Limit)""",
    },
    {
        "nl": "Show os disk latency over time",
        "intent": "host_disk",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries osLatency = avg(cloud.azure.microsoft_compute.virtualmachines.OSDiskLatency), 
by:{azure.resource.name, azure.subscription, azure.location, azure.resource.group, dt.smartscape_source.id},
filter:{
	in(azure.subscription, array($Subscription)) AND 
	in(azure.location, array($Location)) AND 
	in(azure.resource.group, array($ResourceGroup))}
| sort arrayAvg(osLatency) desc
| limit toLong($Limit)""",
    },
    {
        "nl": "Show disk throughput over time",
        "intent": "host_disk",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries {read = avg(cloud.azure.microsoft_compute.virtualmachinescalesets.DiskReadBytes),
          write = avg(cloud.azure.microsoft_compute.virtualmachinescalesets.DiskWriteBytes)}, 
          by:{azure.resource.name, azure.subscription, azure.location, azure.resource.group, dt.smartscape_source.id},
          filter:{
	in(azure.subscription, array($Subscription)) AND 
	in(azure.location, array($Location)) AND 
	in(azure.resource.group, array($ResourceGroup))}
| sort arrayAvg(read) + arrayAvg(write) desc
| limit toLong($Limit)""",
    },
    {
        "nl": "Show disk iops over time",
        "intent": "host_disk",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries {readOps  = avg(cloud.azure.microsoft_compute.virtualmachinescalesets.DiskReadOperations_Sec),
          writeOps = avg(cloud.azure.microsoft_compute.virtualmachinescalesets.DiskWriteOperations_Sec)}, 
          by:{azure.resource.name, azure.subscription, azure.location, azure.resource.group, dt.smartscape_source.id},
filter:{
	in(azure.subscription, array($Subscription)) AND 
	in(azure.location, array($Location)) AND 
	in(azure.resource.group, array($ResourceGroup))}
| sort arrayAvg(readOps) + arrayAvg(writeOps) desc
| limit toLong($Limit)""",
    },
    {
        "nl": "Show disk usage over time",
        "intent": "host_disk",
        "expected_contains": ['timeseries', 'filter', 'by'],
        "dql": """timeseries interval: 1h, percent = max(dt.host.disk.used.percent, filter: { in(dt.entity.host, classicEntitySelector("type(host),tag(\"Cl_ES\")")) }), by: { dt.entity.host, dt.entity.disk }
| fieldsAdd entityName(dt.entity.host), entityName(dt.entity.disk)
| filterOut dt.entity.disk.name == "/boot/efi"
| filterOut dt.entity.disk.name == "/"
| sort arrayMax(percent) desc""",
    },
    {
        "nl": "Show activegates per network zone over time",
        "intent": "host_cpu",
        "expected_contains": ['timeseries', 'by'],
        "dql": """timeseries {
   cpu_usage = count(dt.sfm.active_gate.system.cpu_usage)
 }, by: {
   dt.network_zone.id, dt.active_gate.id
 }
| fieldsAdd network_zone = if(isNull(dt.network_zone.id), "default", else: dt.network_zone.id)
| summarize by:{network_zone}, total_active_gates = countDistinctExact(dt.active_gate.id)""",
    },
    {
        "nl": "Show activegates per group over time",
        "intent": "host_cpu",
        "expected_contains": ['timeseries', 'by'],
        "dql": """timeseries {
   cpu_usage = count(dt.sfm.active_gate.system.cpu_usage)
 }, by: {
   dt.active_gate.group.name, dt.active_gate.id
 }
| fieldsAdd group = if(isNull(dt.active_gate.group.name), "default", else: dt.active_gate.group.name)
| summarize by:{group}, total_active_gates = countDistinctExact(dt.active_gate.id)""",
    },
    {
        "nl": "Show healthy hosts over time",
        "intent": "host_network",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries healthy = avg(cloud.azure.microsoft_network.applicationgateways.HealthyHostCount),
  by:{azure.resource.name, azure.subscription, azure.location, azure.resource.group, dt.smartscape_source.id},
  filter:{in(azure.subscription, array($Subscription)) AND in(azure.location, array($Location)) AND in(azure.resource.group, array($ResourceGroup))}
| sort ArrayAvg(healthy) desc
| limit toLong($Limit)""",
    },

    # === KUBERNETES ===
    {
        "nl": "Show smartscape poller execution times over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter'],
        "dql": """timeseries {
  avg_polling_time = avg(dac.gcp_smartscape_poller.full.polling_time),
  avg_schedule_to_ingest = avg(dac.gcp_smartscape_poller.full.schedule_to_ingest_time)
},
filter: { matchesValue(k8s.cluster.name, { $Cluster }) }""",
    },
    {
        "nl": "Show errors in stateapi",
        "intent": "log_search",
        "expected_contains": ['fetch logs', 'filter'],
        "dql": """fetch logs 
| filter in(k8s.cluster.name, $Cluster)
| filter matchesValue(k8s.namespace.name, "dac-monitoring-state-api")
| filter loglevel == "WARN"""",
    },
    {
        "nl": "Show tenant creation requests",
        "intent": "log_search",
        "expected_contains": ['fetch logs', 'filter'],
        "dql": """fetch logs
| filter dt.system.bucket == "custom_sen_low_logs_platform_service_usage_statistics"
| filter matchesValue(dt.kubernetes.cluster.name, $cluster)
| filter contains(content, "pms_operation")
| parse content, """LD 'JSON:' JSON:entry"""

//| filter matchesValue(entry[tenantUuid], $tenant)
| fieldsFlatten entry, prefix:"pms_operation."
| filter pms_operation.type=="CREATE"
| fields timestamp, pms_operation.tenantUuid,pms_operation.type,cluster=dt.kubernetes.cluster.name
| fieldsRename tenant = pms_operation.tenantUuid
| sort timestamp asc""",
    },
    {
        "nl": "Count of tenant creation requests",
        "intent": "log_count",
        "expected_contains": ['fetch logs', 'count()', 'filter'],
        "dql": """fetch logs
| filter dt.system.bucket == "custom_sen_low_logs_platform_service_usage_statistics"
| filter matchesValue(dt.kubernetes.cluster.name, $cluster)
| filter contains(content, "pms_operation")
| parse content, """LD 'JSON:' JSON:entry"""

//| filter matchesValue(entry[tenantUuid], $tenant)
| fieldsFlatten entry, prefix:"pms_operation."
| filter pms_operation.type=="CREATE"
| summarize count()""",
    },
    {
        "nl": "Count of successful grail tenant creations",
        "intent": "log_count",
        "expected_contains": ['fetch logs', 'count()', 'filter'],
        "dql": """fetch logs
| filter dt.system.bucket == "custom_sen_low_logs_platform_service_usage_statistics"
| filter matchesValue(dt.kubernetes.cluster.name, $cluster)
| filter contains(content, "pms_operation")
| parse content, """LD 'JSON:' JSON:entry"""

//| filter matchesValue(entry[tenantUuid], $tenant)
| fieldsFlatten entry, prefix:"pms_operation."
| filter pms_operation.type=="GRAIL_TENANT_CREATION_FINISHED"
| summarize count()""",
    },
    {
        "nl": "Show grail tenant creation finished",
        "intent": "log_search",
        "expected_contains": ['fetch logs', 'filter'],
        "dql": """fetch logs
| filter dt.system.bucket == "custom_sen_low_logs_platform_service_usage_statistics"
| filter matchesValue(dt.kubernetes.cluster.name, $cluster)
| filter contains(content, "pms_operation")
| parse content, """LD 'JSON:' JSON:entry"""

//| filter matchesValue(entry[tenantUuid], $tenant)
| fieldsFlatten entry, prefix:"pms_operation."
| filter pms_operation.type=="GRAIL_TENANT_CREATION_FINISHED"
| fields timestamp, pms_operation.tenantUuid,pms_operation.type,cluster=dt.kubernetes.cluster.name
| fieldsRename tenant = pms_operation.tenantUuid
| sort timestamp asc""",
    },
    {
        "nl": "Count of initialization finished",
        "intent": "log_count",
        "expected_contains": ['fetch logs', 'count()', 'filter'],
        "dql": """fetch logs
| filter dt.system.bucket == "custom_sen_low_logs_platform_service_usage_statistics"
| filter matchesValue(dt.kubernetes.cluster.name, $cluster)
| filter contains(content, "pms_operation")
| parse content, """LD 'JSON:' JSON:entry"""

//| filter matchesValue(entry[tenantUuid], $tenant)
| fieldsFlatten entry, prefix:"pms_operation."
| filter pms_operation.type=="INITIALIZATION_FINISHED"
| summarize count()""",
    },
    {
        "nl": "Show initialization finished over time",
        "intent": "log_count",
        "expected_contains": ['fetch logs', 'timeseries', 'count()', 'filter'],
        "dql": """fetch logs
| filter dt.system.bucket == "custom_sen_low_logs_platform_service_usage_statistics"
| filter matchesValue(dt.kubernetes.cluster.name, $cluster)
| filter contains(content, "pms_operation")
| parse content, """LD 'JSON:' JSON:entry"""
| fieldsFlatten entry, prefix:"pms_operation."
| filter pms_operation.type=="INITIALIZATION_FINISHED"
| fields timestamp, pms_operation.tenantUuid,pms_operation.type,cluster=dt.kubernetes.cluster.name
| fieldsRename tenant = pms_operation.tenantUuid
| sort timestamp asc
| makeTimeseries `Initialization finished`=count()""",
    },
    {
        "nl": "Show initialization finished",
        "intent": "log_search",
        "expected_contains": ['fetch logs', 'filter'],
        "dql": """fetch logs
| filter dt.system.bucket == "custom_sen_low_logs_platform_service_usage_statistics"
| filter matchesValue(dt.kubernetes.cluster.name, $cluster)
| filter contains(content, "pms_operation")
| parse content, """LD 'JSON:' JSON:entry"""
| fieldsFlatten entry, prefix:"pms_operation."
| filter pms_operation.type=="INITIALIZATION_FINISHED"
| fields timestamp, pms_operation.tenantUuid,pms_operation.type,cluster=dt.kubernetes.cluster.name
| fieldsRename tenant = pms_operation.tenantUuid
| sort timestamp asc""",
    },
    {
        "nl": "Count of tenant deletion requests",
        "intent": "log_count",
        "expected_contains": ['fetch logs', 'count()', 'filter'],
        "dql": """fetch logs
| filter dt.system.bucket == "custom_sen_low_logs_platform_service_usage_statistics"
| filter matchesValue(dt.kubernetes.cluster.name, $cluster)
| filter contains(content, "pms_operation")
| parse content, """LD 'JSON:' JSON:entry"""

//| filter matchesValue(entry[tenantUuid], $tenant)
| fieldsFlatten entry, prefix:"pms_operation."
| filter pms_operation.type=="DELETE"
| summarize count()""",
    },
    {
        "nl": "Show tenant deletion requests",
        "intent": "log_search",
        "expected_contains": ['fetch logs', 'filter'],
        "dql": """fetch logs
| filter dt.system.bucket == "custom_sen_low_logs_platform_service_usage_statistics"
| filter matchesValue(dt.kubernetes.cluster.name, $cluster)
| filter contains(content, "pms_operation")
| parse content, """LD 'JSON:' JSON:entry"""

//| filter matchesValue(entry[tenantUuid], $tenant)
| fieldsFlatten entry, prefix:"pms_operation."
| filter pms_operation.type=="DELETE"
| fields timestamp, pms_operation.tenantUuid,pms_operation.type,cluster=dt.kubernetes.cluster.name
| fieldsRename tenant = pms_operation.tenantUuid
| sort timestamp asc""",
    },
    {
        "nl": "Count of grail tenant creation failed",
        "intent": "log_count",
        "expected_contains": ['fetch logs', 'count()', 'filter'],
        "dql": """fetch logs
| filter dt.system.bucket == "custom_sen_low_logs_platform_service_usage_statistics"
| filter matchesValue(dt.kubernetes.cluster.name, $cluster)
| filter contains(content, "pms_operation")
| parse content, """LD 'JSON:' JSON:entry"""

//| filter matchesValue(entry[tenantUuid], $tenant)
| fieldsFlatten entry, prefix:"pms_operation."
| filter pms_operation.type=="GRAIL_TENANT_CREATION_FAILED" or pms_operation.type=="GRAIL_TENANT_TIMEOUT_FAILED"
| summarize count()""",
    },
    {
        "nl": "Show grail tenant creation failed over time",
        "intent": "log_count",
        "expected_contains": ['fetch logs', 'timeseries', 'count()', 'filter'],
        "dql": """fetch logs
| filter dt.system.bucket == "custom_sen_low_logs_platform_service_usage_statistics"
| filter matchesValue(dt.kubernetes.cluster.name, $cluster)
| filter contains(content, "pms_operation")
| parse content, """LD 'JSON:' JSON:entry"""

| fieldsFlatten entry, prefix:"pms_operation."
| filter pms_operation.type=="GRAIL_TENANT_CREATION_FAILED" or pms_operation.type=="GRAIL_TENANT_TIMEOUT_FAILED"
| fields timestamp, pms_operation.tenantUuid,pms_operation.type,cluster=dt.kubernetes.cluster.name
| fieldsRename tenant = pms_operation.tenantUuid
| sort timestamp asc
| makeTimeseries `Grail tenant creation failed`=count()""",
    },
    {
        "nl": "Show grail tenant creation failed",
        "intent": "log_search",
        "expected_contains": ['fetch logs', 'filter'],
        "dql": """fetch logs
| filter dt.system.bucket == "custom_sen_low_logs_platform_service_usage_statistics"
| filter matchesValue(dt.kubernetes.cluster.name, $cluster)
| filter contains(content, "pms_operation")
| parse content, """LD 'JSON:' JSON:entry"""

//| filter matchesValue(entry[tenantUuid], $tenant)
| fieldsFlatten entry, prefix:"pms_operation."
| filter pms_operation.type=="GRAIL_TENANT_CREATION_FAILED" or pms_operation.type=="GRAIL_TENANT_TIMEOUT_FAILED"
| fields timestamp, pms_operation.tenantUuid,pms_operation.type,cluster=dt.kubernetes.cluster.name
| fieldsRename tenant = pms_operation.tenantUuid
| sort timestamp asc""",
    },
    {
        "nl": "Count of database instances",
        "intent": "query",
        "expected_contains": ['count()', 'filter'],
        "dql": """smartscapeNodes "AWS_RDS_DBINSTANCE"
| fieldsAdd name 
| fieldsAdd aws.object
| filter in(aws.account.id, array($AccountId))
| filter in(aws.region, array($Region))
| parse aws.object, "JSON:json"
| fieldsAdd engine = json[configuration][engine]
| fields name, engine
| summarize count()""",
    },
    {
        "nl": "Count of database instances by class",
        "intent": "query",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """smartscapeNodes "AWS_RDS_DBINSTANCE"
| fieldsAdd aws.resource.name 
| fieldsAdd aws.object
| filter in(aws.account.id, array($AccountId))
| filter in(aws.region, array($Region))
| parse aws.object, "JSON:json"
| fieldsAdd class = json[configuration][dbInstanceClass]
| fields class
| summarize count = count(), by: {class}
| sort count desc
| limit toLong($Limit)""",
    },
    {
        "nl": "Count of database instances by engine",
        "intent": "query",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """smartscapeNodes "AWS_RDS_DBINSTANCE"
| fieldsAdd name 
| fieldsAdd aws.object
| filter in(aws.account.id, array($AccountId))
| filter in(aws.region, array($Region))
| parse aws.object, "JSON:json"
| fieldsAdd engine = json[configuration][engine]
| fields name, engine
| summarize  count=count(), by: {engine}
| sort count desc
| limit toLong($Limit)""",
    },
    {
        "nl": "Show retriever per tenant",
        "intent": "log_search",
        "expected_contains": ['fetch logs', 'filter'],
        "dql": """fetch logs
| filter dt.system.bucket == "custom_sen_low_logs_platform_service_shared" or dt.system.bucket == "custom_sen_low_copilot_logs" or dt.system.bucket == "custom_sen_high_copilot_logs"
| filter matchesValue(k8s.container.name, "copilot-skill-worker")
| filter contains(content, "Retrieved documents")

| fieldsKeep timestamp, content, dt.kubernetes.cluster.name, k8s.pod.name, dt.entity.host, dt.entity.process_group
| sort timestamp desc
//| parse content, "LD 'JSON: ' JSON:json_data"
| parse content, """ TIMESTAMP('yyyy-MM-dd HH:mm:ss Z', tz='UTC'):parsed_timestamp SPACE WORD:parsed_loglevel SPACE LD:parsed_logger SPACE DATA:parsed_message SPACE* "JSON:" SPACE* JSON:parsed_json DATA*:parsed_postjson"""
| fieldsFlatten parsed_json
| fieldsRename cluster = dt.kubernetes.cluster.name, tenant = parsed_json.tenant, query = parsed_json.query, response_time = parsed_json.response_time, retriever = parsed_json.source
| fieldsKeep timestamp, cluster, tenant, query, response_time, retriever
| sort timestamp desc""",
    },
    {
        "nl": "Show retrievals per cluster over time",
        "intent": "log_count",
        "expected_contains": ['fetch logs', 'timeseries', 'count()', 'filter', 'by'],
        "dql": """fetch logs
| filter dt.system.bucket == "custom_sen_low_logs_platform_service_shared" or dt.system.bucket == "custom_sen_low_copilot_logs" or dt.system.bucket == "custom_sen_high_copilot_logs"
| filter matchesValue(k8s.container.name, "copilot-skill-worker")
| filter contains(content, "Retrieved documents")

| fieldsKeep timestamp, content, dt.kubernetes.cluster.name, k8s.pod.name, dt.entity.host, dt.entity.process_group
| sort timestamp desc
//| parse content, "LD 'JSON: ' JSON:json_data"
| parse content, """ TIMESTAMP('yyyy-MM-dd HH:mm:ss Z', tz='UTC'):parsed_timestamp SPACE WORD:parsed_loglevel SPACE LD:parsed_logger SPACE DATA:parsed_message SPACE* "JSON:" SPACE* JSON:parsed_json DATA*:parsed_postjson"""
| fieldsFlatten parsed_json
| fieldsRename cluster = dt.kubernetes.cluster.name, tenant = parsed_json.tenant, query = parsed_json.query, response_time = parsed_json.response_time, retriever = parsed_json.source
| fieldsKeep timestamp, cluster, tenant, query, response_time, retriever
| sort timestamp desc
| makeTimeseries count(), by: {cluster, retriever}, interval: 2h""",
    },
    {
        "nl": "Show response time per retriever & cluster over time",
        "intent": "log_search",
        "expected_contains": ['fetch logs', 'timeseries', 'percentile', 'filter', 'by'],
        "dql": """fetch logs
| filter dt.system.bucket == "custom_sen_low_logs_platform_service_shared" or dt.system.bucket == "custom_sen_low_copilot_logs" or dt.system.bucket == "custom_sen_high_copilot_logs"
| filter matchesValue(k8s.container.name, "copilot-skill-worker")
| filter contains(content, "Retrieved documents")
| fieldsKeep timestamp, content, dt.kubernetes.cluster.name, k8s.pod.name, dt.entity.host, dt.entity.process_group
| sort timestamp desc
//| parse content, "LD 'JSON: ' JSON:json_data"
| parse content, """ TIMESTAMP('yyyy-MM-dd HH:mm:ss Z', tz='UTC'):parsed_timestamp SPACE WORD:parsed_loglevel SPACE LD:parsed_logger SPACE DATA:parsed_message SPACE* "JSON:" SPACE* JSON:parsed_json DATA*:parsed_postjson"""
| fieldsFlatten parsed_json
| fieldsRename cluster = dt.kubernetes.cluster.name, tenant = parsed_json.tenant, query = parsed_json.query, response_time = parsed_json.response_time, retriever = parsed_json.source
| fieldsKeep timestamp, cluster, tenant, query, response_time, retriever
| sort timestamp desc
| makeTimeseries {q1 = percentile(response_time, 25), q3 = percentile(response_time, 75), median = percentile(response_time, 50)} ,by: {cluster, retriever}, interval: 6h""",
    },
    {
        "nl": "Show avg response time per retriever over time",
        "intent": "log_search",
        "expected_contains": ['fetch logs', 'timeseries', 'avg(', 'filter', 'by'],
        "dql": """fetch logs
| filter dt.system.bucket == "custom_sen_low_logs_platform_service_shared" or dt.system.bucket == "custom_sen_low_copilot_logs" or dt.system.bucket == "custom_sen_high_copilot_logs"
| filter matchesValue(k8s.container.name, "copilot-skill-worker")
| filter contains(content, "Retrieved documents")

| fieldsKeep timestamp, content, dt.kubernetes.cluster.name, k8s.pod.name, dt.entity.host, dt.entity.process_group
| sort timestamp desc
//| parse content, "LD 'JSON: ' JSON:json_data"
| parse content, """ TIMESTAMP('yyyy-MM-dd HH:mm:ss Z', tz='UTC'):parsed_timestamp SPACE WORD:parsed_loglevel SPACE LD:parsed_logger SPACE DATA:parsed_message SPACE* "JSON:" SPACE* JSON:parsed_json DATA*:parsed_postjson"""
| fieldsFlatten parsed_json
| fieldsRename cluster = dt.kubernetes.cluster.name, tenant = parsed_json.tenant, query = parsed_json.query, response_time = parsed_json.response_time, retriever = parsed_json.source
| fieldsKeep timestamp, cluster, tenant, query, response_time, retriever
| sort timestamp desc
| makeTimeseries { avg_response_time = avg(response_time)} ,by: {retriever}
| fieldsAdd response_time_avg = arrayAvg(avg_response_time)""",
    },
    {
        "nl": "Show logs",
        "intent": "log_search",
        "expected_contains": ['fetch logs', 'filter'],
        "dql": """fetch logs
| fieldsAdd clusters = array($InstanceGroup)
| filter matchesValue(aws.log_group, "/aws/elasticache/*")
| fieldsAdd log_group = splitString(aws.log_group, "/")
| filter in(clusters,log_group)
| fields timestamp, content, aws.log_group, aws.log_stream
| sort timestamp desc""",
    },
    {
        "nl": "Show latest warnings and errors",
        "intent": "log_errors",
        "expected_contains": ['fetch logs', 'filter'],
        "dql": """fetch logs
| filter dt.kubernetes.cluster.name == $ClusterName
| filter k8s.container.name == "segment-indexer-manager-container"
| filter matchesValue(dt.system.bucket, "custom_sen_low_logs_grail_shared") or matchesValue(dt.system.bucket, "custom_sen_low_logs_grail_usage_statistics")
| filter matchesValue(k8s.namespace.name, "seg-index")
| parse content, "LD '[' LD:logger ']' LD"
| filter in(logger, "L2CacheImpl", "RefCountingDatabase", "Storage", "L2CachingTaskResultListener", "L2CacheVerifyingTaskResultListener", "QueryBackendL2CacheConfig")
| filter status == "WARN" OR status == "ERROR"
| sort timestamp desc
| fields timestamp, status, content""",
    },
    {
        "nl": "Show total size over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries {
  current=avg(deus.queryBackend.l2Cache.current.size),
  previous=avg(deus.queryBackend.l2Cache.previous.size)
}, by:{k8s.pod.name}, filter:entityName(dt.entity.kubernetes_cluster) == $ClusterName
| fieldsAdd total=current[] + previous[]
| fieldsRemove current, previous""",
    },
    {
        "nl": "Show hits total over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries {
  current=sum(deus.queryBackend.l2Cache.current.hit, default:0),
  previous=sum(deus.queryBackend.l2Cache.previous.hit, default:0)
}, union:true, nonempty:true, by:{k8s.pod.name}, filter:entityName(dt.entity.kubernetes_cluster) == $ClusterName
| fieldsAdd total=current[] + previous[]
| fieldsRemove current, previous""",
    },
    {
        "nl": "Show misses total over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries {
  current=sum(deus.queryBackend.l2Cache.current.miss, default:0),
  previous=sum(deus.queryBackend.l2Cache.previous.miss, default:0)
}, union: true, nonempty:true, by:{k8s.pod.name}, filter:entityName(dt.entity.kubernetes_cluster) == $ClusterName
| fieldsAdd total=current[] + previous[]
| fieldsRemove current, previous""",
    },
    {
        "nl": "Show count total over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries {
  current=avg(deus.queryBackend.l2Cache.current.entryMap.entriesCount),
  previous=avg(deus.queryBackend.l2Cache.previous.entryMap.entriesCount)
}, by:{k8s.pod.name}, filter:entityName(dt.entity.kubernetes_cluster) == $ClusterName
| fieldsAdd total=current[] + previous[]
| fieldsRemove current, previous""",
    },
    {
        "nl": "Show memory size total over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries {
  current=avg(deus.queryBackend.l2Cache.current.entryMap.size),
  previous=avg(deus.queryBackend.l2Cache.previous.entryMap.size)
}, by:{k8s.pod.name}, filter:entityName(dt.entity.kubernetes_cluster) == $ClusterName
| fieldsAdd total=current[] + previous[]
| fieldsRemove current, previous""",
    },
    {
        "nl": "Show total count over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries {
  current=avg(deus.queryBackend.l2Cache.current.dedupMap.entriesCount),
  previous=avg(deus.queryBackend.l2Cache.previous.dedupMap.entriesCount)
}, by:{k8s.pod.name}, filter: {type == "TOTAL" and entityName(dt.entity.kubernetes_cluster) == $ClusterName}
| fieldsAdd total=current[] + previous[]
| fieldsRemove current, previous""",
    },
    {
        "nl": "Show total count per type over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries {
  current=avg(deus.queryBackend.l2Cache.current.dedupMap.entriesCount),
  previous=avg(deus.queryBackend.l2Cache.previous.dedupMap.entriesCount)
},
  filter: {type != "TOTAL" and entityName(dt.entity.kubernetes_cluster) == $ClusterName}, 
  by:{type}
| fieldsAdd total=current[] + previous[]
| fieldsRemove current, previous""",
    },

    # === LOGS ===
    {
        "nl": "Count of retrieved document source type",
        "intent": "log_count",
        "expected_contains": ['fetch logs', 'count()', 'sum(', 'filter', 'by'],
        "dql": """fetch logs
| filter { matchesValue(aws.account.id, { "<account-id>", "<account-id>", "<account-id>" }) }
| filter startsWith(aws.log_group, "/aws/lambda/SignedForwarder-dtp-copilot")
| filter startsWith(content, "b'{\"retrieval")
| fieldsAdd raw_json_array = substring(content, from:22, to:-3)
| fieldsAdd valid_json_array = replaceString(raw_json_array, "\\\\", "\\")
| parse valid_json_array, "JSON_ARRAY:results"
| expand results
| fieldsKeep timestamp, results, aws.account.id, cloud.region
| fieldsAdd source_type = results[metadata][source]
| summarize type_count = count(), by: source_type
| summarize { total=sum(type_count), count_summary=collectArray(record(source_type, type_count))}
| expand count_summary
| fields source_type=count_summary[source_type], type_count=count_summary[type_count], type_ratio=100*count_summary[type_count]/total""",
    },
    {
        "nl": "Show all unfiltered attack replay logs",
        "intent": "log_search",
        "expected_contains": ['fetch logs', 'filter'],
        "dql": """fetch logs
| filter matchesValue(dt.app.id, $AppId)
| filter matchesValue(dt.app.function, "attack-replay.js")
| sort timestamp desc""",
    },
    {
        "nl": "Count of # of workflows",
        "intent": "log_count",
        "expected_contains": ['fetch logs', 'filter'],
        "dql": """fetch logs
| filter matchesValue(dt.app.id, $AppId)
| filter matchesValue(dt.app.function, "attack-replay.js")
| fields content
| parse content, "JSON:logobject"
| fields logobject = logobject
| filter isNotNull(logobject[WID])
| filter "any" == $WorkflowId OR logobject[WID] == $WorkflowId
| summarize workflowCount = countDistinct(logobject[WID])
| fields workflowCount""",
    },
    {
        "nl": "Show all unfiltered auto-triaging logs",
        "intent": "log_search",
        "expected_contains": ['fetch logs', 'filter'],
        "dql": """fetch logs
| filter matchesValue(dt.app.id, $AppId)
| sort timestamp desc""",
    },
    {
        "nl": "Show other error and warning logs",
        "intent": "log_errors",
        "expected_contains": ['fetch logs', 'filter'],
        "dql": """fetch logs
| filter matchesValue(dt.app.id, $AppId)
| filter loglevel == "WARN" OR loglevel == "ERROR"
| parse content, "JSON:logobject"
| filter isNull(logobject[WID])
| fieldsRemove logobject
| sort timestamp desc""",
    },
    {
        "nl": "Show daily unique users, 2nd gen services vs. 3rd gen services app over time",
        "intent": "log_count",
        "expected_contains": ['fetch logs', 'timeseries', 'filter', 'by'],
        "dql": """fetch logs
, from: -60d@d
, to: now()@d
  | filter dt.system.bucket == "custom_sen_low_frontend_adoptiondata_ui_logs"
      or dt.system.bucket == "custom_sen_low_frontend_clientlogger_ui_logs"
  | filter contains(content, "AdoptionData") and matchesPhrase(content,"App opened")
  
  | parse content, "DATA? ('App opened (hypothetical)'|'App opened ')? LD? JSON{STRING:environment,STRING:user,STRING:user_type,STRING:app,STRING:gen,STRING:accountId,STRING:account_id,STRING:account_name,STRING:accountName,STRING:license,BOOLEAN:dps}:data"
  
  | filter isNotNull(data)
  | fieldsRemove "data.*"
  | fieldsFlatten data
  
  | filter data.app == "dynatrace.classic.services" or data.app == "dynatrace.services"

  | makeTimeseries { users = countDistinct(data.user, rate: 1d) }, by: { data.app }, interval:1d""",
    },
    {
        "nl": "Show logs: outbound traffic by endpoint over time",
        "intent": "log_count",
        "expected_contains": ['fetch logs', 'timeseries', 'count()', 'filter', 'by'],
        "dql": """fetch logs
| filter dt.app.id == $AppId
| filter not contains(request.host, "dynatrace.com") and not contains(request.host, "dynatracelabs.com")
| makeTimeseries count(), by:{request.path}""",
    },
    {
        "nl": "Show successful http connections over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries total=sum(`log.dtp.app.functions.http-calls.2xx`),
  filter: { dt.app.id == $AppId  },
  by: { request.host }
| fieldsAdd count = arraySum(total)
| fields count, request.host
| sort count desc""",
    },
    {
        "nl": "Show http connections 4xx over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries total=sum(`log.dtp.app.functions.http-calls.4xx`),
  filter: { dt.app.id == $AppId  },
  by: { request.host }
| fieldsAdd count = arraySum(total)
| fields count, request.host
| sort count desc""",
    },
    {
        "nl": "Show http connections 5xx over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries total=sum(`log.dtp.app.functions.http-calls.5xx`),
  filter: { dt.app.id == $AppId  },
  by: { request.host }
| fieldsAdd count = arraySum(total)
| fields count, request.host
| sort count desc""",
    },
    {
        "nl": "Show total request incoming count over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries request_count = sum(remote_dsfm.active_gate.rest.request_count, 
rate: 1m,
filter: {(matchesValue(operation, "POST /logs/ingest") or matchesValue(operation, "POST /logs/ingest/aws_firehose") or  matchesValue(operation, "POST /otlp/v1/logs"))  and (if($include_env_AGs=="true", true, else: dt.active_gate.working_mode==$AGtype))}),
filter: { (if(in("*", $tenantId), true, else: in(dt.tenant.uuid, $tenantId))) },
by: {dt.active_gate.id}

| sort arrayMax(request_count) desc
| limit 5""",
    },
    {
        "nl": "Show total incoming size over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries request_size = sum(remote_dsfm.active_gate.rest.request_size, 
rate: 1m,
filter: {(matchesValue(operation, "POST /logs/ingest") or matchesValue(operation, "POST /logs/ingest/aws_firehose") or  matchesValue(operation, "POST /otlp/v1/logs")) and (if($include_env_AGs=="true", true, else: dt.active_gate.working_mode==$AGtype))}),
filter: { (if(in("*", $tenantId), true, else: in(dt.tenant.uuid, $tenantId))) },
by: {dt.active_gate.id}

| sort arrayMax(request_size) desc
| limit 5""",
    },
    {
        "nl": "Show ag avg response time over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries response_time = avg(remote_dsfm.active_gate.rest.response_time, 
filter: {(matchesValue(operation, "POST /logs/ingest") or matchesValue(operation, "POST /logs/ingest/aws_firehose") or  matchesValue(operation, "POST /otlp/v1/logs")) and (if($include_env_AGs=="true", true, else: dt.active_gate.working_mode==$AGtype))}),
filter: { (if(in("*", $tenantId), true, else: in(dt.tenant.uuid, $tenantId))) },
by: {dt.active_gate.id}

| sort arrayMax(response_time) desc
| limit 5""",
    },
    {
        "nl": "Show avg incoming request count per ag over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter'],
        "dql": """timeseries request_count = sum(remote_dsfm.active_gate.rest.request_count,
rate:1m,
    filter: 
     (matchesValue(operation, "POST /logs/ingest") or matchesValue(operation, "POST /logs/ingest/aws_firehose") or  matchesValue(operation, "POST /otlp/v1/logs")) and (if($include_env_AGs=="true", true, else: dt.active_gate.working_mode==$AGtype)) 
     AND (if(in("*", $tenantId), true, else: in(dt.tenant.uuid, $tenantId))),
      scalar: true
    ), nonempty: true""",
    },
    {
        "nl": "Show avg incomig request size - per ag over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter'],
        "dql": """timeseries request_size = sum(remote_dsfm.active_gate.rest.request_size,
rate:1m,
    filter: 
     (matchesValue(operation, "POST /logs/ingest") or matchesValue(operation, "POST /logs/ingest/aws_firehose") or  matchesValue(operation, "POST /otlp/v1/logs")) and (if($include_env_AGs=="true", true, else: dt.active_gate.working_mode==$AGtype))
      AND (if(in("*", $tenantId), true, else: in(dt.tenant.uuid, $tenantId))),
      scalar: true
    ), nonempty: true""",
    },
    {
        "nl": "Show max ack delay over time",
        "intent": "host_disk",
        "expected_contains": ['timeseries', 'filter'],
        "dql": """timeseries error_count = max(remote_isfm.active_gate.event_ingest.disk_queue_message_ack_delay,
    filter: 
      (if($include_env_AGs=="true", true, else: dt.active_gate.working_mode==$AGtype)),
      scalar: true
    ), nonempty: true""",
    },
    {
        "nl": "Show log records sent to ppx over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter'],
        "dql": """timeseries {
sent_to_PPX = sum(remote_isfm.pipeline.execution.input.count, 
rate: 1m,
filter: dt.pipeline.config_scope_id == "logs" and (if(in("*", $tenantId), true, else: in(dt.tenant.uuid, $tenantId))))}""",
    },
    {
        "nl": "Show grail backpressure count over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries count = sum(remote_isfm.pipeline.queue.backpressure.count), 
filter: {matchesValue(dt.pipeline.processing_unit, "logs")},
by:{dt.backpressure.reason}""",
    },
    {
        "nl": "Show disk queue size over time",
        "intent": "host_disk",
        "expected_contains": ['timeseries', 'filter', 'by'],
        "dql": """timeseries disk_queue_size = max(remote_isfm.active_gate.event_ingest.disk_queue_size,
filter: {(if($include_env_AGs=="true", true, else: dt.active_gate.working_mode==$AGtype))}),
by: {dt.active_gate.id}

| sort arrayMax(disk_queue_size) desc
| limit 3""",
    },
    {
        "nl": "Show max disk queue size over time",
        "intent": "host_disk",
        "expected_contains": ['timeseries', 'filter'],
        "dql": """timeseries error_count = max(remote_isfm.active_gate.event_ingest.disk_queue_size,
    filter: 
      if($include_env_AGs=="true", true, else: dt.active_gate.working_mode==$AGtype),
      scalar: true
    ), nonempty: true""",
    },
    {
        "nl": "Show head-on-queue utilization - max over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'filter', 'by'],
        "dql": """timeseries head_on_queue_utilization = max(remote_isfm.active_gate.event_ingest.head_on_queue_utilization, 
filter: { (if($include_env_AGs=="true", true, else: dt.active_gate.working_mode==$AGtype))}),
by: {dt.active_gate.id}

| sort arrayMax(head_on_queue_utilization) desc
| limit 3""",
    },
    {
        "nl": "Show log bytes sent to ppx over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter'],
        "dql": """timeseries {server_received_bytes = sum(remote_isfm.pipeline.execution.input_bytes.count, 
rate: 1m,
filter: dt.pipeline.config_scope_id == "logs" and (if(in("*", $tenantId), true, else: in(dt.tenant.uuid, $tenantId))))}""",
    },
    {
        "nl": "Show duplicated upload requests over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter'],
        "dql": """timeseries {duplicates = sum(remote_isfm.server.log_and_events_monitoring.upload_requests.duplicates.count),
filter: (if(in("*", $tenantId), true, else: in(dt.tenant.uuid, $tenantId)))
}""",
    },
    {
        "nl": "Show failed otlp ingest api requests by response code over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries request_count = sum(remote_dsfm.active_gate.rest.request_count,
  filter: { matchesValue(operation, "POST /otlp/v1/logs") and (toLong(response_code) > 299) and (if($include_env_AGs=="true", true, else: dt.active_gate.working_mode==$AGtype))}),
  filter: { (if(in("*", $tenantId), true, else: in(dt.tenant.uuid, $tenantId))) },
  by: { response_code }""",
    },
    {
        "nl": "Show failed firehose ingest api requests by response code over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries request_count = sum(remote_dsfm.active_gate.rest.request_count,
  filter: { matchesValue(operation, "POST /logs/ingest/aws_firehose") and (toLong(response_code) > 299) and (if($include_env_AGs=="true", true, else: dt.active_gate.working_mode==$AGtype))}),
  filter: { (if(in("*", $tenantId), true, else: in(dt.tenant.uuid, $tenantId))) },
  by: { response_code }""",
    },
    {
        "nl": "Show failed generic ingest api requests by response code over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries request_count = sum(remote_dsfm.active_gate.rest.request_count, 
  filter: { matchesValue(operation, "POST /logs/ingest") and (toLong(response_code) > 299) and (if($include_env_AGs=="true", true, else: dt.active_gate.working_mode==$AGtype))}),
  filter: { (if(in("*", $tenantId), true, else: in(dt.tenant.uuid, $tenantId))) },
  by: { response_code }""",
    },
    {
        "nl": "Show ack delayed count over time",
        "intent": "host_disk",
        "expected_contains": ['timeseries', 'sum(', 'filter'],
        "dql": """timeseries {disk_queue_message_ack_delayed_count = sum(remote_isfm.active_gate.event_ingest.disk_queue_message_ack_delayed_count)},
filter: {(if($include_env_AGs=="true", true, else: dt.active_gate.working_mode==$AGtype))}""",
    },
    {
        "nl": "Show ack delay time over time",
        "intent": "host_disk",
        "expected_contains": ['timeseries', 'filter'],
        "dql": """timeseries { 
  disk_queue_message_sent_interval = min(remote_isfm.active_gate.event_ingest.disk_queue_message_sent_interval), 
  disk_queue_message_ack_delay = max(remote_isfm.active_gate.event_ingest.disk_queue_message_ack_delay)
}, 
union:true,
filter: {(if($include_env_AGs=="true", true, else: dt.active_gate.working_mode==$AGtype))}""",
    },
    {
        "nl": "Show log pipeline rule execution errors over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries {
  gen2 = sum(remote_isfm.pipeline.rule.execution.errors.count, filter: { dt.pipeline.config_scope_id=="logs" and dt.pipeline.execution.rule.error_type != "flawed" and (if(in("*", $tenantId), true, else: in(dt.tenant.uuid, $tenantId)))}),
  gen3 = sum(platform.ppx_service.isfm.pipeline.rule.execution.errors, filter: { dt.pipeline.config_scope_id=="logs" and dt.pipeline.execution.rule.error_type != "flawed" and (if(in("*", $tenantId), true, else: in(dt.tenant.uuid, $tenantId)))})
}
, by: {dt.pipeline.execution.rule.error_type}
, union:true
| limit 10""",
    },
    {
        "nl": "Show lost logs count over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter'],
        "dql": """timeseries data_loss = sum(remote_isfm.server.logs.ingest.data_lost.count,
    default: 0,
    filter: 
       (if($include_env_AGs=="true", true, else: dt.active_gate.working_mode==$AGtype)) AND (if(in("*", $tenantId), true, else: in(dt.tenant.uuid, $tenantId))),
      scalar: true
    ), nonempty: true""",
    },

    # === METRICS ===
    {
        "nl": "Count of top 10 interactions with your app",
        "intent": "events",
        "expected_contains": ['fetch events', 'count()', 'filter', 'by'],
        "dql": """fetch events
  | filter dt.system.bucket == "strato_ui_events"
  | filter event.type=="behavioral" AND in (bhv.schema_version, {"0.2"})
  | filter in(`bhv.app.id`, $AppID)
  | filterOut matchesPhrase(`bhv.app.id`,".e2e") OR matchesPhrase(`bhv.app.id`,".preview") OR matchesPhrase(`bhv.app.id`,".prpreview") OR matchesPhrase(`bhv.app.id`,"dt.missing.app.id")
  | fieldsAdd bhv.platform = if(bhv.platform == "2g_angular","Classic Angular",else:(if(bhv.platform == "2g_GWT","Classic GWT",else:(if(bhv.platform == "2gw_angular","Wrapped Angular",else:(if(bhv.platform == "2gw_gwt","Wrapped GWT",else:"AppEngine")))))))
   | parse bhv.user.id, "LD'@'LD:domainId"
  | filterOut  `domainId` == "ruxitlabs.com"
  | fieldsAdd user = coalesce(bhv.user.id, dt.rum.instance.id)

  | filter isNotNull(bhv.elem.name)
  | summarize {Interactions = count()}, by: {bhv.elem.name}
  | sort Interactions, direction:"descending"
  | limit 10""",
    },
    {
        "nl": "Count of 5 most used pages",
        "intent": "events",
        "expected_contains": ['fetch events', 'filter', 'by'],
        "dql": """fetch events
  | filter dt.system.bucket == "strato_ui_events"
  | filter event.type=="behavioral" AND in (bhv.schema_version, {"0.2"})
  | filterOut matchesPhrase(`bhv.app.id`,".e2e") OR matchesPhrase(`bhv.app.id`,".preview") OR matchesPhrase(`bhv.app.id`,".prpreview") OR matchesPhrase(`bhv.app.id`,"dt.missing.app.id")
  | filter  `bhv.app.id` == $AppID
  | fieldsAdd user = coalesce(bhv.user.id, dt.rum.instance.id)
  | summarize {
        Users= countDistinct(user)
    }, by: {bhv.page.group}
  | limit 5
  | sort Users desc""",
    },
    {
        "nl": "Count of unique users per month",
        "intent": "events",
        "expected_contains": ['fetch events', 'filter', 'by'],
        "dql": """fetch events
  | filter dt.system.bucket == "strato_ui_events"
  | filter event.type=="behavioral" AND in (bhv.schema_version, {"0.2"})
  | filter in(`bhv.app.id`, {$AppID})
  | filterOut matchesPhrase(`bhv.app.id`,".e2e") OR matchesPhrase(`bhv.app.id`,".preview") OR matchesPhrase(`bhv.app.id`,".prpreview") OR matchesPhrase(`bhv.app.id`,"dt.missing.app.id")
  | parse bhv.user.id, "LD'@'LD:domainId"
  | filterOut  `domainId` == "ruxitlabs.com"
  | fieldsAdd user = coalesce(bhv.user.id, dt.rum.instance.id)
  // users visited something else then a getting started
  // users visited something else then a getting started
  | fieldsAdd monthSplit = formatTimestamp(timestamp, format:"MM") 
  | fieldsAdd yearlySplit = formatTimestamp(timestamp, format:"yyyy") 
  | summarize countDistinct(user), by:{ yearlySplit, monthSplit}
 | sort  yearlySplit, monthSplit""",
    },
    {
        "nl": "Show 👆 app events over time",
        "intent": "events",
        "expected_contains": ['fetch events', 'timeseries', 'sum(', 'filter', 'by'],
        "dql": """fetch events
| filter dt.system.bucket == "strato_ui_events"
| filterOut isNull(bhv.app.id)

| makeTimeseries {
    events=count(default:0)
  }, by:{bhv.name}

| sort arraySum(events) desc
| limit 10""",
    },
    {
        "nl": "Show mcp tool invocations per tenant over time",
        "intent": "events",
        "expected_contains": ['timeseries', 'filter', 'by'],
        "dql": """fetch bizevents 
| filter event.type == "MCP Tool Invocation"
| filter matchesValue(platform, $Platform)
| filter matchesValue(tenant, $Tenant)
| makeTimeseries {success = countIf(status == "SUCCESSFUL", default: 0)}, by: {tenant}, nonempty: true""",
    },
    {
        "nl": "Show list of lookup tables",
        "intent": "query",
        "expected_contains": [],
        "dql": """fetch dt.system.files
| fields name, size, user.email, display_name, description
| sort size desc""",
    },
    {
        "nl": "Count of number of lookup tables",
        "intent": "query",
        "expected_contains": ['count()'],
        "dql": """fetch dt.system.files
| summarize count()""",
    },
    {
        "nl": "Show alerts by type over time",
        "intent": "events",
        "expected_contains": ['fetch events', 'timeseries', 'count()', 'filter', 'by'],
        "dql": """fetch events, from: bin(now(),1h)-duration(toLong($Since_Days), "d"), to: now()
| filter event.owner == "team-colipri" and event.name=="lima-usage-anomaly-detection"
| makeTimeseries count(), by: {event.scenario}, interval: 1h""",
    },
    {
        "nl": "Count of number of user sessions that have viewed a clouds v2 page",
        "intent": "query",
        "expected_contains": ['fetch dt.entity.application', 'count()', 'filter'],
        "dql": """fetch user.events
| join [
  fetch dt.entity.application
  | filter contains(lower(entity.name), "clouds")
], on:{left[dt.rum.application.entity] == right[id]}, prefix:"clouds."
| dedup dt.rum.instance.id
| fields view.url.path
| filterOut matchesPattern(view.url.path, $V1NamesPattern:triplequote) or contains(view.url.path, "intent")
| summarize `User sessions that have viewed a Clouds V2 page`=count()""",
    },
    {
        "nl": "Count of average click events per session",
        "intent": "events",
        "expected_contains": ['fetch events', 'count()', 'avg(', 'filter', 'by'],
        "dql": """fetch events
| filter dt.system.bucket == "strato_ui_events"
| filter contains(bhv.app.name, "Clouds") and bhv.type == "user_action"
| summarize count(), by:{dt.rum.session.id}
| summarize `Average click events per session`=avg(`count()`)""",
    },
    {
        "nl": "Count of gcp cost plotted, split by capability",
        "intent": "events",
        "expected_contains": ['fetch events', 'sum(', 'filter', 'by'],
        "dql": """fetch events, from: now()-1095d
| filter dt.system.bucket == "custom_sen_critical_events_finops_final_nonprod"
AND event.type == "BillingDataAggregate"
AND event.provider == "rnd.data.preaggregation.workflow"
| filter dt_CloudProvider == "Google Cloud"

| filter in(dt_Capability,$Capability)

| filter in(SubAccountName, $GCPProject)

| filter substring(dt_UsageDay, to:7) >= $from AND
substring(dt_UsageDay, to:7) <= $to

| fieldsAdd usageDayTs = toTimestamp(concat(replaceString(dt_UsageDay, ".", "-"), "T00:00:00Z"))
| summarize {cost_per_capability = sum(EffectiveCost)},by:{dt_Capability, dt_UsageDay = bin(usageDayTs,24h)}""",
    },
    {
        "nl": "Count of gcp cost plotted, split by project",
        "intent": "events",
        "expected_contains": ['fetch events', 'sum(', 'filter', 'by'],
        "dql": """fetch events, from: now()-1095d
| filter dt.system.bucket == "custom_sen_critical_events_finops_final_nonprod"
AND event.type == "BillingDataAggregate"
AND event.provider == "rnd.data.preaggregation.workflow"
| filter dt_CloudProvider == "Google Cloud"

| filter in(dt_Capability,$Capability)

| filter in(SubAccountName, $GCPProject)

| filter substring(dt_UsageDay, to:7) >= $from AND
substring(dt_UsageDay, to:7) <= $to

| fieldsAdd usageDayTs = toTimestamp(concat(replaceString(dt_UsageDay, ".", "-"), "T00:00:00Z"))
| summarize {cost_per_capability = sum(EffectiveCost)},by:{SubAccountName, dt_UsageDay = bin(usageDayTs,24h)}""",
    },
    {
        "nl": "Count of gcp cost total plotted",
        "intent": "events",
        "expected_contains": ['fetch events', 'sum(', 'filter', 'by'],
        "dql": """fetch events, from: now()-1095d
| filter dt.system.bucket == "custom_sen_critical_events_finops_final_nonprod"
AND event.type == "BillingDataAggregate"
AND event.provider == "rnd.data.preaggregation.workflow"
| filter dt_CloudProvider == "Google Cloud"

| filter in(dt_Capability,$Capability)

| filter in(SubAccountName, $GCPProject)

| filter substring(dt_UsageDay, to:7) >= $from AND
substring(dt_UsageDay, to:7) <= $to

| fieldsAdd usageDayTs = toTimestamp(concat(replaceString(dt_UsageDay, ".", "-"), "T00:00:00Z"))
| summarize {daily_cost = sum(EffectiveCost)},by:{dt_UsageDay = bin(usageDayTs,24h)}""",
    },
    {
        "nl": "Count of gcp cost total daily",
        "intent": "events",
        "expected_contains": ['fetch events', 'sum(', 'filter', 'by'],
        "dql": """fetch events, from: now()-1095d
| filter dt.system.bucket == "custom_sen_critical_events_finops_final_nonprod"
AND event.type == "BillingDataAggregate"
AND event.provider == "rnd.data.preaggregation.workflow"
| filter dt_CloudProvider == "Google Cloud"

| filter in(dt_Capability,$Capability)

| filter in(SubAccountName, $GCPProject)

| filter substring(dt_UsageDay, to:7) >= $from AND
substring(dt_UsageDay, to:7) <= $to

| summarize {daily_cost = sum(EffectiveCost)},by:{dt_UsageDay = substring(dt_UsageDay, to:7)}
| sort dt_UsageDay""",
    },
    {
        "nl": "Count of gcp cost",
        "intent": "events",
        "expected_contains": ['fetch events', 'sum(', 'filter'],
        "dql": """fetch events, from: now()-1095d
| filter dt.system.bucket == "custom_sen_critical_events_finops_final_nonprod"
AND event.type == "BillingDataAggregate"
AND event.provider == "rnd.data.preaggregation.workflow"
| filter dt_CloudProvider == "Google Cloud"

| filter in(dt_Capability,$Capability)

| filter in(SubAccountName, $GCPProject)

| filter substring(dt_UsageDay, to:7) >= $from AND
substring(dt_UsageDay, to:7) <= $to

| summarize {cost = sum(EffectiveCost)}""",
    },
    {
        "nl": "Count of gcp cost split by account",
        "intent": "events",
        "expected_contains": ['fetch events', 'sum(', 'filter', 'by'],
        "dql": """fetch events, from: now()-1095d
| filter dt.system.bucket == "custom_sen_critical_events_finops_final_nonprod"
AND event.type == "BillingDataAggregate"
AND event.provider == "rnd.data.preaggregation.workflow"
| filter dt_CloudProvider == "Google Cloud"

| filter in(dt_Capability,$Capability)

| filter in(SubAccountName, $GCPProject)

| filter substring(dt_UsageDay, to:7) >= $from AND
substring(dt_UsageDay, to:7) <= $to

| summarize {cost = sum(EffectiveCost)},by:{SubAccountName}
| sort cost desc""",
    },
    {
        "nl": "Show daily active tenants over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'filter'],
        "dql": """fetch user.events
| filter matchesValue(page.url.full, "*settings/openpipeline*") or matchesValue(page.title, "*OpenPipeline*")
| parse `view.url.domain`, """ALNUM "--" ALNUM:tenant LD"""
| makeTimeseries `Active tenants`=countDistinct(tenant), time: start_time, interval: 24h""",
    },
    {
        "nl": "Show total volume over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'avg('],
        "dql": """timeseries { sum(remote_isfm.pipeline.execution.input_bytes.count, rate: 1d), value.A = avg(remote_isfm.pipeline.execution.input_bytes.count, rate: 1d, scalar: true) }
| limit 50""",
    },
    {
        "nl": "Show volume by config scope over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'avg(', 'by'],
        "dql": """timeseries { sum(remote_isfm.pipeline.execution.input_bytes.count, rate: 1d), value.B = avg(remote_isfm.pipeline.execution.input_bytes.count, rate: 1d, scalar: true) }, by: { dt.pipeline.config_scope_id }
| limit 50""",
    },
    {
        "nl": "Show record count over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'avg(', 'filter', 'by'],
        "dql": """timeseries { sum(remote_isfm.pipeline.execution.input.count), value.A = avg(remote_isfm.pipeline.execution.input.count, scalar: true) }, by: { dt.pipeline.config_scope_id }, filter: { matchesValue(dt.pipeline.config_scope_id, { "system.metrics", "smartscape", "user.events" }) }
| limit 50""",
    },
    {
        "nl": "Show deus.query_frontend.dql_query.source over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'by'],
        "dql": """timeseries { avg(deus.query_frontend.dql_query.source), value.A = avg(deus.query_frontend.dql_query.source, scalar: true) }, by: { tenant, source }
| limit 20""",
    },
    {
        "nl": "Show deus.query_frontend.dql_query.command over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'by'],
        "dql": """timeseries { avg(deus.query_frontend.dql_query.command), value.A = avg(deus.query_frontend.dql_query.command, scalar: true) }, by: { tenant, command }
| limit 20""",
    },
    {
        "nl": "Show deus.query_frontend.dql_query.autocomplete over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'by'],
        "dql": """timeseries { avg(deus.query_frontend.dql_query.autocomplete), value.A = avg(deus.query_frontend.dql_query.autocomplete, scalar: true) }, by: { tenant }
| limit 20""",
    },
    {
        "nl": "Show deus.query_frontend.dql_query.parsing.duration over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'by'],
        "dql": """timeseries { avg(deus.query_frontend.dql_query.parsing.duration), value.A = avg(deus.query_frontend.dql_query.parsing.duration, scalar: true) }, by: { tenant }
| limit 20""",
    },
    {
        "nl": "Show pipeline - rule - execution - drops over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'avg(', 'filter', 'by'],
        "dql": """timeseries { drop_total=sum(remote_isfm.pipeline.rule.execution.drops.count), drop_avg = avg(remote_isfm.pipeline.rule.execution.drops.count, scalar: true) }, by: { dt.pipeline.processor_id }, filter: {matchesValue(dt.pipeline.pipeline_id,$pipeline_id) and matchesValue(dt.pipeline.stage_name,$stage_name) and matchesValue(dt.pipeline.processor_id,$processor_id) and matchesValue(dt.pipeline.config_scope_id,$pipeline_type)}
| fieldsRename processor_id=dt.pipeline.processor_id
| sort drop_avg desc""",
    },
    {
        "nl": "Show pipeline - rule - execution - errors over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'avg(', 'filter', 'by'],
        "dql": """timeseries { drop_total=sum(remote_isfm.pipeline.rule.execution.errors.count), drop_avg = avg(remote_isfm.pipeline.rule.execution.errors.count, scalar: true) }, by: { dt.pipeline.execution.rule.error_type, dt.pipeline.processor_id }, filter: {matchesValue(dt.pipeline.pipeline_id,$pipeline_id) and matchesValue(dt.pipeline.stage_name,$stage_name) and matchesValue(dt.pipeline.processor_id,$processor_id) and matchesValue(dt.pipeline.config_scope_id,$pipeline_type)}
| fieldsRename error_type=dt.pipeline.execution.rule.error_type,processor_id=dt.pipeline.processor_id
| sort drop_avg desc""",
    },
    {
        "nl": "Show pipeline - rule - execution - time over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'avg(', 'filter', 'by'],
        "dql": """timeseries { time_total=sum(remote_isfm.pipeline.rule.execution.time), time_avg = avg(remote_isfm.pipeline.rule.execution.time, scalar: true) }, by: { dt.pipeline.processor_id }, filter: {matchesValue(dt.pipeline.pipeline_id,$pipeline_id) and matchesValue(dt.pipeline.stage_name,$stage_name) and matchesValue(dt.pipeline.processor_id,$processor_id) and matchesValue(dt.pipeline.config_scope_id,$pipeline_type)}
| fieldsRename processor_id=dt.pipeline.processor_id
| sort time_avg desc""",
    },
    {
        "nl": "Show ingest volume during bf/cm 2025 split by observability signal over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'by'],
        "dql": """timeseries count = sum(remote_isfm.pipeline.execution.input_bytes.count, rate: 24h), 
by: { dt.pipeline.config_scope_id }, 
interval: 24h""",
    },
    {
        "nl": "Show ingest volume during bf/cm 2025 split by pondtype over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'by'],
        "dql": """timeseries count = sum(deus.segmentIndexerManager.uncompressed_ingested_data_size), 
by: { pondtype },
interval:24h""",
    },
    {
        "nl": "Show metric volume bf/cm 2025 total over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries bytesSum = sum(deus.segmentIndexerManager.uncompressed_ingested_data_size), 
filter: { pondtype == "metric" }, by:{}
| fieldsAdd  Total = arraySum(bytesSum)
| fieldsKeep Total""",
    },

    # === OTHER ===
    {
        "nl": "Show for next grade",
        "intent": "data_record",
        "expected_contains": [],
        "dql": """data record(
RulesForNextGrade = "A1: High Coverage met for your app size (>80%)")""",
    },
    {
        "nl": "Count of total user sessions",
        "intent": "query",
        "expected_contains": ['count()'],
        "dql": """fetch user.sessions
| summarize count()""",
    },
    {
        "nl": "Count of limits actively managed by capability",
        "intent": "query",
        "expected_contains": ['count()', 'filter'],
        "dql": """load "/lookups/sre/v1/product-limit-metadata"
| fields limit_key, managed_by_capability
| filter in(limit_key, array($ProductLimit))
| summarize 
    limits_count = count(),
    managed_by_capability_count = countIf(managed_by_capability)
| fields managed_by_capability_percentage = toDouble(managed_by_capability_count) / toDouble(limits_count) * 100""",
    },
    {
        "nl": "Count of total product limits tracked",
        "intent": "query",
        "expected_contains": ['count()', 'filter'],
        "dql": """load "/lookups/sre/v1/product-limit-metadata"
| filter in(limit_key, $ProductLimit)
| summarize count()""",
    },
    {
        "nl": "Count of limits with defined ownership",
        "intent": "query",
        "expected_contains": ['count()', 'filter'],
        "dql": """load "/lookups/sre/v1/product-limit-metadata"
| fields owner_capability, limit_key, managed_by_capability
| filter in(limit_key, $ProductLimit)
| summarize 
    limits_count = count(),
    managed_by_capability_count = countIf(managed_by_capability)
| fields managed_by_capability_percentage = toDouble(managed_by_capability_count) / toDouble(limits_count) * 100""",
    },
    {
        "nl": "Show selected day: set this number with variable (days left in trial). don't forget to set the time range.",
        "intent": "data_record",
        "expected_contains": [],
        "dql": """data record()
  | fields DaysLeft = toString($DaysLeft)""",
    },
    {
        "nl": "Count of top 10 api types",
        "intent": "query",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """load "/lookups/sre/sre-observability/classic2platform/monaco-classic-api-usage"
| fieldsAdd capability = if(startsWith(capability, "email:"), "UNKNOWN", else:capability)
| filter in(capability, $Capabilities) and in(project, $Projects) and in(api, $API)
| summarize count = count(), by:{api}
| sort count desc
| limit 10""",
    },
    {
        "nl": "Count of top 10 capabilities",
        "intent": "query",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """load "/lookups/sre/sre-observability/classic2platform/monaco-classic-api-usage"
| fieldsAdd capability = if(startsWith(capability, "email:"), "UNKNOWN", else:capability)
| filter in(api, $API) and in(project, $Projects) and in(capability, $Capabilities)
| summarize count = count(), by:{capability}
| sort count desc
| limit 10""",
    },
    {
        "nl": "Count of top 10 projects",
        "intent": "query",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """load "/lookups/sre/sre-observability/classic2platform/monaco-classic-api-usage"
| fieldsAdd capability = if(startsWith(capability, "email:"), "UNKNOWN", else:capability)
| filter in(api, $API) and in(project, $Projects) and in(capability, $Capabilities)
| summarize count = count(), by:{project}
| sort count desc
| limit 10""",
    },
    {
        "nl": "Count of slo's per team",
        "intent": "data_record",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """data record(record=array($filtered_slos))
| expand record
| parse record, "JSON:record"
| fields dt_team_name = record[dt_team_name]

| summarize count = count(), by: {dt_team_name}
| sort count desc""",
    },
    {
        "nl": "Count of total slos",
        "intent": "data_record",
        "expected_contains": ['count()', 'filter'],
        "dql": """// Get details of filtered SLOs
data record(record=array($filtered_slos))
| expand record
| parse record, "JSON:record"
| fields slo_id = record[slo_id]

| summarize count = count()""",
    },
    {
        "nl": "Count of slos per tier",
        "intent": "data_record",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """data record(record=array($filtered_slos))
| expand record
| parse record, "JSON:record"
| fields tier = record[tier]

| summarize count = count(), by: {tier}
| sort count desc""",
    },
    {
        "nl": "Count of slos per capability",
        "intent": "data_record",
        "expected_contains": ['count()', 'filter', 'by'],
        "dql": """data record(record=array($filtered_slos))
| expand record
| parse record, "JSON:record"
| fields dt_capability_name = record[dt_capability_name]

| summarize count = count(), by: {dt_capability_name}
| sort count desc""",
    },
    {
        "nl": "Count of capabilities adopted slos",
        "intent": "data_record",
        "expected_contains": ['filter', 'by'],
        "dql": """data record(record=array($filtered_slos))
| expand record
| parse record, "JSON:record"
| fields dt_capability_id = record[dt_capability_id], joiner = 1
| summarize adopted = countDistinct(dt_capability_id), by:{joiner}
| join [
  load "/lookups/sre-slo/v1/teams"
  | filter capabilityName != "undefined"
  | summarize total = countDistinct(capabilityName)
  | fieldsAdd joiner=1
], on:{joiner}, fields: {total}
| fields adopted, total""",
    },
    {
        "nl": "Show team's slos list",
        "intent": "data_record",
        "expected_contains": ['filter'],
        "dql": """data record(record=array($filtered_slos))
| expand record
| parse record, "JSON:record"
| fields {
    slo_name = record[slo_name],
    tier = record[tier],
    dt_team_name = record[dt_team_name]
  }

| fields team = dt_team_name, slo_name, tier
| sort team, slo_name""",
    },
    {
        "nl": "Show classic api replacements",
        "intent": "query",
        "expected_contains": ['filter'],
        "dql": """load "/lookups/sre/sre-observability/classic2platform/replacements-for-classic-api-usage-in-monaco"
| filter $API == "ALL" or api == $API
| fields api, `3rdGenReplacement`, settingsSchema, note
| sort api""",
    },

    # === SECURITY ===
    {
        "nl": "Count of number of configured snyk users",
        "intent": "query",
        "expected_contains": [],
        "dql": """load "/lookups/security/snyk/sso_users"
| summarize countDistinct(id)""",
    },

    # === SPANS ===
    {
        "nl": "Count of #2**",
        "intent": "span_analysis",
        "expected_contains": ['fetch spans', 'count()', 'filter', 'by'],
        "dql": """fetch spans
| fieldsAdd service_tags = entityAttr(dt.entity.service, "tags")
| filter matchesValue(service_tags, "[SPINE] Account Management API")
| filter contains(http.route, "policies")
or contains(http.route, "policy-overview")
or contains(http.route, "group")
or contains(http.route, "boundaries")
or contains(http.route, "users")
or contains(http.route, "platform-token")
| filter http.response.status_code >= 200 and http.response.status_code < 300
| fieldsRename url = span.name, code = http.response.status_code
| summarize count(), by:{url, code}
| sort `count()` desc, url asc, code asc
| fields url, code, `count()`""",
    },
    {
        "nl": "Count of #4**",
        "intent": "span_analysis",
        "expected_contains": ['fetch spans', 'count()', 'filter', 'by'],
        "dql": """fetch spans
| fieldsAdd service_tags = entityAttr(dt.entity.service, "tags")
| filter matchesValue(service_tags, "[SPINE] Account Management API")
| filter contains(http.route, "policies")
or contains(http.route, "policy-overview")
or contains(http.route, "group")
or contains(http.route, "boundaries")
or contains(http.route, "users")
or contains(http.route, "platform-token")
| filter http.response.status_code >= 400 and http.response.status_code < 500
| fieldsRename url = span.name, code = http.response.status_code
| summarize count(), by:{url, code}
| sort `count()` desc, url asc, code asc
| fields url, code, `count()`""",
    },
    {
        "nl": "Show #5**",
        "intent": "span_analysis",
        "expected_contains": ['fetch spans', 'filter'],
        "dql": """fetch spans
| fieldsAdd service_tags = entityAttr(dt.entity.service, "tags")
| filter matchesValue(service_tags, "[SPINE] Account Management API")
| filter contains(http.route, "policies")
or contains(http.route, "policy-overview")
or contains(http.route, "group")
or contains(http.route, "boundaries")
or contains(http.route, "users")
or contains(http.route, "platform-token")
| filter http.response.status_code >= 500
| fieldsRename url = span.name, code = http.response.status_code, start_time = start_time
| fields url, start_time, code, trace.id""",
    },
    {
        "nl": "Show slowest endpoint",
        "intent": "service_latency",
        "expected_contains": ['fetch spans', 'filter'],
        "dql": """fetch spans
| fieldsAdd service_tags = entityAttr(dt.entity.service, "tags")
| filter matchesValue(service_tags, "[SPINE] Account Management API")
| filter contains(http.route, "policies")
or contains(http.route, "policy-overview")
or contains(http.route, "group")
or contains(http.route, "boundaries")
or contains(http.route, "users")
or contains(http.route, "platform-token")
| filterOut duration < 1s
| fields span.name, duration, trace.id
| fieldsRename url = span.name
| sort duration desc""",
    },
    {
        "nl": "Count of slowest endpoint percentile",
        "intent": "service_latency",
        "expected_contains": ['fetch spans', 'percentile', 'filter', 'by'],
        "dql": """fetch spans
| fieldsAdd service_tags = entityAttr(dt.entity.service, "tags")
| filter matchesValue(service_tags, "[SPINE] Account Management API")
| filter contains(http.route, "policies")
or contains(http.route, "policy-overview")
or contains(http.route, "group")
or contains(http.route, "boundaries")
or contains(http.route, "users")
or contains(http.route, "platform-token")
| fieldsRename url = span.name
| summarize percentile(duration, 95), by: {url}
| sort `percentile(duration, 95)` desc
| limit 10""",
    },
    {
        "nl": "Show failed requests ratio per destination server over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'sum(', 'by'],
        "dql": """timeseries {
    {
      req = sum(`com.dynatrace.extension.haproxy-prometheus.server_http_responses_total.count`),
      errReq = sum(`com.dynatrace.extension.haproxy-prometheus.server_response_errors_total.count`)
    },
    by: { server }
}
| fieldsAdd ratio = (errReq[] / req[])""",
    },
    {
        "nl": "Show api versions over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'by'],
        "dql": """/*
Warning:
 - DQL does not support total value mode, the resulting value may diverge from the result from classic metrics
*/

timeseries GET = sum(platform.settings.service.api.get_schema.count), by: { dt.api.version }
| fieldsAdd GET = arraySum(GET)
| sort GET desc
| append [timeseries LIST = sum(platform.settings.service.api.get_schemas.count), by: { dt.api.version }
         | fieldsAdd LIST = arraySum(LIST)
         | sort LIST desc]
| append [timeseries FIND = sum(platform.settings.service.api.find_schema.count), by: { dt.api.version }
         | fieldsAdd FIND = arraySum(FIND)
         | sort FIND desc]
| summarize { GET = takeAny(GET), LIST = takeAny(LIST), FIND = takeAny(FIND) }, by: { dt.api.version }
| sort GET desc, LIST desc, FIND desc""",
    },
    {
        "nl": "Show client errors over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter'],
        "dql": """timeseries { total = sum(dt.service.request.count) },
  filter: in(dt.entity.service, classicEntitySelector("type(service),tag(\"Dtp_Platform-Services_Settings-Service\")"))
| append [timeseries { errors = sum(dt.service.request.count) },
            filter: http.response.status_code >= 400 
              AND http.response.status_code <= 499 
              AND in(dt.entity.service, classicEntitySelector("type(service),tag(\"Dtp_Platform-Services_Settings-Service\")"))]
| summarize {total = takeAny(total), errors = takeAny(errors), interval = takeAny(interval), timeframe = takeAny(timeframe)}
| fieldsAdd percentage = errors[] / total[] * 100
| fieldsAdd percentage = coalesce(percentage, array(0))""",
    },
    {
        "nl": "Show server errors over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter'],
        "dql": """timeseries { total = sum(dt.service.request.count) },
  filter: in(dt.entity.service, classicEntitySelector("type(service),tag(\"Dtp_Platform-Services_Settings-Service\")"))
| append [timeseries { errors = sum(dt.service.request.count) },
            filter: http.response.status_code >= 500 
              AND http.response.status_code <= 599 
              AND in(dt.entity.service, classicEntitySelector("type(service),tag(\"Dtp_Platform-Services_Settings-Service\")"))]
| summarize {total = takeAny(total), errors = takeAny(errors), interval = takeAny(interval), timeframe = takeAny(timeframe)}
| fieldsAdd percentage = errors[] / total[] * 100
| fieldsAdd percentage = coalesce(percentage, array(0))""",
    },
    {
        "nl": "Show tenant - requests platform settings over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'by'],
        "dql": """timeseries GET = sum(platform.settings.service.api.get_settings_menu_service.count), by:{ dt.tenant.uuid }
| fieldsAdd GET = arraySum(GET)
| sort GET desc""",
    },
    {
        "nl": "Show tenant - shares over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'by'],
        "dql": """timeseries GET = sum(platform.settings.service.api.get_shares.count), by:{ dt.tenant.uuid }
| fieldsAdd GET = arraySum(GET)
| append [timeseries UPDATE = sum(platform.settings.service.api.update_shares.count), by:{ dt.tenant.uuid }
         | fieldsAdd UPDATE = arraySum(UPDATE)]
| summarize { GET = takeAny(GET), UPDATE = takeAny(UPDATE) }, by: { dt.tenant.uuid }
| sort { UPDATE desc, GET desc }""",
    },
    {
        "nl": "Show complexity",
        "intent": "events",
        "expected_contains": ['filter'],
        "dql": """fetch bizevents
| filter event.provider == "dynatrace.site.reliability.guardian"
| filter guardian.id == $Guardian
| filter event.type == "guardian.validation.objective"
| parse execution_context, "JSON:variables"
| filterOut $artifactId != trim(variables[artifactId])
| filterOut trim(variables[artifactVersion]) != $artifactVersion

| fields Complexity = variables[artifactComplexity]
| limit 1""",
    },
    {
        "nl": "Count of top 10 internal users",
        "intent": "events",
        "expected_contains": ['fetch events', 'count()', 'filter', 'by'],
        "dql": """fetch events
| filter dt.system.bucket == "strato_ui_events"
| filter event.type == "behavioral"
| filter `bhv.app.id` == $AppID
   | parse bhv.user.id, "LD'@'LD:domainId"
  | filter  `domainId` == "dynatrace.com"
| fieldsAdd user = if(isNotNull(bhv.user.id),bhv.user.id,else:dt.rum.instance.id)
| summarize count = count(), by:{user}
| sort count desc
//Filter Out Team
| limit 10""",
    },
    {
        "nl": "Count of top 10 external users",
        "intent": "events",
        "expected_contains": ['fetch events', 'count()', 'filter', 'by'],
        "dql": """fetch events
| filter dt.system.bucket == "strato_ui_events"
| filter event.type == "behavioral"
| filter `bhv.app.id` == $AppID
   | parse bhv.user.id, "LD'@'LD:domainId"
  | filterOut  `domainId` == "ruxitlabs.com"
  | filterOut  `domainId` == "dynatrace.com"
| fieldsAdd user = if(isNotNull(bhv.user.id),bhv.user.id,else:dt.rum.instance.id)
| summarize count = count(), by:{user}
| sort count desc
//Filter Out Team
| limit 10""",
    },
    {
        "nl": "Show daily unique users, last 60 days over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries avg(dql_usage_stats.unique_users.by_application), by: { application }
, interval: 24h
, from: -60d@d
, to: now()@d
, filter: { application == "dynatrace.services" }""",
    },
    {
        "nl": "Show daily unique users (7d max), last 360 days over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'filter', 'by'],
        "dql": """timeseries max(dql_usage_stats.unique_users.by_application), by: { application }
, interval: 7d
, from: -360d@d
, to: now()@d
, filter: { application == "dynatrace.services" }""",
    },
    {
        "nl": "Show queries by record type, last 60 days over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries { 
    queries=avg(dql_usage_stats.queries.by_record_type_and_app)
    }
, filter: { application == "dynatrace.services" }
, interval: 24h
, from: -60d
, to: now()
, by: { record_type }""",
    },
    {
        "nl": "Show queries per daily user, last 60 days over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
        "dql": """timeseries { 
    queries=avg(dql_usage_stats.queries.by_record_type_and_app),
    users=avg(dql_usage_stats.unique_users.by_record_type_and_app)
    }
, filter: { application == "dynatrace.services" }
, interval: 24h
, from: -60d
, to: now()
, by: { record_type }

| fieldsAdd span_queries_per_user = queries[] / users[]
| fieldsRemove queries, users""",
    },
    {
        "nl": "Show daily span ingest over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter'],
        "dql": """timeseries series=sum(deus.segmentIndexerManager.uncompressed_ingested_data_size)
, from: $dt_timeframe_from
, to: $dt_timeframe_to
, filter: { in(pondtype, "span") }
, rate:1d""",
    },
    {
        "nl": "Show daily span ingest, last 60 days over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter'],
        "dql": """timeseries series=sum(deus.segmentIndexerManager.uncompressed_ingested_data_size)
, filter: { in(pondtype, "span") }
, interval: 1d
, from: -60d
, to: now()""",
    },
    {
        "nl": "Show daily span ingest (7d average), last 360 days over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter'],
        "dql": """timeseries series=sum(deus.segmentIndexerManager.uncompressed_ingested_data_size)
, filter: { in(pondtype, "span") }
, interval: 7d
, rate: 1d
, from: -360d@d
, to: now()@d""",
    },
    {
        "nl": "Show span ingest over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter'],
        "dql": """timeseries series=sum(deus.segmentIndexerManager.uncompressed_ingested_data_size)
, filter: { in(pondtype, "span") }
, from: -24h
, to: now()
| summarize ingest=sum(arraySum(series))""",
    },
    {
        "nl": "Show span query cpu cores per daily user, last 60 days over time",
        "intent": "host_cpu",
        "expected_contains": ['timeseries', 'sum(', 'avg(', 'filter', 'by'],
        "dql": """timeseries { 
    cost_ns=sum(dql_usage_stats.cost_ns.by_record_type_and_app),
    users=avg(dql_usage_stats.unique_users.by_record_type_and_app)
    }
, filter: { application == "dynatrace.distributedtracing" }
, interval: 24h
, from: -60d@d
, to: now()@d+2h
, by: { record_type }

| fieldsAdd cpu_cores = toDuration(cost_ns[]) / 1d

| fieldsAdd cpu_cores_per_user = cpu_cores[] / users[]
| fieldsRemove cpu_cores, cost_ns, users""",
    },
    {
        "nl": "Show span query cpu cores, last 60 days over time",
        "intent": "host_cpu",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries { 
    cost_ns=sum(dql_usage_stats.cost_ns.by_record_type_and_app)
    }
, filter: { application == "dynatrace.distributedtracing" }
, interval: 24h
, from: -60d@d
, to: now()@d+2h
, by: { record_type }

| fieldsAdd cpu_cores = toDuration(cost_ns[]) / 1d

| fieldsRemove cost_ns""",
    },
    {
        "nl": "Show daily unique users "fetch spans" (7d max), last 360 days over time",
        "intent": "metrics",
        "expected_contains": ['timeseries', 'filter', 'by'],
        "dql": """timeseries max(dql_usage_stats.unique_users.by_record_type), by: { record_type }
, interval: 7d
, from: -360d@d
, to: now()@d+2h
, filter: { record_type == "spans" }""",
    },
    {
        "nl": "Show todo wip over time",
        "intent": "service_latency",
        "expected_contains": ['fetch spans', 'timeseries', 'avg(', 'percentile', 'filter'],
        "dql": """fetch spans, samplingRatio:1
| filter endpoint.name == "/platform/storage/query/v1/query:execute"
| filter `http.request.header.dt-app-context` == "dynatrace.distributedtracing"

| makeTimeseries { 
    avg=avg(duration)
    //,p50=percentile(duration, 50)
    //,p90=percentile(duration, 90)
    ,p99=percentile(duration, 99)
    //,max=max(duration)
}""",
    },
    {
        "nl": "Show top 10 number of failing searches per tenant over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries failed_requests = count(`search.service.search-source-response-time`, default: 0),
  filter: searchsource == $searchSource and (
    matchesValue(responseclass, "4xx") or matchesValue(responseclass, "5xx")
  ),
  by: { tenantid }
| fieldsAdd failed_queries_count = arraySum(failed_requests)
| sort failed_queries_count desc
| limit 10
| fieldsRemove failed_queries_count""",
    },
    {
        "nl": "Show top 10 number of total searches per tenant over time",
        "intent": "service_metrics",
        "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
        "dql": """timeseries failed_requests = count(`search.service.search-source-response-time`, default: 0),
  filter: searchsource == $searchSource,
  by: { tenantid }
| fieldsAdd failed_queries_count = arraySum(failed_requests)
| sort failed_queries_count desc
| limit 10
| fieldsRemove failed_queries_count""",
    },
    {
        "nl": "Count of top 10 most used filter queries",
        "intent": "events",
        "expected_contains": ['fetch events', 'count()', 'filter', 'by'],
        "dql": """fetch events
| filter bhv.app.id == "dynatrace.clouds"
| filter in(bhv.tenant.uuid, $tenant)
| filter isNotNull(bhv.page.hash) and contains(bhv.page.hash, "filtering")
| fields  
  timestamp,
  bhv.user.accountId,
  bhv.user.id,
  bhv.page.hash,
  query = splitString(replaceString(replacePattern(lower(bhv.page.hash), """(("\"")|("*")|("filtering="))""", ""), "+", " "), "=")[0]
| summarize count(), by: {query}
| sort `count()` desc
| limit 10""",
    },
    {
        "nl": "Count of entity details tabs by popularity - measured by tab views",
        "intent": "events",
        "expected_contains": ['fetch events', 'count()', 'filter', 'by'],
        "dql": """fetch events
| filter bhv.app.id == "dynatrace.clouds"
| filter isNotNull(bhv.page.queryParams.detailsId)
| filter if (in($dps, "true"), bhv.license.type == "paying", else: true)
| filter in(bhv.tenant.uuid, $tenant)
| filter contains(bhv.elem.id, "tab-tab")
| fields resolvedName=replaceString(bhv.elem.id, "-tab", "")
| summarize count(), by: {resolvedName}
| sort `count()` desc""",
    },
]
