from ajb.base.events import KafkaTopic


def test_get_all_topics():
    assert KafkaTopic.get_all_topics()
