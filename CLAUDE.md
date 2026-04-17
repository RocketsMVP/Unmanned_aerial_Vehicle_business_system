# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Manage - Enterprise Multi-Agent Platform with RAG capabilities. Python/FastAPI backend with MySQL, Redis, Milvus (vector DB), MinIO (object storage), and Celery (task queue).

## Common Commands

```bash
# Run application (uses uvloop)
python main.py

# Run with custom config
python main.py --config config.yaml


## Architecture

### Directory Structure
```
ai-manage/
├── core/                    # Core framework
│   ├── base/               # Base classes (Assembly, models)
│   ├── intra/              # Internal services (Milvus, Zap logging)
│   └── app/                # Application modules
│       └── system_layer/   # User, Role, Menu, Auth
├── ai_addons/              # AI extensions
│   ├── agent_core/         # Agent core (routes, groups, LLM chat)
│   ├── knowledge_base/     # RAG (Milvus, retrieval)
│   ├── llm_config/         # LLM configuration
│   ├── task_queue/         # Celery tasks (document processing, embedding)
│   └── workflow/           # Workflow engine
├── tests/                  # Pytest test cases
├── main.py                 # Entry point (uvloop + uvicorn)
├── config.yaml             # Configuration
└── docker-compose.yml      # Full stack deployment
```

### Key Layers (per module)
```
module/
├── route/                  # FastAPI routers + Router classes
├── service/                # Business logic (Service classes)
├── models/                 # SQLAlchemy models
│   ├── request/           # Pydantic request schemas
│   └── response/           # Pydantic response schemas
└── source/                # Data initialization
```

### Base Classes
- `base.Assembly`: Base service class providing `get_db()`, `success_correctly_data()`, `fail_correctly()`, logging via `self.S()`
- `base.models.Model`: Base SQLAlchemy model with `model_creator()` and `model_creator_fields()` utilities

### Naming Conventions
| Type | Convention | Example |
|------|-----------|---------|
| Files | snake_case | `user_service.py` |
| Classes | PascalCase | `UserService`, `MenuRouter` |
| Service instances | snake_case | `user_service` |
| Private methods | `_prefix` | `_validate_input()` |

### CRUD Pattern (see `core/app/system_layer/route/menu.py`)
```python
# Route class extends base.Assembly, creates router in __init__
class MenuRouter(base.Assembly):
    def __init__(self):
        self.router = APIRouter(prefix="/menu", tags=["菜单管理"])
        self._setup_routes()

    def _setup_routes(self):
        @self.router.post("/create")   # Full path: POST /menu/create
        @self.router.get("/list")     # Full path: GET /menu/list
        @self.router.get("/tree")     # Tree structure
        @self.router.get("/{id}")     # Detail
        @self.router.put("/update")
        @self.router.delete("/delete")
```

### Service Layer Pattern
```python
class MenuService(base.Assembly):
    async def get_menu_list(self, info: request.MenuSearch):
        async with self.get_db() as session:
            db = select(Menu)
            # ... filters
            return data.all(), count
```

## Configuration

All config in `config.yaml` and environment variables. Key settings:
- `system.host`, `system.port` (default 9088)
- `mysql.*`, `redis.*`, `minio.*`
- Environment variables override config values

