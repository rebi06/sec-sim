# Architecture Notes

- Frontend is presentation-only.
- Backend owns validation, turn resolution, and event logging.
- Domain rules are isolated from API and persistence.
- Game state is persisted as session state plus append-only events.
- The event log is the primary expansion point for WebSocket, audit, replay, and analytics.
