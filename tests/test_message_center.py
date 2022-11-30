from unittest import TestCase
from message_center import MessageCenter

class TestMessageCenter(TestCase):
    def setUp(self) -> None:
        self.message_center  = MessageCenter()
    def test_consume_message(self):
        self.fail()

