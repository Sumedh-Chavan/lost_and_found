# Lost & Found (Flask) — simple README

A small Flask app to register users, report lost/found items, comment, and message other users. This repo is a minimal proof-of-concept I built earlier; it has a tiny frontend and core functionality but is **not production-ready**. Use it as a starting point.

---

## Features

- User signup / login (simple session-based auth)
- Add lost/found items with optional image upload
- Item listing and detail pages
- Comments on items
- Claim an item (creates a conversation/message to the item owner)
- Simple user-to-user conversations
- Admin view to handle claims for items in the admin's responsibility area

---

## Routes / Endpoints (overview)

- `GET /` — Home
- `GET, POST /signup` — Register new user
- `GET, POST /login` — Login
- `GET /logout` — Logout
- `GET /dashboard` — User dashboard
- `GET, POST /add_item` — Add a lost/found item
- `GET /items` — List all items
- `GET /item/<item_id>` — Item detail + comments
- `POST /item/<item_id>/comment` — Post a comment (must be logged in)
- `POST /item/<item_id>/claim` — Submit a claim for an item (starts a conversation)
- `GET /conversations` — List conversations (shows latest message per conversation)
- `GET, POST /conversation/<user_id>` — Conversation thread with another user
- `GET /admin/claims` — Admin-only view (returns `'Unauthorized'` if not admin)

---

## Database models (summary)

- `User` (`Users`) — username (PK), first/last name, password (stored as plaintext in current code — **see security notes**), mis, role
- `Item` (`Items`) — item_id (PK), description, category, report_type, place_of_responsibility, username (FK → Users), image
- `ItemLocation` (`items_locations`) — id (PK), item_id (FK → Items), location
- `Comment` (`Comments`) — comment_id (PK), comment text, item_id (FK → Items), username (FK → Users)
- `Conversation` (`Conversations`) — id (PK), message, sender_id, receiver_id, time_stamp

---