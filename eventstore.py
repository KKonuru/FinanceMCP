from dataclasses import dataclass
from mcp.server.streamable_http import (
    EventCallback,
    EventId,
    EventMessage,
    EventStore,
    StreamId
)
from mcp.types import JSONRPCMessage
from collections import deque
from uuid import uuid4
@dataclass
class EventEntry:
    event_id: EventId
    stream_id: StreamId
    message: JSONRPCMessage

class InMemoryEventStore(EventStore):
    def __init__(self,max_events_per_stream=100):
        self.max_events_per_stream = max_events_per_stream
        self.streams: dict[StreamId, deque[EventEntry]] = {}
        self.event_index: dict[EventId, EventEntry] = {}
    async def store_event(self,stream_id: StreamId, message: JSONRPCMessage) -> EventId:
        event_id = str(uuid4())
        event_entry = EventEntry(
            event_id=event_id,stream_id=stream_id, message=message
        )
        if stream_id not in self.streams:
            self.streams[stream_id] = deque(maxlen=self.max_events_per_stream)
        
        if len(self.streams[stream_id]) ==self.max_events_per_stream:
            oldest_event = self.streams[stream_id][0]
            self.event_index.pop(oldest_event.event_id, None)
        
        self.streams[stream_id].append(event_entry)
        self.event_index[event_id] = event_entry
        return event_id

    async def replay_events_after(self, last_event_id: EventId, send_callback: EventCallback) -> None |StreamId:
        if last_event_id not in self.event_index:
            return None
        last_event = self.event_index[last_event_id]
        stream_id = last_event.stream_id
        stream_events = self.streams.get(last_event.stream_id,deque())

        found_last = False
        for event in stream_events:
            if found_last:
                await send_callback(EventMessage(event.event_id, event.message))
            elif event.event_id == last_event_id:
                found_last = True
        return stream_id
    def debugger(self):
        #Function for me to see what is stored in the self.streams and self.event_index
        print("Streams:")
        for stream_id, events in self.streams.items():
            print(f"Stream ID: {stream_id}, Events: {[event.event_id for event in events]}")
        print("Event Index:")
        for event_id, event_entry in self.event_index.items():
            print(f"Event ID: {event_id}, Stream ID: {event_entry.stream_id}, Message: {event_entry.message}")
