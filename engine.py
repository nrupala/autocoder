"""
AutoCoder Engine v2 - Smart Code Generation
"""

import re
from typing import Dict

class AutoCoderEngine:
    def __init__(self):
        self.provider = "template"
    
    def generate(self, prompt: str, **kwargs) -> str:
        mode = kwargs.get("mode", "standard")
        p = prompt.lower()
        intents = self._detect_intent(p)
        
        if mode == "power":
            return self._minimal(p, intents)
        if mode == "performance":
            return self._detailed(p, intents)
        return self._standard(p, intents)
    
    def _detect_intent(self, p: str) -> Dict:
        return {
            "function": bool(re.search(r"(function|method|def |hello)", p)),
            "class": bool(re.search(r"(class|oop|calculator|user)", p)),
            "struct": bool(re.search(r"(struct|structure)", p)),
            "algorithm": bool(re.search(r"(algorithm|sort|binary|search|merge)", p)),
            "web_api": bool(re.search(r"(api|rest|endpoint|fastapi|flask)", p)),
            "pytest": bool(re.search(r"(pytest|unittest)", p)),
            "test": bool(re.search(r"(test)", p)),
            "docker": bool(re.search(r"(docker|container|dockerfile)", p)),
            "auth": bool(re.search(r"(auth|login|jwt|token)", p)),
            "script": bool(re.search(r"(script|cli|automation)", p)),
            "config": bool(re.search(r"(config|settings|pydantic)", p)),
            "cache": bool(re.search(r"(cache|memoize|redis)", p)),
            "rate": bool(re.search(r"(rate.limit|throttle)", p)),
            "async": bool(re.search(r"(async|aiohttp|await)", p)),
            "http": bool(re.search(r"(http.client|requests|httpx)", p)),
            "retry": bool(re.search(r"(retry|backoff)", p)),
            "logging": bool(re.search(r"(logging|logger)", p)),
            "database": bool(re.search(r"(database|sql|postgres|mysql|mongo)", p)),
            "language": self._detect_language(p),
        }
    
    def _detect_language(self, p: str) -> str:
        # Explicit language - check complete words
        words = p.split()
        
        if "javascript" in p:
            return "javascript"
        if "typescript" in p:
            return "typescript"
        if "golang" in p or "golang" in p:
            return "go"
        if "go" in words or p.startswith("go "):
            return "go"
        if "rust" in words:
            return "rust"
        if "java" in words and "javascript" not in p:
            return "java"
        
        # Framework-based
        if "express" in p or "node" in p:
            return "javascript"
        if "gin" in p:
            return "go"
        
        return "python"
    
    def _minimal(self, p: str, intents: Dict) -> str:
        lang = intents.get("language", "python")
        
        if lang == "python":
            if intents.get("function"): return "def main():\n    print('Hello')"
            if intents.get("class"): return "class Main:\n    pass"
            if intents.get("web_api"): return "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef root(): return {'ok': True}"
            if intents.get("docker"): return "FROM python:3.11-slim\nCMD ['python', 'main.py']"
            if intents.get("test"): return "def test_basic():\n    assert True"
        
        if lang == "javascript":
            if intents.get("function"): return "function main() {\n    console.log('Hello');\n}"
            if intents.get("web_api"): return "const app = require('express')();\napp.get('/', (r, s) => s.json({ok: true}));"
        
        return f"# {lang} - implement"
    
    def _detailed(self, p: str, intents: Dict) -> str:
        return self._standard(p, intents)  # Same as standard for now
    
    def _standard(self, p: str, intents: Dict) -> str:
        lang = intents.get("language", "python")
        
        # Python
        if lang == "python":
            if intents.get("pytest") or intents.get("test") or "pytest" in p or " unittest" in p:
                return self._pytest_basic()
            if intents.get("algorithm") or "sort" in p or "search" in p:
                return self._python_sort()
            if intents.get("function") or "hello" in p:
                return "def hello(name='World'):\n    return f'Hello, {name}!'\n\nif __name__ == '__main__':\n    print(hello())"
            if intents.get("class") or "calculator" in p:
                return self._python_class()
            if intents.get("web_api") or "api" in p or "fastapi" in p:
                return self._fastapi_basic()
            if intents.get("docker"):
                return self._dockerfile()
            if intents.get("auth"):
                return self._auth_basic()
            if intents.get("script"):
                return self._cli_script()
            if intents.get("config") or "config" in p or "settings" in p:
                return self._config_pydantic()
            if intents.get("cache") or "cache" in p:
                return self._cache_decorator()
            if intents.get("rate") or "rate limit" in p or "throttle" in p:
                return self._rate_limiter()
            if intents.get("async") or "aiohttp" in p:
                return self._async_http()
            if intents.get("retry") or "retry" in p:
                return self._retry_decorator()
        
        # JavaScript
        elif lang == "javascript":
            if intents.get("function") or "hello" in p:
                return "function main() {\n    console.log('Hello, World!');\n}\nmain();"
            if intents.get("class") or "calculator" in p:
                return "class Calculator {\n    add(a, b) { return a + b; }\n}\nconst c = new Calculator();\nconsole.log(c.add(2,3));"
            if intents.get("web_api") or "express" in p:
                return self._js_express()
        
        # TypeScript
        elif lang == "typescript":
            return "interface Data {\n    id: string;\n    name: string;\n}\n\nconst getData = (): Data[] => [];"
        
# Go
        elif lang == "go":
            if intents.get("struct"):
                return 'type Data struct {\n    Name string\n    Value int\n}\n\nfunc main() {\n    d := Data{Name: "test", Value: 1}\n    fmt.Println(d)\n}'
            return 'package main\n\nimport "fmt"\n\nfunc main() {\n    fmt.Println("Hello, World!")\n}'
        
        # Rust
        elif lang == "rust":
            if intents.get("struct") or "class" in p:
                return '''struct Calculator {
    result: i32,
}

impl Calculator {
    fn new() -> Self {
        Calculator { result: 0 }
    }
    
    fn add(&mut self, a: i32, b: i32) -> i32 {
        self.result = a + b;
        self.result
    }
}

fn main() {
    let mut calc = Calculator::new();
    println!("Result: {}", calc.add(2, 3));
}'''
            return 'fn main() {\n    println!("Hello, World!");\n}'
        
        # TypeScript
        elif lang == "typescript":
            if intents.get("struct") or "class" in p:
                return '''interface User {
    id: string;
    name: string;
    email?: string;
}

class UserManager {
    private users: User[] = [];
    
    add(user: User): void {
        this.users.push(user);
    }
    
    getAll(): User[] {
        return this.users;
    }
}'''
            return "interface Data {\n    id: string;\n    name: string;\n}\n\nconst getData = (): Data[] => [];"
        
        return "def main():\n    # Your code here\n    pass"
    
    # Templates
    def _python_class(self) -> str:
        return '''class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, x, y):
        self.result = x + y
        return self.result
    
    def subtract(self, x, y):
        self.result = x - y
        return self.result
    
    def multiply(self, x, y):
        self.result = x * y
        return self.result
    
    def divide(self, x, y):
        if y == 0:
            raise ValueError("Cannot divide by zero")
        self.result = x / y
        return self.result

if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(2, 3))'''
    
    def _python_sort(self) -> str:
        return '''def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)

# Test
print(quicksort([3, 6, 8, 10, 1, 2, 1]))'''
    
    def _fastapi_basic(self) -> str:
        return '''from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="AutoCoder API")

class Item(BaseModel):
    name: str
    price: float
    quantity: int = 0

@app.get("/")
def root():
    return {"message": "AutoCoder API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)'''
    
    def _pytest_basic(self) -> str:
        return '''import pytest

def add(a, b):
    return a + b

def test_add_numbers():
    assert add(2, 3) == 5

def test_add_strings():
    assert add("Hello ", "World") == "Hello World"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])'''
    
    def _dockerfile(self) -> str:
        return '''FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000
CMD ["python", "main.py"]'''
    
    def _auth_basic(self) -> str:
        return '''from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta

app = FastAPI()
security = HTTPBearer()
SECRET_KEY = "your-secret-key"

class Token(BaseModel):
    access_token: str
    token_type: str

def create_token(username: str) -> str:
    payload = {"sub": username, "exp": datetime.utcnow() + timedelta(hours=24)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

@app.post("/token")
def login(username: str, password: str):
    token = create_token(username)
    return Token(access_token=token, token_type="bearer")'''
    
    def _cli_script(self) -> str:
        return '''#!/usr/bin/env python3
import argparse

def main():
    parser = argparse.ArgumentParser(description="AutoCoder CLI")
    parser.add_argument("input")
    parser.add_argument("-o", "--output")
    args = parser.parse_args()
    
    result = args.input
    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
    else:
        print(result)

if __name__ == "__main__":
    main()'''
    
    def _config_pydantic(self) -> str:
        return '''from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class Settings(BaseModel):
    """Application settings."""
    app_name: str = "AutoCoder"
    version: str = "1.0.0"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    
    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "autocoder"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Security
    secret_key: str = Field(default="change-me-in-production", min_length=32)
    jwt_expiry_hours: int = 24
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()'''
    
    def _cache_decorator(self) -> str:
        return '''from functools import wraps
from typing import Callable, Any
import time
import hashlib
import json

class Cache:
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def _key(self, *args, **kwargs) -> str:
        key = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, key: str) -> Any:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        if len(self.cache) >= self.max_size:
            oldest = min(self.cache.items(), key=lambda x: x[1][1])
            del self.cache[oldest[0]]
        self.cache[key] = (value, time.time())
    
    def memoize(self, fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = self._key(*args, **kwargs)
            result = self.get(key)
            if result is None:
                result = fn(*args, **kwargs)
                self.set(key, result)
            return result
        return wrapper

cache = Cache()

# Usage: @cache.memoize
def expensive_function(x):
    time.sleep(1)  # simulate work
    return x * 2'''
    
    def _rate_limiter(self) -> str:
        return '''import time
import threading
from collections import deque
from typing import Optional

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, rate: int = 10, per: float = 1.0):
        self.rate = rate  # requests
        self.per = per  # seconds
        self.tokens = rate
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def _refill(self):
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.rate, self.tokens + elapsed * (self.rate / self.per))
        self.last_update = now
    
    def allow(self) -> bool:
        with self.lock:
            self._refill()
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
    
    def wait(self):
        while not self.allow():
            time.sleep(0.01)

limiter = RateLimiter(rate=10, per=1.0)

# Usage
def API_endpoint():
    limiter.wait()
    return {"status": "ok"}'''
    
    def _async_http(self) -> str:
        return '''import aiohttp
import asyncio
from typing import Optional, Dict, Any

class AsyncHTTPClient:
    def __init__(self, base_url: str = "", timeout: int = 30, retries: int = 3):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.retries = retries
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session
    
    async def _request_with_retry(self, method: str, url: str, **kwargs) -> Dict[Any, Any]:
        for attempt in range(self.retries):
            try:
                async with await self._get_session() as session:
                    async with session.request(method, url, **kwargs) as resp:
                        resp.raise_for_status()
                        return await resp.json()
            except Exception as e:
                if attempt == self.retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
        return {}
    
    async def get(self, path: str, **kwargs) -> Dict[Any, Any]:
        url = f"{self.base_url}{path}" if path.startswith("http") else path
        return await self._request_with_retry("GET", url, **kwargs)
    
    async def post(self, path: str, **kwargs) -> Dict[Any, Any]:
        url = f"{self.base_url}{path}" if path.startswith("http") else path
        return await self._request_with_retry("POST", url, **kwargs)
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

# Usage
async def main():
    client = AsyncHTTPClient("https://api.example.com")
    data = await client.get("/data")
    await client.close()

asyncio.run(main())'''
    
    def _retry_decorator(self) -> str:
        return '''import time
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """Retry decorator with exponential backoff."""
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = delay * (backoff ** attempt)
                        logger.warning(f"Attempt {attempt+1} failed: {e}. Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
            raise last_exception
        return wrapper
    return decorator

@retry(max_attempts=3, delay=1.0)
def unstable_api_call():
    # Your flaky API call here
    pass'''
    
    def _js_express(self) -> str:
        return '''const express = require("express");
const cors = require("cors");
const app = express();

app.use(cors());
app.use(express.json());

app.get("/", (req, res) => {
    res.json({ message: "AutoCoder API" });
});

app.get("/api/data", (req, res) => {
    res.json({ data: [] });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server on port ${PORT}`));'''


# Global
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = AutoCoderEngine()
    return _engine

def generate(prompt: str, **kwargs) -> str:
    return get_engine().generate(prompt, **kwargs)
