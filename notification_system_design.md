# Stage 1

Assume a front-end developer colleague has asked you for REST API design, contract and structure to display notifications to the users when they are logged in.

## Core Actions
1. **Fetch Notifications:** Retrieve a list of notifications for the logged-in user.
2. **Mark as Read:** Mark a specific notification or all notifications as read.
3. **Get Unread Count:** Retrieve the number of unread notifications for a badge display.

## REST API Endpoints

### 1. Fetch Notifications
**Endpoint:** `GET /api/v1/notifications`
**Description:** Fetches paginated notifications for the authenticated user.
**Headers:**
```json
{
  "Authorization": "Bearer <token>",
  "Accept": "application/json"
}
```
**Request Query Parameters:**
- `page` (integer, default: 1)
- `limit` (integer, default: 20)
- `unreadOnly` (boolean, default: false)

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "d146095a-0d86-4a34-9e69-3900a14576bc",
      "type": "Result",
      "message": "mid-sem",
      "isRead": false,
      "timestamp": "2026-04-22T17:51:30Z"
    }
  ],
  "meta": {
    "total": 150,
    "page": 1,
    "limit": 20
  }
}
```

### 2. Mark Notification as Read
**Endpoint:** `PATCH /api/v1/notifications/{id}/read`
**Description:** Marks a specific notification as read.
**Headers:**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
```
**Request Body:** None required.
**Response (200 OK):**
```json
{
  "success": true,
  "message": "Notification marked as read"
}
```

### 3. Get Unread Count
**Endpoint:** `GET /api/v1/notifications/unread-count`
**Description:** Retrieves the count of unread notifications.
**Headers:**
```json
{
  "Authorization": "Bearer <token>"
}
```
**Response (200 OK):**
```json
{
  "count": 5
}
```

## Real-time Notifications Mechanism
**WebSockets** or **Server-Sent Events (SSE)** should be used.
- **WebSockets** provide full-duplex communication and are widely supported, making them ideal for high-frequency, two-way communication.
- **Server-Sent Events (SSE)** are simpler and better suited if the communication is strictly one-way (server to client), which perfectly fits a notification system.
**Recommendation:** Implement **Server-Sent Events (SSE)** for pushing real-time notifications to the client as it is more lightweight and leverages standard HTTP, perfectly matching the unidirectional flow of notifications.

# Stage 2

## Persistent Storage Suggestion
**Suggested Database:** **PostgreSQL** (Relational Database) or **MongoDB** (NoSQL Document Database).
**Choice:** **PostgreSQL** with Table Partitioning. Given that notifications have varying metadata depending on the `type`, but generally follow a predictable schema, PostgreSQL provides strong ACID consistency. Partitioning by `createdAt` date handles the sheer volume of time-series-like notification data effectively as it scales.

## DB Schema (PostgreSQL)
```sql
CREATE TYPE notification_type AS ENUM ('Event', 'Result', 'Placement');

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id INT NOT NULL,
    notification_type notification_type NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexing for fast retrieval
CREATE INDEX idx_student_unread ON notifications(student_id) WHERE is_read = false;
CREATE INDEX idx_created_at ON notifications(created_at);
```

## Problems with Data Volume Increase
1. **Slower Reads/Writes:** As the table grows to millions of rows, querying (even with indexes) and inserts become slower.
2. **Index Size:** Indexes will become too large to fit in RAM, leading to disk I/O bottlenecks.
3. **Storage Costs:** Storing years of notifications will drastically increase storage requirements.

## Solutions
1. **Table Partitioning:** Partition the `notifications` table by `created_at` (e.g., monthly partitions). This keeps active indexes small and speeds up queries for recent data.
2. **Data Archiving/TTL:** Move old, read notifications (e.g., older than 3 months) to cold storage or delete them.
3. **Caching:** Cache the "unread count" in Redis to avoid hitting the DB on every page load.

## Queries
**Fetch unread notifications:**
```sql
SELECT id, notification_type, message, created_at 
FROM notifications 
WHERE student_id = 1042 AND is_read = false 
ORDER BY created_at DESC 
LIMIT 20 OFFSET 0;
```

**Mark as read:**
```sql
UPDATE notifications 
SET is_read = true 
WHERE id = 'd146095a-0d86-4a34-9e69-3900a14576bc' AND student_id = 1042;
```

# Stage 3

## Query Analysis
```sql
SELECT * FROM notifications
WHERE studentID = 1042 AND isRead = false
ORDER BY createdAt DESC;
```
**Is this query accurate?** Yes, it accurately fetches all unread notifications for a specific student, ordered by the most recent first.
**Why is this slow?**
If there are 5,000,000 notifications and no appropriate index, the database has to perform a full table scan or sort a massive amount of data in memory. Even with a basic index on `studentID`, if the student has many notifications, sorting by `createdAt` without a composite index can be expensive.
**What would you change and likely computation cost?**
1. Do not use `SELECT *`. Select only required columns (e.g., `id`, `message`, `createdAt`).
2. Add a composite index: `CREATE INDEX idx_student_unread_created ON notifications(studentID, createdAt DESC) WHERE isRead = false;`.
**Computation Cost:** With the partial index, the cost drops from O(N) (table scan) or O(M log M) (sorting M results) to O(log(total_rows) + K) where K is the number of unread notifications, meaning near-instantaneous execution.

## Developer's Advice on Indexes
**Is this advice effective?** No.
**Why/Why not?** Adding indexes on *every* column is a bad practice.
1. **Write Penalty:** Every insert, update, or delete operation requires updating all those indexes, which will drastically slow down write performance (highly detrimental for a notification system with high write volume).
2. **Storage Overhead:** Indexes consume significant disk space and memory. Unnecessary indexes bloat the database size.
3. **Query Planner Confusion:** Too many indexes might confuse the query optimizer, leading to suboptimal query execution plans.

## Query for Placement Notifications in the Last 7 Days
```sql
SELECT DISTINCT studentID
FROM notifications
WHERE notificationType = 'Placement'
  AND createdAt >= NOW() - INTERVAL '7 days';
```

# Stage 4

## Problem
The database is overwhelmed because notifications are fetched on every page load for every student.

## Solutions and Tradeoffs

1. **Implement Caching (Redis/Memcached)**
   Instead of querying the DB on every page load, store the unread count and recent notifications in a fast, in-memory cache like Redis. Invalidate or update the cache when a new notification arrives or when a user reads one.
   * **Tradeoffs:** Increases system complexity. Requires cache invalidation strategies to prevent users from seeing stale data. Additional infrastructure cost.

2. **Client-Side Storage (Local Storage / IndexedDB)**
   Fetch notifications once when the user logs in, store them locally in the browser, and only fetch *new* notifications via a delta endpoint (using a timestamp of the last fetch).
   * **Tradeoffs:** Relies on client capabilities. If the user clears local storage or switches devices, a full fetch is needed again. Can be tricky to synchronize across multiple tabs/devices.

3. **Real-time Push (WebSockets/SSE) Instead of Polling/Page Load Fetches**
   Do not fetch on page load. Instead, the server pushes the unread count/notifications to the client when they connect via WebSocket/SSE and pushes updates in real-time.
   * **Tradeoffs:** Maintaining persistent connections for 50,000 students requires tuning connection limits (e.g., maximum open files) on the server and load balancer. High memory usage for active connections.

**Recommended Approach:** A combination of **Caching (Redis)** for the initial load state and **SSE (Server-Sent Events)** for real-time updates without polling.

# Stage 5

## Shortcomings of the Pseudocode
```python
function notify_all(student_ids: array, message: string):
    for student_id in student_ids:
        send_email(student_id, message) # calls Email API
        save_to_db(student_id, message) # DB insert
        push_to_app(student_id, message)
```
1. **Synchronous Execution:** Sending emails via an external API and pushing notifications are slow, blocking operations. Doing this synchronously in a loop for 50,000 students will cause the request to time out.
2. **Lack of Fault Tolerance:** If `send_email` fails midway (e.g., after 200 students), the loop will throw an exception and terminate. The remaining 49,800 students will not receive the notification or email.
3. **Database Bottleneck:** Firing 50,000 individual `INSERT` statements will overwhelm the database.

## Redesign for Reliability and Fast Execution
Use **Asynchronous Message Queues** (e.g., RabbitMQ, Kafka, or Redis/Celery).
1. The API request should quickly acknowledge receipt.
2. A background worker should generate the notifications.
3. Use **Bulk Inserts** for the database to minimize overhead.
4. Push individual email/app notification tasks to a queue to be processed concurrently with built-in retry mechanisms for failures.

## Should DB Save and Email Send Happen Together?
**No.** They should be decoupled. 
Database saving is an internal system operation that should be fast and bulk-processed. Sending emails relies on external 3rd-party APIs, which have rate limits, latency, and frequent failures. Coupling them means an email API outage prevents users from seeing notifications in the app.

## Revised Pseudocode
```python
function notify_all(student_ids: array, message: string):
    # 1. Bulk insert to DB for high performance
    bulk_save_to_db(student_ids, message)
    
    # 2. Dispatch events to a Message Queue for async processing
    for student_id in student_ids:
        message_queue.publish(
            topic="send_notifications", 
            payload={ "student_id": student_id, "message": message }
        )
    
    return "Notifications queued successfully"

# -- Background Worker Process --
function on_send_notifications_event(payload):
    try:
        push_to_app(payload.student_id, payload.message)
    except AppPushError:
        log_error("App push failed, retrying...")
        message_queue.retry(payload)
        
    try:
        send_email(payload.student_id, payload.message)
    except EmailAPIError:
        log_error("Email failed, retrying...")
        message_queue.retry(payload)
```

# Stage 6

## Approach to Priority Inbox
To efficiently maintain the top 10 most important notifications, I am fetching the notifications from the provided API. I will parse each notification, assign a priority weight based on its `Type` (Placement=3, Result=2, Event=1), and parse the `Timestamp` into a comparable date object. I will then sort the list of notifications first by Weight (descending) and then by Timestamp (descending). Finally, I will slice the top `10` notifications.

**Handling New Incoming Notifications Efficiently:**
If we continuously receive new notifications over an active connection, maintaining a sorted list from scratch is inefficient. Instead, we can maintain a **Min-Heap (Priority Queue) of size 10**. 
- For every new notification, we compare it with the root (minimum element) of the Min-Heap.
- If the new notification has a higher priority than the root, we pop the root and insert the new notification.
- This guarantees O(log 10) -> O(1) time complexity per insertion, which is highly efficient for maintaining a continuous top 10 list.
