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
import os
import redis.asyncio as redis


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

class RedisEventStore(EventStore):
    def __init__(self,max_events_per_stream=50):
        self.max_events_per_stream = max_events_per_stream
        redis_url = os.getenv("REDIS_ADDR")
        redis_username = os.getenv("REDIS_USERNAME")
        redis_password = os.getenv("REDIS_PASSWORD")
        self.redis = redis.from_url(
            f"redis://{redis_username}:{redis_password}@{redis_url}",
            decode_responses=True
        )

    async def store_event(self,stream_id: StreamId, message: JSONRPCMessage) -> EventId:
        event_id = str(uuid4())
        event_key = f"stream:{stream_id}"
        event_data = {
            "event_id": event_id,
            "message": str(message)
        }
        # Check if key exists before setting TTL
        key_exists = await self.redis.exists(event_key)
        await self.redis.rpush(event_key, str(event_data))
        await self.redis.expire(event_key, 60*30)  # TTL of half hour
        await self.redis.ltrim(event_key, -self.max_events_per_stream, -1)
        return event_id
    
    async def replay_events_after(self, last_event_id: EventId, send_callback: EventCallback) -> None |StreamId:
        keys = await self.redis.keys("stream:*")
        for key in keys:
            events = await self.redis.lrange(key, 0, -1)
            found_last = False
            for event_str in events:
                event = eval(event_str)
                if found_last:
                    await send_callback(EventMessage(event["event_id"], eval(event["message"])))
                elif event["event_id"] == last_event_id:
                    found_last = True
            if found_last:
                return key.split("stream:")[1]
        return None