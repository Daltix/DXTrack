# DXTrack
Centralized service and API for metrics / error tracking

# stash - will clean up later
To manually test, do the following
```
STAGE=dev ERROR_TABLE_NAME=dxtrack_error_1 METRIC_TABLE_NAME=dxtrack_metric_1 DB_NAME=dxtrack_dev BUCKET_NAME=dxtrack-dev python deployment/lambda_toathena.py
```

Then add the following to the bottom of the lambda_toathena file
```
main({
     'Records': [
         {'body': 's3://dxtrack-dev/fh-jsonl-error-output-2018/09/07/13/dxtrack-error-input-dev-1-2018-09-07-13-47-38-36c99d56-fe4f-43eb-aea6-9ac38334f814.gz'}
     ]
 })
```
