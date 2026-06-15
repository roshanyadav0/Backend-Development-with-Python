import datetime

def log(*messages, level="INFO", sep=" ", **context):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    body      = sep.join(str(m) for m in messages)
    extras    = " ".join(f"[{k}={v}]" for k, v in context.items())
    print(f"[{timestamp}] {level}: {body} {extras}")

# minimal call
log("Server started")
# → [10:05:01] INFO: Server started

# multiple messages + level
log("Disk", "full", level="WARN")
# → [10:05:02] WARN: Disk full

# rich context via **kwargs
log("User login", level="DEBUG", user="alice", ip="1.2.3.4")
# → [10:05:03] DEBUG: User login [user=alice] [ip=1.2.3.4]


