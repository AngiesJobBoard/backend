from dataclasses import dataclass


@dataclass
class BucketAndMeasurement:
    bucket: str
    measurement: str


@dataclass
class BucketAndMeasurementNames:
    APILogs = BucketAndMeasurement(bucket="APILogs", measurement="log")
