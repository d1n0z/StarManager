from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType


class CreateBotLongPoll(VkBotLongPoll):
    def listen(self):
        """
        The listen function is a generator that yields events from the longpoll.
        It will continue to yield events until an exception occurs,
        at which point it will attempt to reconnect and resume listening.

        :param self: Represent the instance of the class
        :return: A generator object
        :doc-author: Trelent
        """
        while True:
            try:
                for event in self.check():
                    yield event
            except Exception as e:
                if str(e)[1] != '<':
                    print(e, end=" FROM MAIN.PY->MyLongPoll->listen\n")
