# DXTrack

Centralized service and API for metrics / error tracking.

## Warning

This library is in a pre-alpha phase and is not ready for out of the box usage. Feel free to read it and take inspiration
from it but don't consider it bullet-proof in any way.

## Installation

You can include in your pip requirements.txt:

```
git+https://github.com/Daltix/DXTrack.git#egg=dxtrack
```
Be sure to specify a version number unless you always want to use the latest version which might not be safe as APIs can change.

Or you can workon your regular virtualenv and clone / pip install

```bash
python3.6 -m venv venv
source ./venv/bin/activate
git clone git@github.com:Daltix/DXTrack.git
cd DXTrack
pip install -e .
cd ~
python
>> import dxtrack
```

## API

The module will be called `dxtrack` and will have the following very simple api

### Importing and Configuring

```py
from dxtrack import dxtrack

dxtrack.configure(
    stage='test'|'dev'|'prod',
    context='<context-name>',
    run_id='<idenfier>',
    default_metadata={...},
    profile_name='<aws-profile-name>',
    aws_access_key_id='<aws-access-key-id>',
    aws_secret_access_key='<aws-secret-access-key>',
    buffer_metrics=False,
    papertrail_hostport='logsN.papertrailapp.com:XXXXX',
    use_async_requests=True|False
)
```

Where setting the stage to `test` will by default either write errors / metrics to a file OR just print them. Setting to `dev` or `prod` will send errors and metrics to the appropriate destination. 

The `context` and `default_metadata` options will accompany the logging of all metric and errors.

The `run_id` is meant to be a unique identifier for a single run of the context. A good options is to make this a stringified version of your timestamp.

The `profile_name` is an optional argument that allows you to specify which aws set of credentials you would like to use that are present in your aws credentials file.

If you have a papertrail account, you can add all metrics (at the .info level) and errors (at the .error) via the `papertrail_hostport` option..

The `use_async_requests` option can be used to execute the requests from dxtrack to Kinesis asynchronously, **caution: experimental**. By default this functionality is disabled.

You can also pass your credentials directly via the `aws_access_key_id` & `aws_secret_access_key options`. If specified these are preferred over the profile name.

There is a DXTrack user in the datalake account who's credentials can be used to write errors & metrics.

### Tracking errors

#### Tracking handled excecptions

The pattern by which you can track all handled exceptions is the following:

```py
try:
    some_func()
except Exception as e:
    dxtrack.error(metadata={...})
    raise e
```
Note that you should re-raise the error since it was an unexpected one, especially if you are catching the most general Exception.

Note that if `metadata` is provided here, it will be merged with the default metadata configured at the entry point using `dxtrack.configure`

#### Tracking a list of errors

The pattern by which you can track several thrown and caught exceptions is as follows:

```py
errors = []
for i in range(0, n_errors):
try:
    raise ValueError(str(i))
except ValueError as e:
    errors.append(e)
dxtrack.errors(errors, metadata={...})
```

In this pattern you must have an array in which you are collecting handled exceptions. Then when you are ready to report
them, you call `dxtrack.errors` (notice the `s` at the end) to report all of them at once. Note that this does not
collecction stack trace information for the exceptions the way that `dxtrack.error` does. The upside, however, is that
all errors are delivered in one bulk call which generates much less network traffic.

#### Tracking unhandled exceptions

If we want to track all errors that are not explicitly tracked with `dxtrack.error`, it can be done using the [built-in sys.excepthook](https://docs.python.org/3.6/library/sys.html#sys.excepthook) and the default metadata set during configuration time. However, this will not be implemented right now since messing with the internals like sys.excepthook is a very scary thing and should require a good bit of planning.

### Tracking metrics

#### Basic usage

In the case where we want to track expected counts or events such as number of products downloaded per day, number of products downloaded per shop, number of promos parsed per shop per day, etc. we can track metrics with the following:

```py
dxtrack.metric('<dotted_metric_name>', <value>, metadata={...})
```

By default, there is one HTTP to the firehose every time `dxtrack.metric()` is called. If you are tracking lots of metrics
and want to optimize this, you can enable metric buffering by adding `buffer_metrics=True` to the configure call:

```py
dxtrack.configure(
    ...,
    buffer_metrics=True
)
```

However, when you do this, you must remember to call `dxtrack.flush_metrics_buffer()` periodically or they won't get sent!
Here is an example of the full flow:

```py
dxtrack.configure(
    ...,
    buffer_metrics=True
)
for i in range(0, 100):
    # inside of this for loop all metrics are being buffered
    dxtrack.metric('test', i)
# now we have to remember to send them or they will be lost forever!
dxtrack.flush_metrics_buffer()
```

#### Specifying timestamp

By default, the timestamp for a metric is set to the `datetime.datetime.utcnow()` of when the call to `metric()` was made.
If for some reason (like backprocessing) you would like to explicity specify the timestamp with which to associate the call 
to `metric()`, you can do so using the optional `timestamp` parameter. You can do it with:

```py
dxtrack.metric('<dotted-metric-name>', 1, timestamp=datetime(year=1985, month=11, day=20))
```

## Output

All output is sent to a firehose which can be configured to buffer and send errors and metrics to an s3 bucket. This is
a very robust way to save the raw data though you'll need to do another level of processing to make it available in a 
more usable way.

### Snowflake Tables

After your errors or metrics go through the kinesis pipeline (can take up to 1 hour), they will be available in the following snowflake tables tables if you decide to use the DXTrackSnowflakeFeed repo (not currently open-source).

For errors:

```sql
SELECT * from dxtrack_<stage>.public.dxtrack.error_1;
```

For metrics

```sql
SELECT * from dxtrack_<stage>.public..metric_1;
```

### Papertrail

If you are using dxtrack for dashboarding on the level of a few hours or more then the Snowflake Tables should be enough.
If you need faster feedback for debugging purposes then you'll want to use the Papertrail option. Note that you'll need to
set up a Papertrail Account. 

### Error tracking

#### Raw output

Each call to `dxtrack.error` will produce a json object of the following format:

```py
{
    "context": "<context-name>",
    "exception": {
      "type": "<exception-class>",
      "value": "<exception-message>",
      "traceback": "<printable-stack-trace>"
    },
    "stage": "<dev|prod>",
    "metadata": {
          
    },
   "timestamp": "<unix-timestamp>",
   "run_id": "<run-id>",
   "id": hash(context, exception, stage, metadata, timestamp)
}
```

Where `exception.type`, `exception.value`, and `exceptions.traceback` are the same arguments that are passed to [sys.excepthook](https://docs.python.org/3.6/library/sys.html#sys.excepthook).

The `id` is supposed to be a unique identifier for the error itself. As in you need to share a single exception with someone, you would slack them the `id`.

### Metric tracking

#### Raw output

Each call to `dxtrack.metric` will result in a json with the following format:

```py
{
    "context": "<context-name>",
    "metric_name": "<dotted-metric-name>",
    "value": float,
    "stage": "<dev|prod>",
    "metadata": {
          ...
    },
   "run_id": "<run-id>",
   "timestamp": unix_timestamp,
   "id": hash(context, metric_name, stage, metadata, timestamp)
}
```

## The backend

Common to metric and error tracking is the need for a very simple firehose wrapper. Since we have two different AWS accounts that we are using, there will most likely need to be some extra arguments required to configure the `dxtrack` module to use a different set of credentials. This can be added in the `dxtrack.configure()` method.

### Error tracking

All error tracking functionality can be implemented very simply using the very robust builtin if you are using 
the `dxtrack.error()` function:

- [traceback.format_tb](https://docs.python.org/3.6/library/traceback.html#traceback.format_tb)

If you are using the `dxtrack.errors()` function, then you won't be able to get the `traceback` portion of the error.
Some future work should be done on this.

### Metric tracking

Metric tracking is a very simple wrapper around the firehose api, there should be nothing special needed here.

## Architecture

Obviously the above is only the proposed interface. The backend is implemented in a cost-effective way that allows us 
to easily set up alarms and completeness checks. To see some of these implemented, see the Alert repo.

### Cost-optimized

The architecture looks like the following:

![image](https://user-images.githubusercontent.com/424192/47557891-c3efb600-d909-11e8-8ee8-c3e944c06bff.png)

**NOTE** We are not sending anything to sentry yet though this is a possibility. We are only sending the output to Athena at the moment. However, if we do decide to move forward with 3rd party tools we can control how many entries are sent to Sentry or any other service that we decide to use for either the metrics or the error tracking. 
