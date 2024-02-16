from kafka import KafkaProducer, KafkaConsumer


class MockKafkaProducer(KafkaProducer):
    # pylint: disable=super-init-not-called
    def __init__(self, *args, **kwargs):
        self.messages = {}

    def send(self, topic, value, *args, **kwargs):
        self.messages.setdefault(topic, []).append(value)

    def flush(self, *args, **kwargs): ...

    def close(self, *args, **kwargs): ...


class MockKafkaConsumer(KafkaConsumer):
    # pylint: disable=super-init-not-called
    def __init__(self, *args, **kwargs): ...

    def poll(self, *args, **kwargs): ...

    def close(self, *args, **kwargs): ...

    def commit(self, *args, **kwargs): ...
