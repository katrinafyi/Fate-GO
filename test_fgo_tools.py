from fgo_tools import *
import pytest

@pytest.fixture
def drops_data():
    return DropsData({
        'location 1': {
            'mat 1': {
                'initial': 1.5,
                'stacks': 100
            }
        }
    })

class TestEventOptimiser:
    def test_stacks(self, drops_data: DropsData):
        assert drops_data.stacks('location 1') == Items({'mat 1': 100})

    def test_drops(self, drops_data: DropsData):
        assert drops_data.drops_with_bonus('location 1', Items({
            'mat 1': 10
        })) == Items({'mat 1': 1001.5})
