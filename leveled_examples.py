"""
Leveled Golden DQL Examples
Extracted from production Dynatrace dashboards.
Organized by complexity: simple, intermediate, complex.
"""

LEVELED_EXAMPLES = {

    # ======================================================================
    # AWS
    # ======================================================================
    "aws": {
        "simple": [
            {
                "nl": "metric processor errors",
                "intent": "service_metrics",
                "expected_contains": ['timeseries', 'sum(', 'by'],
                "dql": """timeseries failure_count = sum(dt.service.request.failure_count, scalar: true), by: { dt.entity.service}
| fieldsAdd entityName(dt.entity.service)
| limit 100""",
            },
            {
                "nl": "records affected by scheduled jobs",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'by'],
                "dql": """timeseries count = sum(`objectstore.service.api.scheduled-jobs.count`), by: { jobname }""",
            },
            {
                "nl": "all topics consumer lag",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'filter'],
                "dql": """timeseries { max(kafka_consumergroup_lag), value.A = max(kafka_consumergroup_lag, scalar: true) }, filter: { matchesValue(consumergroup, "lima-usage-upload-RawUsageFileCscConsumer") }""",
            },
            {
                "nl": "rabbitmq queue messages",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'filter', 'by'],
                "dql": """timeseries max(rabbitmq_queue_messages), 
by: { queue }, 
filter: { matchesValue(queue, "dac-aws-metrics") OR matchesValue(queue, "dac-aws-metrics-batches") }""",
            },
            {
                "nl": "rabbitmq queue messages published total",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'filter', 'by'],
                "dql": """timeseries max(rabbitmq_queue_messages_published_total), 
by: { queue }, 
filter: { matchesValue(queue, "dac-aws-metrics") OR matchesValue(queue, "dac-aws-metrics-batches") }""",
            },
        ],
        "intermediate": [
            {
                "nl": "not stored records",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'avg(', 'by'],
                "dql": """timeseries sum(dt.sfm.openpipeline.not_stored.records), by: { configuration }
| fieldsAdd not_stored = arrayAvg(`sum(dt.sfm.openpipeline.not_stored.records)`)""",
            },
            {
                "nl": "dql daily unique users",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
                "dql": """timeseries max(dql_usage_stats.unique_users.by_record_type)
, by: { record_type }
, interval: toDuration(toLong($daysOfAggregatedMax)*1000*1000*1000*60*60*24)


// exclude dt.system as it's such an outlier
, filter: record_type != "dt.system" 

| sort arrayAvg(`max(dql_usage_stats.unique_users.by_record_type)`) desc""",
            },
            {
                "nl": "avg cache read tokens",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'avg(', 'filter'],
                "dql": """// Retrieve the amount of token used for Cache Reading
timeseries t = avg(gen_ai.prompt.caching), filter: (gen_ai.system == "amazon" or gen_ai.provider.name == "amazon") and gen_ai.cache.type == "read"
| fieldsAdd total = arraySum(t)""",
            },
            {
                "nl": "avg cache write tokens",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'avg(', 'filter'],
                "dql": """// Retrieve the amount of token used for Cache Writing
timeseries t = avg(gen_ai.prompt.caching), filter: (gen_ai.system == "amazon" or gen_ai.provider.name == "amazon") and gen_ai.cache.type == "write"
| fieldsAdd total = arraySum(t)""",
            },
            {
                "nl": "api gateway 5xx errors",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'by'],
                "dql": """timeseries `5xx_error_sum` = sum(cloud.aws.api_gateway.5xx_error_sum), by: { dt.entity.custom_device }
| fieldsAdd entityName(dt.entity.custom_device)
| sort arraySum(`5xx_error_sum`) desc
| limit 20""",
            },
        ],
        "complex": [
            {
                "nl": "cache hit ratio",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'avg(', 'filter', 'join', 'by'],
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
                "nl": "🏢 tenants per version",
                "intent": "events",
                "expected_contains": ['fetch events', 'timeseries', 'filter', 'by'],
                "dql": """fetch events,  samplingRatio: 8
| filter dt.system.bucket == "strato_ui_events"
| filter in (bhv.app.id, "dynatrace.dashboards")
| fieldsAdd incompatible="✅"
| makeTimeseries tenants = countDistinct(bhv.tenant.uuid, default:0),
    by:{version=bhv.app.version,incompatible}, bins:60
 
| append [
  fetch events
  | filter dt.system.bucket == "default_davis_custom_events"
  | filter matchesPhrase(event.name, "[Dtp][Platform-Services][Channels]")
  | filter `App-Id` == "dynatrace.dashboards"
  | filter Compatibility == "INCOMPATIBLE"
  | fieldsAdd incompatible="🚫 incompatible"
  | fieldsRename Version, version
  | makeTimeseries { incompatibleEnvironments=countDistinct(Environment)},
      by: {version, incompatible}, bins:60
]""",
            },
            {
                "nl": "number of errors per workflow",
                "intent": "aws_query",
                "expected_contains": ['count()', 'filter', 'summarize', 'join', 'by'],
                "dql": """// Number of errors per workflow
fetch dt.system.events
  | filter event.kind == "BILLING_USAGE_EVENT" and event.type == "Automation Workflow"
  | dedup workflow.id
  | filter in(workflow.actor, array("65aa761a-469c-43e6-afc3-5f2a72228f6b", "c30172b2-8a04-480a-8547-a2a556af803d", "b5ffa786-43e8-419f-b735-ccf2f5f8e1cc", "380ec254-d10c-4f82-b0f4-f346b3b9397e", "aa6800bd-66fe-4a41-922d-01c3a0e91710", "1aff8bf1-fd69-4647-ac64-0dc319111b25", "68b329f7-e950-43c3-b9bf-9a0ddc5c0d3b", "30472394-f7d1-45a6-8a20-16f0d0e40701", "bd245279-31f5-4d06-b631-3b51a33b2d22", "2195bfe4-8f41-420d-b597-f083e28ec520", "c5e7acb7-f51a-485d-8b60-c00f2f9c4d18", "0f9ecd77-c82c-44e0-83d3-60af7970d5a5", "2d3a7dd3-d0c9-4ea2-859c-55489fc9cd8c", "01ab23b1-edee-4ecf-9d47-a2d773a903e6", "57f7c7c1-bad5-48aa-a332-12077223e2ee", "f027f9e7-fbc7-4608-b2a2-2fa9da3d6505", "82c7e96e-32c6-461a-a0dd-7411b4c9e850", "046554fc-f7b8-41e9-9deb-38022a62e415"))

| join [fetch dt.system.events
    | filter event.kind == "WORKFLOW_EVENT" and event.provider == "AUTOMATION_ENGINE" and event.type == $EventType],
    on: {left[workflow.id] == right[dt.automation_engine.workflow.id]}

| filter right.dt.automation_engine.state == "ERROR"
| filter in(right.dt.automation_engine.workflow.title, array($Workflow))
| filter isNull($ErrorMessageMatcher) 
    or contains(lower(right.dt.automation_engine.state_info), lower($ErrorMessageMatcher))

| summarize by: {right.dt.automation_engine.workflow.title}, errors = count()
| sort errors desc""",
            },
            {
                "nl": "http apis error rate",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'avg(', 'filter', 'summarize'],
                "dql": """timeseries error1=sum(cloud.aws.apigateway.4xx.By.ApiId.Stage),
           error2=sum(cloud.aws.apigateway.5xx.By.ApiId.Stage),
           count=sum(cloud.aws.apigateway.Count.By.ApiId.Stage),
           by: {aws.account.id, aws.region, dt.smartscape_source.id},
           filter:{in(aws.account.id, array($AccountId)) AND 
                   in(aws.region, array($Region)) AND
                   (in(dt.smartscape_source.id, iCollectArray(toSmartscapeId(array($ApiGatewayInstanceId)[]))) OR matchesValue($ApiGatewayInstanceId, "ALL"))},
           nonempty:true,
           union: true
| fieldsAdd errors = arraySum(error1) + arraySum(error2)
| fieldsAdd count = arraySum(count) 
| fieldsAdd errorPercentage = errors / count * 100
| summarize errorPercentage = avg(errorPercentage)""",
            },
            {
                "nl": "rest apis error rate",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'avg(', 'filter', 'summarize'],
                "dql": """timeseries error1=sum(cloud.aws.apigateway.4XXError.By.ApiName.Stage),
           error2=sum(cloud.aws.apigateway.5XXError.By.ApiName.Stage),
           count=sum(cloud.aws.apigateway.Count.By.ApiName.Stage),
           by: {aws.account.id, aws.region, dt.smartscape_source.id},
           filter:{in(aws.account.id, array($AccountId)) AND 
                   in(aws.region, array($Region)) AND
                   (in(dt.smartscape_source.id, iCollectArray(toSmartscapeId(array($ApiGatewayRestInstanceId)[]))) OR matchesValue($ApiGatewayRestInstanceId, "ALL"))},
           nonempty:true,
           union: true
| fieldsAdd errors = arraySum(error1) + arraySum(error2)
| fieldsAdd count = arraySum(count) 
| fieldsAdd errorPercentage = errors / count * 100
| summarize errorPercentage = avg(errorPercentage)""",
            },
        ],
    },

    # ======================================================================
    # AZURE
    # ======================================================================
    "azure": {
        "simple": [
            {
                "nl": "invocations per minute, azure openai",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'filter', 'summarize', 'by'],
                "dql": """timeseries invocations = sum(copilot.worker.llm_invocations), 
interval: 1m,
by: {skill}
| filter in(skill, $skill)
| summarize `invocations` = sum(invocations[]), by:{timeframe, interval, skill}""",
            },
            {
                "nl": "vm scale sets",
                "intent": "azure_vm_scale_set_entity",
                "expected_contains": ['fetch dt.entity.azure_vm_scale_set', 'count()', 'summarize'],
                "dql": """fetch dt.entity.azure_vm_scale_set 
| summarize  count()""",
            },
            {
                "nl": "azure operations bl call volume",
                "intent": "azure_metrics",
                "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
                "dql": """timeseries {
  requests = sum(dt.service.request.count)
}, union: true, by: { endpoint.name },
filter: { dt.entity.service == $AZURE_OPERATIONS }""",
            },
            {
                "nl": "availability rate by kind",
                "intent": "azure_metrics",
                "expected_contains": ['timeseries', 'summarize', 'by'],
                "dql": """timeseries av = max(cloud.azure.microsoft_cognitiveservices.accounts.AzureOpenAIAvailabilityRate),
by: {azure.resource.kind}
| summarize arrayLast(takeLast(av)), by: {azure.resource.kind}""",
            },
            {
                "nl": "average blob availability",
                "intent": "azure_metrics",
                "expected_contains": ['timeseries', 'avg('],
                "dql": """timeseries avabil = avg(cloud.azure.microsoft_storage.storageaccounts.blobservices.Availability)
| fieldsAdd Availability = arrayAvg(avabil)""",
            },
        ],
        "intermediate": [
            {
                "nl": "avg cache read tokens",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'avg(', 'filter'],
                "dql": """// Retrieve the amount of token used for Cache Reading
timeseries t = avg(gen_ai.prompt.caching), filter: (gen_ai.system == "openai" or gen_ai.provider.name == "openai") and gen_ai.cache.type == "read"
| fieldsAdd total = arraySum(t)""",
            },
            {
                "nl": "error rate %",
                "intent": "network_metrics",
                "expected_contains": ['timeseries', 'sum(', 'avg(', 'filter'],
                "dql": """timeseries failed = sum(cloud.azure.microsoft_network.applicationgateways.FailedRequests, default:0),
          total  = sum(cloud.azure.microsoft_network.applicationgateways.ResponseStatus,   default:0),
  filter:{in(azure.subscription, array($Subscription)) AND in(azure.location, array($Location)) AND in(azure.resource.group, array($ResourceGroup))}
| fieldsAdd rate = 100.0 * (failed[] / total[])
| fieldsAdd avg_rate_pct = arrayAvg(rate)""",
            },
            {
                "nl": "gc suspension time",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
                "dql": """timeseries { max(dt.runtime.jvm.gc.suspension_time), value.A = avg(dt.runtime.jvm.gc.suspension_time, scalar: true) }, by: { dt.entity.process_group }, filter: { matchesValue(entityAttr(dt.entity.process_group_instance, "tags"), { "LIMA Rating" }) }
| fieldsAdd dt.entity.process_group.name = entityName(dt.entity.process_group)
| sort value.A desc
| limit 100""",
            },
            {
                "nl": "avg request duration",
                "intent": "service_latency",
                "expected_contains": ['fetch spans', 'timeseries', 'avg(', 'filter'],
                "dql": """// compute the average request duration
fetch spans, samplingRatio:toLong($Data_Sampling)
| filter lower(coalesce(gen_ai.system, gen_ai.provider.name)) == "openai"
| makeTimeseries requests=avg(duration)
| fieldsAdd value=arrayAvg(requests)""",
            },
            {
                "nl": "error count by title",
                "intent": "security",
                "expected_contains": ['count()', 'filter', 'summarize', 'by'],
                "dql": """fetch security.events
| filter event.type == "DETECTION_EXECUTION_SUMMARY"
| filter execution.result.status == "FAILURE"
| filter contains(detection.title, "[QSP][IDR][Azure]")
| fields title = replaceString(detection.title, "[QSP][IDR][Azure]", "")
| summarize error_count = count(), by: title
| sort error_count desc""",
            },
        ],
        "complex": [
            {
                "nl": "avg time saved",
                "intent": "service_latency",
                "expected_contains": ['fetch spans', 'count()', 'filter', 'summarize'],
                "dql": """// Compute the average time saved serving prompts from a cache
fetch spans, samplingRatio:toLong($Data_Sampling)
| filter coalesce(gen_ai.system, gen_ai.provider.name) == "openai" and gen_ai.prompt_caching == "read"
| summarize read=count(), read_duration = takeMax(duration)
| append [
  fetch spans, samplingRatio: toLong($Data_Sampling)
  | filter coalesce(gen_ai.system, gen_ai.provider.name) == "openai" and isTrueOrNull(gen_ai.prompt_caching != "read")
  | summarize total=count(), rnd_duration = takeMax(duration)
]
| summarize {
  read = takeMax(read_duration),
  normal = takeMax(rnd_duration)
}
| fieldsAdd time_saved = normal-read""",
            },
            {
                "nl": "cache hit ratio",
                "intent": "azure_metrics",
                "expected_contains": ['timeseries', 'avg(', 'filter', 'join', 'by'],
                "dql": """timeseries avg(dt.cloud.azure.redis.cache.hits), by: { dt.entity.azure_redis_cache }, filter: { matchesValue(dt.source_entity.type, "azure_redis_cache") AND matchesValue(entityAttr(dt.entity.azure_redis_cache, "entity.name"), { $Instance }) }
| fieldsAdd dt.entity.azure_redis_cache.name = entityName(dt.entity.azure_redis_cache)
| limit 20
| join [
    timeseries avg(dt.cloud.azure.redis.cache.misses),
    by: { dt.entity.azure_redis_cache },
    filter: { matchesValue(dt.source_entity.type, "azure_redis_cache") AND matchesValue(entityAttr(dt.entity.azure_redis_cache, "entity.name"), { $Instance }) }
    | fieldsAdd dt.entity.azure_redis_cache.name = entityName(dt.entity.azure_redis_cache)
    | limit 20
  ], on: { dt.entity.azure_redis_cache }, fields: { `avg(dt.cloud.azure.redis.cache.misses)` }
| fieldsAdd C = `avg(dt.cloud.azure.redis.cache.hits)`[]/(`avg(dt.cloud.azure.redis.cache.hits)`[]+`avg(dt.cloud.azure.redis.cache.misses)`[])*100
| fieldsRemove `avg(dt.cloud.azure.redis.cache.hits)`, `avg(dt.cloud.azure.redis.cache.misses)`""",
            },
            {
                "nl": "tenant - local dev",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'summarize', 'by'],
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
                "nl": "azure untagged cost",
                "intent": "events",
                "expected_contains": ['fetch events', 'sum(', 'filter', 'summarize'],
                "dql": """fetch events, from: now()-1095d
| filter dt.system.bucket == "custom_sen_critical_events_finops_final_nonprod"
AND event.type == "BillingDataAggregate"
AND event.provider == "rnd.data.preaggregation.workflow"
| filter dt_CloudProvider == "Microsoft"

// only show cost without Capability information tagged
| filter isNull(dt_Capability)

| filter in(SubAccountName, $AzureSubscription)

| filter substring(dt_UsageDay, to:7) >= $from AND
substring(dt_UsageDay, to:7) <= $to

// do a fallback cost assignment based on the account owners capability
| lookup[
fetch events, from: now()-1d
| filter dt.system.bucket == "custom_sen_critical_events_finops_organization_data"
| filter event.provider == "Microsoft" AND event.type == "OrganizationData"
| fields SubAccountName, dt_Capability
],sourceField:SubAccountName,lookupField:SubAccountName,prefix:"lup."

| filter in(lup.dt_Capability,$Capability)

| summarize {cost = sum(EffectiveCost)}""",
            },
            {
                "nl": "azure untagged cost split by account",
                "intent": "events",
                "expected_contains": ['fetch events', 'sum(', 'filter', 'summarize', 'by'],
                "dql": """fetch events, from: now()-1095d
| filter dt.system.bucket == "custom_sen_critical_events_finops_final_nonprod"
AND event.type == "BillingDataAggregate"
AND event.provider == "rnd.data.preaggregation.workflow"
| filter dt_CloudProvider == "Microsoft"

// only show cost without Capability information tagged
| filter isNull(dt_Capability)

| filter in(SubAccountName, $AzureSubscription)

| filter substring(dt_UsageDay, to:7) >= $from AND
substring(dt_UsageDay, to:7) <= $to

// do a fallback cost assignment based on the account owners capability
| lookup[
fetch events, from: now()-1d
| filter dt.system.bucket == "custom_sen_critical_events_finops_organization_data"
| filter event.provider == "Microsoft" AND event.type == "OrganizationData"
| fields SubAccountName, dt_Capability
],sourceField:SubAccountName,lookupField:SubAccountName,prefix:"lup."

| filter in(lup.dt_Capability,$Capability)

| summarize {cost = sum(EffectiveCost)},by:{SubAccountName}
| sort cost desc""",
            },
        ],
    },

    # ======================================================================
    # EVENTS
    # ======================================================================
    "events": {
        "simple": [
            {
                "nl": "test runs / sdlc events",
                "intent": "data_record",
                "expected_contains": [],
                "dql": """data record(
test1 =1,
test2 =2,
test3 =4)""",
            },
            {
                "nl": "user type test",
                "intent": "events",
                "expected_contains": ['fetch events', 'filter'],
                "dql": """fetch events
| filter 113000046@bancobcr.com""",
            },
            {
                "nl": "playground only users on this launchpad",
                "intent": "events",
                "expected_contains": ['fetch events', 'filter', 'summarize'],
                "dql": """fetch events
| filter in(bhv.user.id,$PlaygroundOnly_InfraObs)

| summarize PlaygroundUsersWithTrialAndPay = countDistinct(bhv.user.id)""",
            },
        ],
        "intermediate": [
            {
                "nl": "top 10 root cause entities",
                "intent": "events",
                "expected_contains": ['fetch events', 'filter', 'summarize', 'by'],
                "dql": """fetch events
| filter in(event.category, array($category))
| filter in (labels.alerting_profile, array($alerting_profile))
| filter in (entity_tags, array($tags))
| filter event.kind == "DAVIS_PROBLEM" and isNotNull(root_cause_entity_name)
| expand root_cause_entity_name
| summarize problemCount=countDistinct(event.id), by: {root_cause_entity_name}
| sort problemCount desc
| fields Name=root_cause_entity_name, Count=problemCount
| limit 10""",
            },
            {
                "nl": "affected entities types",
                "intent": "events",
                "expected_contains": ['fetch events', 'filter', 'summarize', 'by'],
                "dql": """fetch events
| filter in(event.category, array($category))
| filter in (labels.alerting_profile, array($alerting_profile))
| filter in (entity_tags, array($tags))
| filter event.kind == "DAVIS_PROBLEM"
| expand entityId = affected_entity_ids
| expand entityType = affected_entity_types
| summarize problemCount=countDistinct(event.id), by: {entityType}
| sort problemCount desc
| fields entityType, Count=problemCount""",
            },
            {
                "nl": "events on root cause entities",
                "intent": "events",
                "expected_contains": ['fetch events', 'filter', 'summarize', 'by'],
                "dql": """fetch events
| filter in(event.category, array($category))
| filter in (labels.alerting_profile, array($alerting_profile))
| filter in (entity_tags, array($tags))
| filter event.kind == "DAVIS_PROBLEM" and isNotNull(root_cause_entity_name)
| expand root_cause_entity_name
| summarize problemCount=countDistinct(event.id), by: {root_cause_entity_name}
| sort problemCount desc
| fields Name=root_cause_entity_name, Count=problemCount""",
            },
        ],
        "complex": [
            {
                "nl": "job queue time",
                "intent": "events",
                "expected_contains": ['fetch events', 'filter', 'summarize', 'by'],
                "dql": """fetch events 
| filter event.kind == "SDLC_EVENT" 
| filter event.provider == "github.com"
| filter (event.category == "task" and event.status == "started") 
  or
  ( event.category == "pipeline" and event.type == "run" and event.status == "started" 
    and in(vcs.repository.name, $Repository) 
    and in(cicd.pipeline.name, $Workflow) 
    and in(cicd.pipeline.run.trigger, $Trigger)
  )
| summarize { 
  tasks = arrayRemoveNulls(collectArray(if(event.category == "task", record(task.name, start_time, task.run.attempt), else: null))),
  pipeline_run = arrayRemoveNulls(collectArray(if(event.category == "pipeline", record(pipeline.name, start_time, cicd.pipeline.run.attempt), else: null))),
  has_matching_pipeline = countif(event.category == "pipeline")
}, by: { cicd.pipeline.run.id }
| expand tasks
| expand pipeline_run
| filterOut has_matching_pipeline == 0
| filterOut tasks[task.run.attempt] != pipeline_run[cicd.pipeline.run.attempt]
| fieldsAdd queueTime = tasks[start_time] - pipeline_run[start_time], startTime = pipeline_run[start_time]
| sort queueTime""",
            },
            {
                "nl": "copy interaction breakdown",
                "intent": "rum",
                "expected_contains": ['count()', 'filter', 'summarize', 'by'],
                "dql": """fetch user.events, bucket:{"default_user_events"}
| filter interaction.name == "click"
| filter startsWith(ui_element.custom_name, "Copy tooltip ")
| fieldsKeep ui_element.properties, ui_element.custom_name
| fieldsAdd ui_element.properties = if(ui_element.custom_name == "Copy tooltip property", ui_element.properties, else: {"fieldLabel: Name"})
| expand ui_element.properties
| parse ui_element.properties, "'fieldLabel:' LD:label"
| filter isNotNull(label)
| summarize count = count(), by:{label}
| sort count desc""",
            },
            {
                "nl": "job runners | top 5",
                "intent": "events",
                "expected_contains": ['fetch events', 'count()', 'filter', 'summarize', 'by'],
                "dql": """fetch events 
| filter event.kind == "SDLC_EVENT" 
| filter event.provider == "github.com"
| filter (event.category == "task" and event.status == "finished") 
  or
  ( event.category == "pipeline" and event.type == "run" and event.status == "finished" 
    and in(vcs.repository.name, $Repository) 
    and in(cicd.pipeline.name, $Workflow) 
    and in(cicd.pipeline.run.trigger, $Trigger)
  )
| summarize { 
  tasks = arrayRemoveNulls(collectArray(if(event.category == "task", record(task.name, task.runner.name), else: null))),
  has_matching_runs = countif(event.category == "pipeline")
}, by: { cicd.pipeline.run.id }
| expand tasks
| filterOut has_matching_runs == 0 
| summarize Count=count(), by:{tasks[task.runner.name]} 
| sort Count desc""",
            },
        ],
    },

    # ======================================================================
    # GRAIL
    # ======================================================================
    "grail": {
        "simple": [
            {
                "nl": "duplicates",
                "intent": "data_record",
                "expected_contains": [],
                "dql": """data record()
| fieldsAdd duplicates=splitString(splitString($incidents, "|")[6], ",")""",
            },
        ],
        "intermediate": [
            {
                "nl": "description",
                "intent": "data_record",
                "expected_contains": [],
                "dql": """data record()
| fieldsAdd ID=splitString($incidents, "|")[4]
| fieldsAdd description=splitString($incidents, "|")[7]
| fieldsAdd detail=splitString($incidents, "|")[5]""",
            },
        ],
        "complex": [
        ],
    },

    # ======================================================================
    # HOSTS
    # ======================================================================
    "hosts": {
        "simple": [
            {
                "nl": "producer record error rate",
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
                "nl": "producer request throttling time",
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
                "nl": "producer in-flight requests",
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
        ],
        "intermediate": [
            {
                "nl": "pipeline output bytes [sum]",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
                "dql": """timeseries {
  outputBytes=sum(platform.ppx_service.isfm.pipeline.execution.output_bytes, default:0, rollup:sum)
},
filter: {dt.host_group.id  == $host_group and in(dt.tenant.uuid, $tenant) and in(table, $table)},
by:{dt.tenant.uuid, table}
| sort arrayMax(outputBytes) desc | limit toLong($limit)""",
            },
            {
                "nl": "enrichment tables requested [sum]",
                "intent": "service_metrics",
                "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
                "dql": """timeseries {
  sum=sum(platform.ppx_service.enrichment_table.get_request.count, default:0)
},
filter: { dt.host_group.id == $host_group and in(dt.tenant.uuid, $tenant) and in(table, $table) },
by:{dt.tenant.uuid, table}
| sort arrayMax(sum) desc | limit toLong($limit)""",
            },
            {
                "nl": "template requests [sum]",
                "intent": "service_metrics",
                "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
                "dql": """timeseries {
  sum=sum(platform.ppx_service.ppx.embedding_layer.davis_events.template_requests)
},
filter: { dt.host_group.id == $host_group and in(dt.tenant.uuid, $tenant) and in(table, $table) },
by:{dt.tenant.uuid, table}
| sort arrayMax(sum) desc | limit toLong($limit)""",
            },
        ],
        "complex": [
            {
                "nl": "agent modules connected",
                "intent": "network_metrics",
                "expected_contains": ['timeseries', 'avg(', 'filter', 'summarize', 'by'],
                "dql": """timeseries agent_modules.connected = max(dt.sfm.active_gate.communication.agent_modules.connected)
,by: {
   dt.network_zone.id, dt.active_gate.group.name, dt.active_gate.id, host.name
 }

| fieldsAdd instance= if($SplitByInstance == "Yes", dt.active_gate.id, else: null)
| fieldsAdd host= if($SplitByInstance == "Yes", host.name, else: null)

// replace null dimensions with 'default' 
| fieldsAdd networkzone = if(isNull(dt.network_zone.id), "default", else: dt.network_zone.id)
| fieldsAdd group = if(isNull(dt.active_gate.group.name), "default", else: dt.active_gate.group.name)
| fieldsRemove dt.network_zone.id, dt.active_gate.group.name, dt.active_gate.id, host.name

// apply filtering by variables
| filter isNull(host) or in(host, $HostName)
| filter isNull(instance) or in(instance, {$InstanceId})
| filter isNull(networkzone) or in(networkzone, $NetworkZone)
| filter isNull(group) or in(group, {$Group})

| summarize avg(agent_modules.connected[]), by: {timeframe,interval, host, instance, networkzone, group}""",
            },
            {
                "nl": "thread pool busy threads",
                "intent": "network_metrics",
                "expected_contains": ['timeseries', 'avg(', 'filter', 'summarize', 'by'],
                "dql": """timeseries {
  busythreads = max(dt.sfm.active_gate.thread_pool.busy_threads)
}, by: {
  dt.network_zone.id, dt.active_gate.group.name, dt.active_gate.id, thread_pool_name, host.name
}

| fieldsAdd instance= if($SplitByInstance == "Yes", dt.active_gate.id, else: null)
| fieldsAdd host= if($SplitByInstance == "Yes", host.name, else: null)

// replace null dimensions with 'default' 
| fieldsAdd networkzone = if(isNull(dt.network_zone.id), "default", else: dt.network_zone.id)
| fieldsAdd group = if(isNull(dt.active_gate.group.name), "default", else: dt.active_gate.group.name)
| fieldsRemove dt.network_zone.id, dt.active_gate.group.name, dt.active_gate.id, host.name

// apply filtering by variables
| filter isNull(host) or in(host, $HostName)
| filter isNull(instance) or in(instance, {$InstanceId})
| filter isNull(networkzone) or in(networkzone, $NetworkZone)
| filter isNull(group) or in(group, {$Group})

| summarize avg(busythreads[]), by: {timeframe,interval, host, instance, networkzone, group, thread_pool_name}""",
            },
            {
                "nl": "thread pool queues sizes",
                "intent": "network_metrics",
                "expected_contains": ['timeseries', 'avg(', 'filter', 'summarize', 'by'],
                "dql": """timeseries {
  queue_size = max(dt.sfm.active_gate.thread_pool.queue_size)
}, by: {
  dt.network_zone.id, dt.active_gate.group.name, dt.active_gate.id, thread_pool_name, host.name
}

| fieldsAdd instance= if($SplitByInstance == "Yes", dt.active_gate.id, else: null)
| fieldsAdd host= if($SplitByInstance == "Yes", host.name, else: null)

// replace null dimensions with 'default' 
| fieldsAdd networkzone = if(isNull(dt.network_zone.id), "default", else: dt.network_zone.id)
| fieldsAdd group = if(isNull(dt.active_gate.group.name), "default", else: dt.active_gate.group.name)
| fieldsRemove dt.network_zone.id, dt.active_gate.group.name, dt.active_gate.id, host.name

// apply filtering by variables
| filter isNull(host) or in(host, $HostName)
| filter isNull(instance) or in(instance, {$InstanceId})
| filter isNull(networkzone) or in(networkzone, $NetworkZone)
| filter isNull(group) or in(group, {$Group})

| summarize avg(queue_size[]), by: {timeframe,interval, host, instance, networkzone, group, thread_pool_name}""",
            },
        ],
    },

    # ======================================================================
    # KUBERNETES
    # ======================================================================
    "kubernetes": {
        "simple": [
            {
                "nl": "mid sized raw response",
                "intent": "host_entity",
                "expected_contains": ['fetch dt.entity.host'],
                "dql": """fetch dt.entity.host
| fieldsAdd contains, accessible_by, belongs_to, called_by, calls, clustered_by, instance_of, runs, runs_on""",
            },
            {
                "nl": "entities with problems",
                "intent": "problems",
                "expected_contains": ['summarize'],
                "dql": """fetch dt.davis.problems
| expand affected_entity_ids
| summarize totalEntities = countDistinct(affected_entity_ids)""",
            },
            {
                "nl": "memory size current",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
                "dql": """timeseries {
  current=avg(deus.queryBackend.l2Cache.current.entryMap.size)
}, by:{k8s.pod.name}, filter:entityName(dt.entity.kubernetes_cluster) == $ClusterName""",
            },
            {
                "nl": "memory size previous",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
                "dql": """timeseries {
  previous=avg(deus.queryBackend.l2Cache.previous.entryMap.size)
}, by:{k8s.pod.name}, filter:entityName(dt.entity.kubernetes_cluster) == $ClusterName""",
            },
            {
                "nl": "avg ssl rate per node",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
                "dql": """timeseries { avg(`com.dynatrace.extension.haproxy-prometheus.process_current_ssl_rate`)}, by: { nodeid }, filter:{nodetype == "PSG"}""",
            },
        ],
        "intermediate": [
            {
                "nl": "zero hit cached key",
                "intent": "log_search",
                "expected_contains": ['fetch logs', 'filter'],
                "dql": """fetch logs
| filter dt.kubernetes.cluster.name == $ClusterName
| filter k8s.container.name=="segment-indexer-manager-container"
| filter matchesValue(dt.system.bucket, "custom_sen_low_logs_grail_shared") or matchesValue(dt.system.bucket, "custom_sen_low_logs_grail_usage_statistics")
| filter matchesValue(k8s.namespace.name, "seg-index")
| filter matchesPhrase(content, "DefaultZeroHitCacheKeyMonitor", caseSensitive:true)
| fields timestamp, content""",
            },
            {
                "nl": "active davis problems",
                "intent": "kubernetes_query",
                "expected_contains": ['filter'],
                "dql": """fetch dt.davis.events
| filter contains(event.name, "ingest-endpoint") and event.status == "ACTIVE" and dt.host_group.id == $Cluster
| fieldsAdd Severity=if(isNull(dt.alert.openpipeline.severity), "Unknown", else:dt.alert.openpipeline.severity)

| fields  Cluster=dt.host_group.id, Problem=event.name,Severity""",
            },
            {
                "nl": "ponds with high blocking ratio",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
                "dql": """timeseries blockingRatio=max(deus.ingestEndpoint.ingest_session_pool_blocking_ratio),
filter: { dt.host_group.id == $Cluster and in(k8s.pod.name, $Pods) },
by:{ tenant, pondtype, pondname }
| sort arrayAvg(blockingRatio) desc
| limit 5""",
            },
            {
                "nl": "recent warning logs",
                "intent": "log_search",
                "expected_contains": ['fetch logs', 'filter'],
                "dql": """fetch logs, bucket: { "custom_sen_low_logs_grail_shared" }
| filter k8s.container.name == "ingest-endpoint-container"
| filter dt.host_group.id == $Cluster and in(k8s.pod.name, $Pods)
| filter in(loglevel, {"WARN"})
| sort timestamp desc
| fields timestamp, pod=k8s.pod.name, content
| sort timestamp desc""",
            },
            {
                "nl": "recent error logs",
                "intent": "log_errors",
                "expected_contains": ['fetch logs', 'filter'],
                "dql": """fetch logs, bucket: { "custom_sen_low_logs_grail_shared" }
| filter k8s.container.name == "ingest-endpoint-container"
| filter dt.host_group.id == $Cluster and in(k8s.pod.name, $Pods)
| filter in(loglevel, {"ERROR", "FATAL"})
| sort timestamp desc
| fields timestamp, content, pod=k8s.pod.name
| sort timestamp desc""",
            },
        ],
        "complex": [
            {
                "nl": "failed to dispatch",
                "intent": "log_count",
                "expected_contains": ['fetch logs', 'timeseries', 'count()', 'filter'],
                "dql": """fetch logs 
| filter in(k8s.cluster.name, $Cluster)
| filter matchesValue(k8s.namespace.name, "dac-scheduler-dispatcher")
| filter contains(content, "Failed to send to RabbitMQ topic")
| filter matchesPhrase(content, "dac.GCP.SMARTSCAPE")
| parse content, "LD '| JobId: ' LD:config '|' LD:type '| TenantId: ' LD:tenantId"
| fields timestamp, config, type, tenantId
| filter $ConfigurationId == "" or matchesValue(config, $ConfigurationId)
| filter $TenantId == "" or matchesValue(tenantId, $TenantId)
| makeTimeseries count()""",
            },
            {
                "nl": "too big tupleset stats",
                "intent": "log_count",
                "expected_contains": ['fetch logs', 'count()', 'avg(', 'filter', 'summarize'],
                "dql": """fetch logs
| filter dt.kubernetes.cluster.name == $ClusterName
| filter k8s.container.name == "segment-indexer-manager-container"
| filter matchesValue(dt.system.bucket, "custom_sen_low_logs_grail_shared") or matchesValue(dt.system.bucket, "custom_sen_low_logs_grail_usage_statistics")
| filter matchesValue(k8s.namespace.name, "seg-index")
| filter matchesPhrase(content, "too big tupleSet") and matchesPhrase(content, "skipped caching of", caseSensitive:true)
| fields timestamp, content
| parse content, "LD 'too big tupleSet (' INTEGER:size ')' LD"
| fields size
| summarize 
    count=count(),
    avg=avg(size),
    min=min(size),
    max=max(size),
    median=median(size),
    `percentiles(50, 60, 70, 80, 90, 95)` = percentiles(size, {50, 60, 70, 80, 90, 95}),
    stddev=stddev(size)""",
            },
            {
                "nl": "$service-api memory p$percentile",
                "intent": "memory_metrics",
                "expected_contains": ['timeseries', 'filter', 'by'],
                "dql": """timeseries 
    {
      result_max = max(dt.kubernetes.container.memory_working_set, default: 0),
      result_avg = median(dt.kubernetes.container.memory_working_set, rollup: avg, default: 0),
      result = percentile(dt.kubernetes.container.memory_working_set, toLong($percentile), rollup: max, default: 0)
    },
    nonempty: true, 
    by:{ k8s.deployment.name },
    filter: { in(k8s.cluster.name, $Cluster) and k8s.namespace.name == $Service and isNotNull(k8s.deployment.name) and k8s.container.name == concat($Service, "-api") }
  | fieldsAdd metricName = "working set memory"
| append [
  timeseries limit_mem = max(dt.kubernetes.container.limits_memory, rollup: max),
    nonempty: true, 
    by:{ k8s.deployment.name },
    filter: { in(k8s.cluster.name, $Cluster) and k8s.namespace.name == $Service and isNotNull(k8s.deployment.name) and k8s.container.name == concat($Service, "-api") }
    | fieldsAdd metricName = "limit memory"
]
| append [
  timeseries requested_mem = max(dt.kubernetes.container.requests_memory, rollup: max),
    nonempty: true, 
    by:{ k8s.deployment.name },
    filter: { in(k8s.cluster.name, $Cluster) and k8s.namespace.name == $Service and isNotNull(k8s.deployment.name) and k8s.container.name == concat($Service, "-api") }
    | fieldsAdd metricName = "request memory"
]
| fieldsAdd metricName = concat(replaceString(k8s.deployment.name, concat($Service, "-"), ""), "::", metricName)""",
            },
            {
                "nl": "$service-scheduler memory p$percentile",
                "intent": "memory_metrics",
                "expected_contains": ['timeseries', 'filter', 'by'],
                "dql": """timeseries 
    {
      result_max = max(dt.kubernetes.container.memory_working_set, default: 0),
      result_avg = median(dt.kubernetes.container.memory_working_set, rollup: avg, default: 0),
      result = percentile(dt.kubernetes.container.memory_working_set, toLong($percentile), rollup: max, default: 0)
    },
    nonempty: true, 
    by:{ k8s.deployment.name },
    filter: { in(k8s.cluster.name, $Cluster) and k8s.namespace.name == $Service and isNotNull(k8s.deployment.name) and k8s.container.name == concat($Service, "-scheduler") }
  | fieldsAdd metricName = "working set memory"
| append [
  timeseries limit_mem = max(dt.kubernetes.container.limits_memory, rollup: max),
    nonempty: true, 
    by:{ k8s.deployment.name },
    filter: { in(k8s.cluster.name, $Cluster) and k8s.namespace.name == $Service and isNotNull(k8s.deployment.name) and k8s.container.name == concat($Service, "-scheduler") }
    | fieldsAdd metricName = "limit memory"
]
| append [
  timeseries requested_mem = max(dt.kubernetes.container.requests_memory, rollup: max),
    nonempty: true, 
    by:{ k8s.deployment.name },
    filter: { in(k8s.cluster.name, $Cluster) and k8s.namespace.name == $Service and isNotNull(k8s.deployment.name) and k8s.container.name == concat($Service, "-scheduler") }
    | fieldsAdd metricName = "request memory"
]
| fieldsAdd metricName = concat(replaceString(k8s.deployment.name, concat($Service, "-"), ""), "::", metricName)""",
            },
            {
                "nl": "$service-migration memory p$mem_p",
                "intent": "memory_metrics",
                "expected_contains": ['timeseries', 'filter', 'by'],
                "dql": """timeseries 
    {
      result_max = max(dt.kubernetes.container.memory_working_set, default: 0),
      result_avg = median(dt.kubernetes.container.memory_working_set, rollup: avg, default: 0),
      result = percentile(dt.kubernetes.container.memory_working_set, toLong($percentile), rollup: max, default: 0)
    },
    nonempty: true, 
    by:{ k8s.container.name },
    filter: { in(k8s.cluster.name, $Cluster) and k8s.namespace.name == $Service and k8s.container.name == concat($Service, "-migration") }
  | fieldsAdd metricName = "working set memory"
| append [
  timeseries limit_mem = max(dt.kubernetes.container.limits_memory, rollup: max),
    nonempty: true, 
    by:{ k8s.container.name },
    filter: { in(k8s.cluster.name, $Cluster) and k8s.namespace.name == $Service and k8s.container.name == concat($Service, "-migration") }
    | fieldsAdd metricName = "limit memory"
]
| append [
  timeseries requested_mem = max(dt.kubernetes.container.requests_memory, rollup: max),
    nonempty: true, 
    by:{ k8s.container.name },
    filter: { in(k8s.cluster.name, $Cluster) and k8s.namespace.name == $Service and k8s.container.name == concat($Service, "-migration") }
    | fieldsAdd metricName = "request memory"
]
| fieldsAdd metricName = concat(replaceString(k8s.container.name, concat($Service, "-"), ""), "::", metricName)""",
            },
        ],
    },

    # ======================================================================
    # LOGS
    # ======================================================================
    "logs": {
        "simple": [
            {
                "nl": "all unfiltered auto-triaging logs",
                "intent": "log_search",
                "expected_contains": ['fetch logs', 'filter'],
                "dql": """fetch logs
| filter matchesValue(dt.app.id, $AppId)
| sort timestamp desc""",
            },
            {
                "nl": "what is log?",
                "intent": "data_record",
                "expected_contains": [],
                "dql": """data
  record(label = "Baby don't hurt me", value = 1),
  record(label = "Don't hurt me", value = 1),
  record(label = "No more", value = 1)""",
            },
            {
                "nl": "customer key activation error details",
                "intent": "log_errors",
                "expected_contains": ['fetch logs', 'filter'],
                "dql": """fetch logs
| filter matchesPhrase(content, "Error while registering tenant bucket key")""",
            },
            {
                "nl": "last logs from related to worker",
                "intent": "log_search",
                "expected_contains": ['fetch logs', 'filter'],
                "dql": """fetch logs
| filter matchesValue(content, "*AgentEventIngestor*") OR matchesValue(content, "*AgentHealthSyncPeriodicWorker*")
| limit 20""",
            },
            {
                "nl": "error logs over time",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
                "dql": """timeseries sum(`log.dtp.app.dynatrace.jira.errorLogs`),
 filter: matchesValue(dt.tenant.uuid, $TenantId),
   by: { dt.tenant.uuid }""",
            },
        ],
        "intermediate": [
            {
                "nl": "ack delay time",
                "intent": "disk_metrics",
                "expected_contains": ['timeseries', 'filter'],
                "dql": """timeseries { 
  disk_queue_message_sent_interval = min(remote_isfm.active_gate.event_ingest.disk_queue_message_sent_interval), 
  disk_queue_message_ack_delay = max(remote_isfm.active_gate.event_ingest.disk_queue_message_ack_delay)
}, 
union:true,
filter: {(if($include_env_AGs=="true", true, else: dt.active_gate.working_mode==$AGtype))}""",
            },
            {
                "nl": "actual data in grail (old hosts)",
                "intent": "log_search",
                "expected_contains": ['fetch logs', 'filter'],
                "dql": """fetch logs
| filter dt.system.bucket == "custom_sen_critical_logs_bdx_iem_prod"
| filter log.source.aws.s3.bucket.name == "ingestion-service-us-east-1-851429953808-prod"
| filter bdx.meta.source == "urn:bdx:src:cdh:iem.host:v1.0.0"
| fieldsAdd dt.system.bucket
| sort timestamp desc
| limit 20""",
            },
            {
                "nl": "ingest bytes [sum]",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
                "dql": """timeseries {
  sum=sum(platform.ppx_service.isfm.logs.ingest.bytes, default:0)
},
filter: { dt.host_group.id == $host_group and in(dt.tenant.uuid, $tenant) and in(table, $table) },
by:{dt.tenant.uuid, table, subtype}
| sort arrayMax(sum) desc | limit toLong($limit)""",
            },
            {
                "nl": "sanitized records [sum]",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
                "dql": """timeseries {
  sum=sum(platform.ppx_service.dsfm.server.log_and_events_monitoring.events_sanitized_count)
},
filter: {dt.host_group.id == $host_group AND in(dt.tenant.uuid, $tenant) AND in(table, $table)},
by: {table, subtype, dt.tenant.uuid}
| sort arrayMax(sum) desc | limit toLong($limit)""",
            },
            {
                "nl": "logs ingest processed [sum]",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
                "dql": """timeseries {
  sum=sum(platform.ppx_service.isfm.server.logs.ingest.processed.count)
},
filter: {dt.host_group.id == $host_group AND in(dt.tenant.uuid, $tenant) AND in(table, $table)},
by: {table, subtype, dt.tenant.uuid}
| sort arrayMax(sum) desc | limit toLong($limit)""",
            },
        ],
        "complex": [
            {
                "nl": "# of errors",
                "intent": "log_errors",
                "expected_contains": ['fetch logs', 'count()', 'filter', 'summarize'],
                "dql": """fetch logs
| filter matchesValue(dt.app.id, $AppId)
| filter matchesValue(dt.app.function, "attack-replay.js")
| filter loglevel == "ERROR"
| parse content, "JSON:logobject"
| filter "any" == $WorkflowId OR logobject[WID] == $WorkflowId
| filter "any" == $ExecutionId OR logobject[EXID] == $ExecutionId
| filter matchesValue(dt.app.function, "attack-replay.js")
| summarize count = count()
| fields count""",
            },
            {
                "nl": "# of warnings",
                "intent": "log_count",
                "expected_contains": ['fetch logs', 'count()', 'filter', 'summarize'],
                "dql": """fetch logs
| filter matchesValue(dt.app.id, $AppId)
| filter matchesValue(dt.app.function, "attack-replay.js")
| filter loglevel == "WARN"
| parse content, "JSON:logobject"
| filter "any" == $WorkflowId OR logobject[WID] == $WorkflowId
| filter "any" == $ExecutionId OR logobject[EXID] == $ExecutionId
| filter matchesValue(dt.app.function, "attack-replay.js")
| summarize count = count()
| fields count""",
            },
            {
                "nl": "sum of logs queried for attack replay",
                "intent": "log_count",
                "expected_contains": ['fetch logs', 'sum(', 'filter', 'summarize'],
                "dql": """fetch logs
| filter matchesValue(dt.app.id, $AppId)
| filter matchesValue(dt.app.function, "attack-replay.js")
| filter loglevel == "INFO"
| parse content, "JSON:logobject"
| fields logobject = logobject
| filter "any" == $WorkflowId OR logobject[WID] == $WorkflowId
| filter "any" == $ExecutionId OR logobject[EXID] == $ExecutionId
| summarize count = sum(logobject[finalStatistics][initialAttackReplayLogs])
| fields count""",
            },
            {
                "nl": "avg logs queried for attack replay",
                "intent": "log_count",
                "expected_contains": ['fetch logs', 'avg(', 'filter', 'summarize'],
                "dql": """fetch logs
| filter matchesValue(dt.app.id, $AppId)
| filter matchesValue(dt.app.function, "attack-replay.js")
| filter loglevel == "INFO"
| parse content, "JSON:logobject"
| fields logobject = logobject
| filter "any" == $WorkflowId OR logobject[WID] == $WorkflowId
| filter "any" == $ExecutionId OR logobject[EXID] == $ExecutionId
| summarize count = avg(logobject[finalStatistics][initialAttackReplayLogs])
| fields count""",
            },
            {
                "nl": "# of attacks without server",
                "intent": "log_count",
                "expected_contains": ['fetch logs', 'sum(', 'filter', 'summarize'],
                "dql": """fetch logs
| filter matchesValue(dt.app.id, $AppId)
| filter matchesValue(dt.app.function, "attack-replay.js")
| filter loglevel == "INFO"
| parse content, "JSON:logobject"
| fields logobject = logobject
| filter "any" == $WorkflowId OR logobject[WID] == $WorkflowId
| filter "any" == $ExecutionId OR logobject[EXID] == $ExecutionId
| summarize count = sum(logobject[finalStatistics][attacksWithoutServer])
| fields count""",
            },
        ],
    },

    # ======================================================================
    # METRICS
    # ======================================================================
    "metrics": {
        "simple": [
            {
                "nl": "list of lookup tables",
                "intent": "metrics_query",
                "expected_contains": [],
                "dql": """fetch dt.system.files
| fields name, size, user.email, display_name, description
| sort size desc""",
            },
            {
                "nl": "user audit in the given timeframe",
                "intent": "events",
                "expected_contains": ['fetch bizevents', 'filter'],
                "dql": """fetch bizevents
| filter matchesValue(dt.system.bucket, $bucket) AND matchesValue(event.provider, { $event_providers }) AND matchesValue(user_uuid, $user_uuid)
| sort timestamp desc""",
            },
            {
                "nl": "total alerting entities",
                "intent": "metrics_query",
                "expected_contains": ['filter', 'summarize', 'by'],
                "dql": """fetch dt.davis.events
| filterOut in(event.category, {"INFO"})
| summarize count=countDistinctExact(dt.source_entity), by:{}""",
            },
            {
                "nl": "number of unique users",
                "intent": "metrics_query",
                "expected_contains": ['filter', 'summarize'],
                "dql": """fetch dt.system.events
| filter event.kind == "GENAI_EVENT"
| summarize countDistinct(user_email)""",
            },
            {
                "nl": "number of unique users over time",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'filter'],
                "dql": """fetch dt.system.events
| filter event.kind == "GENAI_EVENT"
| makeTimeseries unique_users = countDistinct(user_email), interval:24h""",
            },
        ],
        "intermediate": [
            {
                "nl": "mcp tool invocations per tenant",
                "intent": "events",
                "expected_contains": ['fetch bizevents', 'timeseries', 'filter', 'by'],
                "dql": """fetch bizevents 
| filter event.type == "MCP Tool Invocation"
| filter matchesValue(platform, $Platform)
| filter matchesValue(tenant, $Tenant)
| makeTimeseries {success = countIf(status == "SUCCESSFUL", default: 0)}, by: {tenant}, nonempty: true""",
            },
            {
                "nl": "average click events per session",
                "intent": "events",
                "expected_contains": ['fetch events', 'count()', 'avg(', 'filter', 'summarize'],
                "dql": """fetch events
| filter dt.system.bucket == "strato_ui_events"
| filter contains(bhv.app.name, "Clouds") and bhv.type == "user_action"
| summarize count(), by:{dt.rum.session.id}
| summarize `Average click events per session`=avg(`count()`)""",
            },
            {
                "nl": "1h burn rate by installation",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'avg(', 'filter', 'by'],
                "dql": """timeseries {
      burn_rate = sum(sfm.slo.burn_rate, filter:{slo_burn_period == "1h"})
    },
    filter:{entityName(`dt.entity.standardised:slo`) == $slo},
    by:{dt_installation_id}
| sort arrayAvg(burn_rate) desc""",
            },
            {
                "nl": "scans over time",
                "intent": "events",
                "expected_contains": ['fetch events', 'timeseries', 'count()', 'sum(', 'filter'],
                "dql": """fetch events
| filter event.kind == "SDLC_EVENT"
     AND event.status == "finished"
     AND event.provider == "SonarQube"
| filter in(sonarqube.project.id, $Projects)
    AND in(sonarqube.tenant,$TenantURL)
| fieldsAdd end_time=toTimestamp(end_time)
| summarize by:{end_time}, scans=count()
| makeTimeseries Scans=sum(scans), time:end_time, interval:1d""",
            },
            {
                "nl": "token consumption per ai model",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'avg(', 'filter', 'summarize'],
                "dql": """// Split token consuption by model
timeseries tokens=avg(kong_ai_llm_tokens_total), filter: token_type == "total_tokens", by:ai_model
| summarize total=sum(tokens[]), by: {ai_model}
| fieldsAdd total=arraySum(total)""",
            },
        ],
        "complex": [
            {
                "nl": "most burned down error budgets",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'avg(', 'filter', 'summarize'],
                "dql": """timeseries {
    bad = sum(sfm.sli.measurement, rollup: sum, filter: {type == "bad" or failed == "true"}, default: 0),
    total = sum(sfm.sli.measurement, rollup: sum, scalar: true, default: 0)
  },
  filter: { 
          in(`dt.entity.standardised:slo`, {$slo_ids})
          and in(dt_installation_id, array($installation))
          and in(dt_source_entity, array($source_entity_ids))
  },
  by:{`dt.entity.standardised:slo`, dt_installation_id}
| lookup [fetch `dt.entity.standardised:slo` | fields id, slo_target], sourceField:`dt.entity.standardised:slo`, lookupField:id, fields:{slo_target}
// Calculate the error budget burn down.
| fieldsAdd total_error_budget = 100 - toDouble(slo_target)
| fieldsAdd bad_cumulative_sum = arrayCumulativeSum(bad)
| fieldsAdd error_budget_burndown = 100 - (bad_cumulative_sum[] / total * 100)
// normalize to percentages
| fields timeframe, interval, `dt.entity.standardised:slo`, dt_installation_id, error_budget_burndown
| summarize {
  error_budget_burndown = avg(error_budget_burndown[])
}, by: {
  timeframe,
  interval, 
  dt_installation_id, 
  `dt.entity.standardised:slo`= entityName(`dt.entity.standardised:slo`)
}
| sort arrayLast(arrayRemoveNulls(error_budget_burndown))
| limit 25""",
            },
            {
                "nl": "error budget burn down",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'avg(', 'filter', 'summarize'],
                "dql": """timeseries {
    bad = sum(sfm.sli.measurement, rollup: sum, filter: {type == "bad"}, default: 0),
    total = sum(sfm.sli.measurement, rollup: sum, scalar: true, default: 0)
  },
  filter:{entityName(`dt.entity.standardised:slo`) == $slo},
  by:{`dt.entity.standardised:slo`, dt_installation_id}
| lookup [fetch `dt.entity.standardised:slo` | fields id, slo_target], sourceField:`dt.entity.standardised:slo`, lookupField:id, fields:{slo_target}
// Calculate the error budget burn down.
| fieldsAdd total_error_budget = 100 - toDouble(slo_target)
| fieldsAdd bad_cumulative_sum = arrayCumulativeSum(bad)
| fieldsAdd error_budget_burndown = total_error_budget - (bad_cumulative_sum[] / total * 100)
| fields timeframe, interval, `dt.entity.standardised:slo`, dt_installation_id, error_budget_burndown
| summarize {
  error_budget_burndown = avg(error_budget_burndown[])
}, by: {
  timeframe,
  interval, 
  dt_installation_id, 
  `dt.entity.standardised:slo`= entityName(`dt.entity.standardised:slo`)
}
| sort arrayLast(arrayRemoveNulls(error_budget_burndown))
| limit 25""",
            },
            {
                "nl": "task error rate",
                "intent": "metrics_query",
                "expected_contains": ['filter', 'summarize', 'by'],
                "dql": """// Error rate
fetch dt.system.events
| filter event.kind == "WORKFLOW_EVENT" and event.provider == "AUTOMATION_ENGINE" and event.type =="TASK_EXECUTION"
| filter in(dt.automation_engine.workflow.title, array($Workflow))
| filter not startsWith(dt.automation_engine.task.name, "filter")
| filter dt.automation_engine.task.name != "is_not_private_ip_address"
| filter dt.automation_engine.task.name != "is_private_ip_address"
| filter dt.automation_engine.task.name != "is_office_ip_address"
| filter dt.automation_engine.task.name != "is_resource_ip"
| filter dt.automation_engine.task.name != "is_not_resource_ip"
| filter dt.automation_engine.task.name != "is_not_office_ip_address"
| summarize 
    {errors = countIf(dt.automation_engine.state == "ERROR"), 
    successes = countIf(dt.automation_engine.state == "SUCCESS")},
    by: {dt.automation_engine.task.name, dt.automation_engine.workflow.title}
| fieldsAdd finished_executions = toLong(errors) + toLong(successes)
| fieldsAdd error_rate = (toDouble(errors) / (toDouble(finished_executions)) * 100)
| fields dt.automation_engine.task.name,
         dt.automation_engine.workflow.title,
         error_rate,
         errors,
         finished_executions
| sort error_rate desc""",
            },
            {
                "nl": "overall :: availability",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'avg(', 'filter', 'summarize', 'join'],
                "dql": """// This query more expensive than it could be due
// to the cloud_provider, cloud_region, and major_geo
// dimensions being added later.
// It can be simplified after some period of time,
// say, in January 2025.

timeseries avg(isfm.sla.overall),
  by:{source},
  filter:{
    in(cloud_provider, $cloud_providers) and
    in(cloud_region, $cloud_regions) and
    in(major_geo, $major_geos) and
    in(source, $sources)
  }
| join [
    timeseries values=avg(isfm.sla.overall),
      by:{source}
    | fieldsAdd sla_avg = arrayAvg(values)
  ],
  on:{source},
  fields:{sla_avg}
| summarize sla_avg = avg(sla_avg)""",
            },
            {
                "nl": "process :: availability",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'avg(', 'filter', 'summarize', 'join'],
                "dql": """// This query more expensive than it could be due
// to the cloud_provider, cloud_region, and major_geo
// dimensions being added later.
// It can be simplified after some period of time,
// say, in January 2025.

timeseries avg(isfm.sla.process),
  by:{source},
  filter:{
    in(cloud_provider, $cloud_providers) and
    in(cloud_region, $cloud_regions) and
    in(major_geo, $major_geos) and
    in(source, $sources)
  }
| join [
    timeseries values=avg(isfm.sla.process),
      by:{source}
    | fieldsAdd sla_avg = arrayAvg(values)
  ],
  on:{source},
  fields:{sla_avg}
| summarize sla_avg = avg(sla_avg)""",
            },
        ],
    },

    # ======================================================================
    # OTHER
    # ======================================================================
    "other": {
        "simple": [
            {
                "nl": "for next grade",
                "intent": "data_record",
                "expected_contains": [],
                "dql": """data record(
RulesForNextGrade = "A1: High Coverage met for your app size (>80%)")""",
            },
            {
                "nl": "total user sessions",
                "intent": "other_query",
                "expected_contains": ['count()', 'summarize'],
                "dql": """fetch user.sessions
| summarize count()""",
            },
            {
                "nl": "selected day: set this number with variable (days left in trial). dont forget to set the time range.",
                "intent": "data_record",
                "expected_contains": [],
                "dql": """data record()
  | fields DaysLeft = toString($DaysLeft)""",
            },
        ],
        "intermediate": [
            {
                "nl": "teams slos list",
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
                "nl": "slos per team",
                "intent": "data_record",
                "expected_contains": ['count()', 'filter', 'summarize', 'by'],
                "dql": """data record(record=array($filtered_slos))
| expand record
| parse record, "JSON:record"
| fields dt_team_name = record[dt_team_name]

| summarize count = count(), by: {dt_team_name}
| sort count desc""",
            },
            {
                "nl": "slos per tier",
                "intent": "data_record",
                "expected_contains": ['count()', 'filter', 'summarize', 'by'],
                "dql": """data record(record=array($filtered_slos))
| expand record
| parse record, "JSON:record"
| fields tier = record[tier]

| summarize count = count(), by: {tier}
| sort count desc""",
            },
        ],
        "complex": [
            {
                "nl": "capabilities adopted slos",
                "intent": "data_record",
                "expected_contains": ['filter', 'summarize', 'join', 'by'],
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
        ],
    },

    # ======================================================================
    # SPANS
    # ======================================================================
    "spans": {
        "simple": [
            {
                "nl": "# of services",
                "intent": "data_record",
                "expected_contains": ['filter'],
                "dql": """// Total services after applying dimension filters
data record(selected = array($ServiceIDs:triplequote))
| fieldsAdd `Total Services` = toLong(arraySize(selected))
| fields `Total Services`""",
            },
            {
                "nl": "users for: add to favorite",
                "intent": "events",
                "expected_contains": ['fetch events', 'filter', 'summarize'],
                "dql": """// This query was auto-generated by MagicShell
fetch events 
| filter bhv.name == "Add to favorite" and  bhv.app.id == "dynatrace.appshell"  
| summarize countDistinct(bhv.user.id)""",
            },
            {
                "nl": "users for: app menu opened",
                "intent": "events",
                "expected_contains": ['fetch events', 'filter', 'summarize'],
                "dql": """// This query was auto-generated by MagicShell
fetch events 
 | filter bhv.name == "App menu opened" and  bhv.app.id == "dynatrace.appshell"  
|  summarize usage=countDistinct(bhv.user.id)""",
            },
            {
                "nl": "users for: app launched from link",
                "intent": "events",
                "expected_contains": ['fetch events', 'filter', 'summarize'],
                "dql": """// This query was auto-generated by MagicShell
fetch events 
 | filter bhv.name == "App launched from link" and  bhv.app.id == "dynatrace.appshell"  

|  summarize usage=countDistinct(bhv.user.id)""",
            },
            {
                "nl": "daily unique users, last 60 days",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'avg(', 'filter', 'by'],
                "dql": """timeseries avg(dql_usage_stats.unique_users.by_application), by: { application }
, interval: 24h
, from: -60d@d
, to: now()@d
, filter: { application == "dynatrace.services" }""",
            },
        ],
        "intermediate": [
            {
                "nl": "daily span ingest",
                "intent": "metrics",
                "expected_contains": ['timeseries', 'sum(', 'avg(', 'filter', 'summarize'],
                "dql": """timeseries series=sum(deus.segmentIndexerManager.uncompressed_ingested_data_size)
, filter: { in(pondtype, "span") }
, from: -7d
, to: now()
, interval: 1d
| summarize ingest=sum(arrayAvg(series))""",
            },
            {
                "nl": "median daily user",
                "intent": "events",
                "expected_contains": ['fetch bizevents', 'timeseries', 'filter'],
                "dql": """fetch bizevents
| filter event.provider == "dynatrace-apps"
| filter if($User_reach != "all", in(userType, $User_reach), else: userType == userType )
| makeTimeseries sparkline = countDistinct(userId), interval:24h
| fieldsAdd value=arrayMedian(sparkline)""",
            },
            {
                "nl": "unique sessions by city",
                "intent": "events",
                "expected_contains": ['fetch bizevents', 'filter', 'summarize', 'by'],
                "dql": """fetch bizevents
| filter event.provider == "dynatrace-apps"
| filter if($User_reach != "all", in(userType, $User_reach), else: userType == userType )
| summarize count = countDistinct(sessionId), by:{geo.city.name}""",
            },
            {
                "nl": "top 10 tenants with sessions",
                "intent": "events",
                "expected_contains": ['fetch bizevents', 'filter', 'summarize', 'by'],
                "dql": """fetch bizevents
| filter event.provider == "dynatrace-apps"
| filter if($User_reach != "all", in(userType, $User_reach), else: userType == userType )
| summarize sessionCount = countDistinct(sessionId), by: {tenantId}
| sort sessionCount desc
| limit 10""",
            },
            {
                "nl": "tenants in use",
                "intent": "events",
                "expected_contains": ['fetch bizevents', 'filter', 'summarize'],
                "dql": """fetch bizevents
| filter event.provider == "dynatrace-apps"
| filter if($User_reach != "all", in(userType, $User_reach), else: userType == userType )
| summarize value=countDistinct(tenantId)""",
            },
        ],
        "complex": [
            {
                "nl": "top 10 external users",
                "intent": "events",
                "expected_contains": ['fetch events', 'count()', 'filter', 'summarize', 'by'],
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
                "nl": "🛑 request failures",
                "intent": "rum",
                "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
                "dql": """fetch user.events, bucket:{"default_user_events"}
| filter characteristics.has_request
| filter view.url.domain == url.domain
| filter http.response.status_code >= 400

| fieldsAdd url.path = replacePattern(url.path, "UUIDSTRING", "{uuid}")
| fieldsAdd url.path = replacePattern(url.path, "SMARTSCAPEID", "{entity}")
| fieldsAdd url.path = replacePattern(url.path, "'/'[a-zA-Z]{3} [0-9]{5} '/'", "/{tenant}/")
| fieldsAdd url.path = replacePattern(url.path, "('/dynatrace.' | '/my.')[a-zA-Z0-9._-]+", "/{appId}")


| makeTimeSeries {
    httpErrors = count(default:0)
}, by: {url.path, http.response.status_code}, bins: 30

| filter arraySum(httpErrors) > 10 
| sort arraySum(httpErrors) desc
| limit 10""",
            },
            {
                "nl": "🛜  top requests",
                "intent": "rum",
                "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
                "dql": """fetch user.events, bucket:{"default_user_events"}, samplingRatio:10
| filter characteristics.has_request
| filter view.url.domain == url.domain
// | filter matchesPhrase(url.path, "/platform")

| fieldsAdd url.path = replacePattern(url.path, "UUIDSTRING", "{uuid}")
| fieldsAdd url.path = replacePattern(url.path, "SMARTSCAPEID", "{entity}")
| fieldsAdd url.path = replacePattern(url.path, "'/'[a-zA-Z]{3} [0-9]{5} '/'", "/{tenant}/")
| fieldsAdd url.path = replacePattern(url.path, "('/dynatrace.' | '/my.')[a-zA-Z0-9._-]+", "/{appId}")


| makeTimeSeries {
    httpErrors = count(default:0)
}, by: {url.path}, bins: 30

| filter arraySum(httpErrors) > 10 
| sort arraySum(httpErrors) desc
| limit 10""",
            },
            {
                "nl": "⚖️ transfer size",
                "intent": "rum",
                "expected_contains": ['timeseries', 'sum(', 'filter', 'by'],
                "dql": """fetch user.events, bucket:{"default_user_events"}
| filter characteristics.has_request
| filter view.url.domain == url.domain
| filter matchesPhrase(url.path, "/platform")

| fieldsAdd url.path = replacePattern(url.path, "UUIDSTRING", "{uuid}")
| fieldsAdd url.path = replacePattern(url.path, "SMARTSCAPEID", "{entity}")
| fieldsAdd url.path = replacePattern(url.path, "'/'[a-zA-Z]{3} [0-9]{5} '/'", "/{tenant}/")
| fieldsAdd url.path = replacePattern(url.path, "('/dynatrace.' | '/my.')[a-zA-Z0-9._-]+", "/{appId}")

| makeTimeSeries {
    count = count(default: 0),

    size = sum(performance.decoded_body_size)
}, by: {url.path}, bins: 30

| filter arraySum(size) > 10 
| sort arraySum(size) desc
| limit 10""",
            },
            {
                "nl": "🏢 tenants per version",
                "intent": "events",
                "expected_contains": ['fetch events', 'timeseries', 'filter', 'by'],
                "dql": """fetch events,  samplingRatio: 8
| filter dt.system.bucket == "strato_ui_events"
| filter in (bhv.app.id, "dynatrace.appshell")
| fieldsAdd incompatible="✅"
| makeTimeseries tenants = countDistinct(bhv.tenant.uuid, default:0),
    by:{version=bhv.app.version,incompatible}, bins:60
 
| append [
  fetch events
  | filter dt.system.bucket == "default_davis_custom_events"
  | filter matchesPhrase(event.name, "[Dtp][Platform-Services][Channels]")
  | filter `App-Id` == "dynatrace.appshell"
  | filter Compatibility == "INCOMPATIBLE"
  | fieldsAdd incompatible="🚫 incompatible"
  | fieldsRename Version, version
  | makeTimeseries { incompatibleEnvironments=countDistinct(Environment)},
      by: {version, incompatible}, bins:60
]""",
            },
        ],
    },
}

# Flat list for backward compatibility
EXAMPLES = []
for category, levels in LEVELED_EXAMPLES.items():
    for level, examples in levels.items():
        for ex in examples:
            ex_copy = ex.copy()
            ex_copy["category"] = category
            ex_copy["level"] = level
            EXAMPLES.append(ex_copy)
