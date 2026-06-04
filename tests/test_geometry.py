from prom_recognition.utils.geometry import distance


def test_distance() -> None:
    assert distance((0, 0), (3, 4)) == 5

