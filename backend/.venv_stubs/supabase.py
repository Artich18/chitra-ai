"""Minimal Supabase REST API client using raw HTTP requests."""
from __future__ import annotations

import requests
import json


class _TableQuery:
    def __init__(self, client, table, method="select"):
        self._client = client
        self._table = table
        self._method = method
        self._filters = {}
        self._columns = "*"
        self._limit = 1000
        self._order = None
        self._count = None
        self._data = None

    def select(self, columns="*", count=None, head=False):
        self._columns = columns
        self._count = count
        self._head = head
        return self

    def insert(self, data):
        self._method = "insert"
        self._data = data
        return self

    def update(self, data):
        self._method = "update"
        self._data = data
        return self

    def delete(self):
        self._method = "delete"
        return self

    def upsert(self, data):
        self._method = "upsert"
        self._data = data
        return self

    def eq(self, col, val):
        self._filters[col] = val
        return self

    def order(self, col, desc=False):
        self._order = f"{col}.desc" if desc else f"{col}.asc"
        return self

    def limit(self, n):
        self._limit = n
        return self

    def execute(self):
        url = f"{self._client._url}/rest/v1/{self._table}"
        headers = {
            "apikey": self._client._key,
            "Authorization": f"Bearer {self._client._key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

        if self._method == "select":
            params = {"select": self._columns}
            if self._count:
                params["count"] = self._count
                headers["Prefer"] = "count=exact"
            for col, val in self._filters.items():
                params[f"{col}"] = f"eq.{val}"
            if self._order:
                params["order"] = self._order
            if self._limit:
                params["limit"] = self._limit
            if self._head:
                resp = requests.head(url, headers=headers, params=params, timeout=30)
            else:
                resp = requests.get(url, headers=headers, params=params, timeout=30)
            count = None
            if resp.headers.get("content-range"):
                parts = resp.headers["content-range"].split("/")
                if len(parts) > 1:
                    count = int(parts[1])
            if resp.status_code == 200:
                return _Response(resp.json(), count=count)
            return _Response([])

        elif self._method in ("insert", "upsert"):
            if self._method == "upsert":
                headers["Prefer"] = "resolution=merge-duplicates,return=representation"
            else:
                headers["Prefer"] = "return=representation"
            payload = self._data if isinstance(self._data, list) else [self._data]
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code in (200, 201):
                return _Response(resp.json())
            return _Response([])

        elif self._method == "update":
            headers["Prefer"] = "return=representation"
            params = {}
            for col, val in self._filters.items():
                params[f"{col}"] = f"eq.{val}"
            resp = requests.patch(url, headers=headers, params=params, json=self._data, timeout=30)
            if resp.status_code in (200, 204):
                return _Response(resp.json() if resp.text else [])
            return _Response([])

        elif self._method == "delete":
            params = {}
            for col, val in self._filters.items():
                params[f"{col}"] = f"eq.{val}"
            resp = requests.delete(url, headers=headers, params=params, timeout=30)
            if resp.status_code in (200, 204):
                return _Response(resp.json() if resp.text else [])
            return _Response([])

        return _Response([])


class _Table:
    def __init__(self, client, table):
        self._client = client
        self._table = table

    def select(self, columns="*", count=None, head=False):
        return _TableQuery(self._client, self._table, "select").select(columns, count, head)

    def insert(self, data):
        return _TableQuery(self._client, self._table, "insert").insert(data)

    def update(self, data):
        return _TableQuery(self._client, self._table, "update").update(data)

    def delete(self):
        return _TableQuery(self._client, self._table, "delete")

    def upsert(self, data):
        return _TableQuery(self._client, self._table, "upsert").upsert(data)


class _Response:
    def __init__(self, data, count=None):
        self.data = data
        self.count = count


class Client:
    def __init__(self, url: str, key: str):
        self._url = url.rstrip("/")
        self._key = key

    def table(self, name: str):
        return _Table(self, name)


def create_client(url: str, key: str) -> Client:
    return Client(url, key)
