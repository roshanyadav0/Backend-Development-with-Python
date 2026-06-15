import datetime

def log(*message,level = "INFO",s = "",**data) :
    timestamp = datetime.datetime.now()
    body = s.join(str(s) for s in message)
    end = " ".join(f"{k} = {v}" for k,v in data.items())
    print(f"{timestamp} {level} {body} {end}")

# minimal call
log("Server started")
# → [10:05:01] INFO: Server started

# multiple messages + level
log("Disk", "full", level="WARN")
# → [10:05:02] WARN: Disk full

# rich context via **kwargs
log("User login", level="DEBUG", user="alice", ip="1.2.3.4")
# → [10:05:03] DEBUG: User login [user=alice] [ip=1.2.3.4]
