import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class BandClient:
    """
    Band API Adapter for MediChain.
    Demo mode mein sab kuch memory mein store hota hai.
    Real mode mein Band API calls hoti hain.
    """
    
    def __init__(self):
        self.api_key  = os.getenv("BAND_API_KEY", "")
        self.base_url = os.getenv("BAND_BASE_URL", "")
        self.mode     = os.getenv("APP_MODE", "demo")
        
        # Demo mode ke liye in-memory storage
        self._rooms = {}
        
        print(f"[BandClient] Mode: {self.mode}")

    def create_room(self, name: str, metadata: dict = None) -> str:
        """Naya Band room banao - har case ka alag room"""
        
        if self.mode == "demo":
            # Demo: memory mein room banao
            room_id = f"room-{name}-{datetime.now().strftime('%H%M%S')}"
            self._rooms[room_id] = {
                "name": name,
                "messages": [],
                "context": metadata or {},
                "created_at": datetime.now().isoformat()
            }
            print(f"[Band] Room created: {room_id}")
            return room_id
        
        # TODO: Real Band SDK call yahan aayegi
        import requests
        resp = requests.post(
            f"{self.base_url}/rooms",
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"},
            json={"name": name, "metadata": metadata or {}}
        )
        resp.raise_for_status()
        return resp.json()["room_id"]

    def post_message(self, room_id: str, agent_name: str,
                     content: str, metadata: dict = None):
        """Agent Band room mein message post karta hai"""
        
        msg = {
            "sender":    agent_name,
            "content":   content,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "metadata":  metadata or {}
        }
        
        if self.mode == "demo":
            if room_id not in self._rooms:
                self._rooms[room_id] = {"messages": [], "context": {}}
            self._rooms[room_id]["messages"].append(msg)
            print(f"[Band] {agent_name} posted message")
            return
        
        # TODO: Real Band SDK call
        import requests
        requests.post(
            f"{self.base_url}/rooms/{room_id}/messages",
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"},
            json=msg
        )

    def get_messages(self, room_id: str) -> list:
        """Band room ke saare messages padho"""
        
        if self.mode == "demo":
            return self._rooms.get(room_id, {}).get("messages", [])
        
        # TODO: Real Band SDK call
        import requests
        resp = requests.get(
            f"{self.base_url}/rooms/{room_id}/messages",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return resp.json().get("messages", [])

    def update_context(self, room_id: str, key: str, value):
        """Band room mein structured data save karo"""
        
        if self.mode == "demo":
            if room_id not in self._rooms:
                self._rooms[room_id] = {"messages": [], "context": {}}
            self._rooms[room_id]["context"][key] = value
            return
        
        # TODO: Real Band SDK call
        import requests
        requests.patch(
            f"{self.base_url}/rooms/{room_id}/context",
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"},
            json={key: value}
        )

    def get_context(self, room_id: str) -> dict:
        """Band room ka stored context padho"""
        
        if self.mode == "demo":
            return self._rooms.get(room_id, {}).get("context", {})
        
        # TODO: Real Band SDK call
        import requests
        resp = requests.get(
            f"{self.base_url}/rooms/{room_id}/context",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return resp.json()

    def notify_human(self, room_id: str, message: str):
        """Human reviewer ko Band ke through alert karo"""
        
        self.post_message(
            room_id,
            "System-Alert",
            f"🚨 HUMAN REVIEWER REQUIRED: {message}",
            metadata={"type": "human_escalation", "priority": "HIGH"}
        )
        print(f"[Band] Human escalation triggered for room: {room_id}")
    
    def get_room_summary(self, room_id: str) -> str:
        """Poore room ka summary text - Decision agent ke liye"""
        
        messages = self.get_messages(room_id)
        summary  = []
        for msg in messages:
            summary.append(
                f"[{msg['timestamp']}] {msg['sender']}:\n{msg['content']}"
            )
        return "\n\n" + "="*50 + "\n\n".join(summary)