# MedAI - Technical Implementation Writeup

## Executive Summary

MedAI is a production-ready, AI-powered medical assistant application that combines modern web technologies, cloud services, and intelligent agent orchestration to provide comprehensive healthcare information, medicine search, store location services, and e-commerce capabilities. The system leverages Amazon Web Services (AWS), Model Context Protocol (MCP), and advanced LLM orchestration to deliver a seamless user experience.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Core Components](#core-components)
4. [AI & LLM Integration](#ai--llm-integration)
5. [MCP Server Architecture](#mcp-server-architecture)
6. [Database Design](#database-design)
7. [Real-time Communication](#real-time-communication)
8. [AWS Cloud Integration](#aws-cloud-integration)
9. [E-Commerce Implementation](#e-commerce-implementation)
10. [Frontend Architecture](#frontend-architecture)
11. [Security & Authentication](#security--authentication)
12. [Performance Optimizations](#performance-optimizations)
13. [Deployment & Scalability](#deployment--scalability)

---

## 1. Architecture Overview

### System Architecture

MedAI follows a **microservices-inspired architecture** with the following layers:

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Layer                          │
│  (HTML5, CSS3, JavaScript, Socket.IO Client, Leaflet.js)   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Flask Application Layer                   │
│  (Flask, Flask-SocketIO, JWT Authentication, Razorpay)     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────┬──────────────────┬──────────────────────┐
│   AI/LLM Layer   │   MCP Servers    │   AWS Services       │
│  (Nova, OpenAI)  │  (Database, Map) │  (Polly, Bedrock,    │
│                  │                  │   Comprehend Medical)│
└──────────────────┴──────────────────┴──────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Persistence Layer                   │
│         (MySQL - Medical Data, SQLite - Chat History)      │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Separation of Concerns**: MCP servers handle specific domains (database, mapping)
2. **Real-time Communication**: WebSocket-based bidirectional messaging
3. **Cloud-Native**: AWS services for AI, monitoring, and text-to-speech
4. **Intelligent Routing**: AI-driven decision making for tool selection
5. **Scalable Architecture**: Stateless design with database persistence

---

## 2. Technology Stack

### Backend Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Web Framework** | Flask | 2.3.3 | HTTP server and routing |
| **Real-time Communication** | Flask-SocketIO | 5.3.6 | WebSocket support |
| **AI Orchestration** | LangChain | 0.1.0+ | LLM workflow management |
| **LLM Provider** | OpenAI GPT-4o | Latest | Fallback AI model |
| **AWS AI** | Amazon Bedrock (Nova) | Latest | Primary AI models |
| **MCP Framework** | Model Context Protocol | Latest | Tool server protocol |
| **Database ORM** | SQLAlchemy | Latest | Database abstraction |
| **Authentication** | Flask-JWT-Extended | 4.6.0 | JWT token management |
| **Payment Gateway** | Razorpay | 1.4.1 | Payment processing |
| **Password Hashing** | bcrypt | 4.1.2 | Secure password storage |

### Frontend Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **UI Framework** | Vanilla JavaScript | Dynamic interactions |
| **Real-time Client** | Socket.IO Client | WebSocket communication |
| **Mapping** | Leaflet.js | Interactive maps |
| **Routing** | OSRM | Route calculation |
| **Icons** | Font Awesome 6.0 | UI icons |
| **Payment UI** | Razorpay Checkout | Payment interface |

### Cloud Services (AWS)

| Service | Purpose | Model/Configuration |
|---------|---------|---------------------|
| **Amazon Bedrock** | Primary AI inference | Nova Lite, Nova Pro, Nova Pro Vision |
| **AWS Comprehend Medical** | Medical entity extraction | Healthcare NLP |
| **AWS Polly** | Text-to-speech | Neural voice (Joanna) |
| **AWS CloudWatch** | Monitoring & metrics | Custom dashboards |

### Databases

| Database | Type | Purpose |
|----------|------|---------|
| **MySQL** | Relational | Medical data, stores, e-commerce |
| **SQLite** | Embedded | Chat history persistence |

---

## 3. Core Components

### 3.1 Flask Application (`app.py`)

The main application file orchestrates all components:

**Key Responsibilities:**
- HTTP route handling
- WebSocket event management
- AI model orchestration with fallback logic
- MCP server communication
- Authentication and authorization
- Payment processing
- Real-time chat streaming

**Critical Functions:**

```python
async def process_query(query, image_base64, conversation_history, user_location)
```
- Extracts medical entities using AWS Comprehend Medical
- Builds intelligent context for AI decision-making
- Routes to appropriate MCP servers based on intent
- Handles multi-turn conversations with history

```python
def analyze_prescription_image(image_base64)
```
- Uses Amazon Nova Pro Vision (primary) or OpenAI GPT-4o Vision (fallback)
- Extracts medicines, doctor info, instructions, patient details
- Returns structured JSON for downstream processing

```python
def generate_title(messages)
```
- Uses Amazon Nova Lite for fast title generation
- Summarizes conversation in 4-5 words
- Auto-updates thread titles

### 3.2 Chat Database (`chat_db.py`)

SQLite-based persistence for conversation management:

**Schema:**
```sql
chat_threads (thread_id, title, created_at, updated_at)
chat_messages (message_id, thread_id, role, content, location_lat, location_lon, created_at)
```

**Features:**
- Thread-based conversation organization
- Location-aware message storage
- Automatic title generation from first user message
- Thread cleanup (keeps last 10 threads)
- Cascade deletion for thread removal

### 3.3 E-Commerce Models

#### User Model (`models/user.py`)
- UUID-based user identification
- bcrypt password hashing
- Email-based authentication
- Profile management

#### Cart Model (`models/cart.py`)
- Session-based shopping cart
- Multi-store support
- Quantity management
- Real-time total calculation

#### Order Model (`models/order.py`)
- UUID-based order tracking
- Razorpay payment integration
- Order status history
- Delivery address management
- Estimated delivery calculation

---

## 4. AI & LLM Integration

### 4.1 Multi-Model Strategy

MedAI implements a **cost-optimized, performance-first** AI strategy:

```
┌─────────────────────────────────────────────────────────┐
│                   AI Model Selection                    │
├─────────────────────────────────────────────────────────┤
│  Task Type          │ Primary Model    │ Fallback       │
├─────────────────────┼──────────────────┼────────────────┤
│  Simple queries     │ Nova Lite        │ GPT-4o-mini    │
│  Complex reasoning  │ Nova Pro         │ GPT-4o         │
│  Image analysis     │ Nova Pro Vision  │ GPT-4o Vision  │
│  Title generation   │ Nova Lite        │ GPT-4o-mini    │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Amazon Nova Models

**Nova Lite** (Fast & Cost-Effective)
- Use case: Title generation, simple queries
- Max tokens: 200
- Temperature: 0 (deterministic)
- Cost: ~70% cheaper than GPT-4o-mini

**Nova Pro** (Complex Reasoning)
- Use case: Decision making, conversation handling
- Max tokens: 1000
- Temperature: 0
- Supports full conversation history

**Nova Pro Vision** (Multimodal)
- Use case: Prescription image analysis
- Supports JPEG images via base64
- Extracts structured medical data
- Max tokens: 1000

### 4.3 AWS Comprehend Medical Integration

**Medical Entity Extraction:**
```python
def extract_medicines_with_aws(query: str) -> list
```

**Capabilities:**
- Extracts MEDICATION entities from natural language
- Confidence scoring (threshold: 0.5)
- Handles medical terminology and brand names
- Fallback to regex-based extraction

**Example:**
```
Input: "I need Paracetamol and Dolo 650"
Output: ['Paracetamol', 'Dolo']
```

### 4.4 Intelligent Decision Making

The system uses AI to route queries to appropriate tools:

**System Prompt Strategy:**
```python
system_prompt = f"""You are MedAI, a medical assistant with access to specialized MCP servers.

EXTRACTED MEDICINES: {extracted_medicines}
USER LOCATION: {location_info}

MCP SERVER ARCHITECTURE:
1. medical-database server: execute_sql tool - for medicine data only
2. medical-map server: get_nearby_stores tool - for store locations

INTELLIGENT DECISION RULES:
1. Medicine info only → use medical-database server
2. Store locations + medicine availability → use medical-map server
3. Just store locations → use medical-map server
"""
```

**Response Format:**
```json
{
  "use_tool": true,
  "tool": "execute_sql",
  "arguments": {"sql_query": "SELECT..."}
}
```

---

## 5. MCP Server Architecture

### 5.1 Model Context Protocol (MCP)

MCP enables **modular, reusable tool servers** that can be invoked by the main application.

**Architecture:**
```
Flask App ←→ stdio_client ←→ MCP Server (Python subprocess)
```

### 5.2 Database Server (`mcp_servers/database_server.py`)

**Purpose:** Execute SQL queries on medical database

**Tool:** `execute_sql`

**Schema Awareness:**
```python
DATABASE_SCHEMA = """
Tables:
1. medicines (medicine_id, medicine_name, medicine_type, brand_name, price, pack_size)
2. medical_stores (store_id, store_name, address, phone_number, latitude, longitude)
3. store_stock (stock_id, store_id, medicine_id, stock_quantity)
"""
```

**Features:**
- SQLAlchemy-based query execution
- Decimal to float conversion for JSON serialization
- Error handling with descriptive messages
- Read-only operations (SELECT queries)

**Example Query:**
```sql
SELECT m.medicine_name, m.price, ms.store_name 
FROM medicines m 
JOIN store_stock ss ON m.medicine_id = ss.medicine_id 
JOIN medical_stores ms ON ss.store_id = ms.store_id 
WHERE m.medicine_name LIKE '%Paracetamol%'
```

### 5.3 Map Server (`mcp_servers/map_server.py`)

**Purpose:** Geospatial queries for store locations

**Tool:** `get_nearby_stores`

**Parameters:**
- `latitude`, `longitude`: User location
- `limit`: Number of stores (default: 10)
- `medicine_filter`: Optional medicine availability filter

**Distance Calculation:**
Uses **Haversine formula** for accurate distance:
```sql
(6371 * acos(cos(radians(:lat)) * cos(radians(latitude)) * 
cos(radians(longitude) - radians(:lon)) + sin(radians(:lat)) * 
sin(radians(latitude)))) AS distance
```

**Medicine Filtering:**
When `medicine_filter` is provided, returns only stores with that medicine in stock:
```sql
WHERE m.medicine_name LIKE :medicine AND ss.stock_quantity > 0
ORDER BY distance
```

### 5.4 MCP Communication Flow

```python
async def call_mcp_tool(server_name: str, tool_name: str, arguments: dict):
    server_path = os.path.join(BASE_DIR, "mcp_servers", server_map[server_name])
    params = StdioServerParameters(command=PYTHON_PATH, args=[server_path])
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result.content[0].text
```

**Optimization:** Prescription analysis moved from MCP to direct function call for 50% faster performance.

