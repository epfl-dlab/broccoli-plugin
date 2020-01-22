from collections import deque
import time
import asyncio

class DequeProvider():
    def __init__(self, maxlen):
        self.maxlen = maxlen

    def __call__(self, *args, **kwargs):
        return deque([], maxlen=self.maxlen)


class ConstantProvider():
    def __init__(self, c):
        self.c = c

    def __call__(self, *args, **kwargs):
        return self.c


from html.parser import HTMLParser


class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        self.tags.append(f"</{tag}>")

# taken from: https://stackoverflow.com/questions/54352147/python-get-opening-and-closing-html-tags
def get_html_tags(html):
    parser = MyHTMLParser()
    parser.feed(html)
    return parser.tags


class EventLimiter:

    def __init__(self, EVENTS_PER_SEC = 10, POLLS_PER_SEC = 10, MAX_QUEUE = 10):
        self.queue = 1
        self.last_poll = time.monotonic()

        self.EVENTS_PER_SEC = EVENTS_PER_SEC
        self.POLLS_PER_SEC = POLLS_PER_SEC
        self.MAX_QUEUE = MAX_QUEUE

    async def __call__(self):
        await self.wait_for_queue()

    async def wait_for_queue(self):
        while self.queue < 1:
            now = time.monotonic()
            wait_til = self.last_poll + 1 / self.POLLS_PER_SEC
            to_wait = max(wait_til - now, 0)

            dt = now - self.last_poll
            new_events = dt * self.EVENTS_PER_SEC
            self.queue += new_events

            self.queue = min(self.queue, self.MAX_QUEUE)

            self.last_poll = now
            if self.queue < 1:
                await asyncio.sleep(to_wait)
        self.queue -= 1
